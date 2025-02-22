import cv2
import argparse
from basicsr.test_img import image_sr  
from os import path as osp
import os
import shutil
from PIL import Image
import re
import imageio.v2 as imageio

def replace_filename(original_path, suffix):

    directory = os.path.dirname(original_path)
    old_filename = os.path.basename(original_path)
    name_part, file_extension = os.path.splitext(old_filename)
    new_filename = f"{name_part}{suffix}{file_extension}"
    new_path = os.path.join(directory, new_filename)

    return new_path

def create_temp_folder(folder_path):
    
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def delete_temp_folder(folder_path):
    shutil.rmtree(folder_path)

def extract_number(filename):
    s = re.findall(r'\d+', filename)
    return int(s[0]) if s else -1

def bicubic_upsample_opencv(input_image_path, output_image_path, scale_factor):
    
    img = cv2.imread(input_image_path)
    
    original_height, original_width = img.shape[:2]
    
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    
    upsampled_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    cv2.imwrite(output_image_path, upsampled_img)


def video_sr(args):
    file_name = os.path.basename(args.input_dir)
    video_output_path = os.path.join(args.output_dir,file_name)

    if args.SR == 'x4': 
        temp_LR_folder_path = os.path.join(args.output_dir, f'temp_LR/X4')
        video_output_path = replace_filename(video_output_path, '_x4')
        result_temp = osp.join(args.root_path, f'results/test_RGT_x4/visualization/Set5')
    if args.SR == 'x2': 
        temp_LR_folder_path = os.path.join(args.output_dir, f'temp_LR/X2')
        video_output_path = replace_filename(video_output_path, '_x2')
        result_temp = osp.join(args.root_path, f'results/test_RGT_x2/visualization/Set5')
    
    temp_HR_folder_path = os.path.join(args.output_dir, f'temp_HR')
    
    # create_temp_folder(result_temp)
    create_temp_folder(temp_LR_folder_path)
    create_temp_folder(temp_HR_folder_path) 

    cap = cv2.VideoCapture(args.input_dir)
    if not cap.isOpened():
        print("Error opening video file.")
        return

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
    
        frame_path = os.path.join(temp_LR_folder_path, f"frame_{frame_count}{args.SR}.png")
        cv2.imwrite(frame_path, frame)
        HR_frame_path = os.path.join(temp_HR_folder_path, f"frame_{frame_count}.png")
    
        if args.SR == 'x4': 
            bicubic_upsample_opencv(frame_path, HR_frame_path, 4)
        if args.SR == 'x2': 
            bicubic_upsample_opencv(frame_path, HR_frame_path, 2)
        frame_count +=1 

    # progress all frames in video 
    image_sr(args)

    # recover video form all frames
    frame_files = sorted(os.listdir(result_temp), key=extract_number)
    video_frames = [imageio.imread(os.path.join(result_temp, frame_file)) for frame_file in frame_files]
    # get video config
    fps = cap.get(cv2.CAP_PROP_FPS)
    imageio.mimwrite(video_output_path, video_frames, fps=fps, quality=9)  
    
    # release all resources
    cap.release()

    delete_temp_folder(os.path.dirname(temp_LR_folder_path))
    delete_temp_folder(temp_HR_folder_path)
    delete_temp_folder(os.path.join(args.root_path, f'results'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RGT for Video Super-Resolution")
    parser.add_argument("--SR", type=str, choices=['x2', 'x4'], default='x4', help='image resolution')
    parser.add_argument("--input_dir", type=str, default= "/remote-home/lzy/RGT/datasets/video/video_test1.mp4")
    parser.add_argument("--output_dir", type=str, default= "/remote-home/lzy/RGT/datasets/video_output")
    parser.add_argument("--root_path", type=str, default = "/remote-home/lzy/RGT")
    args = parser.parse_args()
    video_sr(args)
