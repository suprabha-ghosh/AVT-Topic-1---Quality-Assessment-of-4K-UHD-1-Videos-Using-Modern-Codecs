import os
import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import pearsonr
import numpy as np
from sklearn.metrics import mean_squared_error

# Try to import adjustText for better label placement
try:
    from adjustText import adjust_text
    has_adjust_text = True
except ImportError:
    print("[INFO] adjustText library not found. Install with: pip install adjustText")
    print("[INFO] Text labels may overlap in plots.")
    has_adjust_text = False


class VMAFAnalyzer:
    def __init__(self, codec="vvc"):
        # Set codec
        self.codec = codec.lower()  # vvc, av1, h265, etc.
        
        # Base directories
        self.base_dir = Path(f"vmaf_analysis_{self.codec}")
        self.source_dir = Path("video_source")
        
        # Input directories based on codec
        if self.codec == "vvc":
            self.encoded_dir = Path("vvc_decoded_videos")
        elif self.codec == "av1":
            self.encoded_dir = Path("av1_encoded_videos")
        elif self.codec == "h265":
            self.encoded_dir = Path("h265_encoded_videos")
        else:
            self.encoded_dir = Path(f"{self.codec}_encoded_videos")
        
        # Output directories
        self.json_dir = self.base_dir / "json_results"
        self.plots_dir = self.base_dir / "plots"
        self.csv_dir = self.base_dir / "csv_results"
        
        # Create output directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.plots_dir.mkdir(parents=True, exist_ok=True)
        self.csv_dir.mkdir(parents=True, exist_ok=True)
        
        # VMAF model configuration
        self.vmaf_models_dir = Path("vmaf_models")
        self.vmaf_models_dir.mkdir(parents=True, exist_ok=True)
        self.vmaf_model_name = "vmaf_4k_v0.6.1.json"
        self.vmaf_model_path = self.vmaf_models_dir / self.vmaf_model_name
        
        # VMAF comparison settings
        self.comparison_resolution = "3840x2160"
        self.comparison_fps = "60"
        
        # Encoding settings
        self.resolutions = [360, 720, 1080, 2160]
        self.qp_values = [24, 30, 36]
        
        # File extensions
        self.supported_ext = [".mp4", ".mkv", ".webm", ".vvc", ".avi", ".mov", ".y4m"]
        
        # Plotting settings
        self.resolution_colors = {360: 'blue', 720: 'green', 1080: 'orange', 2160: 'red'}
        self.qp_markers = {24: 'o', 30: '^', 36: 'D'}

    def verify_setup(self):
        """Verify that the VMAF model exists"""
        if not self.vmaf_model_path.exists():
            print(f"ERROR: 4K VMAF model file not found at '{self.vmaf_model_path}'.")
            print(f"Please download '{self.vmaf_model_name}' from https://github.com/Netflix/vmaf/tree/master/model")
            print(f"and place it in the '{self.vmaf_models_dir}' directory.")
            return False
        return True

    def run_vmaf(self, reference_path, encoded_path, json_path):
        """Run VMAF analysis with upscaling to 4K"""
        filter_complex_cmd = (
            f"[0:v]scale={self.comparison_resolution}:flags=bicubic,fps={self.comparison_fps}[main]; "
            f"[1:v]scale={self.comparison_resolution}:flags=bicubic,fps={self.comparison_fps}[ref]; "
            f"[main][ref]libvmaf=model='path={str(self.vmaf_model_path).replace(os.sep, '/')}'"
            f":log_fmt=json:log_path='{str(json_path).replace(os.sep, '/')}'"
        )
        
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", str(encoded_path),    # Input 0: Distorted video
            "-i", str(reference_path),  # Input 1: Reference video
            "-lavfi", filter_complex_cmd,
            "-f", "null", "-"  # Output to null, we only care about VMAF logs
        ]
        
        try:
            process = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if process.returncode != 0:
                print(f"ERROR running FFmpeg for {encoded_path}:")
                print(process.stderr)
                return False
            return True
        except Exception as e:
            print(f"Exception during VMAF calculation: {e}")
            return False

    def get_bitrate(self, video_path):
        """Get video bitrate using ffprobe"""
        probe_cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "format=bit_rate", "-of", "json", str(video_path)
        ]
        
        try:
            bitrate_output = subprocess.run(probe_cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
            if bitrate_output.returncode == 0:
                bitrate_json = json.loads(bitrate_output.stdout)
                if 'format' in bitrate_json and 'bit_rate' in bitrate_json['format']:
                    return int(bitrate_json['format']['bit_rate']) / 1000
        except Exception as e:
            print(f"Error getting bitrate for {video_path}: {e}")
        
        return None

    def extract_vmaf_score(self, json_path):
        """Extract VMAF score from JSON result file"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                vmaf_data = json.load(f)
            
            vmaf_scores = [frame['metrics']['vmaf'] for frame in vmaf_data['frames']]
            avg_vmaf = sum(vmaf_scores) / len(vmaf_scores) if vmaf_scores else 0
            return avg_vmaf
        except Exception as e:
            print(f"Error extracting VMAF score from {json_path}: {e}")
            return None

    def analyze_videos(self):
        """Process all videos and calculate VMAF scores"""
        if not self.verify_setup():
            return
        
        # Find all source videos
        source_videos = {}
        for ext in self.supported_ext:
            for file in self.source_dir.glob(f"*{ext}"):
                source_videos[file.stem.lower()] = file
        
        if not source_videos:
            print(f"No source videos found in {self.source_dir}")
            return
        
        # Process each source video
        for source_name, source_path in source_videos.items():
            print(f"\nProcessing source video: {source_name}")
            
            # Create output directories for this source
            vmaf_logs_dir = self.json_dir / f"{source_name}"
            vmaf_logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Find encoded videos for this source
            encoded_files = []
            for res in self.resolutions:
                for qp in self.qp_values:
                    pattern = f"{source_name}_{self.codec}_{res}p_qp{qp}.*"
                    matches = list(self.encoded_dir.glob(pattern))
                    if matches:
                        encoded_files.extend(matches)
            
            if not encoded_files:
                print(f"No encoded videos found for {source_name}")
                continue
                
            print(f"Found {len(encoded_files)} encoded videos for {source_name}")
            
            # Process each encoded video
            vmaf_results = []
            for encoded_file in encoded_files:
                # Parse resolution and QP from filename
                parts = encoded_file.stem.split('_')
                try:
                    # Find resolution part (e.g., '360p')
                    res_part = next(p for p in parts if p.endswith('p') and p[:-1].isdigit())
                    resolution = int(res_part.replace('p', ''))
                    
                    # Find QP part (e.g., 'qp24')
                    qp_part = next(p for p in parts if p.startswith('qp') and p[2:].isdigit())
                    qp_value = int(qp_part.replace('qp', ''))
                except (StopIteration, ValueError) as e:
                    print(f"Skipping '{encoded_file.name}': Could not parse resolution or QP. Error: {e}")
                    continue
                
                # Set up JSON log path
                json_log_path = vmaf_logs_dir / f"{encoded_file.stem}.json"
                
                print(f"Running VMAF for {encoded_file.name} (Resolution: {resolution}p, QP: {qp_value})...")
                
                # Run VMAF calculation
                success = self.run_vmaf(source_path, encoded_file, json_log_path)
                
                if not success or not json_log_path.exists():
                    print(f"VMAF calculation failed for {encoded_file.name}")
                    continue
                
                # Extract VMAF score
                vmaf_score = self.extract_vmaf_score(json_log_path)
                if vmaf_score is None:
                    continue
                
                # Get bitrate
                bitrate_kbps = self.get_bitrate(encoded_file)
                
                # Add to results
                vmaf_results.append({
                    "video": str(encoded_file),
                    "resolution": resolution,
                    "qp": qp_value,
                    "bitrate_kbps": bitrate_kbps,
                    "vmaf": vmaf_score
                })
                
                print(f"VMAF score: {vmaf_score:.2f}")
            
            # Save results to CSV
            if vmaf_results:
                df = pd.DataFrame(vmaf_results)
                csv_path = self.csv_dir / f"vmaf_results_{source_name}.csv"
                df.to_csv(csv_path, index=False)
                print(f"Results saved to {csv_path}")
                
                # Generate plots
                self.generate_plots(df, source_name, source_path)
            else:
                print(f"No VMAF results were successfully processed for {source_name}")
    
    def generate_plots(self, df, source_name, reference_video):
        """Generate plots from VMAF results"""
        if df.empty:
            print("No data to plot")
            return
            
        # Set plot style
        sns.set_style("whitegrid")
        
        # --- Plot 1: VMAF Scatter: Encoded vs. Reference ---
        plt.figure(figsize=(12, 10))
        ax_scatter = plt.gca()

        df['vmaf_reference_for_plot'] = df['vmaf']

        # Plot each point with specific marker and color
        for (res, qp), group in df.groupby(['resolution', 'qp']):
            marker = self.qp_markers.get(qp, 's')
            color = self.resolution_colors.get(res, 'gray')
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

        if has_adjust_text:
            adjust_text(texts_scatter, ax=ax_scatter, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6, lw=0.5))

        from matplotlib.lines import Line2D
        legend_elements_res = [Line2D([0], [0], marker='s', color='w', label=f'{res}p',
                                      markerfacecolor=color, markersize=10, markeredgecolor='black')
                               for res, color in self.resolution_colors.items() if res in df['resolution'].values]
        legend_elements_qp = [Line2D([0], [0], marker=marker, color='w', label=f'QP {qp}',
                                      markerfacecolor='gray', markersize=10, markeredgecolor='black')
                               for qp, marker in self.qp_markers.items() if qp in df['qp'].values]

        # Combine and place legends
        legend1 = ax_scatter.legend(handles=legend_elements_res, title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left')
        ax_scatter.add_artist(legend1)
        legend2 = ax_scatter.legend(handles=legend_elements_qp, title="QP", bbox_to_anchor=(1.02, 0.6), loc='upper left')

        plt.title(f"VMAF Scatter: Encoded vs. Reference ({os.path.basename(reference_video)}) (Scaled to 4K) ({self.codec.upper()})", fontsize=16)
        plt.xlabel(f"VMAF Score (Encoded Video)", fontsize=12)
        plt.ylabel(f"VMAF Score (Reference Video)", fontsize=12)
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        plt.tight_layout(rect=[0, 0, 0.88, 1])
        
        scatter_plot_path = self.plots_dir / f"vmaf_scatter_encoded_vs_reference_{source_name}.png"
        plt.savefig(scatter_plot_path, dpi=300)
        plt.close()
        
        # --- Plot 2: VMAF vs. QP ---
        plt.figure(figsize=(12, 8))
        ax_qp = sns.scatterplot(
            data=df,
            x="qp",
            y="vmaf",
            hue="resolution",
            palette=self.resolution_colors,
            s=150,
            zorder=5
        )

        sns.regplot(
            data=df,
            x="qp",
            y="vmaf",
            scatter=False,
            color="blue",
            ci=None,
            order=2,  # Quadratic fit
            ax=ax_qp
        )

        texts_qp = []
        for i, row in df.iterrows():
            texts_qp.append(plt.text(
                row['qp'],
                row['vmaf'] + 1.0,
                f"{row['vmaf']:.1f}",
                fontsize=9,
                ha='center',
                va='bottom'
            ))

        if has_adjust_text:
            adjust_text(texts_qp, ax=ax_qp, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6, lw=0.5))

        pcc_qp, _ = pearsonr(df["qp"], df["vmaf"])
        mse_vmaf_qp = mean_squared_error(df["vmaf"], df["qp"])
        rmse_vmaf_qp = np.sqrt(mse_vmaf_qp)

        plt.title(f"VMAF vs. QP for '{os.path.basename(reference_video)}' ({self.codec.upper()}) (4K Model)\nPCC = {pcc_qp:.3f}, RMSE = {rmse_vmaf_qp:.3f}", fontsize=16)
        plt.xlabel("QP (Quantization Parameter)", fontsize=12)
        plt.ylabel(f"VMAF Score (0-100) (Scaled to {self.comparison_resolution})", fontsize=12)
        plt.ylim(0, 100)
        min_qp = df['qp'].min()
        max_qp = df['qp'].max()
        plt.xlim(min_qp - 2, max_qp + 2)
        plt.xticks(sorted(df['qp'].unique()))
        plt.legend(title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left')
        plt.tight_layout(rect=[0, 0, 0.9, 1])
        
        qp_plot_path = self.plots_dir / f"vmaf_vs_qp_{source_name}_4k_model.png"
        plt.savefig(qp_plot_path, dpi=300)
        plt.close()

        # --- Plot 3: Bitrate vs. VMAF ---
        if 'bitrate_kbps' in df.columns and not df['bitrate_kbps'].isna().all():
            plt.figure(figsize=(12, 8))
            ax_bitrate = sns.scatterplot(
                data=df,
                x="bitrate_kbps",
                y="vmaf",
                hue="resolution",
                palette=self.resolution_colors,
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
                order=2,  # Quadratic fit
                ax=ax_bitrate
            )

            texts_bitrate = []
            for i, row in df.iterrows():
                if pd.notna(row['bitrate_kbps']):  # Only label if bitrate is not NaN
                    texts_bitrate.append(plt.text(
                        row['bitrate_kbps'],
                        row['vmaf'] + 1.0,
                        f"{row['vmaf']:.1f}",
                        fontsize=9,
                        ha='center',
                        va='bottom'
                    ))

            if has_adjust_text:
                adjust_text(texts_bitrate, ax=ax_bitrate, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.6, lw=0.5))

            pcc_bitrate, _ = pearsonr(df["bitrate_kbps"].dropna(), df["vmaf"].dropna())  # Drop NaN for correlation
            mse_bitrate_vmaf = mean_squared_error(df["vmaf"].dropna(), df["bitrate_kbps"].dropna())
            rmse_bitrate_vmaf = np.sqrt(mse_bitrate_vmaf)

            plt.title(f"Bitrate vs. VMAF for '{os.path.basename(reference_video)}' ({self.codec.upper()}) (4K Model)\nPCC = {pcc_bitrate:.3f}, RMSE = {rmse_bitrate_vmaf:.3f}", fontsize=16)
            plt.xlabel("Bitrate (kbps)", fontsize=12)
            plt.ylabel(f"VMAF Score (0-100) (Scaled to {self.comparison_resolution})", fontsize=12)
            plt.ylim(0, 100)
            plt.legend(title="Resolution", bbox_to_anchor=(1.02, 1), loc='upper left')
            plt.grid(True)
            plt.tight_layout(rect=[0, 0, 0.9, 1])
            
            bitrate_plot_path = self.plots_dir / f"bitrate_vs_vmaf_{source_name}_4k_model.png"
            plt.savefig(bitrate_plot_path, dpi=300)
            plt.close()
        
        print(f"Plots saved to {self.plots_dir}")


def main():
    # Process each codec
    codecs = ["vvc", "av1", "h265"]
    
    for codec in codecs:
        print(f"\n{'='*50}")
        print(f"Processing {codec.upper()} encoded videos")
        print(f"{'='*50}")
        analyzer = VMAFAnalyzer(codec)
        analyzer.analyze_videos()


if __name__ == "__main__":
    main()
