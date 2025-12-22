mod camera;
mod processor;
use camera::CameraWorker;
use processor::{Processor, Scorer, DetectionResult};
use eframe::egui;
use egui::ColorImage;

fn main() -> eframe::Result<()> {
    env_logger::init(); 

    let options = eframe::NativeOptions::default();
    eframe::run_native(
        "Precision Scorer",
        options,
        Box::new(|_cc| Box::new(MyApp::new())),
    )
}

struct MyApp {
    camera: CameraWorker,
    processor: Processor,
    scorer: Scorer,
    texture: Option<egui::TextureHandle>,
    last_detection: Option<DetectionResult>,
    
    // Camera Selection State
    available_cameras: Vec<(usize, String)>,
    selected_camera_index: usize,
    use_max_resolution: bool,
    
    // Snapshot State
    is_frozen: bool,
    
    // Static Image State
    source_mode: SourceMode,
    loaded_image: Option<image::RgbImage>,
    reprocess_requested: bool,
    
    // View Options
    scale_to_fit: bool,
}

#[derive(PartialEq)]
enum SourceMode {
    Camera,
    Image,
}

impl MyApp {
    fn new() -> Self {
        let available = camera::get_available_cameras();
        // Default to 0, or if empty, 0 (will fail gracefully later)
        let selected = 0;
        
        Self {
            camera: CameraWorker::new(selected, false),
            processor: Processor::new(),
            scorer: Scorer::new(),
            texture: None,
            last_detection: None,
            available_cameras: available,
            selected_camera_index: selected,
            use_max_resolution: false,
            is_frozen: false,
            scale_to_fit: true,
            source_mode: SourceMode::Camera,
            loaded_image: None,
            reprocess_requested: false,
        }
    }
}

