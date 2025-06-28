import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

print("Video Content Analyzer Starting...")

# Make siti_results folder if it doesn't exist
if not os.path.exists('siti_results'):
    os.makedirs('siti_results')
    print("siti_results folder created.")

# Find MP4 and MKV files
video_list = []
for file in os.listdir('video_source'):
    if file.endswith('.mp4') or file.endswith('.mkv'):
        video_list.append(file)

if len(video_list) == 0:
    print("No MP4 or MKV files found in video_source folder!")
    exit()

print("Found these videos:")
for video in video_list:
    print("- " + video)

# Lists to store data from all videos
all_video_data = []

# Look at each video
for video_name in video_list:
    print("\nAnalysing: " + video_name)
    
    # Open video
    video_path = 'video_source/' + video_name
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Cannot open " + video_name)
        continue
    
    # Get video info
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print("Frames: " + str(frame_count))
    print("FPS: " + str(fps))
    
    # Lists to save numbers
    si_list = []  # complexity numbers
    ti_list = []  # movement numbers
    
    # Read first frame
    ret, old_frame = cap.read()
    if not ret:
        print("Cannot read video.")
        cap.release()
        continue
    
    frame_num = 1
    
    # Go through all frames
    while True:
        ret, new_frame = cap.read()
        if not ret:
            break
        
        frame_num = frame_num + 1
        
        # Make frames gray
        old_gray = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
        new_gray = cv2.cvtColor(new_frame, cv2.COLOR_BGR2GRAY)
        
        # Find edges (complexity)
        edges_x = cv2.Sobel(new_gray, cv2.CV_64F, 1, 0)
        edges_y = cv2.Sobel(new_gray, cv2.CV_64F, 0, 1)
        edges = np.sqrt(edges_x * edges_x + edges_y * edges_y)
        si = np.std(edges)
        si_list.append(si)
        
        # Find difference (movement)
        diff = cv2.absdiff(old_gray, new_gray)
        ti = np.std(diff.astype(float))
        ti_list.append(ti)
        
        # Show progress
        if frame_num % 100 == 0:
            print("Processed " + str(frame_num) + " frames.")
        
        old_frame = new_frame
    
    cap.release()
    
    # Calculate averages
    avg_si = sum(si_list) / len(si_list)
    avg_ti = sum(ti_list) / len(ti_list)
    max_si = max(si_list)
    max_ti = max(ti_list)
    
    print("Average complexity: " + str(round(avg_si, 1)))
    print("Average movement: " + str(round(avg_ti, 1)))
    
    # Store video data for combined graph
    video_data = {}
    video_data['name'] = video_name
    video_data['si_list'] = si_list
    video_data['ti_list'] = ti_list
    video_data['avg_si'] = avg_si
    video_data['avg_ti'] = avg_ti
    video_data['max_si'] = max_si
    video_data['max_ti'] = max_ti
    all_video_data.append(video_data)
    
    # Save individual data to CSV
    csv_name = video_name.replace('.mp4', '_siti.csv').replace('.mkv', '_siti.csv')
    with open('siti_results/' + csv_name, 'w') as f:
        f.write('input_file,si,ti,n\n')  # Header
        for i in range(len(si_list)):
            frame_num = i + 1
            si_value = round(si_list[i], 3)
            ti_value = round(ti_list[i], 3)
            f.write(video_name + ',' + str(si_value) + ',' + str(ti_value) + ',' + str(frame_num) + '\n')
    
    print("Saved data: " + csv_name)

# Creating SITI graph
print("\nCreating  graph...")
plt.figure(figsize=(12, 8))
colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']
color_index = 0

for video_data in all_video_data:
    color = colors[color_index % len(colors)]
    plt.scatter(video_data['si_list'], video_data['ti_list'], 
               alpha=0.6, label=video_data['name'], c=color)
    color_index = color_index + 1

# Create summary CSV with mean SI and TI values
print("\nCreating summary CSV with mean values...")
with open('siti_results/siti_summary.csv', 'w') as f:
    f.write('input_file,si,ti\n')  # Header
    for video_data in all_video_data:
        video_name = video_data['name']
        avg_si = round(video_data['avg_si'], 3)
        avg_ti = round(video_data['avg_ti'], 3)
        f.write(video_name + ',' + str(avg_si) + ',' + str(avg_ti) + '\n')

print("Saved SITI summary: siti_summary.csv")

plt.xlabel('SI')
plt.ylabel('TI')
plt.title('VCA')
plt.grid(True)
plt.legend()

# Save SITI graph
plt.savefig('siti_results/siti.png')
plt.close()

print("Saved SITI")

print("\nAll done! Check the siti_results folder.")
