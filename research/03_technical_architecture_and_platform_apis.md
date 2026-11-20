# Research Report 03: Technical Architecture & Platform APIs

**Document ID:** LORE-RES-003  
**Subject:** Social Media Platform API Realities, Rate Limits, Code-to-Image Engines, and Approval Gate Architecture  
**Date:** 2026-11-20  
**Author:** Antigravity Research Engine  

---

## 1. Executive Summary

To evolve Lore from a CLI generator into a full-fledged, automated social media manager, the system must interface with modern social platform APIs, generate high-engagement visual assets (code diff cards, terminal recordings), and orchestrate real-time approval gates.

This report evaluates:
1. The **API capabilities, rate limits, OAuth life cycles, and cost structures** of target developer platforms: X (Twitter), LinkedIn, Bluesky, GitHub Releases, Dev.to, and Hashnode.
2. The **visual asset rendering pipeline** for automated, syntax-highlighted code cards and terminal animations.
3. The **headless approval architecture** (Slack Block Kit, Discord Webhooks, Telegram Bot) enabling zero-friction sign-offs.

---

## 2. Social Platform API Breakdown

```
+-----------------------------------------------------------------------------------+
|                           PLATFORM PUBLISHING TOPOLOGY                            |
+-------------------+-------------------+-------------------+-----------------------+
| Micro-Blogging    | Professional Net  | Open Federation   | Technical Publications|
| - X (Twitter) v2  | - LinkedIn API v2 | - Bluesky (ATProto)| - Dev.to REST        |
| - Pay-per-use     | - Free, gated app | - Free, open fire | - Hashnode GraphQL    |
| - High friction   | - 60-day OAuth    | - Dev favorite    | - GitHub Releases     |
+-------------------+-------------------+-------------------+-----------------------+
```

### 2.1 X (Twitter) API v2
* **Current State:** X drastically overhauled its API pricing, deprecating the generous v1.1 free tier in favor of paid pay-per-use and tier subscription models.
* **Pricing & Access:**
  * **Free Tier:** Write-only, limited to 1,500 tweets/month per app, but severely restricted for programmatic third parties.
  * **Pay-Per-Use (2024–2026 Model):** Approximately $0.015 per text tweet, $0.20 per media/link tweet.
  * **Basic Tier:** $100–$200/month (10,000 tweets/month read/write).
  * **Pro Tier:** $5,000/month (enterprise).
* **Engineering Challenge:** A small SaaS charging $19/mo cannot provide native shared Twitter API credentials without losing money on API bills.
* **Recommended Lore Architecture:**
  1. **User BYOK (Bring Your Own Keys):** Users input their own Twitter App Developer Keys in `~/.lore/credentials.json`.
  2. **Aggregator Bridges:** Optional integration with third-party webhooks (e.g., Typefully API, Buffer API, or Postiz instance) where users already have connected social handles.
  3. **Direct OAuth 2.0 PKCE:** For Pro/Enterprise hosted tiers with rate-limit pooling.

### 2.2 LinkedIn API (Community Management API v2)
* **Current State:** Highly stable, free of charge, but requires a formal Developer App review and explicit permission scopes (`w_member_social` for personal profiles, `w_organization_social` for company pages).
* **OAuth Life Cycle:**
  * Access tokens expire every **60 days**.
  * Refresh tokens must be exchanged before expiration.
* **Formatting Specifics:**
  * Does not support native Markdown tables or raw markdown code fences.
  * Supports unicode bold/italic formatting, line breaks, and attached images/documents (PDF carousels).
* **Strategic Value:** LinkedIn is currently the highest-ROI platform for technical founders and engineering leadership hiring.

### 2.3 Bluesky (AT Protocol)
* **Current State:** Decentralized, completely free, with high developer adoption.
* **API Details:**
  * Uses the AT Protocol (`com.atproto.repo.createRecord`).
  * Authentication via app passwords (no cumbersome OAuth app review required).
  * Rate limits are generous (thousands of requests per hour).
  * Native support for rich facets (mentions, links, tags) and image embeds.
* **Strategic Value:** Near-zero friction implementation; massive goodwill in the open-source and developer community.

### 2.4 Developer Blogging Platforms (Dev.to, Hashnode, GitHub)
* **Dev.to (Forem API):**
  * Simple API key auth (`api-key: YOUR_KEY`).
  * Direct markdown article publishing with tags, series, and canonical URL mapping.
* **Hashnode:**
  * Modern GraphQL API (`https://gql.hashnode.com`).
  * Headless publishing directly to custom developer subdomains.
