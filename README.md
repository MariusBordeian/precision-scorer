# Precision Scorer

A high-performance Desktop application for automated scoring of precision shooting targets, built with **Rust**, **Egui**, and **ImageProc**.

## 🚀 Features

*   **Multi-Camera Support**: Select any connected USB webcam.
*   **Static Image Loading**: Analyze pre-taken photos of targets.
*   **Live Scoring**: Real-time detection of bullet holes and scoring rings (prototype).
*   **Differential Scoring**: Distinguish new holes from old ones (useful for practice sessions).
*   **Snapshot / Freeze Mode**: Pause the feed for detailed inspection.
*   **View Controls**: Scale to fit window or view at 1:1 native resolution.
*   **Max Resolution**: Support for 4K/1080p cameras.

## 🛠️ Tech Stack

*   **Language**: Rust 🦀
*   **UI Framework**: [eframe](https://github.com/emilk/egui/tree/master/crates/eframe) / [egui](https://github.com/emilk/egui)
*   **Computer Vision**: [imageproc](https://github.com/image-rs/imageproc) & [image](https://github.com/image-rs/image)
*   **Camera Access**: [nokhwa](https://github.com/l1npengtul/nokhwa)

## 📦 Prerequisites

*   **Rust Toolchain**: Install via [rustup.rs](https://rustup.rs/).
*   **Windows**: Ensure **Visual Studio C++ Build Tools** are installed (for the MSVC linker).

## 🏃 How to Run

1.  Clone the repository:
    ```bash
    git clone https://github.com/MariusBordeian/precision-scorer.git
    cd precision-scorer
    ```

2.  Run with Cargo:
    ```bash
    cargo run --release
    ```
    *(Use `--release` for best performance, especially with high-res cameras)*

## 🎮 Controls

*   **Camera Source**: Select your input device from the dropdown.
*   **Source Mode**: Switch between "Live Camera" and "Static Image".
*   **Settings**:
    *   **Threshold**: Adjust darkness sensitivity for hole detection.
    *   **Hole Radius**: Filter noise by specifying min/max hole size.
    *   **Use Max Resolution**: Force the camera to its highest supported resolution.
    *   **Scale to Fit**: Toggle resizing the feed to the window.
*   **Actions**:
    *   **Snapshot/Freeze**: Pause the live video.
    *   **Reset Score**: Clear the current session history.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
