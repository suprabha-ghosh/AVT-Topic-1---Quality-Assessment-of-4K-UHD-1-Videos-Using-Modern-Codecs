import os
import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error
from scipy.stats import pearsonr
import numpy as np

# Ensure adjustText is installed for better label placement (optional but recommended for many labels)
try:
    from adjustText import adjust_text
except ImportError:
    print("adjustText not found. Install with: pip install adjustText")
    print("Labels might overlap without adjustText.")
    adjust_text = None

reference = "water_netflix.mp4" # Updated reference name
encoded_videos = [
    "water_netflix_av1_360p_crf18.mp4", "water_netflix_av1_360p_crf24.mp4",
    "water_netflix_av1_360p_crf30.mp4", "water_netflix_av1_360p_crf36.mp4",
    "water_netflix_av1_720p_crf18.mp4", "water_netflix_av1_720p_crf24.mp4",
    "water_netflix_av1_720p_crf30.mp4", "water_netflix_av1_720p_crf36.mp4",
    "water_netflix_av1_1080p_crf18.mp4", "water_netflix_av1_1080p_crf24.mp4",
    "water_netflix_av1_1080p_crf30.mp4", "water_netflix_av1_1080p_crf36.mp4",
    "water_netflix_av1_2160p_crf18.mp4", "water_netflix_av1_2160p_crf24.mp4",
    "water_netflix_av1_2160p_crf30.mp4", "water_netflix_av1_2160p_crf36.mp4"
]

os.makedirs("vmaf_json_water", exist_ok=True)

vmaf_results = []

for encoded in encoded_videos:
    # --- CRITICAL CHANGE HERE: Corrected indices for Dancers_8s filenames ---
    # For 'Dancers_8s_h265_360p_crf18.mp4', '360p' is at index 3
    res = encoded.split('_')[3].replace('p', '')
    # For 'Dancers_8s_h265_360p_crf18.mp4', 'crf18.mp4' is at index 4 (or -1 for the last)
    crf_str = encoded.split('_')[4].replace('.mp4', '') # Using [4] explicitly
    crf = int(crf_str.replace('crf', ''))

    json_path = f"vmaf_json_water/{encoded.replace('.mp4', '')}.json"

    cmd = [
        "ffmpeg",
        "-i", reference,
        "-i", encoded,
        "-lavfi",
        f"[0:v]scale={res}:-2:flags=bicubic[ref];"
        f"[1:v]scale={res}:-2:flags=bicubic[dist];"
        f"[ref][dist]libvmaf=log_path={json_path}:log_fmt=json",
        "-f", "null", "-"
    ]

    print(f"Running VMAF for {encoded}...")
    process = subprocess.run(cmd, capture_output=True, text=True)

    if process.returncode != 0:
        print(f"ERROR running ffmpeg for {encoded}:")
        print(process.stderr)
        raise RuntimeError("FFmpeg VMAF failed — cannot continue without fixing errors.")

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"VMAF JSON file not found for {encoded}. Something went wrong.")

    with open(json_path, 'r') as f:
        data = json.load(f)
    vmaf_scores_frame = [frame['metrics']['vmaf'] for frame in data['frames']]
    avg_vmaf = sum(vmaf_scores_frame) / len(vmaf_scores_frame)

    print(f"VMAF for {encoded}: {avg_vmaf:.3f}")

    vmaf_results.append({
        "video": encoded,
        "resolution": res,
        "crf": crf,
        "vmaf": avg_vmaf
    })

df = pd.DataFrame(vmaf_results)
df.to_csv("vmaf_results_water.csv", index=False)

# Plotting
sns.set(style="whitegrid")
plt.figure(figsize=(12, 9))

# Scatter plot with hue for resolution
ax = sns.scatterplot(data=df, x="crf", y="vmaf", hue="resolution", alpha=0.7, palette="viridis", s=150)

# --- Polynomial Regression (Curved Line) ---
sns.regplot(data=df, x="crf", y="vmaf", scatter=False, color="blue", ci=None, order=2) # Changed to order=2 for a quadratic curve

# Add VMAF score labels to each point
texts = []
for i, row in df.iterrows():
    texts.append(plt.text(row['crf'], row['vmaf'] + 0.5, f"{row['vmaf']:.1f}",
                          fontsize=8, ha='center', va='bottom'))

# Use adjust_text if available to prevent label overlap
if adjust_text:
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6))
else:
    print("\nTo prevent text labels from overlapping, consider installing 'adjustText': pip install adjustText")


# Calculate PCC and RMSE
pcc, _ = pearsonr(df["crf"], df["vmaf"])
mse = mean_squared_error(df["vmaf"], df["crf"])
rmse = np.sqrt(mse)

# Title with PCC, RMSE, and reference video name
plt.title(f"VMAF vs. CRF for '{reference}' Encoded Videos\nPCC = {pcc:.3f}, RMSE = {rmse:.3f}", fontsize=16)
plt.xlabel("CRF (Constant Rate Factor)", fontsize=14)
plt.ylabel("VMAF Score (0-100)", fontsize=14)

plt.ylim(0, 100)
plt.xlim(15, 38)

plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.legend(title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout(rect=[0, 0, 0.95, 1])
plt.savefig("vmaf_vs_crf_scatter_with_scores_water_curve.png")
plt.show()