import subprocess
import json
from pathlib import Path
import os

# Define input and output directories
INPUT_DIR = Path("video_source")
OUTPUT_DIR = Path("vvc_encoded_videos")
TEMP_DIR = Path("temp_yuv")

# Create directories if they don't exist
INPUT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Path to vvencapp
VVENCAPP_PATH = r"vvc_build\vvenc\bin\release-static\vvencapp.exe"

# Resolution → QP values
QP_MAPPING = {
    360: [24, 30],
    720: [24, 30, 36],
    1080: [24, 30, 36],
    2160: [24, 30, 36],
}

def get_video_properties(video_path):
    """Extract framerate from input video using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=r_frame_rate",
        "-of", "json",
        str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    props = json.loads(result.stdout)["streams"][0]
    num, den = map(int, props["r_frame_rate"].split('/'))
    framerate = round(num / den)
    return framerate

def encode_vvc(input_path, resolution, qp, framerate):
    """Encode video into VVC using vvencapp with scaling and naming."""
    output_name = f"{input_path.stem}_vvc_{resolution}p_qp{qp}.vvc"
    output_path = OUTPUT_DIR / output_name

    if output_path.exists():
        print(f"[SKIP] {output_path.name} already exists")
        return

    print(f"[ENCODE] {input_path.name} → {output_path.name} @QP{qp}, {resolution}p")

    # Calculate width while maintaining aspect ratio from 1080p
    width = int(1920 * resolution / 1080)
    width += width % 2  # Ensure width is even

    # Create a temporary YUV file
    temp_yuv = TEMP_DIR / f"{input_path.stem}_{resolution}p.yuv"
    
    try:
        # Step 1: Convert to YUV
        ffmpeg_cmd = f'ffmpeg -i "{input_path}" -vf "scale={width}:{resolution}" -pix_fmt yuv420p "{temp_yuv}"'
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
        
        # Step 2: Encode YUV to VVC
        vvenc_cmd = f'"{VVENCAPP_PATH}" -i "{temp_yuv}" -s {width}x{resolution} --fps {framerate} -q {qp} -o "{output_path}" --preset faster'
        subprocess.run(vvenc_cmd, shell=True, check=True)
        
        print(f"[SUCCESS] Encoded {output_path.name}")
    except Exception as e:
        print(f"[ERROR] Failed to encode {output_path.name}: {e}")
        if output_path.exists():
            output_path.unlink()
    finally:
        # Clean up temp file
        if temp_yuv.exists():
            os.remove(temp_yuv)

def main():
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
    video_files = []
    for ext in video_extensions:
        video_files.extend(INPUT_DIR.glob(f"*{ext}"))

    if not video_files:
        print(f"[ERROR] No video files found in {INPUT_DIR}")
        print("[INFO] Supported formats: mp4, mkv, avi, mov, webm")
        return

    print(f"[INFO] Found {len(video_files)} video files to encode")

    for input_file in video_files:
        try:
            framerate = get_video_properties(input_file)
            print(f"[INFO] Processing {input_file.name} (FPS: {framerate})")
        except Exception as e:
            print(f"[ERROR] Failed to get video properties for {input_file.name}: {e}")
            continue

        for resolution, qp_list in QP_MAPPING.items():
            for qp in qp_list:
                encode_vvc(input_file, resolution, qp, framerate)

if __name__ == "__main__":
    main()
