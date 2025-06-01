#!/usr/bin/env python3
import os
import subprocess
import re
import time
from pathlib import Path

# Paths and settings
VVDECAPP_PATH = r"vvc_build\vvdec\bin\release-static\vvdecapp.exe"
VVC_DIR = Path("vvc_encoded_videos")
OUTPUT_DIR = Path("upscaled_vvc")
TARGET_4K = "3840x2160"

# Resolution mapping
RESOLUTION_MAP = {
    "360p": "640x360",
    "720p": "1280x720",
    "1080p": "1920x1080",
    "2160p": "3840x2160"
}

def check_tools():
    """Check if required tools are available"""
    try:
        # Check ffmpeg
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        # Check vvdecapp
        if not os.path.exists(VVDECAPP_PATH):
            print(f"[✗] VVC decoder not found at: {VVDECAPP_PATH}")
            return False
            
        return True
    except:
        print("[✗] FFmpeg not found. Please install it.")
        return False

def get_resolution_from_filename(filename):
    """Extract resolution from filename"""
    for res_name, res_value in RESOLUTION_MAP.items():
        if res_name in filename:
            width, height = res_value.split("x")
            return int(width), int(height)
    
    # Default to 1080p if resolution can't be determined
    print(f"[!] Could not determine resolution from filename: {filename}, assuming 1080p")
    return 1920, 1080

def process_vvc_files():
    """Process all VVC files: decode, upscale to 4K with Lanczos, and encode to MP4"""
    if not check_tools():
        return
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all VVC files
    vvc_files = list(VVC_DIR.glob("*.vvc"))
    if not vvc_files:
        print(f"[!] No VVC files found in {VVC_DIR}")
        return
    
    print(f"[i] Found {len(vvc_files)} VVC files to process")
    
    for vvc_file in vvc_files:
        # Output filename
        output_file = OUTPUT_DIR / f"{vvc_file.stem}_upscaled_4k.mp4"
        
        if output_file.exists():
            print(f"[Skip] {output_file.name} already exists")
            continue
        
        print(f"[Processing] {vvc_file.name}")
        start_time = time.time()
        
        # Get resolution from filename
        width, height = get_resolution_from_filename(vvc_file.name)
        print(f"[i] Detected resolution: {width}x{height}")
        
        try:
            # Use raw YUV as intermediate format
            temp_yuv = OUTPUT_DIR / f"{vvc_file.stem}_temp.yuv"
            
            # Step 1: Decode VVC to raw YUV format
            print(f"[Step 1] Decoding VVC to YUV format...")
            vvdec_cmd = [
                VVDECAPP_PATH,
                "-b", str(vvc_file),
                "-o", str(temp_yuv),
                "-v", "0"  # Reduce verbosity
            ]
            
            vvdec_result = subprocess.run(vvdec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if vvdec_result.returncode != 0:
                print(f"[✗] VVC decoding failed: {vvc_file.name}")
                error = vvdec_result.stderr.decode('utf-8', errors='replace')[:200]
                print(f"    Error: {error}")
                if temp_yuv.exists():
                    temp_yuv.unlink()
                continue
            
            # Check if the decoded file exists and has content
            if not temp_yuv.exists() or temp_yuv.stat().st_size == 0:
                print(f"[✗] Decoded file is empty or missing: {temp_yuv}")
                continue
                
            # Step 2: Convert YUV to MP4 with upscaling
            print(f"[Step 2] Upscaling to 4K with Lanczos and encoding...")
            
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-video_size", f"{width}x{height}",
                "-pixel_format", "yuv420p",  # Assume YUV 4:2:0 format
                "-i", str(temp_yuv),
                "-vf", f"scale={TARGET_4K}:flags=lanczos",
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "medium",  # Balance between speed and quality
                "-pix_fmt", "yuv420p",
                str(output_file)
            ]
            
            ffmpeg_result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Clean up temporary file
            if temp_yuv.exists():
                temp_yuv.unlink()
            
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            
            if ffmpeg_result.returncode == 0:
                print(f"[✓] Completed: {output_file.name} in {minutes}m {seconds}s")
            else:
                print(f"[✗] Upscaling/encoding failed: {vvc_file.name}")
                error = ffmpeg_result.stderr.decode('utf-8', errors='replace')[:200]
                print(f"    Error: {error}")
                
        except Exception as e:
            print(f"[✗] Exception processing {vvc_file.name}: {e}")
            # Clean up temporary file if it exists
            if 'temp_yuv' in locals() and temp_yuv.exists():
                temp_yuv.unlink()
    
    print("\n[✓] All VVC files processed and upscaled to 4K.")

if __name__ == "__main__":
    process_vvc_files()
