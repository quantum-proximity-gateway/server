import subprocess
import logging
from litestar.exceptions import HTTPException
import cv2
import os
import shutil

def convert_to_mp4(webm_path: str, mp4_path: str) -> None:
    """Convert a WebM file to MP4 using ffmpeg."""
    # Common options: -c:v libx264 for video, -c:a aac for audio.
    # Adjust as needed for your environment/codecs.
    command = [
        'ffmpeg',
        '-i', webm_path,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-strict', 'experimental',  # Sometimes needed for aac
        '-y',  # Overwrite without asking
        mp4_path
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg conversion failed: {e.stderr.decode('utf-8', errors='replace')}")
        raise HTTPException(status_code=500, detail="Failed to convert WebM to MP4")
    
def split_frames(mp4_path: str, user_video_dir: str):
    # Grab 5 frames from the video
    cap = cv2.VideoCapture(mp4_path)

    if not cap.isOpened():
        logging.error("Error opening video file")
        return {'status': 'error', 'detail': 'Error opening video file'}
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps else 0
    skip_frames = int(0.5 * fps) # skip first 0.5 seconds - camera stabilization

    logging.info(f"Video info - FPS: {fps}, Total frames: {total_frames}, Duration: {duration_sec:.2f}s")

    # not really necessary - but just in case
    if duration_sec < 2: 
        logging.warning("Video duration is shorter than 2 seconds—check the frontend code or device recording.")
    if (total_frames - skip_frames) < 5:
        logging.error("Video too short")
        return {'status': 'error', 'detail': 'Video too short'}

    interval = max(1, (total_frames - skip_frames) // 21)

    frames_dir = os.path.join(user_video_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    extracted_frames = []
    for i in range(1, 21):
        
        frame_idx = skip_frames + i * interval
        if frame_idx >= total_frames: # in case of rounding / video shorter than expected
            break
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret or frame is None:
            logging.warning(f"Error reading frame {i}")
            continue
        
        frame_path = os.path.join(frames_dir, f'frame_{i}.jpg')
        cv2.imwrite(frame_path, frame)
        extracted_frames.append(frame_path)
        logging.info(f"Saved frame {i} to {frame_path}")

    cap.release()
    return extracted_frames