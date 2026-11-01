"""
Browser Helper for Psy Protocol Wallet Login & JWT Extraction
"""

import os
import json
import time
from typing import Optional, Dict, Any
from eth_account import Account
from eth_account.messages import encode_defunct

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


def run_browser_login(
    private_key: Optional[str] = None,
    portal_url: str = "https://psy.xyz/psychonaut",
    timeout_seconds: int = 60
) -> Optional[str]:
    """
    Launch Chrome to perform or assist in wallet login and capture JWT token.
    Works either fully automated (if private_key provided) or as an interactive assistant.
    """
    if not sync_playwright:
        print("[!] Playwright is not installed. Please install with: pip install playwright")
        return None

    captured = {"token": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized"
            ]
        )
        context = browser.new_context(
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )

        if private_key:
            acct = Account.from_key(private_key if private_key.startswith("0x") else f"0x{private_key}")
            address = acct.address.lower()

            def sign_message_py(msg_hex_or_str):
                print("[Browser-Assistant] Received SIWE signature request...")
                if msg_hex_or_str.startswith("0x"):
                    try:
                        raw_text = bytes.fromhex(msg_hex_or_str[2:]).decode("utf-8")
                    except Exception:
                        raw_text = msg_hex_or_str
                else:
                    raw_text = msg_hex_or_str

                sig = acct.sign_message(encode_defunct(text=raw_text)).signature.hex()
                if not sig.startswith("0x"):
                    sig = "0x" + sig
                print(f"[Browser-Assistant] Auto-signed message: {sig[:18]}...")
                return sig

            context.expose_function("pySignMessage", sign_message_py)

            provider_script = f"""
            (() => {{
                Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                const address = "{address}";
                const chainId = "0x1";
                const listeners = {{}};

                const provider = {{
                    isMetaMask: true,
                    selectedAddress: address,
                    chainId: chainId,
                    networkVersion: "1",
                    request: async ({{ method, params }}) => {{
                        if (method === "eth_requestAccounts" || method === "eth_accounts") return [address];
                        if (method === "eth_chainId") return chainId;
                        if (method === "net_version") return "1";
                        if (method === "personal_sign") return await window.pySignMessage(params[0]);
                        return null;
                    }},
                    on: (e, h) => {{ (listeners[e] = listeners[e] || []).push(h); }},
                    removeListener: () => {{}}
                }};
                window.ethereum = provider;

                const info = {{
                    uuid: "350670db-19fa-4704-a166-e52e178b59d2",
                    name: "MetaMask",
                    icon: "",
                    rdns: "io.metamask"
                }};

                function announce() {{
                    window.dispatchEvent(new CustomEvent("eip6963:announceProvider", {{
                        detail: Object.freeze({{ info, provider }})
                    }}));
                }}
                window.addEventListener("eip6963:requestProvider", announce);
                announce();
            }})();
            """
            context.add_init_script(provider_script)

        page = context.new_page()

        def handle_resp(r):
            if "auth/wallet/login" in r.url:
                try:
                    print(f"[Browser-Assistant] Login response status: {r.status}")
                    text = r.text()
                    print(f"[Browser-Assistant] Login response body: {text}")
                    data = json.loads(text)
                    tok = data.get("data", {}).get("token")
                    if tok:
                        captured["token"] = tok
                        print("[Browser-Assistant] Successfully captured JWT Token!")
                except Exception as e:
                    print(f"[Browser-Assistant] Error parsing response: {e}")

        page.on("response", handle_resp)

        print(f"[Browser-Assistant] Opening {portal_url} ...")
        page.goto(portal_url, timeout=60000)

        print("[Browser-Assistant] Waiting for login completion (or complete the Cloudflare Turnstile verification if prompted)...")
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if captured["token"]:
                break

            # Also check localStorage/cookies for jwt_token
            try:
                for frame in page.frames:
                    if "cloudflare" in frame.url or "challenges" in frame.url:
                        chk = frame.locator("input[type='checkbox'], .ctp-checkbox-label, #cf-stage")
                        if chk.count() > 0 and chk.first.is_visible():
                            chk.first.click()
                            print("[Browser-Assistant] Clicked Cloudflare Turnstile box!", flush=True)
            except Exception:
                pass

            try:
                storage_token = page.evaluate("() => localStorage.getItem('jwt_token') || sessionStorage.getItem('jwt_token') || localStorage.getItem('token')")
                if storage_token:
                    captured["token"] = storage_token
                    print("[Browser-Assistant] Found JWT Token in LocalStorage!")
                    break
            except Exception:
                pass

            page.wait_for_timeout(1000)

        browser.close()

    return captured["token"]
