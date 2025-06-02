import os
import subprocess
from pathlib import Path
import time

# Directory setup
ENCODED_DIR = Path("av1_encoded_videos")  # Directory with encoded AV1 videos
UPSCALED_DIR = Path("upscaled_av1")       # Directory for upscaled videos

# 4K resolution for upscaling
TARGET_4K = "3840x2160"

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except:
        print("[✗] FFmpeg not found. Please install it.")
        return False

def upscale_videos():
    """Process all encoded videos to 4K using Lanczos algorithm"""
    if not check_ffmpeg():
        return
    
    # Create upscaled directory
    UPSCALED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all encoded videos
    video_extensions = ['.mp4', '.mkv', '.avi', '.webm']
    encoded_videos = []
    
    for ext in video_extensions:
        encoded_videos.extend(list(ENCODED_DIR.glob(f"*{ext}")))
    
    if not encoded_videos:
        print("[!] No encoded videos found.")
        return
    
    # Count total videos
    total_videos = len(encoded_videos)
    print(f"[i] Found {total_videos} videos to process")
    
    # Process each video
    for video in encoded_videos:
        # Create output filename for processed version
        upscaled_name = f"{video.stem}_upscaled_4k.mp4"
        upscaled_path = UPSCALED_DIR / upscaled_name
        
        if upscaled_path.exists():
            print(f"[Skip] {upscaled_name} exists")
            continue
        
        print(f"[Processing] {video.name} with Lanczos scaling...")
        start_time = time.time()
        
        # Use libx264 with Lanczos scaling
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video),
            "-c:v", "libx264",     # Use H.264 for reliability
            "-crf", "23",          # Standard quality for H.264
            "-preset", "medium",    # Balance between speed and quality
            "-vf", f"scale={TARGET_4K}:flags=lanczos",  # Lanczos scaling algorithm
            "-pix_fmt", "yuv420p", # YUV 4:2:0 pixel format
            str(upscaled_path)
        ]
        
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        
        if result.returncode == 0:
            print(f"[✓] Processed: {upscaled_name} in {minutes}m {seconds}s")
        else:
            print(f"[✗] Processing error: {result.stderr[:100]}...")
    
    print(f"\n[✓] Processing complete. Results saved in '{UPSCALED_DIR}'")

if __name__ == "__main__":
    upscale_videos()
