
import uuid
import json
import os
import random

class WalletManager:
    """Manages the generation and retrieval of agent-exclusive wallet addresses."""

    def __init__(self):
        self.wallets = {}

    def generate_unique_wallet_address(self, agent_id: str) -> str:
        """Generates a pseudo-random unique wallet address (e.g., a mock blockchain address)."""
        # In a real blockchain integration, this would interact with a crypto library.
        # Here, we use UUID for uniqueness for simulation purposes.
        wallet_address = "0x{}".format(uuid.uuid4().hex)
        self.wallets[agent_id] = wallet_address
        return wallet_address

    def get_wallet_address(self, agent_id: str) -> str | None:
        """Retrieves a wallet address for a given agent_id."""
        return self.wallets.get(agent_id)


class CDIVault:
    """Represents the CDI Vault, extended for agent financial autonomy."""

    def __init__(self, agent_data_list: list):
        self.wallet_manager = WalletManager()
        self.agent_data_list = agent_data_list
        self._load_wallets_from_agent_data() # Load existing wallets from agent_data upon initialization

    def _load_wallets_from_agent_data(self):
        """Loads wallet addresses from the existing agent_data structure into WalletManager."""
        for agent in self.agent_data_list:
            agent_name = agent.get('Name_KR')
            if agent_name:
                agent_id = "AGENT_{}".format(agent_name.replace(' ', '_').upper())
                if 'crypto_wallet_address' in agent and agent['crypto_wallet_address']:
                    self.wallet_manager.wallets[agent_id] = agent['crypto_wallet_address']

    def get_agent_wallet(self, agent_name: str) -> str | None:
        """Retrieves the cryptocurrency wallet address for a given agent."""
        agent_id = "AGENT_{}".format(agent_name.replace(' ', '_').upper())
        # First, try to get from the WalletManager (which includes loaded and newly bound wallets)
        wallet_address = self.wallet_manager.get_wallet_address(agent_id)
        if wallet_address:
            return wallet_address

        # If not found, it means the agent might not have a wallet bound yet
        return None

    def bind_new_wallet_to_agent(self, agent_name: str) -> str | None:
        """
        Generates and binds a new wallet address to an agent.
        Updates the agent's profile in the provided agent_data_list.
        """
        agent_id = "AGENT_{}".format(agent_name.replace(' ', '_').upper())

        # Check if a wallet already exists for this agent
        if self.get_agent_wallet(agent_name):
            print("Agent {} already has a wallet bound: {}!".format(agent_name, self.get_agent_wallet(agent_name)))
            return self.get_agent_wallet(agent_name)

        wallet_address = self.wallet_manager.generate_unique_wallet_address(agent_id)

        # Update the global agent_data_list that was passed during initialization
        found_agent = False
        for agent in self.agent_data_list:
            if agent.get('Name_KR') == agent_name:
                agent['crypto_wallet_address'] = wallet_address
                found_agent = True
                break

        if found_agent:
            print("Bound new wallet {} to {}.".format(wallet_address, agent_name))
            return wallet_address
        else:
            print("Error: Agent {} not found in agent_data_list. Cannot bind wallet.".format(agent_name))
            return None

    def get_wallet_balance(self, agent_name: str) -> float | None:
        """
        Retrieves the mock cryptocurrency balance for a given agent.
        In a real scenario, this would query a blockchain or a financial service.
        """
        wallet_address = self.get_agent_wallet(agent_name)
        if wallet_address:
            # Simulate a balance for demonstration purposes
            # For consistency, a simple random value. In a real system, this would be actual balance.
            return round(random.uniform(100.0, 10000.0), 2)
        else:
            print("No wallet found for agent {}. Cannot retrieve balance.".format(agent_name))
            return None

    def simulate_transfer_funds(self, from_agent_name: str, to_agent_name: str, amount: float, currency: str = "USDC") -> bool:
        """
        Simulates a transfer of funds from one agent to another.
        This is a mock implementation; no actual funds are moved or balances updated.
        """
        print("
💸 Initiating simulated transfer of {} {} from {} to {}...".format(amount, currency, from_agent_name, to_agent_name))

        from_wallet = self.get_agent_wallet(from_agent_name)
        to_wallet = self.get_agent_wallet(to_agent_name)

        if not from_wallet:
            print("❌ Transfer failed: No wallet found for sending agent {}.".format(from_agent_name))
            return False
        if not to_wallet:
            print("❌ Transfer failed: No wallet found for receiving agent {}.".format(to_agent_name))
            return False

        # In a real scenario, check balance and perform actual transaction.
        # For this simulation, we assume sufficient funds and successful execution.

        print("✅ Simulated transfer successful: {} {} from {} (Wallet: {}) to {} (Wallet: {}).".format(amount, currency, from_agent_name, from_wallet, to_agent_name, to_wallet))
        return True

    # def record_transaction(self, agent_name: str, type: str, amount: float, details: dict): ...
