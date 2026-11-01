"""
API Client for Psy Protocol Member Backend (https://member-api.psy.xyz)
"""

import json
from typing import Any, Dict, List, Optional
import requests


class PsyAPIClient:
    def __init__(self, jwt_token: Optional[str] = None, proxy: Optional[str] = None, base_url: str = "https://member-api.psy.xyz"):
        self.base_url = base_url.rstrip("/")
        self.jwt_token = jwt_token
        self.proxy = proxy
        self.session = requests.Session()

        if self.proxy:
            self.session.proxies.update({
                "http": self.proxy,
                "https": self.proxy
            })

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
            "Origin": "https://psy.xyz",
            "Referer": "https://psy.xyz/",
            "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        })

        if self.jwt_token:
            self.set_jwt_token(self.jwt_token)

    def set_jwt_token(self, token: str) -> None:
        self.jwt_token = token
        self.session.headers["Authorization"] = f"Bearer {token}"

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        timeout = kwargs.pop("timeout", 20)
        try:
            resp = self.session.request(method, url, timeout=timeout, **kwargs)
            try:
                data = resp.json()
            except Exception:
                resp.raise_for_status()
                return {"code": resp.status_code, "data": resp.text, "msg": "raw"}

            if resp.status_code >= 400:
                err_msg = data.get("msg") or data.get("message") or f"HTTP {resp.status_code}"
                return {"success": False, "status": resp.status_code, "error": err_msg, "raw": data}

            return {"success": True, "status": resp.status_code, "data": data.get("data", data), "msg": data.get("msg", "")}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    # --- Authentication Endpoints ---

    def get_nonce(self, address: str, chain_type: str = "ethereum") -> Dict[str, Any]:
        """Fetch nonce for wallet signature."""
        return self._request("GET", "/auth/wallet/nonce", params={"address": address, "chainType": chain_type})

    def wallet_login(
        self,
        signature: str,
        message: str,
        nonce: str,
        token: str,
        chain_type: str = "ethereum",
        chain_id: int = 1,
        invite_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate with EVM signature & Cloudflare Turnstile token.
        Returns JWT token on success.
        """
        payload = {
            "signature": signature,
            "message": message,
            "nonce": nonce,
            "chainType": chain_type,
            "chainId": chain_id,
            "token": token
        }
        if invite_code:
            payload["inviteCode"] = invite_code
        res = self._request("POST", "/auth/wallet/login", json=payload)
        if res.get("success") and isinstance(res.get("data"), dict) and res["data"].get("token"):
            self.set_jwt_token(res["data"]["token"])
        return res

    # --- User Profile Endpoints ---

    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user stats, score, ranking, inviteCode, and connected accounts."""
        return self._request("GET", "/users/me")

    def bind_invite_code(self, invite_code: str) -> Dict[str, Any]:
        """Bind referral code to account."""
        return self._request("PUT", "/users/me/invite-code", json={"inviteCode": invite_code})

    def check_username_available(self, username: str) -> Dict[str, Any]:
        """Check if username is available."""
        return self._request("GET", "/users/usernames/availability", params={"username": username})

    def set_username(self, username: str, is_public: bool = True) -> Dict[str, Any]:
        """Set user display handle."""
        return self._request("PUT", "/users/me/username", json={"username": username, "isUsernamePublic": is_public})

    # --- Tasks Endpoints ---

    def get_tasks(self, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        """Fetch list of all campaign missions and tasks."""
        return self._request("GET", "/tasks", params={"page": page, "pageSize": page_size})

    def daily_check_in(self) -> Dict[str, Any]:
        """Perform daily login check-in to gain streak points."""
        return self._request("POST", "/tasks/check-in")

    def submit_task_application(self, task_title: str, description: str, link: Optional[str] = None) -> Dict[str, Any]:
        """Submit a mission proof (e.g. tweet link, retweet proof, or social submission)."""
        payload = {
            "data": {
                "taskTitle": task_title,
                "description": description
            }
        }
        if link:
            payload["data"]["link"] = link
        return self._request("POST", "/tasks/applications", json=payload)

    def get_task_applications(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get history and status of submitted tasks."""
        return self._request("GET", "/tasks/applications", params={"page": page, "pageSize": page_size})

    # --- Discord Task Verification ---

    def verify_discord_membership(self) -> Dict[str, Any]:
        """Verify membership in official Psy Discord server."""
        return self._request("POST", "/tasks/discord/membership/verify")

    def verify_discord_messages(self) -> Dict[str, Any]:
        """Verify sending 10 messages in Discord."""
        return self._request("POST", "/tasks/discord/messages/verify")

    def verify_discord_reactions(self) -> Dict[str, Any]:
        """Verify reactions to announcements."""
        return self._request("POST", "/tasks/discord/reactions/verify")

    # --- Referral & Records Endpoints ---

    def get_referral_rewards(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get referral points earned across quantum tiers."""
        return self._request("GET", "/users/referral-rewards", params={"page": page, "pageSize": page_size})

    def get_invite_records(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Get list of users referred."""
        return self._request("GET", "/users/invite-records", params={"page": page, "pageSize": page_size})
