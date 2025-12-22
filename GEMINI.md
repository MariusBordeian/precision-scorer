# Gemini Context

## Project Overview
Precision Scorer is a Rust-based desktop application for target shooting scoring. It uses computer vision to detect bullet holes on targets via webcam or static images.

## Development Environment
*   **OS**: Windows (Primary), Linux (Target)
*   **Language**: Rust 2021
*   **Build System**: Cargo

## Key Commands
*   `cargo run` - Start the app
*   `cargo check` - Fast compile check
*   `cargo clippy` - Linters
*   `cargo build --release` - Production build

## Codebase Structure
*   **`src/main.rs`**: The Egui application. It owns the `CameraWorker`, `Processor`, and `Scorer`.
*   **`src/camera.rs`**: Handles `nokhwa` camera interaction in a background thread.
*   **`src/processor.rs`**: Contains `Processor` (CV logic) and `Scorer` (Game logic).

## Principles
*   **Responsiveness**: Heavy computation or I/O should be threaded.
*   **Robustness**: Handle camera disconnections and invalid image files gracefully.
*   **User Feedback**: Use the UI to show what's happening (e.g., "Waiting for camera...", Overlays).

## Current Status
*   We have Basic Detection (Contours).
*   We have Differential Scoring (New vs Old holes).
*   We support Live Feed and Static Images.
*   We have UI controls for Thresholds and Radius.
