"""
Automated Task Runner for Psy Protocol
Handles On-Chain Testnet Interactions & Web Psychonaut Campaign Quests
"""

import time
import random
import string
from typing import Dict, Any, Optional
from core.api import PsyAPIClient
from core.onchain import SepoliaTestnetClient


class TaskRunner:
    def __init__(self, account_config: Dict[str, Any], global_config: Dict[str, Any]):
        self.account_config = account_config
        self.global_config = global_config
        self.name = account_config.get("name", f"Account-{account_config.get('id', 1)}")
        self.jwt_token = account_config.get("jwt_token")
        self.private_key = account_config.get("private_key")
        self.proxy = account_config.get("proxy")

        self.api = PsyAPIClient(
            jwt_token=self.jwt_token,
            proxy=self.proxy,
            base_url=self.global_config.get("api_base_url", "https://member-api.psy.xyz")
        )

        self.onchain_client = None
        if self.private_key:
            try:
                self.onchain_client = SepoliaTestnetClient(
                    private_key=self.private_key,
                    rpc_url=self.global_config.get("sepolia_rpc", "https://ethereum-sepolia-rpc.publicnode.com"),
                    faucet_address=self.global_config.get("contracts", {}).get("sepolia", {}).get("faucet_manager", "0x45C75b923d48A58575e38D77ffDdF132277d7Ad9"),
                    usdt_address=self.global_config.get("contracts", {}).get("sepolia", {}).get("usdt_token", "0x58869e0a2Ef41aB08D2669B0e8508A29A9DE1cE7"),
                    psy_address=self.global_config.get("contracts", {}).get("sepolia", {}).get("psy_token", "0x625b5b6239074FA9B4325Bc1e5535E7dAB23459f")
                )
            except Exception:
                pass

    def run_all(self, verbose: bool = False) -> Dict[str, Any]:
        """Execute full automated pipeline for the account (On-chain + Web tasks)."""
        results = {
            "account": self.name,
            "address": self.onchain_client.address if self.onchain_client else self.account_config.get("address", "-"),
            "eth_balance": 0.0,
            "pusdt_balance": 0.0,
            "psy_balance": 0.0,
            "faucet_usdt_status": "Dilewati",
            "faucet_psy_status": "Dilewati",
            "checkin_status": "Butuh Login",
            "username": "-",
            "rank": "-",
            "total_score": 0,
            "referral_code": "-",
            "success": False,
            "actions": []
        }

        # -------------------------------------------------------------
        # STEP 1: ON-CHAIN TESTNET FAUCET & BALANCES
        # -------------------------------------------------------------
        if self.onchain_client:
            try:
                results["address"] = self.onchain_client.address
                results["eth_balance"] = self.onchain_client.get_eth_balance()
                
                # Check eligibility and claim 10,000 pUSDT
                can_claim_usdt, _ = self.onchain_client.check_can_claim(self.onchain_client.usdt_address)
                if can_claim_usdt:
                    res_usdt = self.onchain_client.claim_faucet("USDT")
                    if res_usdt.get("success"):
                        results["faucet_usdt_status"] = "Sukses (+10k)"
                        results["actions"].append("Klaim 10k pUSDT")
                    else:
                        results["faucet_usdt_status"] = res_usdt.get("error", "Error")
                else:
                    results["faucet_usdt_status"] = "Cooldown"

                # Check eligibility and claim test PSY
                can_claim_psy, _ = self.onchain_client.check_can_claim(self.onchain_client.psy_address)
                if can_claim_psy:
                    res_psy = self.onchain_client.claim_faucet("PSY")
                    if res_psy.get("success"):
                        results["faucet_psy_status"] = "Sukses"
                        results["actions"].append("Klaim PSY")
                    else:
                        results["faucet_psy_status"] = res_psy.get("error", "Error")
                else:
                    results["faucet_psy_status"] = "Cooldown"

                # Get final balances
                tokens = self.onchain_client.get_token_balances()
                results["pusdt_balance"] = tokens.get("pUSDT", 0.0)
                results["psy_balance"] = tokens.get("PSY", 0.0)
                results["success"] = True

            except Exception as e:
                results["faucet_usdt_status"] = f"Error: {e}"

        # -------------------------------------------------------------
        # STEP 2: WEB PSYCHONAUT CAMPAIGN TASKS
        # -------------------------------------------------------------
        if not self.jwt_token:
            results["checkin_status"] = "Butuh Login"
            return results

        profile_res = self.api.get_user_profile()
        if not profile_res.get("success"):
            results["checkin_status"] = "Token Expired"
            return results

        profile = profile_res.get("data", {})
        results["username"] = profile.get("username") or "Belum Diatur"
        results["total_score"] = profile.get("score", 0)
        results["referral_code"] = profile.get("inviteCode", "-")
        invited_by = profile.get("invitedBy")
        level = profile.get("level", 1)
        tier_map = {1: "Cadet", 2: "Ensign", 3: "Lieutenant", 4: "Captain", 5: "Visionary"}
        results["rank"] = tier_map.get(level, str(level))

        # Auto-bind Referral Code (if specified in config)
        target_invite = self.global_config.get("invite_code", "")
        if not invited_by and self.global_config.get("auto_bind_invite", True) and target_invite:
            bind_res = self.api.bind_invite_code(target_invite)
            if bind_res.get("success"):
                results["actions"].append(f"Bind: {target_invite}")

        # Auto-set Username
        if (not results["username"] or results["username"] == "Belum Diatur") and self.global_config.get("auto_set_username", True):
            rand_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
            new_username = f"psychonaut_{rand_suffix}"
            set_res = self.api.set_username(new_username, is_public=True)
            if set_res.get("success"):
                results["username"] = new_username
                results["actions"].append(f"Set user: {new_username}")

        # Daily Check-in
        if self.global_config.get("auto_check_in", True):
            checkin_res = self.api.daily_check_in()
            if checkin_res.get("success"):
                results["checkin_status"] = "Sukses (+XP)"
                results["actions"].append("Daily check-in")
                # Add reward to local score
                results["total_score"] += checkin_res.get("data", {}).get("rewardScore", 10)
            else:
                err = checkin_res.get("error") or checkin_res.get("msg") or "Sudah Check-in"
                results["checkin_status"] = "Sudah Check" if "already" in str(err).lower() else str(err)[:12]

        # Social Tasks
        if self.global_config.get("auto_submit_social_tasks", True):
            delay = self.global_config.get("delay_between_tasks", 1)
            time.sleep(delay)
            self._handle_available_tasks(results, verbose=verbose)

        # Discord Quests
        if profile.get("discordUser"):
            self.api.verify_discord_membership()
            self.api.verify_discord_messages()
            self.api.verify_discord_reactions()

        results["success"] = True
        return results

    def _handle_available_tasks(self, results: Dict[str, Any], verbose: bool = False) -> None:
        """Fetch tasks from /tasks and auto-submit allowable proofs."""
        tasks_res = self.api.get_tasks(page=1, page_size=50)
        if not tasks_res.get("success"):
            return

        task_list = tasks_res.get("data", [])
        if not isinstance(task_list, list):
            task_list = []

        auto_submittable = {
            "Follow @PsyProtocol": "Followed official @PsyProtocol on X",
            "Like Posts": "Liked recent official announcements on @PsyProtocol",
            "Retweet a Post": "Retweeted official update on @PsyProtocol",
            "Reply with #PsyProtocol": "Replied to announcement with #PsyProtocol",
            "Quote tweet a Psy Protocol Post": "Quote tweeted announcement",
            "Tweet About Psy": "Posted tweet about Psy Protocol testnet and privacy architecture"
        }

        for task in task_list:
            title = task.get("title", "")
            completion = task.get("completionStatus", {})
            if completion.get("isCompleted", False):
                continue

            if title in auto_submittable and completion.get("canComplete", True):
                desc = auto_submittable[title]
                sub_res = self.api.submit_task_application(
                    task_title=title,
                    description=desc,
                    link="https://x.com/PsyProtocol"
                )
                if sub_res.get("success"):
                    results["actions"].append(f"Misi: {title}")
