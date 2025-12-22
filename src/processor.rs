use image::{GrayImage, ImageBuffer, Rgb, Luma};
use imageproc::contours::find_contours;

#[derive(Clone, Debug)]
pub struct DetectionResult {
    pub target_center: (u32, u32),
    pub holes: Vec<(f32, f32, f32)>, // x, y, radius
}

pub struct Processor {
    pub threshold_value: u8,
    pub min_hole_radius: f32,
    pub max_hole_radius: f32,
}

impl Processor {
    pub fn new() -> Self {
        Self {
            threshold_value: 100,
            min_hole_radius: 2.0,
            max_hole_radius: 20.0,
        }
    }

    pub fn process(&self, frame: &ImageBuffer<Rgb<u8>, Vec<u8>>) -> Option<DetectionResult> {
        let gray: GrayImage = image::imageops::grayscale(frame);
        
        // Thresholding
        let binary = image::ImageBuffer::from_fn(gray.width(), gray.height(), |x, y| {
            let p = gray.get_pixel(x, y)[0];
            if p < self.threshold_value {
                Luma([255u8]) // Hole
            } else {
                Luma([0u8])   // Background
            }
        });

        let contours = find_contours::<i32>(&binary);
        
        let mut holes = Vec::new();
        let target_center = (frame.width() / 2, frame.height() / 2); // Default to center

        for contour in contours {
            // Filter by bounding box
            if contour.points.len() > 10 && contour.points.len() < 500 {
                // Calculate centroid
                let mut sum_x = 0.0;
                let mut sum_y = 0.0;
                for p in &contour.points {
                    sum_x += p.x as f32;
                    sum_y += p.y as f32;
                }
                let count = contour.points.len() as f32;
                let cx = sum_x / count;
                let cy = sum_y / count;
                
                // Approximate radius
                let radius = (count / std::f32::consts::PI).sqrt();
                
                if radius >= self.min_hole_radius && radius <= self.max_hole_radius {
                    holes.push((cx, cy, radius));
                }
            }
        }



        Some(DetectionResult {
            target_center,
            holes,
        })
    }
}

pub struct Scorer {
    known_holes: Vec<(f32, f32)>,
    pub total_score: u32,
    pub last_shot_score: Option<u32>,
}

impl Scorer {
    pub fn new() -> Self {
        Self {
            known_holes: Vec::new(),
            total_score: 0,
            last_shot_score: None,
        }
    }

    pub fn reset(&mut self) {
        self.known_holes.clear();
        self.total_score = 0;
        self.last_shot_score = None;
    }

    pub fn update(&mut self, detection: &DetectionResult) {
        // Differential logic: Find NEW holes
        for (hx, hy, _hr) in &detection.holes {
            let mut is_new = true;
            for (kx, ky) in &self.known_holes {
                let dist = ((hx - kx).powi(2) + (hy - ky).powi(2)).sqrt();
                if dist < 10.0 { // Tolerance
                    is_new = false;
                    break;
                }
            }
            
            if is_new {
                self.known_holes.push((*hx, *hy));
                // Dummy score calculation based on distance to center
                // Real implementation would map radius to rings
                self.total_score += 10; 
                self.last_shot_score = Some(10);
            }
        }
    }
}

