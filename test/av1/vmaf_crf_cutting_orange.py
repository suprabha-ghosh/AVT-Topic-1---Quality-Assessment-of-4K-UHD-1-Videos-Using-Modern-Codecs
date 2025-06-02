import os
import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error
from scipy.stats import pearsonr
import numpy as np

try:
    from adjustText import adjust_text
except ImportError:
    print("adjustText not found. Install with: pip install adjustText")
    adjust_text = None

reference = "cutting_orange_tuil_8s.mp4"
encoded_videos = [
    "cutting_orange_tuil_8s_av1_360p_crf18.mkv", "cutting_orange_tuil_8s_av1_360p_crf24.mkv",
    "cutting_orange_tuil_8s_av1_360p_crf30.mkv", "cutting_orange_tuil_8s_av1_360p_crf36.mkv",
    "cutting_orange_tuil_8s_av1_720p_crf18.mkv", "cutting_orange_tuil_8s_av1_720p_crf24.mkv",
    "cutting_orange_tuil_8s_av1_720p_crf30.mkv", "cutting_orange_tuil_8s_av1_720p_crf36.mkv",
    "cutting_orange_tuil_8s_av1_1080p_crf18.mkv", "cutting_orange_tuil_8s_av1_1080p_crf24.mkv",
    "cutting_orange_tuil_8s_av1_1080p_crf30.mkv", "cutting_orange_tuil_8s_av1_1080p_crf36.mkv",
    "cutting_orange_tuil_8s_av1_2160p_crf18.mkv", "cutting_orange_tuil_8s_av1_2160p_crf24.mkv",
    "cutting_orange_tuil_8s_av1_2160p_crf30.mkv", "cutting_orange_tuil_8s_av1_2160p_crf36.mkv"
]

os.makedirs("vmaf_json_cuttin_orange_tuil_av1", exist_ok=True)

vmaf_results = []

for encoded in encoded_videos:
    # --- CORRECTED INDEXES FOR RESOLUTION AND CRF EXTRACTION ---
    # Based on filename structure: cuttin_orange_tuil_8s_av1_360p_crf18.mkv
    # split('_') gives:
    # ['cuttin', 'orange', 'tuil', '8s', 'av1', '360p', 'crf18.mkv']
    res = encoded.split('_')[5].replace('p', '')  # '360p' is at index 5
    crf_str = encoded.split('_')[6].replace('.mkv', '') # 'crf18.mkv' is at index 6
    crf = int(crf_str.replace('crf', ''))
    json_path = f"vmaf_json_cuttin_orange_tuil_av1/{encoded.replace('.mkv', '')}.json"

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
        continue

    if not os.path.exists(json_path):
        print(f"Missing VMAF JSON for {encoded} — skipping.")
        continue

    with open(json_path, 'r') as f:
        data = json.load(f)
    vmaf_scores = [frame['metrics']['vmaf'] for frame in data['frames']]
    avg_vmaf = sum(vmaf_scores) / len(vmaf_scores)

    probe_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "format=bit_rate", "-of", "json", encoded]
    bitrate_output = subprocess.run(probe_cmd, capture_output=True, text=True)
    bitrate_json = json.loads(bitrate_output.stdout)
    bitrate = int(bitrate_json['format']['bit_rate']) / 1000 if 'bit_rate' in bitrate_json['format'] else None

    vmaf_results.append({
        "video": encoded,
        "resolution": res,
        "crf": crf,
        "bitrate_kbps": bitrate,
        "vmaf": avg_vmaf
    })

df = pd.DataFrame(vmaf_results)
df.to_csv("vmaf_results_cuttin_orange_tuil_av1.csv", index=False)

sns.set(style="whitegrid")
plt.figure(figsize=(12, 9))
ax = sns.scatterplot(data=df, x="crf", y="vmaf", hue="resolution", alpha=0.7, palette="viridis", s=150)
sns.regplot(data=df, x="crf", y="vmaf", scatter=False, color="blue", ci=None, order=2)

texts = []
for i, row in df.iterrows():
    texts.append(plt.text(row['crf'], row['vmaf'] + 0.5, f"{row['vmaf']:.1f}",
                              fontsize=8, ha='center', va='bottom'))

if adjust_text:
    adjust_text(texts, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6))

pcc, _ = pearsonr(df["crf"], df["vmaf"])
mse = mean_squared_error(df["vmaf"], df["crf"]) # This MSE calculation (VMAF vs CRF) is unusual. Usually, it's actual vs predicted.
rmse = np.sqrt(mse) # RMSE here means RMSE of VMAF scores compared to CRF values, not typically a quality metric.

plt.title(f"VMAF vs. CRF for AV1: '{reference}'\nPCC = {pcc:.3f}, RMSE = {rmse:.3f}", fontsize=16)
plt.xlabel("CRF", fontsize=14)
plt.ylabel("VMAF", fontsize=14)
plt.ylim(0, 100)
plt.xlim(15, 38)
plt.legend(title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left')
plt.tight_layout(rect=[0, 0, 0.95, 1])
plt.savefig("vmaf_vs_crf_av1_cuttin_orange_tuil.png")
plt.show()

# Bitrate vs VMAF plot
plt.figure(figsize=(12, 9))
sns.scatterplot(data=df, x="bitrate_kbps", y="vmaf", hue="resolution", palette="magma", s=150)
sns.regplot(data=df, x="bitrate_kbps", y="vmaf", scatter=False, color="red", ci=None, order=2)
plt.xlabel("Bitrate (kbps)", fontsize=14)
plt.ylabel("VMAF", fontsize=14)
plt.title("Bitrate vs. VMAF for AV1 Encoded Videos", fontsize=16)
plt.grid(True)
plt.tight_layout()
plt.savefig("bitrate_vs_vmaf_av1_cuttin_orange_tuil.png")
plt.show()