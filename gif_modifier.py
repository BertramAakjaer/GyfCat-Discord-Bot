import imageio.v3 as iio
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
from typing import Union
import os
from logger_setup import setup_logger
import textwrap
import os.path

logger = setup_logger('gif_modifier')

def wrap_text(text: str, max_width: int) -> list:
    """Wrap text based on maximum width in pixels."""
    words = text.split()
    lines = []
    current_line = []
    current_width = 0

    font_path = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'Futura Extra Black Condensed Regular.otf')
    try:
        font = ImageFont.truetype(font_path, size=60)
    except Exception:
        font = ImageFont.load_default()

    # Create temporary drawing context for measurements
    draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))

    for word in words:
        word_bbox = draw.textbbox((0, 0), word + " ", font=font)
        word_width = word_bbox[2] - word_bbox[0]

        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_width = word_width

    if current_line:
        lines.append(' '.join(current_line))

    return lines

async def caption_gif(gif_url: str, caption_text: str) -> Union[BytesIO, None]:
    """Add a caption to a GIF."""
    try:
        # Download GIF
        response = requests.get(gif_url, timeout=30)
        response.raise_for_status()
        
        # Read GIF frames
        gif = Image.open(BytesIO(response.content))
        frames = []
        
        # Load custom font
        font_path = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'Futura Extra Black Condensed Regular.otf')
        try:
            font = ImageFont.truetype(font_path, size=80)
            logger.info("Using custom font")
        except Exception as e:
            logger.warning(f"Could not load custom font: {e}. Using default font.")
            font = ImageFont.load_default()
        
        # Get first frame to calculate dimensions
        first_frame = Image.open(BytesIO(response.content))
        
        # Calculate margins (20% of frame width for side margins)
        side_margin = int(first_frame.width * 0.20)
        max_text_width = first_frame.width - (side_margin * 2)
        
        # Wrap text with new width constraint
        lines = wrap_text(caption_text, max_text_width)
        line_padding = 20  # Padding between lines
        outer_padding = 30  # Padding around all text (top/bottom)
        
        # Calculate text sizes
        draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        line_heights = []
        line_widths = []
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_heights.append(bbox[3] - bbox[1])
            line_widths.append(bbox[2] - bbox[0])
        
        # Calculate caption height
        caption_height = (
            outer_padding * 2 +
            sum(line_heights) +
            (line_padding * (len(lines) - 1))
        )
        
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
                
                # Draw each line of text
                y_position = outer_padding
                for i, (line, width) in enumerate(zip(lines, line_widths)):
                    x_position = (new_frame.width - width) // 2
                    draw.text((x_position, y_position - line_padding), line, font=font, fill='black')
                    y_position += line_heights[i] + line_padding
                
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
