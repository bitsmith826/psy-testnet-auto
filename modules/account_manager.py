"""
Account Manager for Multi-Account Psy Protocol Testnet Automation
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from modules.tasks_runner import TaskRunner
from core.browser_login import run_browser_login


class AccountManager:
    def __init__(self, config_path: str = "config/config.json", accounts_path: str = "config/accounts.json", keys_path: str = "keys.txt"):
        self.config_path = config_path
        self.accounts_path = accounts_path
        self.keys_path = keys_path
        self.config = self._load_json(self.config_path, default={})
        self.accounts = self._load_json(self.accounts_path, default=[])

        # Auto-sync from keys.txt if it exists
        self._sync_from_keys_txt()

    def _sync_from_keys_txt(self) -> None:
        if not os.path.exists(self.keys_path):
            return

        try:
            with open(self.keys_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

            if not lines:
                return

            existing_pks = {a.get("private_key", "").lower() for a in self.accounts if a.get("private_key")}
            updated = False

            # If accounts only has a dummy empty account, replace it
            if len(self.accounts) == 1 and not self.accounts[0].get("private_key") and not self.accounts[0].get("jwt_token"):
                self.accounts = []

            for idx, raw_key in enumerate(lines, start=1):
                pk = raw_key if raw_key.startswith("0x") else f"0x{raw_key}"
                if pk.lower() not in existing_pks:
                    new_id = max([a.get("id", 0) for a in self.accounts], default=0) + 1
                    self.accounts.append({
                        "id": new_id,
                        "name": f"Account-{new_id}",
                        "private_key": pk,
                        "jwt_token": "",
                        "proxy": ""
                    })
                    existing_pks.add(pk.lower())
                    updated = True

            if updated:
                self.save_accounts()
        except Exception:
            pass

    def _load_json(self, path: str, default: Any) -> Any:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default

    def save_accounts(self) -> None:
        with open(self.accounts_path, "w", encoding="utf-8") as f:
            json.dump(self.accounts, f, indent=2)

    def add_account(self, name: str, private_key: str = "", jwt_token: str = "", proxy: str = "") -> Dict[str, Any]:
        new_id = max([a.get("id", 0) for a in self.accounts], default=0) + 1
        acc = {
            "id": new_id,
            "name": name or f"Account-{new_id}",
            "private_key": private_key.strip(),
            "jwt_token": jwt_token.strip(),
            "proxy": proxy.strip()
        }
        self.accounts.append(acc)
        self.save_accounts()
        return acc

    def update_jwt_token(self, account_id: int, jwt_token: str) -> bool:
        for acc in self.accounts:
            if acc.get("id") == account_id:
                acc["jwt_token"] = jwt_token.strip()
                self.save_accounts()
                return True
        return False

    def run_account_login_assistant(self, account_id: int) -> bool:
        """Launch browser helper to login and auto-update JWT token for an account."""
        target_acc = None
        for acc in self.accounts:
            if acc.get("id") == account_id:
                target_acc = acc
                break

        if not target_acc:
            print(f"[!] Account ID {account_id} not found.")
            return False

        pk = target_acc.get("private_key")
        portal_url = self.config.get("portal_url", "https://psy.xyz/psychonaut")

        print(f"[*] Starting Browser Login Assistant for {target_acc['name']}...")
        token = run_browser_login(private_key=pk, portal_url=portal_url)
        if token:
            target_acc["jwt_token"] = token
            self.save_accounts()
            print(f"[OK] Token captured and saved for {target_acc['name']}!")
            return True
        else:
            print(f"[x] Could not capture token for {target_acc['name']}.")
            return False

    def ensure_all_authenticated(self) -> None:
        """Ensure all accounts have valid JWT tokens via Camoufox headless engine."""
        from core.camoufox_login import ensure_accounts_authenticated
        ref_code = self.config.get("invite_code", "")
        self.accounts = ensure_accounts_authenticated(
            self.accounts,
            accounts_path=self.accounts_path,
            invite_code=ref_code
        )

    def run_all_accounts(self) -> List[Dict[str, Any]]:
        """Run tasks for all configured accounts."""
        self.ensure_all_authenticated()
        results = []
        delay = self.config.get("delay_between_accounts", 5)

        for idx, acc in enumerate(self.accounts):
            runner = TaskRunner(account_config=acc, global_config=self.config)
            res = runner.run_all()
            results.append(res)

            if idx < len(self.accounts) - 1:
                print(f"\n[Cooldown] Waiting {delay} seconds before next account...")
                time.sleep(delay)

        return results
