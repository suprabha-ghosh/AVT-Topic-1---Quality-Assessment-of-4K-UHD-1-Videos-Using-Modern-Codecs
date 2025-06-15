import subprocess
from pathlib import Path
import os

# Define paths
INPUT_DIR = Path("vvc_encoded_videos")
Y4M_DIR = Path("decoded_y4m")
OUTPUT_DIR = Path("vvc_decoded_videos")
VVDECAPP_PATH = r"vvc_build\vvdec\bin\release-static\vvdecapp.exe"

# Create necessary directories
Y4M_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def decode_vvc_to_y4m(vvc_path, y4m_path):
    """Decode VVC to Y4M using vvdecapp with --y4m."""
    cmd = [
        VVDECAPP_PATH,
        "-b", str(vvc_path),
        "--y4m",
        "-o", str(y4m_path)
    ]
    print(f"[DECODING] {vvc_path.name} → {y4m_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"vvdecapp failed:\n{result.stderr}")

def encode_y4m_to_mp4(y4m_path, output_path):
    """Convert Y4M to MP4 using ffmpeg with libx265."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(y4m_path),
        "-c:v", "libx265",
        "-preset", "faster",
        "-vf", "scale=-2:2160",
        "-crf", "0",  
        str(output_path)
    ]
    print(f"[ENCODING] {output_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

def process_vvc_files():
    """Process all VVC files in the input directory."""
    vvc_files = list(INPUT_DIR.glob("*.vvc"))
    if not vvc_files:
        print(f"[ERROR] No VVC files found in {INPUT_DIR}")
        return
    
    print(f"[INFO] Found {len(vvc_files)} VVC files to process")
    
    for vvc_file in vvc_files:
        y4m_path = Y4M_DIR / (vvc_file.stem + ".y4m")
        output_path = OUTPUT_DIR / (vvc_file.stem + ".mkv") 
        
        if output_path.exists():
            print(f"[SKIP] {output_path.name} already exists")
            continue
        
        try:
            decode_vvc_to_y4m(vvc_file, y4m_path)
            encode_y4m_to_mp4(y4m_path, output_path)
            print(f"[SUCCESS] {output_path.name}")
        except Exception as e:
            print(f"[ERROR] {vvc_file.name}: {e}")
        finally:
            # Clean up Y4M file to save space
            if y4m_path.exists():
                try:
                    os.remove(y4m_path)
                    print(f"[CLEANUP] Removed {y4m_path.name}")
                except:
                    print(f"[WARNING] Could not remove {y4m_path.name}")

if __name__ == "__main__":
    process_vvc_files()
