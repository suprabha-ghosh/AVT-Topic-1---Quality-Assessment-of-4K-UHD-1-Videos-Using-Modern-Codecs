import os
import subprocess
from pathlib import Path

# Directory setup
SOURCE_DIR = Path("video_source")
OUTPUT_DIR = Path("av1_encoded_videos")

# CRF values per resolution
QP_VALUES = {
    "360p": [24, 30],
    "720p": [24, 30, 36],
    "1080p": [24, 30, 36],
    "2160p": [24, 30, 36]
}

RESOLUTIONS = {
    "360p": "640x360",
    "720p": "1280x720",
    "1080p": "1920x1080",
    "2160p": "3840x2160"
}

def check_ffmpeg():
    try:
        result = subprocess.run(["ffmpeg", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "libaom-av1" not in result.stdout:
            print("[✗] FFmpeg found but AV1 encoder (libaom-av1) is not available.")
            return False
        return True
    except:
        print("[✗] FFmpeg not found. Please install it.")
        return False

def get_exact_framerate(filepath):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(filepath)
        ], capture_output=True, text=True)

        fps_raw = result.stdout.strip()
        if "/" in fps_raw:
            num, denom = map(int, fps_raw.split("/"))
            return round(num / denom, 6)
        return round(float(fps_raw), 6)
    except Exception as e:
        print(f"[!] Could not get FPS for {filepath.name}: {e}")
        return None

def get_duration(filepath):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(filepath)
        ], capture_output=True, text=True)
        return round(float(result.stdout.strip()), 3)
    except Exception as e:
        print(f"[!] Could not get duration for {filepath.name}: {e}")
        return None

def encode_av1():
    if not check_ffmpeg():
        return

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
    source_files = [f for f in SOURCE_DIR.glob("*") if f.is_file() and f.suffix.lower() in video_extensions]

    if not source_files:
        print("[!] No source videos found.")
        return

    print(f"[i] Found {len(source_files)} video file(s)")

    for src in source_files:
        print(f"\n[i] Processing {src.name}")
        original_fps = get_exact_framerate(src)
        duration = get_duration(src)

        if original_fps is None or duration is None:
            print("[!] Skipping due to FPS/duration read error.")
            continue

        for res_name, res_value in RESOLUTIONS.items():
            width, height = res_value.split("x")
            qp_list = QP_VALUES[res_name]

            for qp in qp_list:
                output_name = f"{src.stem}_av1_{res_name}_qp{qp}.mkv"
                output_path = OUTPUT_DIR / output_name

                if output_path.exists():
                    print(f"[Skip] {output_name} already exists")
                    continue

                print(f"[Encode] {output_name}")

                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", str(src),
                    "-vf", f"scale={width}:{height}",
                    "-r", str(original_fps),
                    "-t", str(duration),
                    "-c:v", "libaom-av1",
                    "-crf", str(qp),
                    "-b:v", "0",
                    "-cpu-used", "6",
                    "-pix_fmt", "yuv420p",
                    str(output_path)
                ]

                result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    print(f"[✓] Encoded: {output_name}")
                else:
                    error_msg = result.stderr.decode("utf-8", errors="replace")[:300]
                    print(f"[✗] Error encoding {output_name}:\n{error_msg}\n")

    print("\n[✓] AV1 encoding complete.")
    print(f"[i] Encoded videos saved in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    encode_av1()
