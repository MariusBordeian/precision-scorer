# Agent Context: Precision Scorer

This file provides high-level context for AI agents working on this codebase.

## Project Goal
Build a cross-platform (Windows/Linux) desktop application for automated scoring of paper shooting targets using computer vision.

## Architecture

### 1. Presentation Layer (`src/main.rs`)
*   **Framework**: `eframe` (egui).
*   **Responsibility**:
    *   Render the UI (Sidebars, Image Viewer, Overlays).
    *   Manage application state (`MyApp` struct).
    *   Handle user input (sliders, buttons, mode switching).
    *   Coordinate between Camera, Processor, and Scorer.

### 2. Input Layer (`src/camera.rs`)
*   **Library**: `nokhwa`.
*   **Design**:
    *   Runs in a separate thread (`CameraWorker`).
    *   Communicates via `mpsc::channel` to prevent UI freezing.
    *   Handles camera initialization, resolution fallback, and frame polling.
    *   Raw frames are converted to `image::RgbImage` before sending.

### 3. Logic Layer (`src/processor.rs`)
*   **Processor**:
    *   Stateless image analysis.
    *   Uses `imageproc` for grayscale conversion, thresholding, and contour detection.
    *   Returns `DetectionResult` (list of holes and target center).
*   **Scorer**:
    *   Stateful tracking.
    *   Maintains `known_holes` to implement differential scoring (ignoring pre-existing holes).
    *   Calculates scores (currently dummy logic `+10`).

## Coding Conventions
*   **Style**: Standard Rust (`rustfmt`).
*   **Error Handling**: Use `Result` and `Option` extensively. Avoid `unwrap()` in the main loop/UI threads.
*   **Concurrency**: Camera I/O MUST be off the main thread.
*   **Performance**: Avoid heavy image cloning in the `update` loop if possible (e.g., utilize "Lazy Reprocessing" for static images).

## Common Tasks
*   **Adding Dependencies**: Check `Cargo.toml`.
*   **Running**: `cargo run`.
*   **Building Release**: `cargo build --release`.