* **GitHub Releases & Discussions:**
  * Uses GitHub REST/GraphQL API with personal access tokens (`gh` auth).
  * Allows automatic generation of release notes directly from merged PRs and git tags.

---

## 3. Automated Visual Asset Generation Pipeline

Technical social media posts with code visuals receive **3.8x higher engagement** than plain text. However, manually copying code into tools like Carbon or Ray.so breaks automation.

### 3.1 Architecture for Headless Code-to-Image
Lore must incorporate a zero-dependency, local-friendly visual generator:

```
[ Git Diff / Code Snippet ]
            │
            ▼
┌─────────────────────────┐
│   AST / Syntax Parser   │  Detect language, extract diff lines (+ / -)
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   HTML/SVG Card Styler  │  Dark theme (Catppuccin / Tokyo Night), 
│                         │  traffic light window controls, file badge
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Headless Rasterizer     │  Playwright CLI / Resvg / Silicon / Freeze
│ (resvg-py or Playwright)│
└───────────┬─────────────┘
            │
            ▼
[ Optimized PNG (1200x675) ]  Ready for X / LinkedIn / OpenGraph card
```

### 3.2 Evaluation of Rendering Engines

| Engine | Mechanism | Speed | Dependencies | Output Quality | Recommendation |
|---|---|---|---|---|---|
| **Freeze / Silicon (Rust)** | Native binary compiling AST to PNG | ~80ms | Requires binary install (`freeze` or `silicon`) | Exceptional, highly customizable | **Best for Local CLI** |
| **Resvg-py + Rich/Pyments** | Python wrapper around Rust resvg | ~150ms | Pure pip wheels (`resvg-py`) | Great SVG/PNG rendering, zero browser needed | **Best for Python Library** |
| **Playwright / Puppeteer** | Headless Chrome screenshot | ~800ms | Requires Chromium download (~150MB) | 100% CSS fidelity, HTML templates | **Best for Cloud SaaS** |

---

## 4. Headless Approval Gate Architecture

Developers reject tools that post autonomously without review. Conversely, they reject tools that force them to log into a bloated web dashboard every morning. The ideal approval gate is **asynchronous, push-based, and friction-free**.

### 4.1 Interactive Channels & Webhook Flows

```
[ Git Scan & Generation ]
            │
            ▼
[ Evidence & DLP Check ] (Passed)
            │
            ▼
┌────────────────────────────────────────────────────────┐
│             Dispatch Interactive Webhook              │
├──────────────────────────┬─────────────────────────────┤
│      Slack Channel       │       Discord Channel       │
│  (Block Kit with Action  │    (Embed with Action       │
│        Buttons)          │         Buttons)            │
└───────────┬──────────────┴──────────────┬──────────────┘
            │                             │
            ▼                             ▼
   [ User Clicks Approve ]       [ User Clicks Edit/Regen ]
            │                             │
            ▼                             ▼
[ Queued to Publisher ]         [ Dispatches CLI prompt ]
```

### 4.2 Slack Block Kit Design
* **Payload:** Contains the platform badge (e.g. `[LinkedIn]`), the target publication time, the full post text, the generated code-diff image attachment, and the verified evidence tags (e.g. `Verified Commit: 3de4d39`).
* **Buttons:**
  1. `[Approve & Schedule]` -> Triggers webhook callback to queue post.
  2. `[Regenerate with New Angle]` -> Re-runs generation with alternate angle (e.g., "Architecture Deep Dive" instead of "Before/After").
  3. `[Reject / Dismiss]` -> Archives draft in SQLite database.

### 4.3 Discord & Telegram Fallbacks
* Discord Webhook with components (Message Buttons) or a lightweight bot listener.
* Telegram Bot API with inline keyboard markup (`InlineKeyboardButton`) allowing instantaneous 1-tap approvals directly from mobile notifications.

---

## 5. Architectural Synthesis: Local Core vs. Cloud Extension

To maximize commercial flexibility, Lore’s architecture splits cleanly into two layers:

1. **The Local Core (Free / Open Source):**
   * Local SQLite database (`~/.lore/lore.db`).
   * Local Git scanner and project walker.
   * Local DLP & Shannon entropy scrubber.
   * Local Ollama / LLM API client.
   * Local `resvg-py` code card renderer.
   * Terminal review UI (`lore review`) and clipboard exporter.

2. **The Cloud Extension (Paid / SaaS Tier):**
   * Multi-platform scheduled publisher daemon.
   * Managed OAuth token refresh (LinkedIn, X, Bluesky, Mastodon).
   * Inbound Slack / Discord webhook receiver for mobile interactive approvals.
   * Centralized social analytics and post-performance tracking loop.
