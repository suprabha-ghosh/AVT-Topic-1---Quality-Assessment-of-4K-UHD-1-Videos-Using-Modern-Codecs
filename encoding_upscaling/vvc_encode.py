#!/usr/bin/env python3
import os
import subprocess
import re
from pathlib import Path

# Configuration
SOURCE_DIR = Path("video_source")
OUTPUT_DIR = Path("vvc_encoded_videos")

VVENCAPP_PATH = r"vvc_build\vvenc\bin\release-static\vvencapp.exe"

CRF_RANGE = [18, 24, 30, 36]
PRESETS = ["faster"]
RESOLUTIONS = {
    "360p": "640x360",
    "720p": "1280x720",
    "1080p": "1920x1080",
    "2160p": "3840x2160"
}

def check_binary(path, name):
    try:
        subprocess.run([path, "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"[✓] Found {name} at: {path}")
        return True
    except Exception as e:
        print(f"[✗] {name} not found at {path} → {e}")
        return False

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except:
        print("[✗] FFmpeg not found.")
        return False

def encode_videos():
    if not check_binary(VVENCAPP_PATH, "vvencapp") or not check_ffmpeg():
        return

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm']
    source_files = [f for f in SOURCE_DIR.glob("*") if f.suffix.lower() in video_extensions]

    if not source_files:
        print("[!] No source videos found.")
        return

    print(f"[i] Found {len(source_files)} video(s) in {SOURCE_DIR}")

    for src in source_files:
        print(f"\n[i] Processing {src.name}")
        
        for res_name, res_value in RESOLUTIONS.items():
            width, height = res_value.split("x")
            
            for crf in CRF_RANGE:
                for preset in PRESETS:
                    vvc_name = f"{src.stem}_vvc_{res_name}_crf{crf}.vvc"
                    vvc_path = OUTPUT_DIR / vvc_name

                    # Skip if file already exists
                    if vvc_path.exists():
                        print(f"[Skip] File exists: {vvc_name}")
                        continue

                    # Encode to VVC
                    print(f"[Encoding] {src.name} → {vvc_name}")
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
                            print(f"[✓] Saved VVC: {vvc_path.name}")
                        else:
                            # Filter out unwanted lines from error output
                            error_output = p2.stderr.decode(errors='ignore')
                            filtered_output = '\n'.join([
                                line for line in error_output.splitlines()
                                if not (line.startswith("POC") or "vvdecapp [info]: decoded Frames:" in line)
                            ])
                            print(f"[✗] VVC encode failed: {filtered_output[:200]}")
                    except Exception as e:
                        print(f"[✗] Exception during VVC encoding: {e}")

    print("\n[✓] All encoding complete.")
    print(f"[i] Encoded VVC saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    encode_videos()
