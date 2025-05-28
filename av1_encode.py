import os
import subprocess
from pathlib import Path

# Directory setup
SOURCE_DIR = Path("video_source")
OUTPUT_DIR = Path("av1_encoded_videos")
RESOLUTIONS = {
    "360p": "640x360",
    "720p": "1280x720",
    "1080p": "1920x1080",
    "2160p": "3840x2160"
}
CRF_RANGE = [18, 24, 30, 36]

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except:
        print("[✗] FFmpeg not found. Please install it.")
        return False

def encode_av1():
    if not check_ffmpeg():
        return

    # Create output directory
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

        for res_name, res_value in RESOLUTIONS.items():
            width, height = res_value.split("x")

            for crf in CRF_RANGE:
                output_name = f"{src.stem}_av1_{res_name}_crf{crf}.mkv"
                output_path = OUTPUT_DIR / output_name

                if output_path.exists():
                    print(f"[Skip] {output_name} already exists")
                    continue

                print(f"[Encode] {output_name}")

                ffmpeg_cmd = [
                    "ffmpeg", "-y",
                    "-i", str(src),
                    "-vf", f"scale={width}:{height}",
                    "-c:v", "libaom-av1",
                    "-crf", str(crf),
                    "-b:v", "0",  # Use constant quality
                    "-cpu-used", "4",  # Speed vs quality tradeoff (0–8), higher = faster
                    "-strict", "experimental",  # Ensures AV1 compatibility in some ffmpeg builds
                    str(output_path)
                ]

                result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    print(f"[✓] Encoded: {output_name}")
                else:
                    error_msg = result.stderr.decode("utf-8", errors="replace")[:200]
                    print(f"[✗] Error: {error_msg}...")

    print("\n[✓] AV1 encoding complete.")
    print(f"[i] Encoded videos saved in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    encode_av1()
