"""
====================================================================
PSY PROTOCOL — PURE ON-CHAIN TESTNET BOT (NO JWT / NO CLOUDFLARE)
Direct Smart Contract Interaction on Ethereum Sepolia
====================================================================
"""

import sys
import os
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from modules.account_manager import AccountManager
from core.onchain import SepoliaTestnetClient

console = Console(legacy_windows=False)


def run_pure_onchain_testnet():
    console.print("[bold cyan]+------------------------------------------------------------+[/bold cyan]")
    console.print("[bold magenta]|      PSY PROTOCOL -- 100% ON-CHAIN TESTNET AUTOMATION      |[/bold magenta]")
    console.print("[yellow]|      No JWT Tokens | No Cloudflare | Direct Web3 Contracts |[/yellow]")
    console.print("[bold cyan]+------------------------------------------------------------+[/bold cyan]\n")

    manager = AccountManager()
    config = manager.config
    accounts = manager.accounts

    sepolia_rpc = config.get("sepolia_rpc", "https://ethereum-sepolia-rpc.publicnode.com")
    faucet_addr = config.get("contracts", {}).get("sepolia", {}).get("faucet_manager", "0x45C75b923d48A58575e38D77ffDdF132277d7Ad9")
    usdt_addr = config.get("contracts", {}).get("sepolia", {}).get("usdt_token", "0x58869e0a2Ef41aB08D2669B0e8508A29A9DE1cE7")
    psy_addr = config.get("contracts", {}).get("sepolia", {}).get("psy_token", "0x625b5b6239074FA9B4325Bc1e5535E7dAB23459f")

    active_accounts = [a for a in accounts if a.get("private_key")]
    if not active_accounts:
        console.print("[red][!] Belum ada private key yang diisi![/red]")
        console.print("[yellow]Bisa paste private key di 'keys.txt' (1 key per baris) atau di 'config/accounts.json'.[/yellow]")
        return

    table = Table(title="Hasil On-Chain Testnet", show_header=True, header_style="bold magenta")
    table.add_column("Akun", style="bold")
    table.add_column("Address", style="cyan")
    table.add_column("Sepolia ETH", justify="right")
    table.add_column("Klaim pUSDT", style="yellow")
    table.add_column("Klaim test PSY", style="green")

    for acc in active_accounts:
        name = acc.get("name", "Account")
        pk = acc.get("private_key")
        console.print(f"[*] Memproses on-chain testnet untuk [bold cyan]{name}[/bold cyan]...")

        try:
            client = SepoliaTestnetClient(
                private_key=pk,
                rpc_url=sepolia_rpc,
                faucet_address=faucet_addr,
                usdt_address=usdt_addr,
                psy_address=psy_addr
            )

            eth_bal = client.get_eth_balance()
            console.print(f"    Address: {client.address}")
            console.print(f"    Saldo ETH: {eth_bal:.4f} ETH")

            # 1. Klaim test pUSDT
            usdt_status = "Skipped"
            can_usdt, next_b1 = client.check_can_claim(usdt_addr)
            if can_usdt:
                console.print(f"    -> Mengklaim 10,000 pUSDT dari TokenFaucetManager...")
                res_usdt = client.claim_faucet("USDT")
                if res_usdt.get("success"):
                    usdt_status = "[bold green]10,000 pUSDT Berhasil![/bold green]"
                    console.print(f"       [green]Tx: {res_usdt.get('explorer_url')}[/green]")
                else:
                    usdt_status = f"[red]{res_usdt.get('error')}[/red]"
            else:
                usdt_status = f"[dim]Cooldown (Block {next_b1})[/dim]"

            # 2. Klaim test PSY
            psy_status = "Skipped"
            can_psy, next_b2 = client.check_can_claim(psy_addr)
            if can_psy:
                console.print(f"    -> Mengklaim test PSY dari TokenFaucetManager...")
                res_psy = client.claim_faucet("PSY")
                if res_psy.get("success"):
                    psy_status = "[bold green]PSY Berhasil![/bold green]"
                    console.print(f"       [green]Tx: {res_psy.get('explorer_url')}[/green]")
                else:
                    psy_status = f"[red]{res_psy.get('error')}[/red]"
            else:
                psy_status = f"[dim]Cooldown (Block {next_b2})[/dim]"

            table.add_row(
                name,
                f"{client.address[:6]}...{client.address[-4:]}",
                f"{eth_bal:.4f} ETH",
                usdt_status,
                psy_status
            )

        except Exception as e:
            console.print(f"[red][!] Error: {e}[/red]")
            table.add_row(name, "-", "-", f"[red]{e}[/red]", "-")

        time.sleep(2)

    console.print("\n")
    console.print(table)
    console.print("\n[bold green]✓ Selesai! Interaksi on-chain smart contract testnet telah dieksekusi.[/bold green]")


if __name__ == "__main__":
    run_pure_onchain_testnet()
