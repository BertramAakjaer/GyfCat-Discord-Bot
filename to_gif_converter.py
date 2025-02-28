import imageio.v3 as iio
import os
import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from typing import Union
import tempfile
from logger_setup import setup_logger
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = setup_logger('gif_converter')

# Create a thread pool with limited workers
thread_pool = ThreadPoolExecutor(max_workers=2)

# Feature flag for video support
VIDEO_SUPPORT_ENABLED = False  # Set to True to enable video processing

async def is_video(url: str, content_type: str = '') -> bool:
    """Check if file is video based on extension and content type."""
    video_extensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv']
    video_mimetypes = ['video/', 'application/mp4']
    
    # Check file extension
    has_video_ext = any(url.lower().endswith(ext) for ext in video_extensions)
    # Check content type
    has_video_mime = any(mime in content_type.lower() for mime in video_mimetypes)
    
    return has_video_ext or has_video_mime

async def file_to_gif(url: str) -> Union[BytesIO, None, str]:
    """
    Converts an image or video from a URL to a GIF.

    Args:
        url: The URL of the image or video.

    Returns:
        A BytesIO object containing the GIF, or None if an error occurred.
    """
    try:
        # Add timeout to requests
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # Log content type for debugging
        content_type = response.headers.get('content-type', '')
        logger.info(f"File content type: {content_type}")

        # Read content once
        content = response.content
        content_io = BytesIO(content)
        content_io.seek(0)

        # Check content signature for MP4
        content_start = content[:16].hex()
        logger.info(f"File starts with bytes: {content_start}")
        
        is_video_file = await is_video(url, content_type) or 'ftyp' in content_start

        if is_video_file:
            if not VIDEO_SUPPORT_ENABLED:
                return "Video conversion is temporarily disabled"
                
            logger.info("Processing video file")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                try:
                    # Write content to temp file
                    tmp_file.write(content)
                    tmp_file.flush()
                    
                    # Wrap video processing in asyncio timeout
                    async with asyncio.timeout(60):  # 60 second timeout
                        # Run video processing in thread pool
                        loop = asyncio.get_event_loop()
                        frames = await loop.run_in_executor(thread_pool, process_video, tmp_file.name)
                    
                    if not frames:
                        raise ValueError("No frames extracted from video")

                    # Create GIF with reduced quality for faster processing
                    gif_buffer = BytesIO()
                    iio.imwrite(gif_buffer, frames, extension='.gif', fps=8)  # Reduced FPS
                    gif_buffer.seek(0)
                    
                    logger.info("Video successfully converted to GIF")
                    return gif_buffer
                
                except asyncio.TimeoutError:
                    logger.error("Video processing timed out after 60 seconds")
                    raise
                except Exception as e:
                    logger.error(f"Video processing error: {str(e)}")
                    raise
                finally:
                    if os.path.exists(tmp_file.name):
                        os.unlink(tmp_file.name)
        else:
            logger.info("Processing image file")
            try:
                img = Image.open(content_io)
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                gif_buffer = BytesIO()
                img.save(gif_buffer, format='GIF')
                gif_buffer.seek(0)
                
                logger.info("Image successfully converted to GIF")
                return gif_buffer

            except Exception as e:
                logger.error(f"Image processing error: {str(e)}")
                raise

    except Exception as e:
        logger.error(f"Error converting to GIF: {e}")
        logger.exception("Full traceback:")
        return None

def process_video(filename: str):
    """Process video in a separate thread to avoid blocking."""
    frames = []
    reader = iio.imread(filename, index=None)
    
    # Take every 4th frame instead of 3rd to reduce processing
    for i, frame in enumerate(reader):
        if i % 4 == 0:
            # Reduce frame size to 480p if larger
            h, w = frame.shape[:2]
            if h > 480:
                scale = 480 / h
                new_w = int(w * scale)
                frame = iio.imresize(frame, (480, new_w))
        frames.append(frame)
    
    return frames
