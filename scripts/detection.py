import argparse
import os
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import cv2
import time
from joblib import Parallel, delayed
import pandas as pd
from matplotlib.colors import ListedColormap

# CLEAR THE CONSOLE
os.system('cls' if os.name == 'nt' else 'clear')


start_string = """
WELCOME TO THE ANT DETECTION SCRIPT
---------------------------------------------
This script will take the video data and background data and detect the ants
"""
print(start_string)

# Get the arguments
parser = argparse.ArgumentParser(description='Ant Detection')
parser.add_argument('-d', '--data_dir', type=str, default='./data/', help='Path to the processed data directory (default: ./data/)')
parser.add_argument('-p', '--processed_data_dir', type=str, default='./processed_data/', help='Path to the processed data directory (default: ./processed_data/)')
parser.add_argument('-o', '--output_dir', type=str, default='', help='Path to the output directory (default: the associated processed data subdirectory)')
parser.add_argument('-n', '--n_threads', type=int, default=1, help='Number of threads to use (default: 1)')
parser.add_argument('-s', '--skip_frames', type=int, default=1, help='Number of frames to skip (default: 1)')
parser.add_argument('-c', '--cut_off', type=int, default=-50, help='Cut off for background subtraction (default: -50)')
parser.add_argument('-f', '--fill_nan', type=bool, default=True, help='Fill nan values (default: True)')
parser.add_argument('-pl', '--plot', type=bool, default=True, help='Plot the results (default: True)')
parser.add_argument('-n_bins', '--n_bins', type=int, default=100, help='Number of bins for the histogram (default: 100)')
parser.add_argument('-exp', '--experiment', type=str, default='experiment', help='Experiment name (default: experiment)')
parser.add_argument('-x', '--overwrite', type=bool, default=False, help='Overwrite existing data (default: False)')



# Parse the arguments
args = parser.parse_args()
data_dir = args.data_dir
processed_data_dir = args.processed_data_dir
output_dir = args.output_dir
n_threads = args.n_threads
# assert the number of threads is greater than 0 and less than the number of cores
assert n_threads>0, 'Number of threads must be greater than 0'
assert n_threads<=os.cpu_count(), 'Number of threads must be less than or equal to the number of cores'
skip_frames = args.skip_frames
# assert the number of frames to skip is greater than 0
assert skip_frames>0, 'Number of frames to skip must be greater than 0'
cut_off = args.cut_off
fill_nan = args.fill_nan
plot = args.plot
n_bins = args.n_bins
experiment = args.experiment

## FUNCTIONS

# fill nan values in a array with linear interpolation of the last valid value and the next valid value
def fillna(x):
    # check if all the values are nan, if so, return the array
    if np.isnan(x).sum()==len(x):
        return x
    # find the first valid value
    first_valid = np.where(~np.isnan(x))[0][0]
    # fill the nan values before the first valid value with the first valid value
    x[:first_valid] = x[first_valid]
    # find the last valid value
    last_valid = np.where(~np.isnan(x))[0][-1]
    # fill the nan values after the last valid value with the last valid value
    x[last_valid:] = x[last_valid]
    # loop through the array, when you find a nan value, find the next valid value and the previous valid value
    # then linearly interpolate between the two
    i = first_valid + 1
    while i<last_valid:
        if np.isnan(x[i]):
            # get the next valid value
            next_valid = np.where(~np.isnan(x[i:]))[0][0] + i
            # get the previous valid value
            prev_valid = np.where(~np.isnan(x[:i]))[0][-1]
            # fill the nan value with the linear interpolation
            x[i:next_valid] = np.linspace(x[prev_valid], x[next_valid], next_valid-prev_valid+1)[1:-1]
            # set i to the next valid value
            i = next_valid+1
        else:
            i += 1
    # make sure there are no nan values
    if np.isnan(x).sum()>0:
        print('There are still nan values')
        print(x)
    return x

# make a function that combines the entire process given a frame and a background
def get_ant_locations(frame, background, background_masks, N_ARENAS):
    # get the only ant mask
    only_ants = ((frame.mean(axis=2)- background.mean(axis=2))>-50).astype(np.uint8)
    only_ants = np.array([only_ants, only_ants, only_ants]).transpose(1,2,0)*255
    # convert to grayscale
    only_ants = cv2.cvtColor(only_ants, cv2.COLOR_BGR2GRAY)
    # apply a gaussian blur
    only_ants = cv2.GaussianBlur(only_ants, (55,55), 0)
    # apply a blob detector
    detector = cv2.SimpleBlobDetector_create()
    keypoints = detector.detect(only_ants)
    # convert to numpy array and get the positions and areas
    keypoints = np.array([[kp.pt[0], kp.pt[1], kp.size] for kp in keypoints])
    pos = np.ones((N_ARENAS, 2))*np.nan
    arena_sizes = np.zeros(N_ARENAS)
    for i in keypoints:
        x,y = int(i[0]), int(i[1])
        arena_vals = background_masks[:,y,x]
        # make sure not all the values are 0
        if arena_vals.sum()==0:
            continue
        # check if there are multiple arenas
        if arena_vals.sum()>255:
            continue
        arena_id = arena_vals.argmax()
        # check if the new keypoint is larger than the previous one
        if i[2]>arena_sizes[arena_id]:
            arena_sizes[arena_id] = i[2]
            pos[arena_id] = [i[0], i[1]]
        else:
            continue

    return pos

