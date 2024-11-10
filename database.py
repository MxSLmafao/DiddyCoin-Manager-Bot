import os
import asyncpg
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('diddy_bot')

class Database:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        try:
            self.pool = await asyncpg.create_pool(
                user=os.environ['PGUSER'],
                password=os.environ['PGPASSWORD'],
                database=os.environ['PGDATABASE'],
                host=os.environ['PGHOST'],
                port=os.environ['PGPORT']
            )

            # Create tables if they don't exist
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS accounts (
                        user_id BIGINT PRIMARY KEY,
                        balance BIGINT NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT,
                        amount BIGINT,
                        type VARCHAR(50),
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS active_games (
                        id SERIAL PRIMARY KEY,
                        game_type VARCHAR(50),
                        creator_id BIGINT,
                        bet_amount BIGINT,
                        status VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id SERIAL PRIMARY KEY,
                        sender_id BIGINT,
                        receiver_id BIGINT,
                        amount BIGINT,
                        status VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (sender_id) REFERENCES accounts(user_id),
                        FOREIGN KEY (receiver_id) REFERENCES accounts(user_id)
                    )
                ''')

        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    async def create_account(self, user_id: int, initial_balance: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                'INSERT INTO accounts (user_id, balance) VALUES ($1, $2)',
                user_id, initial_balance
            )

    async def get_balance(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                'SELECT balance FROM accounts WHERE user_id = $1',
                user_id
            )

    async def update_balance(self, user_id: int, amount: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    'UPDATE accounts SET balance = balance + $1 WHERE user_id = $2',
                    amount, user_id
                )
                await conn.execute(
                    'INSERT INTO transactions (user_id, amount, type) VALUES ($1, $2, $3)',
                    user_id, amount, 'update'
                )

    async def create_trade(self, sender_id: int, receiver_id: int, amount: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                '''INSERT INTO trades (sender_id, receiver_id, amount, status)
                   VALUES ($1, $2, $3, 'pending')
                   RETURNING id''',
                sender_id, receiver_id, amount
            )

    async def get_pending_trades(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                '''SELECT * FROM trades 
                   WHERE receiver_id = $1 AND status = 'pending'
                   ORDER BY created_at DESC''',
                user_id
            )

    async def execute_trade(self, trade_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                trade = await conn.fetchrow(
                    'SELECT * FROM trades WHERE id = $1 AND status = \'pending\'',
                    trade_id
                )
                
                if not trade:
                    return False

                # Update balances
                await conn.execute(
                    'UPDATE accounts SET balance = balance - $1 WHERE user_id = $2',
                    trade['amount'], trade['sender_id']
                )
                await conn.execute(
                    'UPDATE accounts SET balance = balance + $1 WHERE user_id = $2',
                    trade['amount'], trade['receiver_id']
                )
                
                # Update trade status
                await conn.execute(
                    'UPDATE trades SET status = \'completed\' WHERE id = $1',
                    trade_id
                )
                
                # Record transactions
                await conn.execute(
                    'INSERT INTO transactions (user_id, amount, type) VALUES ($1, $2, $3)',
                    trade['sender_id'], -trade['amount'], 'trade_sent'
                )
                await conn.execute(
                    'INSERT INTO transactions (user_id, amount, type) VALUES ($1, $2, $3)',
                    trade['receiver_id'], trade['amount'], 'trade_received'
                )
                
                return True

    async def cancel_trade(self, trade_id: int):
        async with self.pool.acquire() as conn:
            return await conn.execute(
                'UPDATE trades SET status = \'cancelled\' WHERE id = $1 AND status = \'pending\'',
                trade_id
            )

    async def create_game(self, game_type: str, creator_id: int, bet_amount: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                '''INSERT INTO active_games (game_type, creator_id, bet_amount, status)
                   VALUES ($1, $2, $3, 'open')
                   RETURNING id''',
                game_type, creator_id, bet_amount
            )

    async def get_active_games(self, game_type: str):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                '''SELECT * FROM active_games 
                   WHERE game_type = $1 AND status = 'open'
                   ORDER BY created_at DESC''',
                game_type
            )

    # Analytics methods
    async def get_total_currency_supply(self):
        """Get the total amount of currency in circulation"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval('SELECT SUM(balance) FROM accounts')

    async def get_richest_users(self, limit=10):
        """Get the users with highest balances"""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT user_id, balance 
                FROM accounts 
                ORDER BY balance DESC 
                LIMIT $1
            ''', limit)

    async def get_transaction_volume(self, days=7):
        """Get total transaction volume for the last N days"""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT DATE(timestamp) as date,
                       COUNT(*) as num_transactions,
                       SUM(ABS(amount)) as volume
                FROM transactions
                WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '$1 days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            ''', days)

    async def get_trading_stats(self):
        """Get statistics about trading activity"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed_trades,
                    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_trades,
                    AVG(amount) FILTER (WHERE status = 'completed') as avg_trade_amount
                FROM trades
            ''')

    async def get_gambling_stats(self):
        """Get statistics about gambling activity"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total_games,
                    AVG(bet_amount) as avg_bet_amount,
                    MAX(bet_amount) as highest_bet
                FROM active_games
                WHERE status != 'open'
            ''')

    async def get_user_transaction_history(self, user_id: int, limit=10):
        """Get recent transaction history for a user"""
        async with self.pool.acquire() as conn:
            return await conn.fetch('''
                SELECT type, amount, timestamp
                FROM transactions
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            ''', user_id, limit)
