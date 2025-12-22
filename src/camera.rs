use image::RgbImage;
use nokhwa::{
    pixel_format::RgbFormat,
    utils::{CameraIndex, RequestedFormat, RequestedFormatType},
    Camera,
    nokhwa_initialize, query,
};
use std::sync::mpsc::{channel, Receiver, TryRecvError};
use std::thread;

pub struct CameraWorker {
    rx: Receiver<RgbImage>,
}

pub fn get_available_cameras() -> Vec<(usize, String)> {
    let _ = nokhwa_initialize(|_| {});
    match query(nokhwa::utils::ApiBackend::Auto) {
        Ok(cameras) => {
            cameras.into_iter().enumerate().map(|(i, info)| {
                (i, info.human_name())
            }).collect()
        }
        Err(e) => {
            eprintln!("Failed to query cameras: {}", e);
            vec![]
        }
    }
}

impl CameraWorker {
    pub fn new(index: usize, use_max_res: bool) -> Self {
        let (tx, rx) = channel();

        thread::spawn(move || {
            let index = CameraIndex::Index(index as u32);
            
            let attempts = if use_max_res {
                 vec![
                    // 1. Explicitly ask for highest resolution
                    RequestedFormat::new::<RgbFormat>(RequestedFormatType::HighestResolution(nokhwa::utils::Resolution::new(3840, 2160))), // Hint 4K
                    RequestedFormat::new::<RgbFormat>(RequestedFormatType::HighestResolution(nokhwa::utils::Resolution::new(1920, 1080))),
                ]
            } else {
                 vec![
                    // 1. Try 720p MJPEG (Good for modern webcams)
                    RequestedFormat::new::<RgbFormat>(RequestedFormatType::Closest(
                        nokhwa::utils::CameraFormat::new_from(1280, 720, nokhwa::utils::FrameFormat::MJPEG, 30)
                    )),
                    // 2. Try 720p YUYV (Another common format)
                    RequestedFormat::new::<RgbFormat>(RequestedFormatType::Closest(
                        nokhwa::utils::CameraFormat::new_from(1280, 720, nokhwa::utils::FrameFormat::YUYV, 30)
                    )),
                 ]
            };
            
            // Backup catch-all
            let mut final_attempts = attempts;
            final_attempts.push(RequestedFormat::new::<RgbFormat>(RequestedFormatType::AbsoluteHighestFrameRate));

            let mut camera = None;

            for req in final_attempts {
                if let Ok(mut cam) = Camera::new(index.clone(), req) {
                     if let Ok(_) = cam.open_stream() {
                         camera = Some(cam);
                         break;
                     }
                }
            }

            let mut camera = match camera {
                Some(c) => c,
                None => {
                    eprintln!("Failed to open camera with any known config.");
                    return;
                }
            };

            loop {
                match camera.frame() {
                    Ok(frame) => {
                        // Decode to whatever version nokhwa uses
                        if let Ok(decoded) = frame.decode_image::<RgbFormat>() {
                            let width = decoded.width();
                            let height = decoded.height();
                            let raw = decoded.into_raw();
                            
                            // Reconstruct using our version of 'image'
                            if let Some(buf) = RgbImage::from_raw(width, height, raw) {
                                if tx.send(buf).is_err() {
                                    break; 
                                }
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!("Failed to get frame: {}", e);
                        thread::sleep(std::time::Duration::from_millis(100));
                    }
                }
            }
        });

        Self { rx }
    }

    pub fn poll(&self) -> Option<RgbImage> {
        match self.rx.try_recv() {
            Ok(frame) => Some(frame),
            Err(TryRecvError::Empty) => None,
            Err(TryRecvError::Disconnected) => None,
        }
    }
}
