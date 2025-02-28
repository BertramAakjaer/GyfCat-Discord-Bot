import discord, os
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from image_converter import image_to_gif # Import the image_to_gif function

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        
        try: 
            synced =  await self.tree.sync()
            print(f"Synced {len(synced)} commands")
    
        except Exception as e:
            print(f"Failed to sync commands: {e}")


    async def on_message(self, message):
        #print(f'Message from {message.author}: {message.content}')

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
        await interaction.response.send_message("Ping ping pongerfucker !!")
        
    @client.tree.command(name="printer", description="I will print whatever you say")
    async def printer(interaction: discord.Interaction, message: str):
        await interaction.response.send_message(message)

    @client.tree.command(name="to_gif", description="I will convert your image to a GIF")
    async def to_gif(interaction: discord.Interaction, image: discord.Attachment):
        gif_data = await image_to_gif(image.url)
        if gif_data:
            await interaction.response.send_message(file=discord.File(gif_data, filename="gamerimage69.gif"))
        else:
            await interaction.response.send_message("Failed to convert image to GIF.")

    client.run(token)

if __name__ == '__main__':
    main()