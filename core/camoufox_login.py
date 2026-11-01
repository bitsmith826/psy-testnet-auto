"""
Automated Stealth Camoufox Login Engine for Psy Protocol (Psychonaut Campaign)
Bypasses Cloudflare Turnstile headlessly, signs SIWE with EVM private key,
and acquires JWT tokens for all accounts automatically.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from colorama import Fore, Style
from camoufox.sync_api import Camoufox


def is_jwt_valid(jwt_token: str, base_url: str = "https://member-api.psy.xyz") -> bool:
    """Check whether a JWT token is currently valid by calling /users/me."""
    if not jwt_token or len(jwt_token) < 20:
        return False
    try:
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
            "Origin": "https://psy.xyz",
            "Referer": "https://psy.xyz/"
        }
        r = requests.get(f"{base_url}/users/me", headers=headers, timeout=8)
        return r.status_code == 200 and r.json().get("code") == 0
    except Exception:
        return False


def solve_turnstile(page, timeout: int = 25) -> Optional[str]:
    """Inject Turnstile widget on psy.xyz and wait for Camoufox to solve it."""
    page.evaluate('''() => {
        let old = document.getElementById("cf-ts-container");
        if (old) old.remove();

        let div = document.createElement("div");
        div.id = "cf-ts-container";
        div.className = "cf-turnstile";
        div.setAttribute("data-sitekey", "0x4AAAAAAB4Dnwf7VH4TyqYB");
        div.style.cssText = "position:fixed;top:20px;left:20px;z-index:999999;width:300px;height:70px;background:white;";
        document.body.appendChild(div);

        if (window.turnstile) {
            window.turnstile.render("#cf-ts-container", {
                sitekey: "0x4AAAAAAB4Dnwf7VH4TyqYB"
            });
        } else {
            let s = document.createElement("script");
            s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
            s.async = true;
            s.defer = true;
            document.body.appendChild(s);
        }
    }''')

    for _ in range(timeout):
        tok = page.evaluate('() => document.querySelector(\'#cf-ts-container input[name="cf-turnstile-response"]\')?.value')
        if tok and len(tok) > 10:
            return tok
        time.sleep(1)
    return None


def login_single_account(page, private_key: str, invite_code: Optional[str] = None) -> Optional[str]:
    """Solve Turnstile, sign SIWE, and login to obtain JWT token."""
    account = Account.from_key(private_key)
    address = account.address

    # 1. Solve Turnstile
    tok = solve_turnstile(page)
    if not tok:
        page.reload(wait_until="domcontentloaded")
        tok = solve_turnstile(page)
        if not tok:
            return None

    # 2. Get Nonce
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
        "Origin": "https://psy.xyz",
        "Referer": "https://psy.xyz/",
        "Content-Type": "application/json"
    }
    nonce_res = requests.get(
        f"https://member-api.psy.xyz/auth/wallet/nonce?address={address}&chainType=ethereum",
        headers=headers,
        timeout=15
    )
    if nonce_res.status_code != 200:
        return None

    nonce = nonce_res.json().get("data", {}).get("nonce")
    if not nonce:
        return None

    # 3. Build SIWE message with Spruce EIP-4361 compliance (\n\n\n)
    issued_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    siwe_message = (
        f"https://psy.xyz wants you to sign in with your Ethereum account:\n"
        f"{address}\n\n\n"
        f"URI: https://psy.xyz\n"
        f"Version: 1\n"
        f"Chain ID: 1\n"
        f"Nonce: {nonce}\n"
        f"Issued At: {issued_at}"
    )

    # 4. Sign message with private key
    signable = encode_defunct(text=siwe_message)
    signed = account.sign_message(signable)
    sig_hex = signed.signature.hex()
    if not sig_hex.startswith("0x"):
        sig_hex = "0x" + sig_hex

    # 5. POST to /auth/wallet/login
    payload = {
        "signature": sig_hex,
        "message": siwe_message,
        "nonce": nonce,
        "chainType": "ethereum",
        "token": tok,
        "chainId": 1
    }
    if invite_code:
        payload["inviteCode"] = invite_code
    res = requests.post(
        "https://member-api.psy.xyz/auth/wallet/login",
        json=payload,
        headers=headers,
        timeout=20
    )
    if res.status_code == 200:
        data = res.json().get("data", {})
        return data.get("token")
    return None


def ensure_accounts_authenticated(accounts: List[Dict[str, Any]], accounts_path: str = "config/accounts.json", invite_code: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Checks all accounts. If any account lacks a valid JWT token, launches Camoufox
    to automatically log in, update, and persist accounts.
    """
    needed_login = []
    for acc in accounts:
        jwt = acc.get("jwt_token", "")
        pk = acc.get("private_key", "")
        if not pk:
            continue
        if not is_jwt_valid(jwt):
            needed_login.append(acc)

    if not needed_login:
        return accounts

    try:
        from core.display import Display
        Display.auth_box(len(needed_login))
    except Exception:
        print(f"\n{Fore.CYAN}[*] {Fore.WHITE}Menemukan {Fore.YELLOW}{len(needed_login)}{Fore.WHITE} akun butuh login Turnstile...")

    try:
        with Camoufox(headless=True) as browser:
            page = browser.new_page()
            page.goto("https://psy.xyz", wait_until="domcontentloaded", timeout=45000)

            for i, acc in enumerate(needed_login, start=1):
                name = acc.get("name", f"Account-{acc.get('id')}")
                pk = acc.get("private_key")
                addr = acc.get("address")
                if not addr and pk:
                    addr = Account.from_key(pk).address
                    acc["address"] = addr

                short_addr = f"{addr[:6]}...{addr[-4:]}"
                print(f"    {Fore.CYAN}[{i}/{len(needed_login)}] {Fore.WHITE}Logging in {Fore.YELLOW}{name}{Fore.WHITE} ({short_addr}) via Camoufox...{Style.RESET_ALL}", end="", flush=True)

                jwt = login_single_account(page, pk, invite_code=invite_code)
                if jwt:
                    acc["jwt_token"] = jwt
                    print(f" {Fore.GREEN}[SUKSES] Token JWT didapatkan!{Style.RESET_ALL}")
                    # Simpan progres langsung ke disk agar aman
                    with open(accounts_path, "w", encoding="utf-8") as f:
                        json.dump(accounts, f, indent=2)
                else:
                    print(f" {Fore.RED}[GAGAL] Tidak dapat token.{Style.RESET_ALL}")

                # Reload for next account solve if there are more
                if i < len(needed_login):
                    page.reload(wait_until="domcontentloaded")
                    time.sleep(1)

        # Save updated accounts to file
        with open(accounts_path, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=2)
        print(f"{Fore.GREEN}[OK] Berhasil memperbarui token untuk semua akun di {accounts_path}!{Style.RESET_ALL}\n")

    except Exception as e:
        print(f"{Fore.RED}[!] Error pada sesi Camoufox login: {e}{Style.RESET_ALL}")

    return accounts
