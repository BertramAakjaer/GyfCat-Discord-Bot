import imageio.v3 as iio
import os
import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError
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

        # Log content type for debugging
        content_type = response.headers.get('content-type', '')
        logger.info(f"File content type: {content_type}")

        # Create BytesIO from response content and reset position
        content_io = BytesIO(response.content)
        content_io.seek(0)

        # Check if it's a video
        if await is_video(url):
            logger.info("Processing video file")
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1]) as tmp_file:
                    tmp_file.write(content_io.read())
                    tmp_file.flush()
                    
                    try:
                        # Read the video and convert to frames
                        reader = iio.imread(tmp_file.name, index=None)
                        frames = []
                        
                        for i, frame in enumerate(reader):
                            if i % 3 == 0:
                                frames.append(frame)
                        
                        if not frames:
                            raise ValueError("No frames extracted from video")

                        gif_buffer = BytesIO()
                        iio.imwrite(gif_buffer, frames, extension='.gif', fps=10)
                        gif_buffer.seek(0)
                        
                        logger.info("Video successfully converted to GIF")
                        return gif_buffer
                    
                    finally:
                        # Ensure temp file is deleted
                        if os.path.exists(tmp_file.name):
                            os.unlink(tmp_file.name)
            
            except Exception as e:
                logger.error(f"Video processing error: {str(e)}")
                raise
        else:
            logger.info("Processing image file")
            try:
                # Try to read first few bytes to verify it's an image
                content_start = content_io.read(16)
                content_io.seek(0)
                logger.info(f"File starts with bytes: {content_start.hex()}")
                
                img = Image.open(content_io)
                img_format = img.format
                logger.info(f"Detected image format: {img_format}")
                
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                gif_buffer = BytesIO()
                img.save(gif_buffer, format='GIF')
                gif_buffer.seek(0)
                
                logger.info("Image successfully converted to GIF")
                return gif_buffer

            except UnidentifiedImageError:
                logger.error("The file could not be identified as a valid image")
                raise
            except Exception as e:
                logger.error(f"Image processing error: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Error converting to GIF: {e}")
        logger.exception("Full traceback:")
        return None
