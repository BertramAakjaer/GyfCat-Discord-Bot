import discord, os
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from to_gif_converter import file_to_gif # Import the image_to_gif function
from logger_setup import setup_logger
from gif_modifier import caption_gif

logger = setup_logger('discord_bot')

class Client(commands.Bot):
    async def on_ready(self):
        logger.info(f'Logged on as {self.user}!')
        
        try: 
            synced =  await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
    
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")


    async def on_message(self, message):
        logger.info(f'Message from {message.author}: {message.content}')

        if message.author == self.user:
            return
        
        return
        #if message.content == 'ping':
        #    await message.channel.send('pong')


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.dm_messages = True


    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')

    client = Client(command_prefix="!", intents=intents)

    @client.tree.command(name="ping", description="Responds with pong")
    async def ping(interaction: discord.Interaction):
        await interaction.response.send_message("ping pong pang pung")
        
    @client.tree.command(name="printer", description="I will print whatever you say")
    async def printer(interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)

    @client.tree.command(name="to_gif", description="Convert an image or video to a GIF")
    async def to_gif(interaction: discord.Interaction, file: discord.Attachment):
        await interaction.response.defer()
        logger.info(f"Converting file: {file.filename}")
        
        gif_data = await file_to_gif(file.url)
        if isinstance(gif_data, str):
            # Handle disabled video message
            await interaction.followup.send(gif_data)
        elif gif_data:
            await interaction.followup.send(file=discord.File(gif_data, filename="converted_to.gif"))
            logger.info(f"Successfully converted {file.filename} to GIF")
        else:
            await interaction.followup.send("Failed to convert file to GIF.")
            logger.error(f"Failed to convert {file.filename} to GIF")

    @client.tree.command(name="caption", description="Add a caption to a GIF")
    async def caption(interaction: discord.Interaction, gif: discord.Attachment, text: str):
        await interaction.response.defer()
        logger.info(f"Captioning GIF: {gif.filename} with text: {text}")
        
        if not gif.filename.lower().endswith('.gif'):
            await interaction.followup.send("Please provide a GIF file!")
            return
            
        captioned_gif = await caption_gif(gif.url, text)
        if captioned_gif:
            await interaction.followup.send(
                file=discord.File(captioned_gif, filename="captioned.gif")
            )
            logger.info(f"Successfully captioned GIF {gif.filename}")
        else:
            await interaction.followup.send("Failed to caption the GIF.")
            logger.error(f"Failed to caption GIF {gif.filename}")

    client.run(token)

if __name__ == '__main__': 
    main()