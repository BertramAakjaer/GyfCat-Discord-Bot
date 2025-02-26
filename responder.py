import discord

from discord.ext import commands
from discord import app_commands

class Client(commands.Bot):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        
        if message.author == self.user:
            return
        
        if message.content == 'ping':
            await message.channel.send('pong')