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

# --- Configuration ---
reference_video = "Dancers_8s.mp4" # Your high-quality reference video

# Define the resolutions and QP values you've encoded for H.265.
# This structure helps generate filenames and iterate.
encode_settings = {
    "360": ["24", "30"],
    "720": ["24", "30", "36"],
    "1080": ["24", "30", "36"],
    "2160": ["24", "30", "36"]
}

# Define the full list of encoded video filenames based on the settings
encoded_videos = []
for res, qp_list in encode_settings.items():
    for qp in qp_list:
        # Filename pattern for H.265 using 'qp'
        # IMPORTANT: Ensure your H.265 files actually follow this pattern, e.g., Dancers_8s_h265_360p_qp24.mp4
        encoded_videos.append(f"Dancers_8s_h265_{res}p_qp{qp}.mp4") # Changed from _av1_ to _h265_ and .mkv to .mp4 (common for H.265)

# Directory for VMAF JSON logs and CSV/plot outputs for H.265
output_log_dir = "vmaf_logs_dancers_h265"
os.makedirs(output_log_dir, exist_ok=True)

# --- VMAF Model Configuration ---
# IMPORTANT: Download 'vmaf_4k_v0.6.1.json' from
# https://github.com/Netflix/vmaf/tree/master/model
# and place it in the directory specified below.
VMAF_MODELS_DIR = "vmaf_models" # Directory to store VMAF model files
os.makedirs(VMAF_MODELS_DIR, exist_ok=True) # Ensure the directory exists
VMAF_4K_MODEL_NAME = "vmaf_4k_v0.6.1.json"
VMAF_4K_MODEL_PATH = os.path.join(VMAF_MODELS_DIR, VMAF_4K_MODEL_NAME)

# Verify the 4K VMAF model file exists
if not os.path.exists(VMAF_4K_MODEL_PATH):
    print(f"ERROR: 4K VMAF model file not found at '{VMAF_4K_MODEL_PATH}'.")
    print(f"Please download '{VMAF_4K_MODEL_NAME}' from https://github.com/Netflix/vmaf/tree/master/model")
    print(f"and place it in the '{VMAF_MODELS_DIR}' directory.")
    print("Exiting script.")
    exit() # Exit if the model file is not found

# --- VMAF Comparison Settings ---
# Scaling both reference and distorted to 3840x2160 (4K) at 60fps for VMAF comparison.
VMAF_COMPARISON_RESOLUTION = "3840x2160"
VMAF_COMPARISON_FPS = "60"

vmaf_results_data = []

print(f"Starting VMAF analysis for '{reference_video}' using 4K VMAF model (H.265)...")

