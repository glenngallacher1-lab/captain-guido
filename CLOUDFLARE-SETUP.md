# CAPTAIN GUIDO - CLOUDFLARE SECURITY SETUP GUIDE

## Why Cloudflare?
- ✅ FREE DDoS protection
- ✅ Real firewall (WAF - Web Application Firewall)
- ✅ Bot protection
- ✅ SSL/HTTPS automatic
- ✅ Faster loading (CDN)
- ✅ Analytics & threat detection

---

## STEP 1: Set Up Cloudflare (10 minutes)

### 1. Create Cloudflare Account
1. Go to https://www.cloudflare.com
2. Click "Sign Up" (it's FREE)
3. Enter your email and create password

### 2. Add Your Site
1. Click "Add a Site"
2. Enter your domain: `captainguido.com` (or whatever you buy)
3. Select the FREE plan
4. Click "Continue"

### 3. Change Your Domain's Nameservers
Cloudflare will show you 2 nameservers like:
```
bob.ns.cloudflare.com
linda.ns.cloudflare.com
```

Go to where you bought your domain (Namecheap, GoDaddy, etc):
1. Find "DNS Settings" or "Nameservers"
2. Change from current nameservers to Cloudflare's
3. Save changes
4. Wait 5-60 minutes for changes to apply

### 4. Cloudflare Will Now Protect Your Site!

---

## STEP 2: Configure Firewall Rules (FREE Tier)

Once Cloudflare is active, set up these security rules:

### Go to: Security → WAF → Create rule

### Rule 1: Block Known Bots
```
Rule name: Block Bad Bots
Field: Known Bots
Operator: equals
Value: On
Action: Block
```

### Rule 2: Block Countries (Optional - if you get attacked)
```
Rule name: Geo Block
Field: Country
Operator: equals
Value: [Countries to block - only if needed]
Action: Block
```

### Rule 3: Challenge Suspicious Traffic
```
Rule name: Challenge Suspicious
Field: Threat Score
Operator: greater than
Value: 10
Action: Managed Challenge
```

### Rule 4: Block SQL Injection Attempts
```
Rule name: Block SQL Injection
Field: URI Path
Operator: contains
Value: union select
Action: Block
```

---

## STEP 3: Enable Security Features

### Go to: Security → Settings

Turn ON these:
- ✅ Security Level: Medium or High
- ✅ Challenge Passage: 30 minutes
- ✅ Browser Integrity Check: ON
- ✅ Privacy Pass Support: ON

### Go to: Security → Bots

Turn ON:
- ✅ Bot Fight Mode (FREE)
- ✅ Super Bot Fight Mode (if on paid plan)

---

## STEP 4: SSL/TLS Settings

### Go to: SSL/TLS → Overview

Set to: **Full (strict)**

This ensures HTTPS is always on and secure.

---

## STEP 5: Page Rules (Speed + Security)

### Go to: Rules → Page Rules

### Rule 1: Force HTTPS
```
URL: http://*captainguido.com/*
Setting: Always Use HTTPS
```

### Rule 2: Cache Everything
```
URL: *captainguido.com/*.png
*captainguido.com/*.jpg
*captainguido.com/*.css
*captainguido.com/*.js
Setting: Cache Level = Cache Everything
```

---

## STEP 6: Rate Limiting (Prevent DDoS)

### Go to: Security → WAF → Rate limiting rules

### Rule 1: Limit API/Wallet Calls
```
Rule name: Wallet Connection Rate Limit
If incoming requests match:
  - URI Path contains "/connect"
  
Then:
  Rate: 10 requests per 10 seconds
  Action: Block
  Duration: 60 seconds
```

---

## ALTERNATIVE: If You Don't Want a Custom Domain Yet

### Use Cloudflare for GitHub Pages:

1. Keep your GitHub Pages URL: `username.github.io/captain-guido`
2. You can STILL use Cloudflare for protection
3. Just proxy it through Cloudflare (advanced setup)

**OR wait until you get a custom domain** - it's easier that way!

---

## STEP 7: Monitor Your Security

### Go to: Security → Analytics

Check:
- Threats blocked
- Countries accessing your site
- Bot traffic
- DDoS attempts

You'll see everything Cloudflare is protecting you from!

---

## Cost Breakdown

**Cloudflare FREE Plan includes:**
- ✅ Unlimited DDoS protection
- ✅ Basic firewall rules
- ✅ Bot protection
- ✅ SSL certificate
- ✅ CDN (faster loading worldwide)
- ✅ Analytics

**Cloudflare Pro Plan ($20/month) adds:**
- 🔥 Advanced DDoS protection
- 🔥 WAF (Web Application Firewall)
- 🔥 Image optimization
- 🔥 Mobile optimization
- 🔥 Priority support

**Recommendation:** Start with FREE, upgrade to Pro if you get serious traffic or attacks.

---

## STEP 8: Additional Security Headers

I already added these to your HTML, but verify they're working:

### Test Your Security Headers:
1. Go to: https://securityheaders.com
2. Enter your site URL
3. Check your score (should be A or A+)

---

## GitHub Security Settings (Do This NOW)

### Go to your GitHub repo → Settings → Security

1. **Enable Dependabot:**
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates

2. **Enable Secret Scanning:**
   - ✅ Secret scanning

3. **Enable Code Scanning:**
   - Click "Set up" → "Default setup"

---

## Common Attack Vectors & How Cloudflare Blocks Them

| Attack Type | How Cloudflare Blocks |
|------------|----------------------|
| DDoS (overwhelming traffic) | Automatic detection + blocking |
| SQL Injection | WAF rules + pattern matching |
| XSS (Cross-site scripting) | Already blocked in your HTML |
| Bots/Scrapers | Bot Fight Mode |
| Brute force attacks | Rate limiting |
| Hotlinking | Page rules to block |
| Bad IPs | IP Access Rules |

---

## Emergency: If You Get Attacked

### If someone is attacking your site RIGHT NOW:

1. **Go to Cloudflare → Security → Under Attack Mode**
   - Toggle "I'm Under Attack Mode" to ON
   - This will challenge ALL visitors before they access your site
   - Turn off after attack stops

2. **Check Security Events:**
   - See what IPs are attacking
   - Block specific countries/IPs if needed

3. **Contact Cloudflare Support:**
   - Even on free plan, they help with major attacks

---

## What About Your Smart Contract?

**Cloudflare protects your WEBSITE.**

For your **Smart Contract**, you need different security:

1. **Smart Contract Audit** (before launch)
   - CertiK: $5k-$50k
   - Hacken: $5k-$20k
   - OpenZeppelin: Contact for quote

2. **Bug Bounty Program**
   - Immunefi.com (list your contract)
   - Offer rewards for finding bugs
   - Starts at $1k-$10k per critical bug

3. **Multi-Sig Wallet for Contract Owner**
   - Gnosis Safe
   - Requires 2-3 signatures to make changes
   - Prevents single point of failure

---

## Summary: Your Security Stack

```
USER
  ↓
CLOUDFLARE (Firewall/DDoS Protection)
  ↓
GITHUB PAGES (Hosting)
  ↓
YOUR WEBSITE (Security headers in HTML)
  ↓
WALLET CONNECTION (Validated in JavaScript)
  ↓
SMART CONTRACT (Needs separate audit)
```

---

## Quick Start Checklist

**Do these in order:**

- [ ] Sign up for Cloudflare (free)
- [ ] Add your domain to Cloudflare
- [ ] Change nameservers at your domain registrar
- [ ] Wait for activation (check email)
- [ ] Enable Bot Fight Mode
- [ ] Set SSL/TLS to "Full (strict)"
- [ ] Create firewall rules (above)
- [ ] Enable "Always Use HTTPS"
- [ ] Test site: https://securityheaders.com
- [ ] Monitor Security → Analytics weekly

**For Smart Contract (BEFORE launch):**

- [ ] Get contract audited
- [ ] Set up multi-sig wallet
- [ ] Test on testnet for 2+ weeks
- [ ] Create bug bounty program
- [ ] Have emergency pause function

---

## Need Help?

**Cloudflare Docs:** https://developers.cloudflare.com/

**Security Questions:**
- r/CloudFlare (Reddit)
- Cloudflare Community Forums

**Smart Contract Security:**
- OpenZeppelin Forum
- r/ethdev (Reddit)

---

## Pro Tip:

Once you set up Cloudflare, your site will be SIGNIFICANTLY more secure than 99% of crypto projects out there. Most scam coins don't even bother with basic security - you're already ahead! 🔒⚓
