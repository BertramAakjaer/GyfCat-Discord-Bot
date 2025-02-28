import imageio.v3 as iio
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from typing import Union
import os
from logger_setup import setup_logger

logger = setup_logger('gif_modifier')

async def caption_gif(gif_url: str, caption_text: str) -> Union[BytesIO, None]:
    """Add a caption to a GIF."""
    try:
        # Download GIF
        response = requests.get(gif_url, timeout=30)
        response.raise_for_status()
        
        # Read GIF frames
        gif = Image.open(BytesIO(response.content))
        frames = []
        
        # Calculate optimal font size and caption height
        base_font_size = 60
        font = ImageFont.load_default()
        padding = 20  # Padding around text
        
        # Get initial text size
        draw = ImageDraw.Draw(Image.new('RGBA', (1, 1), (0, 0, 0, 0)))
        text_bbox = draw.textbbox((0, 0), caption_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Calculate caption height with padding
        caption_height = text_height + (padding * 2)
        
        try:
            while True:
                frame = gif.copy()
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')
                
                # Create new frame with white background for caption
                new_frame = Image.new('RGBA', (frame.width, frame.height + caption_height), 'white')
                new_frame.paste(frame, (0, caption_height))
                
                # Add caption
                draw = ImageDraw.Draw(new_frame)
                
                # Calculate centered position
                text_x = (new_frame.width - text_width) // 2
                text_y = (caption_height - text_height) // 2
                
                # Draw text in black
                draw.text((text_x, text_y), caption_text, font=font, fill='black')
                
                frames.append(new_frame)
                gif.seek(gif.tell() + 1)
                
        except EOFError:
            pass
        
        # Save the result
        output = BytesIO()
        duration = gif.info.get('duration', 100)
        frames[0].save(
            output,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            optimize=False
        )
        output.seek(0)
        
        return output
        
    except Exception as e:
        logger.error(f"Error captioning GIF: {e}")
        logger.exception("Full traceback:")
        return None