for encoded_file in encoded_videos:
    # --- Parse resolution and QP from filename ---
    # Example filename: Dancers_8s_h265_360p_qp24.mp4
    parts = encoded_file.split('_')
    try:
        # Find the part containing resolution (e.g., '360p')
        res_str = next(p for p in parts if 'p' in p and p.replace('p', '').isdigit())
        resolution = int(res_str.replace('p', ''))

        # Find the part containing qp (e.g., 'qp24.mp4')
        qp_str_with_ext = next(p for p in parts if 'qp' in p and (p.endswith('.mp4') or p.endswith('.mkv')))
        qp_value = int(qp_str_with_ext.replace('qp', '').rsplit('.', 1)[0]) # Remove 'qp' and file extension
    except (StopIteration, ValueError) as e:
        print(f"Skipping '{encoded_file}': Could not parse resolution or QP. Error: {e}")
        continue

    json_log_path = os.path.join(output_log_dir, f"{os.path.splitext(encoded_file)[0]}.json")

    # --- FFmpeg VMAF Command ---
    # The VMAF filter expects [reference_stream][distorted_stream] as inputs.
    # In 'ffmpeg -i encoded_file -i reference_video', encoded_file is [0:v] and reference_video is [1:v].
    # Using 'model=' for 4K VMAF model.
    # Removed 'name' and 'psnr' options as they caused issues with your FFmpeg build.
    filter_complex_cmd = (
        f"[0:v]scale={VMAF_COMPARISON_RESOLUTION}:flags=bicubic,fps={VMAF_COMPARISON_FPS}[main]; "
        f"[1:v]scale={VMAF_COMPARISON_RESOLUTION}:flags=bicubic,fps={VMAF_COMPARISON_FPS}[ref]; "
        f"[main][ref]libvmaf=model='path={VMAF_4K_MODEL_PATH.replace(os.sep, '/')}'" \
        f":log_fmt=json:log_path='{json_log_path.replace(os.sep, '/')}'"
    )

    ffmpeg_cmd = [
        "ffmpeg",
        "-i", encoded_file,    # Input 0: Distorted video
        "-i", reference_video, # Input 1: Reference video
        "-lavfi", filter_complex_cmd,
        "-f", "null", "-" # Output to null, we only care about VMAF logs
    ]

    print(f"Running VMAF for {encoded_file} (Resolution: {resolution}p, QP: {qp_value})...")
    process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

    if process.returncode != 0:
        print(f"ERROR running FFmpeg for {encoded_file}:")
        print(process.stderr)
        continue

    if not os.path.exists(json_log_path):
        print(f"VMAF JSON log not created for {encoded_file} — skipping.")
        continue

    # --- Parse VMAF Results ---
    try:
        with open(json_log_path, 'r', encoding='utf-8') as f:
            vmaf_data = json.load(f)
        vmaf_scores = [frame['metrics']['vmaf'] for frame in vmaf_data['frames']]
        avg_vmaf = sum(vmaf_scores) / len(vmaf_scores) if vmaf_scores else 0
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"Error reading or parsing VMAF JSON for {encoded_file}: {e} — skipping.")
        continue

    # --- Get Bitrate using FFprobe ---
    probe_cmd = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "format=bit_rate", "-of", "json", encoded_file
    ]
    bitrate_output = subprocess.run(probe_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

    bitrate_kbps = None
    if bitrate_output.returncode == 0:
        try:
            bitrate_json = json.loads(bitrate_output.stdout)
            if 'format' in bitrate_json and 'bit_rate' in bitrate_json['format']:
                bitrate_kbps = int(bitrate_json['format']['bit_rate']) / 1000
        except json.JSONDecodeError:
            print(f"Warning: Could not parse ffprobe output for bitrate of {encoded_file}")
    else:
        print(f"Error running ffprobe for {encoded_file}:\n{bitrate_output.stderr}")

    vmaf_results_data.append({
        "video": encoded_file,
        "resolution": resolution,
        "qp": qp_value, # Using 'qp' column name
        "bitrate_kbps": bitrate_kbps,
        "vmaf": avg_vmaf
    })

df = pd.DataFrame(vmaf_results_data)
# Save results to a H.265-specific CSV
df.to_csv("vmaf_results_dancers_h265.csv", index=False)
print("\n--- VMAF Analysis Complete ---")
print("Results saved to vmaf_results_dancers_h265.csv")


# --- Plotting ---
sns.set_style("whitegrid")

# Check if DataFrame is empty before plotting
if df.empty:
    print("\nNo VMAF data was successfully processed. Cannot generate plots.")
else:
    # --- Plot 1: VMAF Scatter: Encoded vs. Reference ---
    plt.figure(figsize=(12, 10))
    ax_scatter = plt.gca()

    df['vmaf_reference_for_plot'] = df['vmaf']

    # Define markers for QP values
    qp_markers = {24: 'o', 30: '^', 36: 'D'}

    # Define a consistent color palette for resolutions
    resolution_colors = {360: 'blue', 720: 'green', 1080: 'orange', 2160: 'red'}

    # Plot each point with specific marker and color
    for (res, qp), group in df.groupby(['resolution', 'qp']): # Group by 'qp'
        marker = qp_markers.get(qp, 's')
        color = resolution_colors.get(res, 'gray')
        label = f"{res}p"

        ax_scatter.scatter(
            group['vmaf'],
            group['vmaf'],
            label=label,
            s=150,
            marker=marker,
            color=color,
            edgecolors='black',
            linewidths=0.8,
            zorder=5
        )

    # Add the 1:1 diagonal line
    plt.plot([0, 100], [0, 100], color='lightgray', linestyle='--', linewidth=1.5, zorder=1)

    # Add VMAF score labels to points
    texts_scatter = []
    for i, row in df.iterrows():
        texts_scatter.append(plt.text(
            row['vmaf'] + 0.5,
            row['vmaf'] + 1.0,
            f"{row['vmaf']:.1f}",
            fontsize=9,
            ha='left',
            va='bottom'
        ))

    if adjust_text:
        adjust_text(texts_scatter, ax=ax_scatter, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6, lw=0.5))

    from matplotlib.lines import Line2D
    legend_elements_res = [Line2D([0], [0], marker='s', color='w', label=f'{res}p',
                                  markerfacecolor=color, markersize=10, markeredgecolor='black')
                           for res, color in resolution_colors.items()]
    legend_elements_qp = [Line2D([0], [0], marker=marker, color='w', label=f'QP {qp}', # Label as 'QP'
                                  markerfacecolor='gray', markersize=10, markeredgecolor='black')
                           for qp, marker in qp_markers.items()]

    # Combine and place legends
    legend1 = ax_scatter.legend(handles=legend_elements_res, title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left')
    ax_scatter.add_artist(legend1)
    legend2 = ax_scatter.legend(handles=legend_elements_qp, title="QP", bbox_to_anchor=(1.02, 0.6), loc='upper left') # Title as 'QP'

    plt.title(f"VMAF Scatter: Encoded vs. Reference ({os.path.basename(reference_video)}) (Scaled to 4K) (H.265)", fontsize=16) # Updated title
    plt.xlabel(f"VMAF Score (Encoded Video)", fontsize=12)
    plt.ylabel(f"VMAF Score (Reference Video)", fontsize=12)
    plt.xlim(0, 100)
    plt.ylim(0, 100)
    plt.tight_layout(rect=[0, 0, 0.88, 1])
    plt.savefig("vmaf_scatter_encoded_vs_reference_dancers_h265.png", dpi=300) # Updated filename
    plt.show()

    # --- Plot 2: VMAF vs. QP ---
    plt.figure(figsize=(12, 8))
    ax_qp = sns.scatterplot(
        data=df,
        x="qp", # Use 'qp' column
        y="vmaf",
        hue="resolution",
        palette=resolution_colors,
        s=150,
        zorder=5
    )

    sns.regplot(
        data=df,
        x="qp", # Use 'qp' column
        y="vmaf",
        scatter=False,
        color="blue",
        ci=None,
        order=2, # Quadratic fit
        ax=ax_qp
    )

    texts_qp = []
    for i, row in df.iterrows():
        texts_qp.append(plt.text(
            row['qp'], # Use 'qp'
            row['vmaf'] + 1.0,
            f"{row['vmaf']:.1f}",
            fontsize=9,
            ha='center',
            va='bottom'
        ))

    if adjust_text:
        adjust_text(texts_qp, ax=ax_qp, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6, lw=0.5))

    pcc_qp, _ = pearsonr(df["qp"], df["vmaf"])
    mse_vmaf_qp = mean_squared_error(df["vmaf"], df["qp"])
    rmse_vmaf_qp = np.sqrt(mse_vmaf_qp)

    plt.title(f"VMAF vs. QP for '{os.path.basename(reference_video)}' (H.265) (4K Model)\nPCC = {pcc_qp:.3f}, RMSE = {rmse_vmaf_qp:.3f}", fontsize=16) # Updated title
    plt.xlabel("QP (Quantization Parameter)", fontsize=12)
    plt.ylabel(f"VMAF Score (0-100) (Scaled to {VMAF_COMPARISON_RESOLUTION})", fontsize=12)
    plt.ylim(0, 100)
    min_qp = df['qp'].min()
    max_qp = df['qp'].max()
    plt.xlim(min_qp - 2, max_qp + 2)
    plt.xticks(sorted(df['qp'].unique()))
    plt.legend(title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.savefig("vmaf_vs_qp_dancers_h265_4k_model.png", dpi=300) # Updated filename
    plt.show()

    # --- Plot 3: Bitrate vs. VMAF ---
    plt.figure(figsize=(12, 8))
    ax_bitrate = sns.scatterplot(
        data=df,
        x="bitrate_kbps",
        y="vmaf",
        hue="resolution",
        palette=resolution_colors,
        s=150,
        zorder=5
    )

    sns.regplot(
        data=df,
        x="bitrate_kbps",
        y="vmaf",
        scatter=False,
        color="red",
        ci=None,
        order=2, # Quadratic fit
        ax=ax_bitrate
    )

    texts_bitrate = []
    for i, row in df.iterrows():
        if pd.notna(row['bitrate_kbps']): # Only label if bitrate is not NaN
            texts_bitrate.append(plt.text(
                row['bitrate_kbps'],
                row['vmaf'] + 1.0,
                f"{row['vmaf']:.1f}",
                fontsize=9,
                ha='center',
                va='bottom'
            ))

    if adjust_text:
        adjust_text(texts_bitrate, ax=ax_bitrate, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6, lw=0.5))

    pcc_bitrate, _ = pearsonr(df["bitrate_kbps"].dropna(), df["vmaf"].dropna()) # Drop NaN for correlation
    mse_bitrate_vmaf = mean_squared_error(df["vmaf"].dropna(), df["bitrate_kbps"].dropna())
    rmse_bitrate_vmaf = np.sqrt(mse_bitrate_vmaf)

    plt.title(f"Bitrate vs. VMAF for '{os.path.basename(reference_video)}' (H.265) (4K Model)\nPCC = {pcc_bitrate:.3f}, RMSE = {rmse_bitrate_vmaf:.3f}", fontsize=16) # Updated title
    plt.xlabel("Bitrate (kbps)", fontsize=12)
    plt.ylabel(f"VMAF Score (0-100) (Scaled to {VMAF_COMPARISON_RESOLUTION})", fontsize=12)
    plt.ylim(0, 100)
    plt.legend(title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.savefig("bitrate_vs_vmaf_dancers_h265_4k_model.png", dpi=300) # Updated filename
    plt.show()

print("\nScript finished.")