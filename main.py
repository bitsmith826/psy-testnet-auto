"""
====================================================================
PSY PROTOCOL TESTNET & PSYCHONAUT ALL-IN-ONE AUTOMATION
Direct Execution Bot: 100% On-Chain Testnet + Web Psychonaut Quests
====================================================================
"""

import sys
import os
import time
import json
import random
from typing import List, Dict, Any

from core.display import Display
from modules.account_manager import AccountManager
from modules.tasks_runner import TaskRunner


def run_direct_execution(manager: AccountManager):
    config = manager.config
    accounts = manager.accounts

    if not accounts:
        print("[!] Tidak ada akun yang ditemukan di keys.txt atau config/accounts.json.")
        return

    invite_code = config.get("invite_code", "")
    rpc_url = config.get("sepolia_rpc", "https://ethereum-sepolia-rpc.publicnode.com")
    loop_mode = config.get("loop_mode", False) or ("--loop" in sys.argv)
    delay_between_accs = config.get("delay_between_accounts", 4)

    Display.config_box(len(accounts), invite_code, rpc_url, loop_mode)

    # Otomatis pastikan semua akun terotentikasi via Camoufox stealth engine (Turnstile auto-bypass)
    manager.ensure_all_authenticated()
    accounts = manager.accounts

    results = []
    total = len(accounts)

    for idx, acc in enumerate(accounts, 1):
        name = acc.get("name", f"Akun-{idx}")
        runner = TaskRunner(account_config=acc, global_config=config)
        res = runner.run_all()
        results.append(res)

        # Print precision account card
        Display.account_card(
            idx=idx,
            total=total,
            name=name,
            address=res.get("address", "-"),
            username=res.get("username", "-"),
            rank=res.get("rank", "-"),
            eth_bal=res.get("eth_balance", 0.0),
            pusdt_bal=res.get("pusdt_balance", 0.0),
            faucet_msg=res.get("faucet_usdt_status", "-"),
            checkin_msg=res.get("checkin_status", "-"),
            xp_score=res.get("total_score", 0)
        )

        if idx < total:
            delay = delay_between_accs + random.uniform(1.0, 2.5)
            time.sleep(delay)

    # Print precision summary table & finish card
    Display.summary_table(results)

    success_claims = sum(1 for r in results if "sukses" in str(r.get("faucet_usdt_status", "")).lower() or "+10k" in str(r.get("faucet_usdt_status", "")).lower())
    total_pusdt = sum(r.get("pusdt_balance", 0.0) for r in results)
    total_xp = sum(r.get("total_score", 0) for r in results)
    Display.finish_box(total_accounts=len(accounts), total_pusdt=total_pusdt, total_xp=total_xp, success_claims=success_claims)


def main():
    Display.banner()
    manager = AccountManager()

    # CLI option: Browser Login Assistant
    if "--login" in sys.argv:
        acc_id = 1
        for arg in sys.argv:
            if arg.isdigit():
                acc_id = int(arg)
        print(f"Membuka Browser Assistant untuk Akun ID {acc_id}...")
        manager.run_account_login_assistant(acc_id)
        return

    # CLI option: Interactive Menu (hanya jika diminta eksplisit dengan --menu)
    if "--menu" in sys.argv:
        print("\nMode Menu:")
        print("1. Jalankan Semua Task (Default)")
        print("2. Browser Login Assistant")
        choice = input("Pilih (1/2): ").strip()
        if choice == "2":
            acc_id = int(input("Masukkan Akun ID: ").strip() or "1")
            manager.run_account_login_assistant(acc_id)
            return
        else:
            run_direct_execution(manager)
            return

    # DEFAULT BEHAVIOR: LANGSUNG KERJAKAN SEMUA SECARA PRESISI
    loop_mode = manager.config.get("loop_mode", False) or ("--loop" in sys.argv)
    interval_hours = manager.config.get("loop_interval_hours", 24)

    if loop_mode:
        print(f"\nMode Loop Aktif! Bot akan berjalan otomatis setiap {interval_hours} jam.")
        while True:
            try:
                run_direct_execution(manager)
            except Exception as e:
                print(f"Error saat iterasi loop: {e}")

            sleep_sec = interval_hours * 3600
            print(f"\nMenunggu siklus harian berikutnya dalam {interval_hours} jam ({sleep_sec}s)...")
            time.sleep(sleep_sec)
    else:
        run_direct_execution(manager)


if __name__ == "__main__":
    main()
