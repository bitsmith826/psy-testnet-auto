"""
Quick Daily Runner for Psy Protocol
Jalankan satu perintah ini untuk daily check-in dan tugas-tugas yang bisa dikerjakan:
    python daily.py
"""

import sys
import os

# Ensure UTF-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from modules.account_manager import AccountManager
from modules.tasks_runner import TaskRunner

console = Console(legacy_windows=False)

def run_daily():
    console.print("[bold cyan]============================================================[/bold cyan]")
    console.print("[bold magenta]       PSY PROTOCOL — DAILY TASKS & CHECK-IN RUNNER         [/bold magenta]")
    console.print("[yellow]       Official Portal: https://psy.xyz/psychonaut          [/yellow]")
    console.print("[bold cyan]============================================================[/bold cyan]\n")

    manager = AccountManager()
    accounts = manager.accounts

    if not accounts:
        console.print("[bold red][!] Tidak ada akun di config/accounts.json![/bold red]")
        console.print("[yellow]Silakan tambahkan akun Anda ke config/accounts.json terlebih dahulu.[/yellow]")
        return

    # Check if any account has token
    for acc in accounts:
        if not acc.get("jwt_token") and acc.get("private_key"):
            console.print(f"[yellow][*] Akun '{acc.get('name')}' belum memiliki JWT Token.[/yellow]")
            console.print("[cyan]Membuka Browser Assistant untuk login & ambil token otomatis...[/cyan]")
            manager.run_account_login_assistant(acc.get("id"))

    # Now run tasks for all accounts
    console.print("\n[bold green]>> Memulai eksekusi Daily Check-in & Tugas yang tersedia...[/bold green]")
    results = manager.run_all_accounts()

    # Display clean result table
    console.print("\n[bold cyan]HASIL DAILY TASK:[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Akun", style="bold")
    table.add_column("Username")
    table.add_column("Pangkat/Rank", style="cyan")
    table.add_column("Total Psy Points", justify="right", style="green")
    table.add_column("Daily Check-in")
    table.add_column("Tugas Dikerjakan", style="yellow")

    for r in results:
        stats = r.get("stats", {})
        actions = r.get("actions", [])
        
        # Check-in action status
        checkin_status = "[dim]Skipped[/dim]"
        completed_tasks = []
        for a in actions:
            if "check-in" in a.lower():
                checkin_status = "[bold green]Berhasil[/bold green]" if "completed" in a.lower() else f"[yellow]{a}[/yellow]"
            else:
                completed_tasks.append(a)

        tasks_summary = ", ".join(completed_tasks) if completed_tasks else "[dim]Tidak ada tugas baru[/dim]"

        table.add_row(
            r.get("account", "-"),
            stats.get("username", "-"),
            stats.get("rank", "-"),
            str(stats.get("total_score", 0)),
            checkin_status,
            tasks_summary
        )

    console.print(table)
    console.print("\n[bold green]Selesai! Semua task harian yang bisa dikerjakan telah diproses.[/bold green]")


if __name__ == "__main__":
    run_daily()
