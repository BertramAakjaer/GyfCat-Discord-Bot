import imageio.v3 as iio
import os
import requests
from io import BytesIO
from PIL import Image
from typing import Union
import tempfile
from logger_setup import setup_logger

logger = setup_logger('gif_converter')

async def is_video(url: str) -> bool:
    video_extensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv']
    return any(url.lower().endswith(ext) for ext in video_extensions)

async def file_to_gif(url: str) -> Union[BytesIO, None]:
    """
    Converts an image or video from a URL to a GIF.

    Args:
        url: The URL of the image or video.

    Returns:
        A BytesIO object containing the GIF, or None if an error occurred.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Create BytesIO from response content and reset position
        content_io = BytesIO(response.content)
        content_io.seek(0)

        # Check if it's a video
        if await is_video(url):
            logger.info("Processing video file")
            # Create a temporary file to store the video
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1]) as tmp_file:
                tmp_file.write(content_io.read())  # Use content_io instead of response.content
                tmp_file.flush()
                
                # Read the video and convert to frames
                frames = []
                reader = iio.imread(tmp_file.name, index=None)
                
                # Sample frames (take every 3rd frame to reduce size)
                for i, frame in enumerate(reader):
                    if i % 3 == 0:
                        frames.append(frame)
                
                # Create GIF in memory
                gif_buffer = BytesIO()
                iio.imwrite(gif_buffer, frames, extension='.gif', fps=10)
                gif_buffer.seek(0)
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
                logger.info("Video successfully converted to GIF")
                return gif_buffer
        else:
            logger.info("Processing image file")
            # Handle image as before
            img = Image.open(content_io)  # Use content_io instead of BytesIO(response.content)
            
            if img.mode != 'RGB':
                img = img.convert('RGB')

            gif_buffer = BytesIO()
            img.save(gif_buffer, format='GIF')
            gif_buffer.seek(0)
            
            logger.info("Image successfully converted to GIF")
            return gif_buffer

    except Exception as e:
        logger.error(f"Error converting to GIF: {e}")
        logger.exception("Full traceback:")  # This will log the full stack trace
        return None
