import discord
from discord import app_commands
from discord.ext import commands
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger('diddy_bot')

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rob_cooldowns = {}

    @app_commands.command()
    async def new(self, interaction: discord.Interaction):
        """Create a new DiddyCoin account"""
        try:
            initial_balance = self.bot.config['bot']['initial_balance']  # Changed as per manager's request
            await self.bot.db.create_account(interaction.user.id, initial_balance)
            formatted_balance = self.bot.converter.format_amount(initial_balance)
            await interaction.response.send_message(
                f"Account created with {formatted_balance}!"
            )
        except Exception as e:
            await interaction.response.send_message("Account already exists or error occurred.")
            logger.error(f"Account creation error: {e}")

    # Rest of the file remains unchanged
    @app_commands.command()
    async def balance(self, interaction: discord.Interaction):
        """Check your DiddyCoin balance"""
        balance = await self.bot.db.get_balance(interaction.user.id)
        if balance is None:
            await interaction.response.send_message("You don't have an account! Use /new to create one.")
            return

        formatted_balance = self.bot.converter.format_amount(balance)
        await interaction.response.send_message(f"Balance: {formatted_balance}")

    @app_commands.command()
    async def rob(self, interaction: discord.Interaction, target: discord.User):
        """Attempt to rob another user"""
        if target.id == interaction.user.id:
            await interaction.response.send_message("You can't rob yourself!")
            return

        # Check cooldown
        cooldown = 3600  # 1 hour cooldown
        current_time = datetime.now().timestamp()
        last_rob = self.rob_cooldowns.get(interaction.user.id, 0)
        
        if current_time - last_rob < cooldown:
            time_left = int(cooldown - (current_time - last_rob))
            minutes = time_left // 60
            seconds = time_left % 60
            await interaction.response.send_message(
                f"You must wait {minutes}m {seconds}s before attempting another robbery!"
            )
            return

        # Check balances
        robber_balance = await self.bot.db.get_balance(interaction.user.id)
        target_balance = await self.bot.db.get_balance(target.id)

        if robber_balance is None:
            await interaction.response.send_message("You don't have an account! Use /new to create one.")
            return

        if target_balance is None:
            await interaction.response.send_message("Target doesn't have an account!")
            return

        if target_balance < 100:  # Minimum 1 coin worth of cents to rob
            await interaction.response.send_message("Target doesn't have enough money to rob!")
            return

        # Rob mechanics
        success_rate = 0.3  # 30% success rate
        if random.random() < success_rate:
            stolen_amount = random.randint(10, min(target_balance // 4, 1000))  # Max 10 coins or 25% of balance
            
            # Update balances
            await self.bot.db.update_balance(target.id, -stolen_amount)
            await self.bot.db.update_balance(interaction.user.id, stolen_amount)
            
            formatted_amount = self.bot.converter.format_amount(stolen_amount)
            await interaction.response.send_message(
                f"🎭 Robbery successful! You stole {formatted_amount} from {target.name}!"
            )
        else:
            # Failed robbery penalty (lose some money)
            penalty = random.randint(50, 200)  # Lose 0.5-2 coins worth of cents
            if robber_balance >= penalty:
                await self.bot.db.update_balance(interaction.user.id, -penalty)
                formatted_penalty = self.bot.converter.format_amount(penalty)
                await interaction.response.send_message(
                    f"😅 Robbery failed! You got caught and lost {formatted_penalty}!"
                )
            else:
                await interaction.response.send_message(
                    "😅 Robbery failed! You got caught but had nothing to lose!"
                )

        # Set cooldown
        self.rob_cooldowns[interaction.user.id] = current_time

    @app_commands.command()
    async def baltop(self, interaction: discord.Interaction, limit: int = 5):
        """Show top DiddyCoin balances (default: top 5)"""
        if not 1 <= limit <= 20:
            await interaction.response.send_message("Please specify a limit between 1 and 20.")
            return

        rich_users = await self.bot.db.get_richest_users(limit)
        if not rich_users:
            await interaction.response.send_message("No accounts found!")
            return

        msg = "💰 **Top DiddyCoin Balances**\n```"
        for i, user_data in enumerate(rich_users, 1):
            user = await self.bot.fetch_user(user_data['user_id'])
            formatted_balance = self.bot.converter.format_amount(user_data['balance'])
            msg += f"{i}. {user.name}: {formatted_balance}\n"
        msg += "```"

        await interaction.response.send_message(msg)

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
    async def trade(self, interaction: discord.Interaction, user: discord.User, amount: int):
        """Send DiddyCoins to another user"""
        if user.id == interaction.user.id:
            await interaction.response.send_message("You can't trade with yourself!")
            return

        sender_balance = await self.bot.db.get_balance(interaction.user.id)
        if sender_balance is None:
            await interaction.response.send_message("You don't have an account! Use /new to create one.")
            return

        if sender_balance < amount:
            await interaction.response.send_message("Insufficient funds!")
            return

        receiver_balance = await self.bot.db.get_balance(user.id)
        if receiver_balance is None:
            await interaction.response.send_message("The recipient doesn't have an account!")
            return

        trade_id = await self.bot.db.create_trade(interaction.user.id, user.id, amount)
        formatted_amount = self.bot.converter.format_amount(amount)
        await interaction.response.send_message(
            f"Trade offer sent to {user.name}!\n"
            f"Amount: {formatted_amount}\n"
            f"They can accept it using `/accept {trade_id}`"
        )

    @app_commands.command()
    async def accept(self, interaction: discord.Interaction, trade_id: int):
        """Accept a pending trade"""
        if await self.bot.db.execute_trade(trade_id):
            await interaction.response.send_message("Trade completed successfully!")
        else:
            await interaction.response.send_message("Trade not found or already processed!")

    @app_commands.command()
    async def decline(self, interaction: discord.Interaction, trade_id: int):
        """Decline a pending trade"""
        if await self.bot.db.cancel_trade(trade_id):
            await interaction.response.send_message("Trade cancelled successfully!")
        else:
            await interaction.response.send_message("Trade not found or already processed!")

    @app_commands.command()
    async def trades(self, interaction: discord.Interaction):
        """List your pending trades"""
        pending_trades = await self.bot.db.get_pending_trades(interaction.user.id)
        if not pending_trades:
            await interaction.response.send_message("No pending trades!")
            return

        trades_list = "Pending Trades:\n"
        for trade in pending_trades:
            sender = await self.bot.fetch_user(trade['sender_id'])
            formatted_amount = self.bot.converter.format_amount(trade['amount'])
            trades_list += f"ID: {trade['id']} | From: {sender.name} | Amount: {formatted_amount}\n"

        await interaction.response.send_message(trades_list)

    @app_commands.command()
    async def help(self, interaction: discord.Interaction):
        """Show available commands"""
        commands_list = """
        Available Commands:
        /new - Create a new account
        /balance - Check your balance
        /baltop [limit] - Show top DiddyCoin balances
        /value - Check current DiddyCoin value
        /trade <user> <amount> - Send DiddyCoins to another user
        /accept <trade_id> - Accept a pending trade
        /decline <trade_id> - Decline a pending trade
        /trades - List your pending trades
        /rob <user> - Attempt to rob another user
        /coinflip - Start a coinflip game
        /cfjoin - Join a coinflip game
        /cflist - List active coinflip games
        """
        await interaction.response.send_message(commands_list)

async def setup(bot):
    await bot.add_cog(Economy(bot))
