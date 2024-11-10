import os
import asyncpg
import logging
from datetime import datetime

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
