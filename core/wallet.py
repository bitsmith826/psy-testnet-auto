"""
Wallet & SIWE Authentication Utilities for Psy Protocol
"""

import re
from datetime import datetime, timezone
from typing import Optional, Tuple
from eth_account import Account
from eth_account.messages import encode_defunct


class EVMWallet:
    def __init__(self, private_key: str):
        cleaned_key = private_key.strip()
        if not cleaned_key.startswith("0x"):
            cleaned_key = "0x" + cleaned_key
        self.private_key = cleaned_key
        self.account = Account.from_key(self.private_key)
        self.address = self.account.address

    @classmethod
    def create_ephemeral(cls) -> "EVMWallet":
        """Generate a random new EVM account."""
        new_acc = Account.create()
        return cls(new_acc.key.hex())

    def format_siwe_message(self, nonce: str, chain_id: int = 1) -> str:
        """
        Build exact SIWE (EIP-4361) message expected by Psy Protocol:
        https://psy.xyz wants you to sign in with your Ethereum account:
        <address>

        URI: https://psy.xyz
        Version: 1
        Chain ID: 1
        Nonce: <nonce>
        Issued At: <iso8601_time>
        """
        iso_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        message = (
            f"https://psy.xyz wants you to sign in with your Ethereum account:\n"
            f"{self.address}\n\n"
            f"URI: https://psy.xyz\n"
            f"Version: 1\n"
            f"Chain ID: {chain_id}\n"
            f"Nonce: {nonce}\n"
            f"Issued At: {iso_time}"
        )
        return message

    def sign_message(self, message: str) -> str:
        """Sign message using standard personal_sign (EIP-191)."""
        signable = encode_defunct(text=message)
        signed = self.account.sign_message(signable)
        sig = signed.signature.hex()
        if not sig.startswith("0x"):
            sig = "0x" + sig
        return sig
