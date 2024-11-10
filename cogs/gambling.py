import discord
from discord import app_commands
from discord.ext import commands
import random
import logging

logger = logging.getLogger('diddy_bot')

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def coinflip(self, interaction: discord.Interaction, amount: int):
        """Start a coinflip game"""
        if amount < self.bot.config['gambling']['min_bet']:
            await interaction.response.send_message(
                f"Minimum bet is {self.bot.config['gambling']['min_bet']} {self.bot.config['currency']['cents_name']}"
            )
            return

        if amount > self.bot.config['gambling']['max_bet']:
            await interaction.response.send_message(
                f"Maximum bet is {self.bot.config['gambling']['max_bet']} {self.bot.config['currency']['cents_name']}"
            )
            return

        balance = await self.bot.db.get_balance(interaction.user.id)
        if balance is None or balance < amount:
            await interaction.response.send_message("Insufficient funds!")
            return

        game_id = await self.bot.db.create_game('coinflip', interaction.user.id, amount)
        await interaction.response.send_message(
            f"Coinflip game created! Game ID: {game_id}\n"
            f"Bet amount: {amount} {self.bot.config['currency']['cents_name']}\n"
            f"Use /cfjoin {game_id} to join!"
        )

    @app_commands.command()
    async def cfjoin(self, interaction: discord.Interaction, game_id: int):
        """Join a coinflip game"""
        game = await self.bot.db.get_active_games('coinflip')
        game = next((g for g in game if g['id'] == game_id), None)

        if not game:
            await interaction.response.send_message("Game not found!")
            return

        if game['creator_id'] == interaction.user.id:
            await interaction.response.send_message("You can't join your own game!")
            return

        balance = await self.bot.db.get_balance(interaction.user.id)
        if balance is None or balance < game['bet_amount']:
            await interaction.response.send_message("Insufficient funds!")
            return

        # Process the game
        winner = random.choice([game['creator_id'], interaction.user.id])
        loser = game['creator_id'] if winner == interaction.user.id else interaction.user.id

        await self.bot.db.update_balance(winner, game['bet_amount'])
        await self.bot.db.update_balance(loser, -game['bet_amount'])

        winner_name = (await self.bot.fetch_user(winner)).name
        await interaction.response.send_message(
            f"🎲 Game Results 🎲\n"
            f"Winner: {winner_name}\n"
            f"Prize: {game['bet_amount']} {self.bot.config['currency']['cents_name']}"
        )

    @app_commands.command()
    async def cflist(self, interaction: discord.Interaction):
        """List active coinflip games"""
        games = await self.bot.db.get_active_games('coinflip')
        if not games:
            await interaction.response.send_message("No active games found!")
            return

        games_list = "Active Coinflip Games:\n"
        for game in games:
            creator = await self.bot.fetch_user(game['creator_id'])
            games_list += f"ID: {game['id']} | Creator: {creator.name} | "
            games_list += f"Bet: {game['bet_amount']} {self.bot.config['currency']['cents_name']}\n"

        await interaction.response.send_message(games_list)

async def setup(bot):
    await bot.add_cog(Gambling(bot))
