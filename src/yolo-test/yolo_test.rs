use anyhow::Result;
use image::GenericImageView;
use ndarray::Array;
use ort::{GraphOptimizationLevel, Session};
use std::path::Path;

fn main() -> Result<()> {
    println!("Starting YOLO ONNX Runtime Test...");

    // 1. Load ONNX Model
    let model_path = "yolo/yolo12x.onnx";
    if !Path::new(model_path).exists() {
        anyhow::bail!("Model file not found at: {}", model_path);
    }

    println!("Loading model: {}", model_path);
    let session = Session::builder()?
        .with_optimization_level(GraphOptimizationLevel::Level3)?
        .with_intra_threads(4)?
        .commit_from_file(model_path)?;

    println!("Model loaded successfully!");

    // 2. Load and preprocess image
    let img_path = "C:/Users/mbord/.gemini/antigravity/brain/57903aa7-65ed-41e6-af5e-3e9ea55e5cec/uploaded_image_1766454700360.png";
    if !Path::new(img_path).exists() {
        println!("Test image not found, skipping inference.");
        return Ok(());
    }

    let original_image = image::open(img_path)?;
    let (width, height) = original_image.dimensions();
    println!("Image loaded: {}x{}", width, height);

    // 3. Preprocess: Resize to 640x640 and normalize
    let img = original_image.resize_exact(640, 640, image::imageops::FilterType::Triangle);
    let img_rgb = img.to_rgb8();
    
    // Convert to ndarray [1, 3, 640, 640] with normalization
    let mut input_array = Array::zeros((1, 3, 640, 640));
    for y in 0..640 {
        for x in 0..640 {
            let pixel = img_rgb.get_pixel(x, y);
            input_array[[0, 0, y as usize, x as usize]] = pixel[0] as f32 / 255.0;
            input_array[[0, 1, y as usize, x as usize]] = pixel[1] as f32 / 255.0;
            input_array[[0, 2, y as usize, x as usize]] = pixel[2] as f32 / 255.0;
        }
    }

    // 4. Run inference
    println!("Running inference on yolo12x...");
    let outputs = session.run(ort::inputs!["images" => input_array.view()]?)?;
    
    // 5. Extract output
    println!("Inference complete!");
    let output = &outputs["output0"];
    println!("Output shape: {:?}", output.shape());
    println!("First few values: {:?}", &output.try_extract_raw_tensor::<f32>()?.as_slice().unwrap()[0..10]);

    Ok(())
}
