import re
import sys
from datetime import datetime
from colorama import init, Fore, Style
from typing import List, Dict, Any

# Ensure stdout handles UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

init(autoreset=True)

ANSI_REGEX = re.compile(r'\x1b\[[0-9;]*m')


class Display:
    BOX_WIDTH = 88

    @staticmethod
    def strip_ansi(text: str) -> str:
        return ANSI_REGEX.sub('', text)

    @classmethod
    def vlen(cls, text: str) -> int:
        return len(cls.strip_ansi(text))

    @classmethod
    def pad_box(cls, content: str, width: int = None, border_col: str = Fore.CYAN) -> str:
        w = width or cls.BOX_WIDTH
        pad = (w - 2) - cls.vlen(content)
        return f"{border_col}|{Style.RESET_ALL}{content}{' ' * max(0, pad)}{border_col}|{Style.RESET_ALL}"

    @classmethod
    def pad_cell(cls, text: str, width: int, align: str = "<") -> str:
        raw_len = cls.vlen(text)
        pad = width - raw_len
        if pad <= 0:
            return text
        if align == "<":
            return text + (" " * pad)
        elif align == ">":
            return (" " * pad) + text
        else:
            left_pad = pad // 2
            right_pad = pad - left_pad
            return (" " * left_pad) + text + (" " * right_pad)

    @classmethod
    def banner(cls):
        w = cls.BOX_WIDTH
        top_eq = Fore.CYAN + "+" + "=" * (w - 2) + "+" + Style.RESET_ALL

        art_lines = [
            "  _____   _______     __  _____  _____   ____ _______ ____   _____ ____  _      ",
            " |  __ \\ / ____\\ \\   / / |  __ \\|  __ \\ / __ \\__   __/ __ \\ / ____/ __ \\| |     ",
            " | |__) | (___  \\ \\_/ /  | |__) | |__) | |  | | | | | |  | | |   | |  | | |     ",
            " |  ___/ \\___ \\  \\   /   |  ___/|  _  /| |  | | | | | |  | | |   | |  | | |     ",
            " | |     ____) |  | |    | |    | | \\ \\| |__| | | | | |__| | |___| |__| | |____ ",
            " |_|    |_____/   |_|    |_|    |_|  \\_\\\\____/  |_|  \\____/ \\_____\\____/|______|",
        ]

        print("\n" + top_eq)
        inner = w - 2
        for line in art_lines:
            pad_left = (inner - len(line)) // 2
            centered = " " * pad_left + line
            print(cls.pad_box(f"{Fore.LIGHTCYAN_EX}{Style.BRIGHT}{centered}", w))

        print(cls.pad_box(" ", w))
        tagline = ">> PSY PROTOCOL (PSYCHONAUT) ALL-IN-ONE AUTOMATION BOT <<"
        p_tag = (inner - len(tagline)) // 2
        print(cls.pad_box(f"{' ' * p_tag}{Fore.YELLOW}{Style.BRIGHT}{tagline}{Style.RESET_ALL}", w))

        feats = "* Sepolia Faucet  * Stealth Camoufox  * Daily Check-In  * Multi-Account *"
        p_feat = (inner - len(feats)) // 2
        print(cls.pad_box(f"{' ' * p_feat}{Fore.LIGHTBLACK_EX}{feats}{Style.RESET_ALL}", w))
        print(top_eq)

    @classmethod
    def config_box(cls, total_accounts: int, ref_code: str, rpc_url: str, loop_mode: bool):
        w = cls.BOX_WIDTH
        loop_text = "Aktif (Loop 24 Jam)" if loop_mode else "Single Run (Sekali Eksekusi)"
        ref_disp = ref_code if ref_code else "None (Disabled)"
        title = " [ KONFIGURASI SISTEM ] "
        dash_r = w - 2 - len(title) - 2
        top_dash = Fore.CYAN + "+" + "-" * (w - 2) + "+" + Style.RESET_ALL

        print(f"\n{Fore.CYAN}+--{Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}{Fore.CYAN}{'-' * max(2, dash_r)}+{Style.RESET_ALL}")
        print(cls.pad_box(f"  {Fore.WHITE}Total Dompet EVM : {Fore.YELLOW}{Style.BRIGHT}{total_accounts} Akun Terdaftar{Style.RESET_ALL}{' '*6}{Fore.WHITE}Target Referral : {Fore.GREEN}{Style.BRIGHT}{ref_disp}", w))
        print(cls.pad_box(f"  {Fore.WHITE}Sepolia Testnet  : {Fore.CYAN}{rpc_url[:35]}...{Style.RESET_ALL}", w))
        print(cls.pad_box(f"  {Fore.WHITE}Engine Browser   : {Fore.LIGHTMAGENTA_EX}Camoufox (Stealth Firefox Anti-Detect Turnstile)", w))
        print(cls.pad_box(f"  {Fore.WHITE}Mode Eksekusi    : {Fore.MAGENTA}{loop_text}", w))
        print(top_dash)

    @classmethod
    def auth_box(cls, total_needed: int):
        w = cls.BOX_WIDTH
        title = " [ OTENTIKASI STEALTH CAMOUFOX ] "
        dash_r = w - 2 - len(title) - 2
        print(f"\n{Fore.YELLOW}+--{Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}{Fore.YELLOW}{'-' * max(2, dash_r)}+{Style.RESET_ALL}")
        print(cls.pad_box(f"  {Fore.WHITE}Status Mesin  : {Fore.CYAN}Menjalankan engine Camoufox headless...", w, Fore.YELLOW))
        print(cls.pad_box(f"  {Fore.WHITE}Target Antrean: {Fore.YELLOW}{total_needed} Akun{Fore.WHITE} butuh token JWT baru (Turnstile Auto-Bypass)", w, Fore.YELLOW))
        print(Fore.YELLOW + "+" + "-" * (w - 2) + "+" + Style.RESET_ALL)

    @classmethod
    def account_card(cls, idx: int, total: int, name: str, address: str, username: str, rank: str, eth_bal: float, pusdt_bal: float, faucet_msg: str, checkin_msg: str, xp_score: int):
        w = cls.BOX_WIDTH
        short_addr = f"{address[:6]}...{address[-4:]}" if len(address) > 12 else address
        is_faucet_ok = "sukses" in faucet_msg.lower() or "+10k" in faucet_msg.lower()
        tag = f"{Fore.GREEN}[OK]{Style.RESET_ALL}" if is_faucet_ok else f"{Fore.YELLOW}[COOLDOWN]{Style.RESET_ALL}"
        
        user_disp = username if username and username != "-" else "psychonaut"
        rank_disp = rank if rank and rank != "-" else "Cadet"

        hdr = f" [AKUN {idx:02d}/{total:02d}] {name} ({short_addr}) {tag} "
        dash_r = w - 2 - len(Display.strip_ansi(hdr)) - 2

        print(f"\n{Fore.CYAN}+--{Fore.WHITE}{Style.BRIGHT}{hdr}{Fore.CYAN}{'-' * max(2, dash_r)}+{Style.RESET_ALL}")
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}EVM Address     : {Fore.LIGHTWHITE_EX}{address}", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Psychonaut User : {Fore.YELLOW}{Style.BRIGHT}{user_disp}{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}(Rank: {Fore.LIGHTMAGENTA_EX}{rank_disp}{Fore.LIGHTBLACK_EX})", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Sepolia Gas ETH : {Fore.CYAN}{eth_bal:.4f} ETH", w))

        color_faucet = Fore.GREEN if is_faucet_ok else Fore.YELLOW
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Sepolia Faucet  : {color_faucet}{faucet_msg}", w))

        color_check = Fore.GREEN if "sukses" in checkin_msg.lower() else (Fore.CYAN if "sudah" in checkin_msg.lower() else Fore.YELLOW)
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Web Daily Check : {color_check}{checkin_msg}", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[+] {Fore.WHITE}Saldo pUSDT     : {Fore.YELLOW}{Style.BRIGHT}{pusdt_bal:,.0f} pUSDT", w))
        print(cls.pad_box(f"  {Fore.LIGHTBLACK_EX}[=] {Fore.WHITE}Total Skor XP   : {Fore.GREEN}{Style.BRIGHT}{xp_score:,} XP", w))
        print(Fore.CYAN + "+" + "-" * (w - 2) + "+" + Style.RESET_ALL)

    @classmethod
    def summary_table(cls, rows: List[Dict[str, Any]]):
        cols = [
            {"name": "No",          "key": "no",       "width": 3,  "align": "^"},
            {"name": "Address",     "key": "addr",     "width": 13, "align": "<"},
            {"name": "Username",    "key": "user",     "width": 15, "align": "<"},
            {"name": "Faucet",      "key": "faucet",   "width": 12, "align": "^"},
            {"name": "Check-In",    "key": "check",    "width": 11, "align": "^"},
            {"name": "Saldo pUSDT", "key": "pusdt",    "width": 14, "align": ">"},
            {"name": "Skor XP",     "key": "xp",       "width": 10, "align": ">"},
        ]

        def get_sep(char="-"):
            parts = ["+" + char * (c["width"] + 2) for c in cols]
            return Fore.CYAN + "".join(parts) + "+" + Style.RESET_ALL

        print("\n" + get_sep("-"))
        hdr_cells = [cls.pad_cell(f"{Fore.WHITE}{Style.BRIGHT}{c['name']}{Style.RESET_ALL}", c["width"], "^") for c in cols]
        print(Fore.CYAN + "| " + (" " + Fore.CYAN + "| " + Style.RESET_ALL).join(hdr_cells) + " " + Fore.CYAN + "|")
        print(get_sep("="))

        total_pusdt = 0
        total_xp = 0
        success_faucet = 0
        success_checkin = 0

        for idx, r in enumerate(rows, 1):
            no = f"{idx:02d}"
            raw_addr = r.get("address", "")
            addr = f"{raw_addr[:5]}...{raw_addr[-4:]}" if len(raw_addr) > 12 else raw_addr

            user = str(r.get("username", "-"))[:15]
            if user == "-" or not user or user == "Belum Diatur":
                user = f"psychonaut_{idx:02d}"

            # Faucet
            f_raw = str(r.get("faucet_usdt_status", ""))
            if "sukses" in f_raw.lower() or "+10k" in f_raw.lower():
                success_faucet += 1
                faucet_disp = f"{Fore.GREEN}+10k pUSDT{Style.RESET_ALL}"
            elif "cooldown" in f_raw.lower():
                faucet_disp = f"{Fore.YELLOW}Cooldown{Style.RESET_ALL}"
            else:
                faucet_disp = f"{Fore.RED}Gagal{Style.RESET_ALL}"

            # Checkin
            c_raw = str(r.get("checkin_status", ""))
            if "sukses" in c_raw.lower():
                success_checkin += 1
                check_disp = f"{Fore.GREEN}Sukses (+XP){Style.RESET_ALL}"
            elif "sudah" in c_raw.lower():
                success_checkin += 1
                check_disp = f"{Fore.CYAN}Sudah Check{Style.RESET_ALL}"
            else:
                check_disp = f"{Fore.YELLOW}Pending{Style.RESET_ALL}"

            # Saldo pUSDT
            pusdt_val = r.get("pusdt_balance", 0.0)
            total_pusdt += pusdt_val
            pusdt_disp = f"{Fore.YELLOW}{Style.BRIGHT}{pusdt_val:,.0f} pUSDT{Style.RESET_ALL}"

            # Skor XP
            xp_val = r.get("total_score", 0)
            total_xp += xp_val
            xp_disp = f"{Fore.GREEN}{Style.BRIGHT}{xp_val:,} XP{Style.RESET_ALL}"

            row_data = {
                "no": no,
                "addr": addr,
                "user": user,
                "faucet": faucet_disp,
                "check": check_disp,
                "pusdt": pusdt_disp,
                "xp": xp_disp
            }

            cells = [cls.pad_cell(str(row_data[c["key"]]), c["width"], c["align"]) for c in cols]
            print(Fore.CYAN + "| " + (" " + Fore.CYAN + "| " + Style.RESET_ALL).join(cells) + " " + Fore.CYAN + "|")

        # Footer separator with exact character math matching columns 0..3
        merged_w = sum(c["width"] + 2 for c in cols[:4]) + len(cols[:4]) - 1
        footer_parts = ["+" + "-" * merged_w] + ["+" + "-" * (c["width"] + 2) for c in cols[4:]]
        footer_sep = Fore.CYAN + "".join(footer_parts) + "+" + Style.RESET_ALL

        print(footer_sep)
        cell_left = cls.pad_cell(f" {Fore.WHITE}{Style.BRIGHT}TOTAL: {len(rows)}/{len(rows)} AKUN TERPROSES", merged_w - 2, "<")
        cell_check = cls.pad_cell(f"{Fore.CYAN}{success_checkin} Aktif", cols[4]["width"], "^")
        cell_pusdt = cls.pad_cell(f"{Fore.YELLOW}{Style.BRIGHT}{total_pusdt:,.0f} pUSDT{Style.RESET_ALL}", cols[5]["width"], ">")
        cell_xp = cls.pad_cell(f"{Fore.GREEN}{Style.BRIGHT}{total_xp:,} XP{Style.RESET_ALL}", cols[6]["width"], ">")

        print(Fore.CYAN + "| " + cell_left + " " + Fore.CYAN + "| " + cell_check + " " + Fore.CYAN + "| " + cell_pusdt + " " + Fore.CYAN + "| " + cell_xp + " " + Fore.CYAN + "|")
        print(footer_sep)

    @classmethod
    def finish_box(cls, total_accounts: int, total_pusdt: float, total_xp: int, success_claims: int):
        w = cls.BOX_WIDTH
        title = " [ STATUS PENYELESAIAN EKSEKUSI ] "
        dash_r = w - 2 - len(title) - 2
        top_eq = Fore.GREEN + "+" + "=" * (w - 2) + "+" + Style.RESET_ALL

        print(f"\n{Fore.GREEN}+=={Fore.WHITE}{Style.BRIGHT}{title}{Style.RESET_ALL}{Fore.GREEN}{'=' * max(2, dash_r)}+{Style.RESET_ALL}")
        print(cls.pad_box(f"  {Fore.WHITE}Status Eksekusi      : {Fore.GREEN}{Style.BRIGHT}{total_accounts}/{total_accounts} Akun Terproses Sempurna", w, Fore.GREEN))
        print(cls.pad_box(f"  {Fore.WHITE}Klaim Faucet Baru    : {Fore.GREEN}{success_claims} Akun Sukses Klaim Token (+10k pUSDT)", w, Fore.GREEN))
        print(cls.pad_box(f"  {Fore.WHITE}Total Saldo pUSDT    : {Fore.YELLOW}{Style.BRIGHT}{total_pusdt:,.0f} pUSDT di seluruh dompet", w, Fore.GREEN))
        print(cls.pad_box(f"  {Fore.WHITE}Total Akumulasi XP   : {Fore.GREEN}{Style.BRIGHT}{total_xp:,} XP Terkumpul", w, Fore.GREEN))
        print(cls.pad_box(f"  {Fore.WHITE}Waktu Penyelesaian   : {Fore.CYAN}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} WIB", w, Fore.GREEN))
        print(top_eq + "\n")
