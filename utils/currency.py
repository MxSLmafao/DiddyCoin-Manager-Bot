class CurrencyConverter:
    def __init__(self, config):
        self.config = config

    def coins_to_cents(self, coins: int) -> int:
        """Convert coins to cents"""
        return coins * self.config['currency']['cents_per_coin']

    def cents_to_coins(self, cents: int) -> tuple[int, int]:
        """Convert cents to coins and remaining cents"""
        coins = cents // self.config['currency']['cents_per_coin']
        remaining_cents = cents % self.config['currency']['cents_per_coin']
        return coins, remaining_cents

    def format_amount(self, cents: int) -> str:
        """Format amount in a human-readable format"""
        coins, remaining_cents = self.cents_to_coins(cents)
        return f"{coins} {self.config['currency']['name']} and {remaining_cents} {self.config['currency']['cents_name']}"
