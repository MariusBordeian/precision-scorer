# Claude Context

## Commands
*   **Run**: `cargo run`
*   **Build**: `cargo build`
*   **Build Release**: `cargo build --release`
*   **Test**: `cargo test`
*   **Format**: `cargo fmt`
*   **Lint**: `cargo clippy`

## Tech Stack
*   **Language**: Rust
*   **GUI**: egui / eframe
*   **Camera**: nokhwa
*   **Image Processing**: image, imageproc

## Architecture Overview
*   `src/main.rs`: Entry point, UI loop (`update`), State management.
*   `src/camera.rs`: Threaded webcam capture to `mpsc::Receiver`.
*   `src/processor.rs`: Computer vision logic (thresholding, contours) and Scoring state.

## Guidelines
1.  **UI Performance**: The `update` loop runs every frame (vsync). Don't block it.
2.  **State**: Persist widget state in the `MyApp` struct.
3.  **Cross-Platform**: Keep Windows (MSVC) compatibility in mind.
