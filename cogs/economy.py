import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger('diddy_bot')

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def new(self, interaction: discord.Interaction):
        """Create a new DiddyCoin account"""
        try:
            initial_balance = self.bot.config['bot']['initial_balance']
            await self.bot.db.create_account(interaction.user.id, initial_balance)
            await interaction.response.send_message(
                f"Account created with {initial_balance} {self.bot.config['currency']['name']}!"
            )
        except Exception as e:
            await interaction.response.send_message("Account already exists or error occurred.")
            logger.error(f"Account creation error: {e}")

    @app_commands.command()
    async def balance(self, interaction: discord.Interaction):
        """Check your DiddyCoin balance"""
        balance = await self.bot.db.get_balance(interaction.user.id)
        if balance is None:
            await interaction.response.send_message("You don't have an account! Use /new to create one.")
            return

        coins = balance // self.bot.config['currency']['cents_per_coin']
        cents = balance % self.bot.config['currency']['cents_per_coin']
        
        await interaction.response.send_message(
            f"Balance: {coins} {self.bot.config['currency']['name']} "
            f"and {cents} {self.bot.config['currency']['cents_name']}"
        )

    @app_commands.command()
    async def value(self, interaction: discord.Interaction):
        """Check current DiddyCoin value"""
        base_value = 1.0
        days_active = 30  # Placeholder for actual days calculation
        value = base_value * (1 + self.bot.config['bot']['daily_value_increase']) ** days_active
        
        await interaction.response.send_message(
            f"Current {self.bot.config['currency']['name']} value: ${value:.2f} USD"
        )

    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Show available commands"""
        commands_list = """
        Available Commands:
        /new - Create a new account
        /balance - Check your balance
        /value - Check current DiddyCoin value
        /exchange - Convert between coins and cents
        /coinflip - Start a coinflip game
        /cfjoin - Join a coinflip game
        /cflist - List active coinflip games
        """
        await interaction.response.send_message(commands_list)

async def setup(bot):
    await bot.add_cog(Economy(bot))
