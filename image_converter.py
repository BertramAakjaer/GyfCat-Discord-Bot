import imageio
import os
import requests
from io import BytesIO
from PIL import Image

from typing import Union

async def image_to_gif(image_url: str) -> Union[BytesIO, None]:
    """
    Converts an image from a URL to a GIF.

    Args:
        image_url: The URL of the image.

    Returns:
        A BytesIO object containing the GIF, or None if an error occurred.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        img = Image.open(BytesIO(response.content))
        
        # Convert the image to RGB mode if it's not already
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Save the image as a GIF in memory
        gif_buffer = BytesIO()
        img.save(gif_buffer, format='GIF')
        gif_buffer.seek(0)  # Reset the buffer's position to the beginning

        return gif_buffer

    except Exception as e:
        print(f"Error converting image to GIF: {e}")
        return None
