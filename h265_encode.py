import os
import subprocess
from pathlib import Path

SOURCE_DIR = Path("video_source")
OUTPUT_DIR = Path("h265_encoded_videos")
UPSCALED_DIR = Path("upscaled_h265")  # New directory for upscaled videos

# H.265/HEVC codec configuration
CODEC = {
    "lib": "libx265",
    "name": "h265", 
    "crf_range": [18, 24, 30, 36], 
    "ext": ".mp4",
    "preset": "fast"
}

RESOLUTIONS = {
    "360p": "640x360",
    "720p": "1280x720",
    "1080p": "1920x1080",
    "2160p": "3840x2160"
}

# 4K resolution for upscaling
TARGET_4K = "3840x2160"

def check_ffmpeg():
    """Check if ffmpeg is available with H.265 support"""
    try:
        result = subprocess.run(["ffmpeg", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "libx265" not in result.stdout:
            print("[✗] FFmpeg found but H.265 encoder (libx265) is not available.")
            return False
        return True
    except:
        print("[✗] FFmpeg not found. Please install it.")
        return False

def upscale_to_4k(encoded_videos):
    """Upscale encoded videos to 4K for subjective testing"""
    print("\n[i] Starting 4K upscaling for subjective testing...")
    
    # Create upscaled directory
    UPSCALED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Skip 4K videos as they're already at target resolution
    videos_to_upscale = [v for v in encoded_videos if "2160p" not in v.name]
    
    if not videos_to_upscale:
        print("[!] No videos to upscale.")
        return
    
    print(f"[i] Found {len(videos_to_upscale)} videos to upscale to 4K")
    
    for video in videos_to_upscale:
        # Create output filename for upscaled version
        upscaled_name = f"{video.stem}_upscaled_4k{video.suffix}"
        upscaled_path = UPSCALED_DIR / upscaled_name
        
        if upscaled_path.exists():
            print(f"[Skip] {upscaled_name} exists")
            continue
        
        print(f"[Upscaling] {video.name} to 4K...")
        
        # Use lanczos scaling algorithm for high-quality upscaling
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
            "-c:v", "libx265",  # Re-encode with H.265
            "-crf", "18",       # Use high quality for subjective testing
            "-preset", "medium",
            "-vf", f"scale={TARGET_4K}:flags=lanczos",  # Lanczos algorithm for better quality
            "-pix_fmt", "yuv420p",
            str(upscaled_path)
        ]
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"[✓] Upscaled: {upscaled_name}")
        else:
            print(f"[✗] Upscaling error: {result.stderr[:100]}...")
    
    print("\n[✓] 4K upscaling complete.")

def encode():
    """Encode videos using H.265"""
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
    
    # Keep track of successfully encoded videos
    encoded_videos = []

    for src in source_files:
        print(f"\n[i] Processing {src.name}")

        for res_name, res_value in RESOLUTIONS.items():
            for crf in CODEC["crf_range"]:
                out_name = f"{src.stem}_{CODEC['name']}_{res_name}_crf{crf}{CODEC['ext']}"
                out_path = OUTPUT_DIR / out_name

                if out_path.exists():
                    print(f"[Skip] {out_name} exists")
                    encoded_videos.append(out_path)  # Add to list even if skipped
                    continue

                # Standard FFmpeg encoding with H.265
                cmd = [
                    "ffmpeg", "-y",
                    "-i", str(src),
                    "-c:v", CODEC["lib"],
                    "-crf", str(crf),
                    "-preset", CODEC["preset"],
                    "-vf", f"scale={res_value}",
                    "-pix_fmt", "yuv420p",
                    str(out_path)
                ]

                print(f"[Encoding] {out_name}")
                result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
                
                if result.returncode == 0:
                    print(f"[✓] Done: {out_name}")
                    encoded_videos.append(out_path)  # Add to list of successful encodes
                else:
                    print(f"[✗] Error: {result.stderr[:100]}...")

    print("\n[✓] H.265 encoding complete.")
    
    # Perform upscaling after encoding is complete
    upscale_to_4k(encoded_videos)

if __name__ == "__main__":
    encode()
