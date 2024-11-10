import discord
from discord import app_commands
from discord.ext import commands
import logging

logger = logging.getLogger('diddy_bot')

def is_admin():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in interaction.client.config['bot']['admin_ids']
    return app_commands.check(predicate)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @is_admin()
    async def cent(self, interaction: discord.Interaction, action: str, user: discord.User, amount: int):
        """Admin command to give or remove cents from a user"""
        if action not in ['give', 'remove']:
            await interaction.response.send_message("Invalid action. Use 'give' or 'remove'.")
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be positive.")
            return

        user_balance = await self.bot.db.get_balance(user.id)
        if user_balance is None:
            await interaction.response.send_message(f"{user.name} doesn't have an account!")
            return

        if action == 'remove' and user_balance < amount:
            await interaction.response.send_message(f"{user.name} doesn't have enough {self.bot.config['currency']['cents_name']}!")
            return

        delta = amount if action == 'give' else -amount
        await self.bot.db.update_balance(user.id, delta)
        
        action_text = "given to" if action == 'give' else "removed from"
        await interaction.response.send_message(
            f"{amount} {self.bot.config['currency']['cents_name']} {action_text} {user.name}"
        )

    @app_commands.command()
    @is_admin()
    async def clear(self, interaction: discord.Interaction, user: discord.User):
        """Admin command to clear a user's balance"""
        user_balance = await self.bot.db.get_balance(user.id)
        if user_balance is None:
            await interaction.response.send_message(f"{user.name} doesn't have an account!")
            return

        await self.bot.db.update_balance(user.id, -user_balance)
        await interaction.response.send_message(f"Cleared {user.name}'s balance.")

    @cent.error
    @clear.error
    async def admin_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("You don't have permission to use this command!", ephemeral=True)
        else:
            logger.error(f"Admin command error: {error}")
            await interaction.response.send_message("An error occurred while executing the command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