impl eframe::App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        let mut image_buffer_to_process: Option<image::RgbImage> = None;

        match self.source_mode {
            SourceMode::Camera => {
                 // Poll camera only if not frozen
                if !self.is_frozen {
                    if let Some(buf) = self.camera.poll() {
                        image_buffer_to_process = Some(buf);
                    }
                }
            },
            SourceMode::Image => {
                 if let Some(img) = &self.loaded_image {
                     if self.reprocess_requested {
                        image_buffer_to_process = Some(img.clone());
                        self.reprocess_requested = false;
                     }
                 }
            }
        }

        if let Some(image_buffer) = image_buffer_to_process {
             // 1. Process
             if let Some(detection) = self.processor.process(&image_buffer) {
                 self.scorer.update(&detection);
                 self.last_detection = Some(detection);
             }

             // 2. Convert to UI Texture
             let size = [image_buffer.width() as usize, image_buffer.height() as usize];
             let pixels = image_buffer.into_raw();
             let color_image = ColorImage::from_rgb(size, &pixels);
             
             self.texture = Some(ctx.load_texture(
                 "camera-frame",
                 color_image,
                 egui::TextureOptions::default(),
             ));
        }

        egui::SidePanel::left("options_panel").show(ctx, |ui| {
            ui.heading("Settings");
            ui.separator();
            
            // Source Selection
            ui.label("Source Mode");
            if ui.radio_value(&mut self.source_mode, SourceMode::Camera, "Live Camera").changed() {
                 self.reprocess_requested = true;
            }
            if ui.radio_value(&mut self.source_mode, SourceMode::Image, "Static Image").changed() {
                 self.reprocess_requested = true;
            }
            
            ui.separator();
            
            match self.source_mode {
                SourceMode::Camera => {
                    // Camera Selection
                    ui.label("Camera Source");
                    let previous_selection = self.selected_camera_index;
                    egui::ComboBox::from_id_source("camera_selector")
                        .selected_text(
                            self.available_cameras
                                .iter()
                                .find(|(i, _)| *i == self.selected_camera_index)
                                .map(|(_, name)| name.as_str())
                                .unwrap_or("Unknown")
                        )
                        .show_ui(ui, |ui| {
                            for (index, name) in &self.available_cameras {
                                ui.selectable_value(&mut self.selected_camera_index, *index, name);
                            }
                        });
                    
                    if previous_selection != self.selected_camera_index {
                        // Re-initialize camera
                        self.camera = CameraWorker::new(self.selected_camera_index, self.use_max_resolution);
                    }
                    
                    if ui.checkbox(&mut self.use_max_resolution, "Use Max Resolution").changed() {
                         // Re-initialize camera
                         self.camera = CameraWorker::new(self.selected_camera_index, self.use_max_resolution);
                    }
                },
                SourceMode::Image => {
                    if ui.button("📂 Open Image...").clicked() {
                        if let Some(path) = rfd::FileDialog::new()
                            .add_filter("images", &["png", "jpg", "jpeg", "bmp"])
                            .pick_file() 
                        {
                            if let Ok(img) = image::open(&path) {
                                self.loaded_image = Some(img.to_rgb8());
                                self.reprocess_requested = true;
                                // Reset scorer when loading new image? Maybe optional.
                                // self.scorer.reset(); 
                            } else {
                                eprintln!("Failed to load image: {:?}", path);
                            }
                        }
                    }
                }
            }
            
            ui.separator();
            ui.label("View Options");
            ui.checkbox(&mut self.scale_to_fit, "Scale to Fit Window");
            
            ui.separator();

            ui.label("Threshold (0-255)");
            if ui.add(egui::Slider::new(&mut self.processor.threshold_value, 0..=255).text("Darkness")).changed() {
                self.reprocess_requested = true;
            }

            ui.label("Hole Radius (px)");
            if ui.add(egui::Slider::new(&mut self.processor.min_hole_radius, 1.0..=10.0).text("Min")).changed() {
                 self.reprocess_requested = true;
            }
            if ui.add(egui::Slider::new(&mut self.processor.max_hole_radius, 5.0..=50.0).text("Max")).changed() {
                 self.reprocess_requested = true;
            }
            
            ui.separator();
            ui.heading("Actions");
            
            if ui.button(if self.is_frozen { "▶ Resume Feed" } else { "⏸ Snapshot / Freeze" }).clicked() {
                self.is_frozen = !self.is_frozen;
            }
            
            if ui.button("Reset Score").clicked() {
                self.scorer.reset();
            }
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("Precision Scorer");
            ui.horizontal(|ui| {
                ui.label(format!("Total Score: {}", self.scorer.total_score));
                if let Some(last) = self.scorer.last_shot_score {
                    ui.label(format!("  Last Shot: +{}", last));
                }
            });
            ui.separator();
            
            if let Some(texture) = &self.texture {
                let image_size = texture.size_vec2();
                
                let show_image = |ui: &mut egui::Ui| -> egui::Response {
                    if self.scale_to_fit {
                         // Shrink to fit available space, maintain aspect ratio
                         ui.add(
                            egui::Image::new((texture.id(), image_size)).shrink_to_fit()
                         )
                    } else {
                        // show actual size
                        ui.add(
                            egui::Image::new((texture.id(), image_size))
                        )
                    }
                };

                // If not scaling to fit, we might need scrollbars
                let response = if !self.scale_to_fit {
                     egui::ScrollArea::both()
                        .show(ui, |ui| show_image(ui))
                        .inner
                } else {
                    show_image(ui)
                };

                let rect = response.rect;
                
                // Calculate scale factors
                let scale_x = rect.width() / image_size.x;
                let scale_y = rect.height() / image_size.y;
                
                if let Some(detection) = &self.last_detection {
                     let painter = ui.painter();
                     let to_screen = |x: f32, y: f32| -> egui::Pos2 {
                         rect.min + egui::vec2(x * scale_x, y * scale_y)
                     };

                     // Draw holes
                     for (x, y, r) in &detection.holes {
                         painter.circle_stroke(
                             to_screen(*x, *y), 
                             *r * scale_x.max(scale_y), // Scale radius too
                             egui::Stroke::new(2.0, egui::Color32::RED)
                         );
                     }
                     
                     // Draw center
                     let (tx, ty) = detection.target_center;
                     painter.circle_filled(
                         to_screen(tx as f32, ty as f32), 
                         5.0, 
                         egui::Color32::GREEN
                     );
                }
            } else {
                ui.label("Waiting for camera...");
                ui.spinner();
            }
        });
        
        ctx.request_repaint();
    }
}
