import imageio.v3 as iio
import os
import requests
from io import BytesIO
from PIL import Image
from typing import Union
import tempfile

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

        # Check if it's a video
        if await is_video(url):
            # Create a temporary file to store the video
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(url)[1]) as tmp_file:
                tmp_file.write(response.content)
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
                
                return gif_buffer
        else:
            # Handle image as before
            img = Image.open(BytesIO(response.content))
            
            if img.mode != 'RGB':
                img = img.convert('RGB')

            gif_buffer = BytesIO()
            img.save(gif_buffer, format='GIF')
            gif_buffer.seek(0)
            
            return gif_buffer

    except Exception as e:
        print(f"Error converting to GIF: {e}")
        return None
