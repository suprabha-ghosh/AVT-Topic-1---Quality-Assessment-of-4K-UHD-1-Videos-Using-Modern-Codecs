# Quality Assessment of 4K UHD-1 Videos Using Modern Codecs

A comprehensive video quality assessment toolkit that compares the performance of modern video codecs.

## Quick Start

### Software Requirements

Before starting, make sure you have these programs installed:

#### 1. Python (Required)

- **Download:** [Python 3.8 or newer](https://www.python.org/downloads/)
- **Check if installed:** Type `python --version` in terminal

#### 2. FFmpeg (Required) 

- **For Windows:** Download from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
- **For Mac:** Install using Homebrew: `brew install ffmpeg`
- **For Linux:** `sudo apt install ffmpeg` (Ubuntu/Debian) or `sudo yum install ffmpeg` (CentOS/RHEL)
- **Check if installed:** Type `ffmpeg -version` in terminal

#### 3. VVC Codec Tools (Required)

- **Download:** [VVenC/VVdeC from Fraunhofer](https://github.com/fraunhoferhhi/vvenc)

### Python Libraries (Required)

The project needs these Python libraries:
- `opencv-python==4.8.1.78` - For video processing and analysis
- `numpy==1.24.3` - For mathematical calculations  
- `matplotlib==3.7.2` - For creating charts and graphs
- `pandas==2.0.3` - For handling data and creating CSV files
- `seaborn==0.12.2` - For advanced plotting
- `scipy==1.11.1` - For statistical analysis
- `scikit-learn==1.3.0` - For machine learning metrics
- `adjustText==0.8.1` - For better plot label positioning

## Installation Guide

### Step 1: Clone/Download the Project

```bash
# Option A: If you have git installed
git clone <repository-url>
cd AVT-Topic-1---Quality-Assessment-of-4K-UHD-1-Videos-Using-Modern-Codecs

# Option B: Download ZIP file and extract it
# Then navigate to the folder in terminal/command prompt
```

### Step 2: Install Python Libraries

Run the following command in terminal:
```bash
pip install opencv-python==4.8.1.78 numpy==1.24.3 matplotlib==3.7.2 pandas==2.0.3 seaborn==0.12.2 scipy==1.11.1 scikit-learn==1.3.0 adjustText==0.8.1
```

## Project Structure

```
Project Folder
├── README.md                       # Guide
├── Python Scripts
│   ├── av1_encode.py               # Encodes videos using AV1 codec
│   ├── h265_encode.py              # Encodes videos using H.265 codec  
│   ├── vvc_encode.py               # Encodes videos using VVC codec
│   ├── siti_analyzer.py            # Analyzes video complexity (SITI)
│   ├── calculate_vmaf.py           # Measures video quality (VMAF)
│   ├── upscale_av1.py              # Upscales AV1 videos to 4K
│   ├── upscale_h265.py             # Upscales H.265 videos to 4K
│   └── upscale_vvc.py              # Upscales VVC videos to 4K
├── Input/Output Folders
│   ├── video_source/               # Put source videos here (for encoding)
│   ├── siti/videos/                # Put source videos here (for SITI analysis)
│   ├── av1_encoded_videos/         # AV1 encoded results
│   ├── h265_encoded_videos/        # H.265 encoded results
│   ├── vvc_encoded_videos/         # VVC encoded results
│   ├── upscaled_av1/               # 4K upscaled AV1 videos
│   ├── upscaled_h265/              # 4K upscaled H.265 videos
│   ├── upscaled_vvc/               # 4K upscaled VVC videos
│   ├── siti_results/               # SITI analysis results
│   ├── vmaf_analysis_av1/          # VMAF results for AV1
│   ├── vmaf_analysis_h265/         # VMAF results for H.265
│   ├── vmaf_analysis_vvc/          # VMAF results for VVC
│   └── vmaf_models/                # VMAF model files
```

## How to Use This Project

### Step 1: Prepare Your Videos

- Put your source videos in `video_source/` folder:
    - for SITI complexity analysis
    - for encoding with different codecs

#### Official Test Videos

For standardized testing and comparison with research results, download the official AVT-VQDB-UHD-1 videos:
🔗 **Download Link**: [https://telecommunication-telemedia-assessment.github.io/AVT-VQDB-UHD-1/](https://telecommunication-telemedia-assessment.github.io/AVT-VQDB-UHD-1/)

**Test Videos:**
- [`Bigbuck Bunny 8Bit`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/bigbuck_bunny_8bit.mkv)
- [`Cutting Orange Tuil 8S`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/cutting_orange_tuil_8s.mkv)
- [`Dancers 8S`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/Dancers_8s.mkv)
- [`Daydreamer Sdr 8S 3840X2160 8`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/Daydreamer_SDR_8s_3840x2160_8.mkv)
- [`Fr-041 Debris 3840X2160 60P 422 Ffvhuff 4 8S`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/fr-041_debris_3840x2160_60p_422_ffvhuff_4_8s.mkv)
- [`Giftmord-Sdr 8S 11 3840X2160`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/Giftmord-SDR_8s_11_3840x2160.mkv)
- [`Sparks Cut 15`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/Sparks_cut_15.mkv)
- [`Vegetables Tuil`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/vegetables_tuil.mkv)
- [`Water Netflix 8S`](https://avtshare01.rz.tu-ilmenau.de/avt-vqdb-uhd-1/src_videos/water_netflix_8s.mkv)

### Step 2: Analyze Video Complexity (SITI Analysis)

```bash
python siti_analyzer.py
```

**What this does:**
- Measures **Spatial Information (SI)**: How much detail/texture is in each frame
- Measures **Temporal Information (TI)**: How much motion/change between frames
- Creates charts showing video complexity

### Step 3: Encode Videos with Different Codecs

#### Encode with H.265/HEVC

```bash
python h265_encode.py
```

#### Encode with AV1

```bash
python av1_encode.py
```

#### Encode with VVC/H.266

```bash
python vvc_encode.py
```

**What encoding does:**
- Creates multiple versions of each video at different resolutions (360p, 720p, 1080p, 2160p/4K) and quantization parameters (QP 24, 30, 36)

### Step 4: Upscale Videos to 4K

```bash
# Upscale H.265 videos  
python upscale_h265.py

# Upscale AV1 videos
python upscale_av1.py

# Upscale VVC videos
python upscale_vvc.py
```

**Why upscale?**
- VMAF comparison requires all videos to be the same resolution
- Upscaling to 4K ensures fair quality comparisons

### Step 5: Calculate VMAF Quality Scores

```bash
python calculate_vmaf.py
```

**What VMAF analysis does:**
- Compares each encoded video to the original
- Gives quality scores from 0-100 (higher = better quality)
- Creates detailed charts showing quality vs. compression tradeoffs
- Saves results as CSV files and graphs

## Understanding Your Results

### SITI Results (`siti_results/` folder)
- **Individual CSV files**: Frame-by-frame complexity data for each video
- **siti_summary.csv**: Average complexity values for all videos
- **siti_all_frames.png**: Scatter plot showing complexity of all frames
- **siti_average_values.png**: Chart comparing average complexity between videos

### VMAF Results (`vmaf_analysis_*/` folders)
- **CSV files**: Quality scores for each encoded video
- **Scatter plots**: Show how encoded quality compares to original

### Key Metrics

#### VMAF Score (0-100)
- **90-100**: Excellent quality, visually identical to original
- **80-90**: Very good quality, minor differences  
- **70-80**: Good quality, some visible differences
- **60-70**: Acceptable quality, noticeable differences
- **Below 60**: Poor quality, significant degradation

#### QP (Quantization Parameter)
- **Lower QP (24)**: Higher quality, larger file size
- **Medium QP (30)**: Balanced quality and size
- **Higher QP (36)**: Lower quality, smaller file size

## License and Credits

### Software License
This project is for educational and research purposes. Please respect the licenses of the tools and libraries used (FFmpeg, OpenCV, etc.).

### Video Content Licenses
The official test videos used in this project are from the [AVT-VQDB-UHD-1 database](https://github.com/Telecommunication-Telemedia-Assessment/AVT-VQDB-UHD-1) created by TU Ilmenau's Telecommunication and Telemedia Assessment group.

### Acknowledgments
- **AVT-VQDB-UHD-1 Database**: Created by the Telecommunication and Telemedia Assessment group at TU Ilmenau
- **Original Video Sources**: Big Buck Bunny (Blender Foundation), Netflix content providers
- **Research Community**: For developing and maintaining open video quality assessment standards
