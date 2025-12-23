use image::{GrayImage, ImageBuffer, Rgb, Luma};
use imageproc::contours::find_contours;
use imageproc::point::Point;

#[derive(Clone, Debug)]
pub struct DetectionResult {
    pub target_center: (u32, u32),
    pub holes: Vec<(f32, f32, f32)>, // x, y, radius
}

pub struct Processor {
    pub threshold_value: u8,
    pub min_hole_radius: f32,
    pub max_hole_radius: f32,
    pub min_circularity: f32,
}

impl Processor {
    pub fn new() -> Self {
        Self {
            threshold_value: 100,
            min_hole_radius: 2.0,
            max_hole_radius: 20.0,
            min_circularity: 0.7, // 0.0 to 1.0 (1.0 is perfect circle)
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
            // Filter by point count (noise)
            if contour.points.len() > 10 && contour.points.len() < 500 {
                
                // Calculate Circularity
                let area = polygon_area(&contour.points);
                let perimeter = polygon_perimeter(&contour.points);
                
                // Avoid division by zero
                if perimeter > 0.0 {
                    let circularity = (4.0 * std::f32::consts::PI * area) / (perimeter * perimeter);
                    
                    if circularity < self.min_circularity {
                        continue;
                    }
                } else {
                    continue;
                }

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
                
                // Approximate radius based on Area (more robust than count)
                // Area = PI * r^2  =>  r = sqrt(Area / PI)
                let radius = (area / std::f32::consts::PI).sqrt();
                
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

// Shoelace Formula
fn polygon_area(points: &[Point<i32>]) -> f32 {
    let n = points.len();
    let mut area: f32 = 0.0;
    for i in 0..n {
        let j = (i + 1) % n;
        area += (points[i].x * points[j].y) as f32;
        area -= (points[j].x * points[i].y) as f32;
    }
    area.abs() / 2.0
}

fn polygon_perimeter(points: &[Point<i32>]) -> f32 {
    let mut perimeter = 0.0;
    for i in 0..points.len() {
        let p1 = points[i];
        let p2 = points[(i + 1) % points.len()];
        let dx = (p2.x - p1.x) as f32;
        let dy = (p2.y - p1.y) as f32;
        perimeter += (dx*dx + dy*dy).sqrt();
    }
    perimeter
}

pub struct ScoringConfig {
    pub target_diameter_mm: f32, // 154.4 for 50m Rifle
    pub ring_10_diameter_mm: f32, // 10.4
    pub bullet_diameter_mm: f32, // 4.5
    pub pixels_per_mm: f32,      // Calibration factor
}

impl ScoringConfig {
    pub fn default_50m_rifle() -> Self {
        Self {
            target_diameter_mm: 154.4,
            ring_10_diameter_mm: 10.4,
            bullet_diameter_mm: 4.5,
            pixels_per_mm: 10.0, // Default guess, needs calibration
        }
    }
}

pub struct Scorer {
    known_holes: Vec<(f32, f32)>,
    pub total_score: f32, // Changed to f32 for decimal scoring
    pub last_shot_score: Option<f32>,
    pub config: ScoringConfig,
}

impl Scorer {
    pub fn new() -> Self {
        Self {
            known_holes: Vec::new(),
            total_score: 0.0,
            last_shot_score: None,
            config: ScoringConfig::default_50m_rifle(),
        }
    }

    pub fn reset(&mut self) {
        self.known_holes.clear();
        self.total_score = 0.0;
        self.last_shot_score = None;
    }

    pub fn update(&mut self, detection: &DetectionResult) {
        let (tx, ty) = detection.target_center;
        
        // Differential logic: Find NEW holes
        for (hx, hy, _hr) in &detection.holes {
            let mut is_new = true;
            for (kx, ky) in &self.known_holes {
                let dist = ((hx - kx).powi(2) + (hy - ky).powi(2)).sqrt();
                if dist < 10.0 { // Tolerance in pixels
                    is_new = false;
                    break;
                }
            }
            
            if is_new {
                self.known_holes.push((*hx, *hy));
                
                // Calculate Score
                let dist_px = ((*hx - tx as f32).powi(2) + (*hy - ty as f32).powi(2)).sqrt();
                let dist_mm = dist_px / self.config.pixels_per_mm;
                
                // Effective distance (edge of bullet closest to center)
                // In ISSF, if the bullet TOUCHES the higher ring, you get the score.
                // So we subtract the bullet radius to find the inner edge.
                let bullet_radius_mm = self.config.bullet_diameter_mm / 2.0;
                let effective_dist_mm = (dist_mm - bullet_radius_mm).max(0.0);
                
                // Simplified Decimal Scoring for 50m Rifle
                // Ring 10 (10.4mm diam) -> Radius 5.2mm
                // If effective_dist_mm <= 5.2, it's a 10.
                // But we want 10.0 to 10.9.
                // Center shot (dist 0) = 10.9
                // Edge of 10 ring (dist 5.2) = 10.0
                // Linear drop off?
                // Ring widths are typically 8mm for 50m rifle (Ring 9 diam 26.4, Ring 8 diam 42.4...)
                // Let's use a simplified linear model for prototype:
                // Score = 11.0 - (EffectiveDist / RingWidth)
                // Assuming ring width approx 8mm.
                let ring_width_mm = 8.0; 
                let score = 11.0 - (effective_dist_mm / ring_width_mm);
                let score = score.clamp(0.0, 10.9);
                // Round to 1 decimal
                let score = (score * 10.0).round() / 10.0;
                
                self.total_score += score; 
                self.last_shot_score = Some(score);
            }
        }
    }
}