# make a function that processes the frames
def process_frames(video_file, frames, background, background_masks, N_ARENAS, verbose=True):
    positions = []
    frame_no = []
    if verbose:
        start_time = time.time()
    # open the video
    cap = cv2.VideoCapture(video_file)
    # load the video into memory
    start_frame = frames[0]
    end_frame = frames[-1]
    skip_frames = frames[1]-frames[0]
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    COUNT = 0
    for n,i in enumerate(range(end_frame-start_frame)):
        if skip_frames>1 and n%skip_frames!=0:
            continue
        ret, frame = cap.read()
        # check if the frame is valid
        if not ret or frame is None:
            frame = np.zeros((background.shape[0], background.shape[1], 3))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        positions.append(get_ant_locations(frame, background, background_masks, N_ARENAS))
        frame_no.append(start_frame+n)
        COUNT += 1
        if verbose and COUNT%100==0:
            print('Processed {}/{}, Time elapsed: {:.2f}s'.format(COUNT, len(frames), time.time()-start_time))
    # release the video
    cap.release()
    return positions, frame_no

def make_cmap(color):
    # get the color RGB values
    r,g,b,_ = color
    # create a linear gradient from black to the color
    cmap = np.array([np.linspace(0,r,256), np.linspace(0,g,256), np.linspace(0,b,256)]).T
    return ListedColormap(cmap)

### MAIN SCRIPT
# find the data
data_files = os.listdir(data_dir)
experiment_files = [file for file in data_files if experiment in file]
assert len(experiment_files) == 1, 'More than one or no experiment files found'
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
                data_dir = processed_data_dir + dir.split('/')[-2]
                if os.path.exists(data_dir):
                    found = True
                    print('Processed Data directory: {}'.format(data_dir))
                    break
                else:
                    Exception('Processed Data directory does not exist')
        if not found:
            Exception('Experiment directory does not exist')
else:
    Exception('Experiment file is not a json file')
# find all camera directories
CAM_NOs = list(set([int(x.split('_')[0][3:]) for x in os.listdir(data_dir) if x.startswith('cam')]))
# GET THE NUMBER OF CAMERAS
num_cams = len(CAM_NOs)
print('Number of cameras: {}'.format(num_cams))
# check if the output directory is specified
if output_dir=='':
    output_dir = data_dir

