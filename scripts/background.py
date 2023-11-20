import argparse
import os
import numpy as np
import json
import matplotlib.pyplot as plt
import os
from tqdm import tqdm
import cv2

start_string = """
WELCOME TO THE BACKGROUND CALCULATION SCRIPT
---------------------------------------------
This script will take the video data and calculate the background for each camera
"""
print(start_string)

# Get the arguments
parser = argparse.ArgumentParser(description='Background Subtraction')
parser.add_argument('-d', '--data_dir', type=str, default='./data/', help='Path to the data directory (default: data)')
parser.add_argument('-o', '--output_dir', type=str, default='./processed_data/', help='Path to the output directory (default: processed_data)')
parser.add_argument('-m', '--mode', type=str, default='random', help='Mode for background calculation (random/full) (default: random)')
parser.add_argument('-r', '--random_frames', type=int, default=100, help='Number of random frames to use for background calculation (default: 100)')
parser.add_argument('-x', '--overwrite', type=bool, default=False, help='Overwrite existing background files (default: False)')
parser.add_argument('-exp', '--experiment', type=str, default='experiment', help='Experiment name (default: experiment)')

# Parse the arguments
args = parser.parse_args()
data_dir = args.data_dir
original_output_dir = args.output_dir
mode = args.mode
n_random_frames = args.random_frames
overwrite = args.overwrite
experiment = args.experiment

# find the data
data_files = os.listdir(data_dir)
experiment_files = [file for file in data_files if experiment in file]
assert len(experiment_files) == 1, 'More than one Experiment file found'
experiment_file = experiment_files[0]
# check if its a json file, if so, read it in
if experiment_file.endswith('.json'):
    experiment_file = json.load(open(data_dir + experiment_file))
    experiment_dir = experiment_file['dir']
    if len(experiment_dir)>0:
        found = False
        # loop through the Experiment dir options to find the one that exists
        for dir in experiment_dir:
            if os.path.exists(dir):
                experiment_dir = dir
                found = True
                print('Experiment directory: {}'.format(experiment_dir))
                break
        if not found:
            Exception('Experiment directory does not exist')
else:
    Exception('Experiment file is not a json file')
# find all cam directories in the Experiment directory
experiment_dirs = os.listdir(experiment_dir)
experiment_dirs = [dir for dir in experiment_dirs if 'cam' in dir]
# GET THE NUMBER OF CAMERAS
num_cams = len(experiment_dirs)
print('Number of cameras: {}'.format(num_cams))

