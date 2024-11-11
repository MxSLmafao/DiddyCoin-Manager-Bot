import os
import discord
from discord import app_commands
from discord.ext import commands
import yaml
import asyncio
from database import Database
from utils.currency import CurrencyConverter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('diddy_bot')

# Load configuration
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

class DiddyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=config['bot']['prefix'], intents=intents)
        self.config = config
        self.db = Database()
        self.converter = CurrencyConverter(config)  # Initialize the currency converter

    async def setup_hook(self):
        await self.db.initialize()
        await self.load_extension('cogs.economy')
        await self.load_extension('cogs.gambling')
        await self.load_extension('cogs.analytics')
        await self.load_extension('cogs.admin')  # Load the admin cog
        await self.tree.sync()

    async def on_ready(self):
        logger.info(f'Logged in as {self.user.name}')
        await self.change_presence(activity=discord.Game(name="Managing DiddyCoin"))

async def main():
    bot = DiddyBot()
    async with bot:
        await bot.start(os.environ.get('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main())
