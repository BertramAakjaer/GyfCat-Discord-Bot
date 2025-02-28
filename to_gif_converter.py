import imageio.v3 as iio
import os
import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from typing import Union
import tempfile
from logger_setup import setup_logger

logger = setup_logger('gif_converter')

async def is_video(url: str, content_type: str = '') -> bool:
    """Check if file is video based on extension and content type."""
    video_extensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv']
    video_mimetypes = ['video/', 'application/mp4']
    
    # Check file extension
    has_video_ext = any(url.lower().endswith(ext) for ext in video_extensions)
    # Check content type
    has_video_mime = any(mime in content_type.lower() for mime in video_mimetypes)
    
    return has_video_ext or has_video_mime

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

        # Read content once
        content = response.content
        content_io = BytesIO(content)
        content_io.seek(0)

        # Check content signature for MP4
        content_start = content[:16].hex()
        logger.info(f"File starts with bytes: {content_start}")
        
        is_video_file = await is_video(url, content_type) or 'ftyp' in content_start

        if is_video_file:
            logger.info("Processing video file")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                try:
                    # Write content to temp file
                    tmp_file.write(content)
                    tmp_file.flush()
                    
                    # Process video
                    reader = iio.imread(tmp_file.name, index=None)
                    frames = []
                    
                    # Take every 3rd frame
                    for i, frame in enumerate(reader):
                        if i % 3 == 0:
                            frames.append(frame)
                    
                    if not frames:
                        raise ValueError("No frames extracted from video")

                    # Create GIF
                    gif_buffer = BytesIO()
                    iio.imwrite(gif_buffer, frames, extension='.gif', fps=10)
                    gif_buffer.seek(0)
                    
                    logger.info("Video successfully converted to GIF")
                    return gif_buffer
                
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
