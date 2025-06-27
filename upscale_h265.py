import os
import subprocess
from pathlib import Path

INPUT_DIR = Path("h265_encoded_videos")
OUTPUT_DIR = Path("upscaled_h265")
SUPPORTED_EXTENSIONS = [".mp4", ".mkv", ".webm"]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def upscale_to_4k(input_path: Path, output_path: Path):
    if output_path.exists():
        print(f"[SKIP] Already upscaled: {output_path.name}")
        return
    print(f"[UPSCALE] {input_path.name} → {output_path.name}")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-c:v", "libx265",
        "-crf", "0",
        "-vf", "scale=-2:2160:flags=lanczos",
        "-preset", "faster",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to upscale {input_path.name}: {e}")

def main():
    for video_file in INPUT_DIR.glob("*"):
        if video_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"[SKIP] Unsupported format: {video_file.name}")
            continue

        output_file = OUTPUT_DIR / f"{video_file.stem}_upscaled_4k.mp4"
        upscale_to_4k(video_file, output_file)

if __name__ == "__main__":
    main()