# loop through the cameras and find the video files
for CAM_NO in range(0, num_cams):
    # GET THE VIDEO FILE NAMES
    cam_dir = experiment_dir + [dir for dir in experiment_dirs if 'cam_{}'.format(CAM_NO) in dir][0] + '/1_48/'
    print('Camera {} directory: {}'.format(CAM_NO, cam_dir))
    cam_files = os.listdir(cam_dir)
    # filter out the non-video files
    cam_files = [file for file in cam_files if file.endswith('.mp4')]
    # sort the files by their number and drop the last file (incomplete)
    cam_files = sorted(cam_files, key=lambda x: int(x.split('_')[-1].split('.')[0]))
    cam_files = cam_files[:-1]
    print('Number of video files: {}'.format(len(cam_files)))

    # MERGE THE VIDEO FILES USING FFMPEG 
    # create the temp directory
    output_dir = original_output_dir + '{}/'.format(cam_dir.split('/')[-4])
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # create a list of the video files
    video_files = []
    for file in cam_files:
        video_files.append(cam_dir + file)
    # create the ffmpeg command
    ffmpeg_command = 'ffmpeg -f concat -safe 0 -i {} -c copy {}cam{}_merged.mp4'.format(output_dir + 'files.txt', output_dir, CAM_NO)
    # create the files.txt file
    with open(output_dir + 'files.txt', 'w') as f:
        for file in video_files:
            f.write("file '{}'\n".format(file))
    # check if the file already exists
    if os.path.exists(output_dir + 'cam{}_merged.mp4'.format(CAM_NO)):
        if overwrite:
            print('Merged video file already exists. Overwriting...')
            os.remove(output_dir + 'cam{}_merged.mp4'.format(CAM_NO))
            # run the ffmpeg command
            os.system(ffmpeg_command)
            # remove the files.txt file
            os.remove(output_dir + 'files.txt')
        else:
            print('Merged video file already exists. Skipping...')
            os.remove(output_dir + 'files.txt')
    else:
        print('Merging video files...')
        # run the ffmpeg command
        os.system(ffmpeg_command)
        # remove the files.txt file
        os.remove(output_dir + 'files.txt')    

    frames = []
    # check mode
    if mode == 'random':
        # GET THE RANDOM FRAMES
        # open the video file
        cap = cv2.VideoCapture(output_dir + 'cam{}_merged.mp4'.format(CAM_NO))
        # get the number of frames
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # get the random frames
        random_frames = np.random.randint(0, num_frames, size=n_random_frames)
        random_frames = np.sort(random_frames)
        # loop through the random frames
        for FRAME_NO in tqdm(random_frames):
            # read the frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, FRAME_NO)
            ret, frame = cap.read()
            # check if the frame is valid
            if ret:
                # convert to grayscale
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # convert to numpy array
                frame = np.array(frame, dtype=np.uint8)
                # append to frames
                frames.append(frame)
            else:
                Exception('Frame {} is not valid'.format(FRAME_NO))
        # release the video
        cap.release()
    elif mode == 'full':
        # LOOP THROUGH THE VIDEO AND GET ALL THE FRAMES
        # open the video file
        cap = cv2.VideoCapture(output_dir + 'merged_cam{}.mp4'.format(CAM_NO))
        # get the number of frames
        num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # MAKE SURE THE MEMORY IS BIG ENOUGH
        # get the memory size
        mem_size = os.popen('free -m').readlines()[1].split()[1]
        # get the n_pixels in each frame
        frame_size = cap.get(cv2.CAP_PROP_FRAME_WIDTH) * cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # assuming datatype is uint8, get the number of bytes per frame
        frame_size = frame_size * 8 / 1024 / 1024
        # get the number of frames that can fit in the memory
        n_frames = int(mem_size / frame_size)
        # check if the number of frames is greater than the number of frames in the video
        if n_frames > num_frames:
            Exception('Memory size is too small to fit the video')
        # get the number of frames to skip
        skip_frames = int(num_frames / n_frames) if int(num_frames / n_frames) > 0 else 1
        # loop through the frames
        for FRAME_NO in tqdm(range(0, num_frames, skip_frames)):
            # read the frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, FRAME_NO)
            ret, frame = cap.read()
            # check if the frame is valid
            if ret:
                # convert to grayscale
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # convert to numpy array
                frame = np.array(frame, dtype=np.uint8)
                # append to frames
                frames.append(frame)
            else:
                Exception('Frame {} is not valid'.format(FRAME_NO))
        # release the video
        cap.release()
    else:
        Exception('Mode {} is not valid'.format(mode))

    # CALCULATE THE BACKGROUND
    # calculate the mean difference between each frame and the next frame
    mean_diff = []
    for i in range(len(frames)-1):
        mean_diff.append(np.mean(np.abs(frames[i] - frames[i+1])))
    # keep only frames with a mean difference greater than 76
    frames = [frames[i] for i in range(len(frames)-1) if mean_diff[i] > 76]
    # convert to numpy array
    frames = np.array(frames)
    # calculate the background
    background = np.median(frames, axis=0)
    # save the background
    np.save(output_dir + 'cam{}_background.npy'.format(CAM_NO), background)
    # save the background as an image
    cv2.imwrite(output_dir + 'cam{}_background.png'.format(CAM_NO), background)





