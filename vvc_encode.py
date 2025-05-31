#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

SOURCE_DIR = Path("video_source")
OUTPUT_DIR = Path("vvc_encoded_videos")
VVENCAPP_PATH = r"C:\Users\Suprabha Ghosh\vvc_build\vvenc\bin\release-static\vvencapp.exe"

CRF_RANGE = [18, 24, 30, 36]
PRESETS = ["faster"]
RESOLUTIONS = {
    "360p": "640x360",
    "720p": "1280x720",
    "1080p": "1920x1080",
    "2160p": "3840x2160"
}

def check_vvencapp():
    try:
        result = subprocess.run(
            [VVENCAPP_PATH, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            print(f"[✓] VVC encoder found: {result.stdout.strip()}")
            return True
        else:
            print(f"[✗] VVC encoder check failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[✗] Error checking VVC encoder: {e}")
        return False

def encode_vvc_only():
    if not check_vvencapp():
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
        
        for res_name, res_value in RESOLUTIONS.items():
            width, height = res_value.split("x")
            
            for crf in CRF_RANGE:
                for preset in PRESETS:
                    vvc_name = f"{src.stem}_vvc_{res_name}_crf{crf}.vvc"
                    vvc_path = OUTPUT_DIR / vvc_name

                    if vvc_path.exists():
                        print(f"[Skip] {vvc_name} already exists")
                        continue

                    print(f"[Encoding] {src.name} at {res_name} with CRF {crf}")
                    
                    # ffmpeg pipe directly to vvencapp
                    ffmpeg_cmd = [
                        "ffmpeg", "-i", str(src),
                        "-vf", f"scale={width}:{height}",
                        "-pix_fmt", "yuv420p",
                        "-f", "yuv4mpegpipe", "-"
                    ]
                    
                    vvencapp_cmd = [
                        VVENCAPP_PATH,
                        "-s", f"{width}x{height}",
                        "--qp", str(crf),
                        "--preset", preset,
                        "-i", "-", "-o", str(vvc_path)
                    ]

                    try:
                        p1 = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE)
                        p2 = subprocess.run(vvencapp_cmd, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        p1.stdout.close()
                        p1.wait()

                        if p2.returncode == 0:
                            print(f"[✓] Saved: {vvc_path.name}")
                        else:
                            error_msg = p2.stderr.decode('utf-8', errors='replace')[:200]
                            print(f"[✗] Encode error: {error_msg}...")
                    except Exception as e:
                        print(f"[✗] Exception during encoding: {e}")

    print("\n[✓] VVC encoding complete.")

if __name__ == "__main__":
    encode_vvc_only()
