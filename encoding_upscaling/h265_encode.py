import os
import subprocess
from pathlib import Path

SOURCE_DIR = Path("video_source")
OUTPUT_DIR = Path("h265_encoded_videos")

# H.265/HEVC codec configuration
CODEC = {
    "lib": "libx265",
    "name": "h265",
    "qp_values": {
        "360p": [24, 30],
        "720p": [24, 30, 36],
        "1080p": [24, 30, 36],
        "2160p": [24, 30, 36]
    },
    "ext": ".mp4",
    "preset": "fast"
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
        if "libx265" not in result.stdout:
            print("[✗] FFmpeg found but H.265 encoder (libx265) is not available.")
            return False
        return True
    except:
        print("[✗] FFmpeg not found. Please install it.")
        return False

def get_exact_framerate(filepath):
    """Returns exact FPS (as float) from ffprobe"""
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

def encode():
    if not check_ffmpeg():
        return

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
    source_files = [f for f in SOURCE_DIR.glob("*") if f.is_file() and f.suffix.lower() in video_extensions]

    if not source_files:
        print("[!] No source videos found.")
        return

    print(f"[i] Found {len(source_files)} video files")

    for src in source_files:
        print(f"\n[i] Processing {src.name}")

        original_fps = get_exact_framerate(src)
        if original_fps is None:
            print("[!] Skipping due to FPS read error.")
            continue

        for res_name, res_value in RESOLUTIONS.items():
            for qp in CODEC["qp_values"][res_name]:
                out_name = f"{src.stem}_{CODEC['name']}_{res_name}_qp{qp}{CODEC['ext']}"
                out_path = OUTPUT_DIR / out_name

                if out_path.exists():
                    print(f"[Skip] {out_name} exists")
                    continue

                cmd = [
                    "ffmpeg", "-y",
                    "-r", str(original_fps),      # Input FPS (important for VFR sources)
                    "-i", str(src),
                    "-vf", f"scale={res_value}",
                    "-r", str(original_fps),      # Output FPS
                    "-c:v", CODEC["lib"],
                    "-x265-params", f"qp={qp}",
                    "-preset", CODEC["preset"],
                    "-pix_fmt", "yuv420p",
                    "-shortest",                  # Ensures no duration overshoot
                    str(out_path)
                ]

                print(f"[Encoding] {out_name}")
                result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)

                if result.returncode == 0:
                    print(f"[✓] Done: {out_name}")
                else:
                    print(f"[✗] Error in {out_name}:\n{result.stderr.splitlines()[-10:]}")

    print("\n[✓] H.265 encoding complete.")
    print(f"[i] Encoded videos saved in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    encode()
