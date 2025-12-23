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
    
    // ROI State (Margins in pixels)
    crop_left: u32,
    crop_right: u32,
    crop_top: u32,
    crop_bottom: u32,
    
    // Alignment State
    manual_center: Option<(f32, f32)>, // Relative to cropped image
    show_rings: bool,

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
            crop_left: 0,
            crop_right: 0,
            crop_top: 0,
            crop_bottom: 0,
            manual_center: None,
            show_rings: true,
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

        if let Some(mut image_buffer) = image_buffer_to_process {
             // Apply Cropping / ROI
             // Calculate valid crop region
             let width = image_buffer.width();
             let height = image_buffer.height();
             
             // Ensure we don't crop everything
             if self.crop_left + self.crop_right < width && self.crop_top + self.crop_bottom < height {
                 let new_width = width - self.crop_left - self.crop_right;
                 let new_height = height - self.crop_top - self.crop_bottom;
                 
                 // Perform crop
                 let cropped = image::imageops::crop(&mut image_buffer, self.crop_left, self.crop_top, new_width, new_height);
                 image_buffer = cropped.to_image();
             }

             // 1. Process
             if let Some(mut detection) = self.processor.process(&image_buffer) {
                 // Override center if manual is set
                 let (cx, cy) = if let Some((mx, my)) = self.manual_center {
                     (mx as u32, my as u32)
                 } else {
                     detection.target_center
                 };
                 detection.target_center = (cx, cy);
                 
                 // Filter detections outside the target paper (plus margin)
                 // Target Diameter 154.4mm. Let's allow 1.5x margin just in case.
                 let ppm = self.scorer.config.pixels_per_mm;
                 let max_radius_mm = (self.scorer.config.target_diameter_mm / 2.0) * 1.5;
                 let max_radius_px = max_radius_mm * ppm;
                 
                 detection.holes.retain(|(hx, hy, _)| {
                     let dist = ((*hx - cx as f32).powi(2) + (*hy - cy as f32).powi(2)).sqrt();
                     dist <= max_radius_px
                 });
                 
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
            ui.label("ROI / Cropping (px)");
            if ui.add(egui::Slider::new(&mut self.crop_left, 0..=300).text("Left")).changed() { self.reprocess_requested = true; }
            if ui.add(egui::Slider::new(&mut self.crop_right, 0..=300).text("Right")).changed() { self.reprocess_requested = true; }
            if ui.add(egui::Slider::new(&mut self.crop_top, 0..=300).text("Top")).changed() { self.reprocess_requested = true; }
            if ui.add(egui::Slider::new(&mut self.crop_bottom, 0..=300).text("Bottom")).changed() { self.reprocess_requested = true; }

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
            
            ui.label("Filter Shape");
            if ui.add(egui::Slider::new(&mut self.processor.min_circularity, 0.0..=1.0).text("Min Circularity")).changed() {
                 self.reprocess_requested = true;
            }
            
            ui.separator();
            ui.label("Visual Alignment");
            ui.checkbox(&mut self.show_rings, "Show Scoring Rings");
            if ui.button("Reset Target Center").clicked() {
                self.manual_center = None;
                if self.source_mode == SourceMode::Image {
                    self.scorer.reset();
                    self.reprocess_requested = true;
                }
            }
            ui.label("Right-click image to set center!");
            
            ui.separator();
            ui.label("Calibration");
            ui.label(format!("Pixels per mm: {:.2}", self.scorer.config.pixels_per_mm));
            if ui.add(egui::Slider::new(&mut self.scorer.config.pixels_per_mm, 1.0..=50.0).text("Px/mm")).changed() {
                 // Recalculate all scores? 
                 // For now, new calibration only affects NEW shots unless we re-score everything.
                 // Ideally we'd store raw hole positions and re-score on change.
                 // But for prototype, just allow adjustment.
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
                ui.label(format!("Total Score: {:.1}", self.scorer.total_score));
                if let Some(last) = self.scorer.last_shot_score {
                    ui.label(format!("  Last Shot: +{:.1}", last));
                }
            });
            ui.separator();
            
            if let Some(texture) = &self.texture {
                let image_size = texture.size_vec2();
                
                let show_image = |ui: &mut egui::Ui| -> egui::Response {
                    if self.scale_to_fit {
                         // Shrink to fit available space, maintain aspect ratio
                         ui.add(
                            egui::Image::new((texture.id(), image_size))
                                .shrink_to_fit()
                                .sense(egui::Sense::click())
                         )
                    } else {
                        // show actual size
                        ui.add(
                            egui::Image::new((texture.id(), image_size))
                                .sense(egui::Sense::click())
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
                     
                     // Determine Center (Manual or Auto)
                     let (cx, cy) = self.manual_center.unwrap_or((
                         detection.target_center.0 as f32, 
                         detection.target_center.1 as f32
                     ));
                     
                     // Handle Clicks to set Center (Right Click)
                     if response.clicked_by(egui::PointerButton::Secondary) {
                        if let Some(pos) = response.interact_pointer_pos() {
                            let rel_x = (pos.x - rect.min.x) / scale_x;
                            let rel_y = (pos.y - rect.min.y) / scale_y;
                            self.manual_center = Some((rel_x, rel_y));
                            
                            // Trigger Re-score if static
                            if self.source_mode == SourceMode::Image {
                                self.scorer.reset();
                                self.reprocess_requested = true;
                            }
                        }
                     }

                     // Draw holes
                     for (x, y, r) in &detection.holes {
                         painter.circle_stroke(
                             to_screen(*x, *y), 
                             *r * scale_x.max(scale_y), 
                             egui::Stroke::new(2.0, egui::Color32::RED)
                         );
                     }
                     
                     // Draw Center
                     painter.circle_filled(
                         to_screen(cx, cy), 
                         5.0, 
                         egui::Color32::GREEN
                     );
                     
                     // Draw Rings
                     if self.show_rings {
                         let ppm = self.scorer.config.pixels_per_mm;
                         // 50m Rifle Rings (Diameter -> Radius)
                         // 10: 10.4mm -> 5.2
                         // 9: 26.4 -> 13.2
                         // 8: 42.4 -> 21.2
                         // ... steps of 16mm diam (8mm radius) usually
                         let ring_radii_mm = [
                             5.2,   // 10
                             13.2,  // 9
                             21.2,  // 8
                             29.2,  // 7
                             37.2,  // 6
                             45.2,  // 5
                             53.2,  // 4
                         ];
                         
                         for (i, r_mm) in ring_radii_mm.iter().enumerate() {
                             let r_px = r_mm * ppm;
                             painter.circle_stroke(
                                 to_screen(cx, cy),
                                 r_px * scale_x.max(scale_y),
                                 egui::Stroke::new(1.0, egui::Color32::from_rgba_unmultiplied(0, 255, 0, 100))
                             );
                         }
                     }
                }
            } else {
                ui.label("Waiting for camera...");
                ui.spinner();
            }
        });
        
        ctx.request_repaint();
    }
}
