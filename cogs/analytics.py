import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('diddy_bot')

def create_bar_chart(values, labels, title, width=20):
    """Create an ASCII bar chart"""
    if not values:
        return "No data available"
    
    max_val = max(values)
    max_label_len = max(len(str(label)) for label in labels)
    
    chart = f"{title}\n\n"
    for i, (value, label) in enumerate(zip(values, labels)):
        bar_length = int((value / max_val) * width) if max_val > 0 else 0
        chart += f"{str(label):<{max_label_len}} | {'█' * bar_length} {value}\n"
    
    return f"```{chart}```"

class Analytics(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    async def stats(self, interaction: discord.Interaction):
        """Show overall DiddyCoin statistics"""
        total_supply = await self.bot.db.get_total_currency_supply()
        trading_stats = await self.bot.db.get_trading_stats()
        gambling_stats = await self.bot.db.get_gambling_stats()

        stats_msg = f"📊 **DiddyCoin Statistics**\n\n"
        stats_msg += f"Total Supply: {total_supply} {self.bot.config['currency']['cents_name']}\n\n"
        
        stats_msg += "**Trading Activity**\n"
        stats_msg += f"Total Trades: {trading_stats['total_trades']}\n"
        stats_msg += f"Completed Trades: {trading_stats['completed_trades']}\n"
        stats_msg += f"Cancelled Trades: {trading_stats['cancelled_trades']}\n"
        if trading_stats['avg_trade_amount']:
            stats_msg += f"Average Trade Amount: {trading_stats['avg_trade_amount']:.2f} {self.bot.config['currency']['cents_name']}\n\n"
        
        stats_msg += "**Gambling Activity**\n"
        stats_msg += f"Total Games: {gambling_stats['total_games']}\n"
        if gambling_stats['avg_bet_amount']:
            stats_msg += f"Average Bet: {gambling_stats['avg_bet_amount']:.2f} {self.bot.config['currency']['cents_name']}\n"
        if gambling_stats['highest_bet']:
            stats_msg += f"Highest Bet: {gambling_stats['highest_bet']} {self.bot.config['currency']['cents_name']}\n"

        await interaction.response.send_message(stats_msg)

    @app_commands.command()
    async def richlist(self, interaction: discord.Interaction):
        """Show the richest DiddyCoin holders"""
        rich_users = await self.bot.db.get_richest_users(10)
        
        if not rich_users:
            await interaction.response.send_message("No accounts found!")
            return

        values = [user['balance'] for user in rich_users]
        labels = []
        for user_data in rich_users:
            user = await self.bot.fetch_user(user_data['user_id'])
            labels.append(user.name)

        chart = create_bar_chart(values, labels, "🏆 Richest DiddyCoin Holders")
        await interaction.response.send_message(chart)

    @app_commands.command()
    async def volume(self, interaction: discord.Interaction, days: int = 7):
        """Show transaction volume over time"""
        if not 1 <= days <= 30:
            await interaction.response.send_message("Please specify between 1 and 30 days.")
            return

        volume_data = await self.bot.db.get_transaction_volume(days)
        if not volume_data:
            await interaction.response.send_message("No transaction data available.")
            return

        dates = [row['date'].strftime('%Y-%m-%d') for row in volume_data]
        volumes = [row['volume'] for row in volume_data]
        transactions = [row['num_transactions'] for row in volume_data]

        volume_chart = create_bar_chart(volumes, dates, "📈 Transaction Volume")
        trans_chart = create_bar_chart(transactions, dates, "🔄 Number of Transactions")

        await interaction.response.send_message(f"{volume_chart}\n{trans_chart}")

    @app_commands.command()
    async def history(self, interaction: discord.Interaction):
        """Show your transaction history"""
        history = await self.bot.db.get_user_transaction_history(interaction.user.id)
        if not history:
            await interaction.response.send_message("No transaction history found!")
            return

        msg = "📜 **Your Recent Transactions**\n```"
        for trans in history:
            amount = trans['amount']
            symbol = '+" if amount > 0 else "-'
            msg += f"{trans['timestamp'].strftime('%Y-%m-%d %H:%M')} | "
            msg += f"{symbol}{abs(amount)} {self.bot.config['currency']['cents_name']} | "
            msg += f"{trans['type']}\n"
        msg += "```"

        await interaction.response.send_message(msg)

async def setup(bot):
    await bot.add_cog(Analytics(bot))
