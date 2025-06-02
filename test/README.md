<<<<<<< HEAD

# Video Quality Assessment using FFmpeg and VMAF

This project helps evaluate video quality using the **VMAF** (Video Multi-Method Assessment Fusion) metric with **FFmpeg**. VMAF is a perceptual video quality assessment algorithm developed by Netflix.

---

## 📦 Prerequisites

- Python 3.7+
- `ffmpeg` and `ffprobe` with `libvmaf` support
- `pip` for installing Python dependencies

---

## 🖥️ Installation

### 🔹 macOS

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install FFmpeg with VMAF support**:
   ```bash
   brew install ffmpeg --with-libvmaf
   ```

3. **Verify installation**:
   ```bash
   ffmpeg -filters | grep vmaf
   ```

4. **Install Python dependencies**:
   ```bash
   pip install pandas seaborn scikit-learn matplotlib adjustText
   ```

---

### 🔹 Windows

1. **Download FFmpeg with VMAF support**:
   - Visit [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
   - Download a full build that includes `libvmaf`.

2. **Add FFmpeg to your PATH**:
   - Extract the zip file.
   - Add the `bin/` folder to the system environment variable `PATH`.

3. **Verify installation**:
   Open Command Prompt and run:
   ```bash
   ffmpeg -filters | findstr vmaf
   ```

4. **Install Python and dependencies**:
   - Download Python from [https://www.python.org](https://www.python.org)
   - Then run:
     ```bash
     pip install pandas seaborn scikit-learn matplotlib adjustText
     ```

---

## 🚀 Usage

1. Place your original/reference video and encoded versions in the same folder.
2. Run your VMAF evaluation script using Python and FFmpeg.
3. It will generate VMAF scores and visualizations such as CRF vs VMAF and Bitrate vs VMAF.

---

## 📊 Output

- CSV file with VMAF results
- Scatter plots CRF vs VMAF and Bitrate vs VMAF (with av1)
- PCC and RMSE values for analysis

---

## 📚 References

- [Netflix VMAF GitHub](https://github.com/Netflix/vmaf)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)

---


=======
# AVT-Topic-1---Quality-Assessment-of-4K-UHD-1-Videos-Using-Modern-Codecs
>>>>>>> f97ed9aff3d58d9278b420b6f222baa75ea7857b
