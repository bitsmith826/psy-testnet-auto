"""
On-Chain Sepolia Testnet Interactor (Faucet & Bridge for Psy Protocol)
"""

from typing import Any, Dict, Optional, Tuple
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

# Minimal ABI for TokenFaucetManager
FAUCET_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
        "name": "claim",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "address", "name": "token", "type": "address"}
        ],
        "name": "canClaim",
        "outputs": [
            {"internalType": "bool", "name": "ok", "type": "bool"},
            {"internalType": "uint64", "name": "nextEligibleBlock", "type": "uint64"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Minimal ABI for ERC20
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function"
    }
]


class SepoliaTestnetClient:
    def __init__(
        self,
        private_key: str,
        rpc_url: str = "https://ethereum-sepolia-rpc.publicnode.com",
        faucet_address: str = "0x45C75b923d48A58575e38D77ffDdF132277d7Ad9",
        usdt_address: str = "0x58869e0a2Ef41aB08D2669B0e8508A29A9DE1cE7",
        psy_address: str = "0x625b5b6239074FA9B4325Bc1e5535E7dAB23459f"
    ):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.private_key = private_key if private_key.startswith("0x") else f"0x{private_key}"
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.address = self.account.address
        self.faucet_address = Web3.to_checksum_address(faucet_address)
        self.usdt_address = Web3.to_checksum_address(usdt_address)
        self.psy_address = Web3.to_checksum_address(psy_address)

        self.faucet_contract = self.w3.eth.contract(address=self.faucet_address, abi=FAUCET_ABI)
        self.usdt_contract = self.w3.eth.contract(address=self.usdt_address, abi=ERC20_ABI)
        self.psy_contract = self.w3.eth.contract(address=self.psy_address, abi=ERC20_ABI)

    def is_connected(self) -> bool:
        return self.w3.is_connected()

    def get_eth_balance(self) -> float:
        """Returns native Sepolia ETH balance."""
        balance_wei = self.w3.eth.get_balance(self.address)
        return float(self.w3.from_wei(balance_wei, "ether"))

    def get_token_balances(self) -> Dict[str, float]:
        """Returns pUSDT and test PSY balances."""
        try:
            usdt_raw = self.usdt_contract.functions.balanceOf(self.address).call()
            usdt_bal = usdt_raw / 10**6  # USDT has 6 decimals
        except Exception:
            usdt_bal = 0.0

        try:
            psy_raw = self.psy_contract.functions.balanceOf(self.address).call()
            psy_bal = psy_raw / 10**9   # PSY has 9 decimals
        except Exception:
            psy_bal = 0.0

        return {"pUSDT": usdt_bal, "PSY": psy_bal}

    def check_can_claim(self, token_address: str) -> Tuple[bool, int]:
        """Check if eligible to claim faucet token."""
        try:
            checksum_token = Web3.to_checksum_address(token_address)
            ok, next_block = self.faucet_contract.functions.canClaim(self.address, checksum_token).call()
            return ok, next_block
        except Exception as e:
            return False, 0

    def claim_faucet(self, token_name: str = "USDT") -> Dict[str, Any]:
        """Claim test pUSDT or test PSY from Sepolia Faucet Manager."""
        token_addr = self.usdt_address if token_name.upper() == "USDT" else self.psy_address
        ok, next_block = self.check_can_claim(token_addr)
        current_block = self.w3.eth.block_number

        if not ok:
            return {
                "success": False,
                "error": f"Faucet on cooldown until block {next_block} (Current block: {current_block})"
            }

        eth_bal = self.get_eth_balance()
        if eth_bal < 0.0005:
            return {
                "success": False,
                "error": f"Insufficient Sepolia ETH for gas fee (Balance: {eth_bal:.4f} ETH). Claim Sepolia ETH from Google/Alchemy faucet first."
            }

        try:
            nonce = self.w3.eth.get_transaction_count(self.address)
            gas_price = self.w3.eth.gas_price

            tx = self.faucet_contract.functions.claim(token_addr).build_transaction({
                "from": self.address,
                "nonce": nonce,
                "gasPrice": int(gas_price * 1.2),
                "chainId": 11155111
            })

            # Estimate gas
            try:
                gas_est = self.w3.eth.estimate_gas(tx)
                tx["gas"] = int(gas_est * 1.2)
            except Exception:
                tx["gas"] = 150000

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hex = tx_hash.hex()

            return {
                "success": True,
                "tx_hash": tx_hex,
                "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hex}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
