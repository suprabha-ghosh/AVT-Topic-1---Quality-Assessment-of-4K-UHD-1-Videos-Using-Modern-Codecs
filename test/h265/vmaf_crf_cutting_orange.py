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

reference = "cutting_orange_tuil_8s.mp4"
encoded_videos = [
    "cutting_orange_tuil_8s_h265_360p_crf18.mp4", "cutting_orange_tuil_8s_h265_360p_crf24.mp4",
    "cutting_orange_tuil_8s_h265_360p_crf30.mp4", "cutting_orange_tuil_8s_h265_360p_crf36.mp4",
    "cutting_orange_tuil_8s_h265_720p_crf18.mp4", "cutting_orange_tuil_8s_h265_720p_crf24.mp4",
    "cutting_orange_tuil_8s_h265_720p_crf30.mp4", "cutting_orange_tuil_8s_h265_720p_crf36.mp4",
    "cutting_orange_tuil_8s_h265_1080p_crf18.mp4", "cutting_orange_tuil_8s_h265_1080p_crf24.mp4",
    "cutting_orange_tuil_8s_h265_1080p_crf30.mp4", "cutting_orange_tuil_8s_h265_1080p_crf36.mp4",
    "cutting_orange_tuil_8s_h265_2160p_crf18.mp4", "cutting_orange_tuil_8s_h265_2160p_crf24.mp4",
    "cutting_orange_tuil_8s_h265_2160p_crf30.mp4", "cutting_orange_tuil_8s_h265_2160p_crf36.mp4"
]

os.makedirs("vmaf_json_cutting_orange_tuil", exist_ok=True)

vmaf_results = []

for encoded in encoded_videos:
    # --- CRITICAL CHANGE HERE ---
    # For 'cutting_orange_tuil_8s_h265_360p_crf18.mp4', '360p' is at index 5
    res = encoded.split('_')[5].replace('p', '')
    # The CRF string is still correctly identified by [-1] (last element)
    crf_str = encoded.split('_')[-1].replace('.mp4', '')
    crf = int(crf_str.replace('crf', ''))

    json_path = f"vmaf_json_cutting_orange_tuil/{encoded.replace('.mp4', '')}.json"

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
df.to_csv("vmaf_results_cutting_orange_tuil.csv", index=False)

# Plotting
sns.set(style="whitegrid")
plt.figure(figsize=(12, 9)) # Further adjusted figure size for more room for labels

# Scatter plot with hue for resolution
ax = sns.scatterplot(data=df, x="crf", y="vmaf", hue="resolution", alpha=0.7, palette="viridis", s=150) # Increased marker size and alpha

# Regression line
sns.regplot(data=df, x="crf", y="vmaf", scatter=False, color="blue", ci=None)

# Add VMAF score labels to each point
texts = []
for i, row in df.iterrows():
    # Use f-string for formatted label: "{score:.1f}" means one decimal place
    texts.append(plt.text(row['crf'], row['vmaf'] + 0.5, f"{row['vmaf']:.1f}",
                          fontsize=8, ha='center', va='bottom'))

# Use adjust_text if available to prevent label overlap
if adjust_text: # This condition is now active
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

# Set y-axis and x-axis limits as requested
plt.ylim(0, 100)
plt.xlim(15, 38)

plt.xticks(fontsize=12)
plt.yticks(fontsize=12)
plt.legend(title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.) # Adjust legend position
plt.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout(rect=[0, 0, 0.95, 1]) # Adjust layout to make space for the legend outside the plot area
plt.savefig("vmaf_vs_crf_scatter_with_scores_cutting_orange_tuil.png")
plt.show()