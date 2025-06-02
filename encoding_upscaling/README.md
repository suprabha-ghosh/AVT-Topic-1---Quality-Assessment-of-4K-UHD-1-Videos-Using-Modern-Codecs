# 📽️ 4K/UHD-1 Video Encoding and Upscaling Pipeline using H.265, AV1, and VVC

This project provides an automated pipeline to **encode 4K 60fps videos** into different formats (AV1, H.265, VVC) at multiple resolutions and CRF levels, followed by **optional upscaling to original resolution** using FFmpeg.

## 🔍 Project Overview

The pipeline does the following:
1. **Accepts 4K/UHD-1 raw source videos** (`.mp4`, `.mkv`, `.avi`, `.webm,`, `.mov`)
2. **Encodes** them to 3 different codecs: **AV1, HEVC (H.265), VVC**
3. Saves each encoding at **4 resolutions** (2160p, 1080p, 720p, 360p)
4. Uses **4 CRF values** per codec (e.g., 18, 24, 30, 36)
5. **Optionally decodes and upscales** the compressed videos back to 4K using high-quality FFmpeg filters
6. Generates **intermediate formats** (`.vvc`, `.ivf`, `.yuv`) and **final playback-ready `.mp4` or `.mkv` files**

---


---

## 🧰 Requirements

Before running the project, make sure the following tools are installed and available in your system path:

### ✅ Required Packages

| Tool | Description | Installation Guide |
|------|-------------|--------------------|
| **Python 3.7+** | For scripting | [Python.org](https://www.python.org/downloads/) |
| **FFmpeg (latest)** | Video encoding/decoding tool | [FFmpeg Builds](https://ffmpeg.org/download.html) |
| **x265** | HEVC encoder | Usually included in FFmpeg |
| **VTM encoder/decoder** | For VVC encoding/decoding | [VTM GitHub](https://vcgit.hhi.fraunhofer.de/jvet/VVCSoftware_VTM) |
| **NumPy & tqdm** | Python libraries | `pip install numpy tqdm` |

---

## 💾 Input Files

- Place your **raw lossless 4K 60fps videos** inside the `video_sorce/` folder.
- File format supported: (`.mp4`, `.mkv`, `.avi`, `.webm,`, `.mov`).
- Ensure each file is **3840x2160 resolution & 60 fps**.




