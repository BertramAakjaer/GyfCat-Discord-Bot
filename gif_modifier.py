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
        
        try:
            while True:
                # Copy frame
                frame = gif.copy()
                
                # Convert to RGBA if needed
                if frame.mode != 'RGBA':
                    frame = frame.convert('RGBA')
                
                # Create new image with space for caption
                caption_height = 60
                new_frame = Image.new('RGBA', (frame.width, frame.height + caption_height), (0, 0, 0, 0))
                
                # Paste original frame
                new_frame.paste(frame, (0, caption_height))
                
                # Add caption
                draw = ImageDraw.Draw(new_frame)
                
                # Use a built-in font (you can add custom fonts later)
                font_size = 30
                font = ImageFont.load_default()
                
                # Calculate text position (center it)
                text_bbox = draw.textbbox((0, 0), caption_text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_x = (new_frame.width - text_width) // 2
                
                # Draw text with black outline
                outline_positions = [(x, y) for x in [-1, 0, 1] for y in [-1, 0, 1]]
                for x_offset, y_offset in outline_positions:
                    draw.text((text_x + x_offset, y_offset + 10), caption_text, font=font, fill='black')
                
                # Draw main text in white
                draw.text((text_x, 10), caption_text, font=font, fill='white')
                
                # Append the frame
                frames.append(new_frame)
                
                # Go to next frame
                gif.seek(gif.tell() + 1)
                
        except EOFError:
            pass  # We've processed all frames
        
        # Save the result
        output = BytesIO()
        # Save with original frame duration
        duration = gif.info.get('duration', 100)  # Default to 100ms if not specified
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
