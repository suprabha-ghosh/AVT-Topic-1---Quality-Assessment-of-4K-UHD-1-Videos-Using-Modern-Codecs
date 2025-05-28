import os
import cv2
import glob
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# ------------------------- CONFIGURATION -------------------------

INPUT_FOLDER = "video_source"          # 🔁 Your input folder
OUTPUT_FOLDER = "output"         # 📁 Results saved here
SUPPORTED_FORMATS = ["*.mp4", "*.mov", "*.mkv", "*.avi", "*.webm"]

# ------------------------- SITI FUNCTIONS -------------------------

def compute_siti(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open {video_path}")
        return None

    si_vals, ti_vals = [], []
    prev_gray = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Spatial Information (SI)
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel = np.sqrt(sobel_x**2 + sobel_y**2)
        si_vals.append(np.std(sobel))

        # Temporal Information (TI)
        if prev_gray is not None:
            diff = gray.astype(np.float32) - prev_gray.astype(np.float32)
            ti_vals.append(np.std(diff))

        prev_gray = gray

    cap.release()

    return np.mean(si_vals), np.mean(ti_vals) if ti_vals else 0.0

def categorize_video(si, ti):
    if si < 20 and ti < 10:
        return "Low Detail / Low Motion"
    elif si > 50 and ti > 20:
        return "High Detail / High Motion"
    elif si > 50:
        return "High Detail / Low Motion"
    elif ti > 20:
        return "Low Detail / High Motion"
    else:
        return "Moderate"

# ------------------------- FILE PROCESSING -------------------------

def get_video_files(folder):
    all_files = []
    for ext in SUPPORTED_FORMATS:
        all_files.extend(glob.glob(os.path.join(folder, ext)))
    return all_files

def analyze_videos(folder):
    video_files = get_video_files(folder)
    results = []

    print("\n[INFO] Processing videos...\n")
    for video_path in video_files:
        filename = os.path.basename(video_path)
        si, ti = compute_siti(video_path)
        category = categorize_video(si, ti)
        print(f"{filename} => SI: {si:.2f}, TI: {ti:.2f} → {category}")
        results.append((filename, si, ti, category))
    return results

# ------------------------- OUTPUT UTILS -------------------------

def save_results_csv(results):
    df = pd.DataFrame(results, columns=["Filename", "SI", "TI", "Category"])
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    output_csv = os.path.join(OUTPUT_FOLDER, "siti_results.csv")
    df.to_csv(output_csv, index=False)
    print(f"\n[✓] Results saved to {output_csv}")
    return df

def plot_si_ti(df):
    plt.figure(figsize=(10, 7))
    scatter = plt.scatter(df["SI"], df["TI"], c='blue', edgecolors='k', s=100)

    for i in range(len(df)):
        plt.text(df["SI"][i]+0.5, df["TI"][i]+0.5, df["Filename"][i][:12], fontsize=8)

    plt.title("Video Content Complexity: SI vs. TI", fontsize=14)
    plt.xlabel("Spatial Information (SI)")
    plt.ylabel("Temporal Information (TI)")
    plt.grid(True)
    plt.tight_layout()

    output_plot = os.path.join(OUTPUT_FOLDER, "siti_scatter_plot.png")
    plt.savefig(output_plot)
    plt.show()
    print(f"[✓] Plot saved to {output_plot}")

# ------------------------- MAIN -------------------------

if __name__ == "__main__":
    results = analyze_videos(INPUT_FOLDER)
    if results:
        df = save_results_csv(results)
        plot_si_ti(df)
    else:
        print("[!] No videos found or unable to process.")