# loop through the cameras and find the video files
for CAM_NO in CAM_NOs:
    # check if the data has already been processed
    if os.path.exists(output_dir + '/cam{}_ant_locations.csv'.format(CAM_NO)) and  \
        os.path.exists(output_dir + '/cam{}_ant_locations.png'.format(CAM_NO)) and \
        os.path.exists(output_dir + '/cam{}_ant_locations_hist.png'.format(CAM_NO)):
        if args.overwrite:
            print('Overwriting existing data')
        else:
            print('Data already exists, skipping')
            continue
    print('Processing camera {}'.format(CAM_NO))
    # get all the files in the data directory with the correct camera number
    data_files = os.listdir(data_dir)
    data_files = [file for file in data_files if 'cam{}'.format(CAM_NO) in file]
    # make sure there is (1) merged.mp4 file (2) background.png file (3) background_endpoints.json file (4) background_pois.json file
    assert 'cam{}_merged.mp4'.format(CAM_NO) in data_files, 'No merged.mp4 file found'
    assert 'cam{}_background.png'.format(CAM_NO) in data_files, 'No background.png file found'
    assert 'cam{}_background_endpoints.json'.format(CAM_NO) in data_files, 'No background_endpoints.json file found'
    assert 'cam{}_background_pois.json'.format(CAM_NO) in data_files, 'No background_pois.json file found'
    print('All Camera and Metadata files found')
    # get the background image
    print('Loading background image')
    background = cv2.imread(data_dir + '/cam{}_background.png'.format(CAM_NO))
    background = cv2.cvtColor(background, cv2.COLOR_BGR2RGB)
    # get the background masks
    print('Loading background masks')
    background_endpoints = json.load(open(data_dir + '/cam{}_background_endpoints.json'.format(CAM_NO)))
    background_pois = json.load(open(data_dir + '/cam{}_background_pois.json'.format(CAM_NO)))
    background_masks = json.load(open(data_dir + '/cam{}_background_masks.json'.format(CAM_NO)))
    background_masks = np.array([background_masks[key] for key in background_masks.keys()])
    # get the number of arenas
    N_ARENAS = background_masks.shape[0]
    print('Number of arenas: {}'.format(N_ARENAS))
    # get the video file
    print('Loading video to set up frames')
    cap = cv2.VideoCapture(data_dir + '/cam{}_merged.mp4'.format(CAM_NO))
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    n_frames_per_thread = int(np.ceil(n_frames/n_threads))
    frames_per_thread = [np.arange(i*n_frames_per_thread, (i+1)*n_frames_per_thread, skip_frames) for i in range(n_threads)]
    cap.release()
    # process the frames
    print('Running processing in parallel with {} threads'.format(n_threads))
    processed_data = Parallel(n_jobs=n_threads)(delayed(process_frames)(data_dir + '/cam{}_merged.mp4'.format(CAM_NO), frames, background, background_masks, N_ARENAS) for frames in frames_per_thread)
    pos = np.concatenate([processed_data[i][0] for i in range(len(processed_data))])
    t = np.concatenate([processed_data[i][1] for i in range(len(processed_data))])
    # fill in the nan values
    if fill_nan:
        print('Filling nan values')
        for i in range(pos.shape[1]):
            pos[:,i,0] = fillna(pos[:,i,0])
            pos[:,i,1] = fillna(pos[:,i,1])
    # save the data
    print('Saving data')
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    # make into pandas dataframe
    columns = ['frame'] + ['arena_{}_x'.format(i+1) for i in range(N_ARENAS)] + ['arena_{}_y'.format(i+1) for i in range(N_ARENAS)]
    data = np.zeros((pos.shape[0], pos.shape[1]*2+1))
    data[:,0] = t
    for i in range(N_ARENAS):
        data[:,i+1] = pos[:,i,0]
        data[:,i+1+N_ARENAS] = pos[:,i,1]
    # data = np.zeros((pos.shape[0]*pos.shape[1], pos.shape[2]+2))    
    # data[:,0] = np.repeat(t, pos.shape[1])
    # data[:,1] = np.tile(np.arange(pos.shape[1]), pos.shape[0])
    # data[:,2:] = pos.reshape(-1, pos.shape[2])
    data = pd.DataFrame(data, columns=columns)
    data.to_csv(output_dir + '/cam{}_ant_locations.csv'.format(CAM_NO), index=False)
    # plot the results
    if plot:
        print('Plotting results...')
        # TIME SERIES
        fig, ax = plt.subplots(1,1,figsize=(10,10))
        plt.imshow(background)
        for arena_id in range(N_ARENAS):
            # check if any of the values are nan
            if np.isnan(pos[:,arena_id,0]).sum()>0 or np.isnan(pos[:,arena_id,1]).sum()>0:
                continue
            plt.scatter(pos[:,arena_id,0], pos[:,arena_id,1], s=10, c=t, cmap=make_cmap(plt.cm.rainbow(arena_id/N_ARENAS)), alpha=0.3)
            # plot the POIs
            pois = np.array(background_pois["arena_{}_original".format(arena_id+1)])
            for i in range(pois.shape[0]):
                plt.scatter(pois[i,0], pois[i,1], s=100, c='k', marker='x')
        # hide the axes
        ax.get_xaxis().set_visible(False)
        ax.get_yaxis().set_visible(False)
        plt.savefig(output_dir + '/cam{}_ant_locations.png'.format(CAM_NO), bbox_inches='tight', pad_inches=0)
        plt.close()
        # HISTOGRAM
        background_small = cv2.resize(background, (int(n_bins*background.shape[1]/background.shape[0]), n_bins))
        plt.imshow(background_small)
        for arena_id in range(N_ARENAS):
            # check if any of the values are nan
            if np.isnan(pos[:,arena_id,0]).sum()>0 or np.isnan(pos[:,arena_id,1]).sum()>0:
                continue
            # get the positions for the arena
            x = pos[:,arena_id,0]
            y = pos[:,arena_id,1]
            # create the 2d histogram

            H, xedges, yedges = np.histogram2d(y, x, bins=(n_bins,int(n_bins*background.shape[1]/background.shape[0])),range=[[0, background.shape[0]], [0, background.shape[1]]])
            # log transform the histogram
            H = np.log(H+1)
            # plot the 2d histogram (make 0 values transparent)

            masked_array = np.ma.masked_where(H == 0, H)
            plt.imshow(masked_array, cmap=make_cmap(plt.cm.rainbow(arena_id/N_ARENAS)), interpolation='nearest', vmin=0, vmax=H[H>0].max(), alpha=0.5)
            # plot the POIs
            pois = np.array(background_pois["arena_{}_original".format(arena_id+1)])
            for i in range(pois.shape[0]):
                plt.scatter(pois[i,0]*n_bins/background.shape[0], pois[i,1]*n_bins/background.shape[0], s=100, c='k', marker='x')
        # hide the axes
        plt.gca().get_xaxis().set_visible(False)
        plt.gca().get_yaxis().set_visible(False)
        plt.savefig(output_dir + '/cam{}_ant_locations_hist.png'.format(CAM_NO), bbox_inches='tight', pad_inches=0)
        plt.close()
    
    print('Finished processing camera {}'.format(CAM_NO))
print('DONE')








