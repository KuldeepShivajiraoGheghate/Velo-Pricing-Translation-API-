# Software Requirements Specification (SRS)
## Project: Velo — Global Pricing Translation API for SaaS

---

## 0. Document Control

| Field | Detail |
|---|---|
| Document Title | SRS – Velo Pricing Translation API |
| Version | 1.0 |
| Based on Idea | "An API that lets SaaS apps automatically translate pricing pages into local currencies and regulations in under five minutes." — Ideas AI (@levelsio) |
| Reference UI | `app.html` mockup — tabs: Integrations, Rules, Preview, Activity |
| Intended Builder | Antigravity (AI build agent) |
| Prepared For | Solo-founder / student-led build |

---

## 1. Introduction

### 1.1 Purpose
This SRS defines, in complete detail, the requirements for **Velo**, a developer-facing API and dashboard that lets SaaS companies automatically convert their pricing pages into localized versions — correct currency, correct tax/VAT/GST treatment, and correct regional compliance disclosures — with near-zero manual work. This document is written so a build agent (Antigravity) or a human engineering team can implement the system without needing further clarification on scope, data model, or behavior.

### 1.2 Problem Statement
SaaS companies price in a single base currency (usually USD) and rarely adapt pricing pages for international visitors. Manual localization requires legal review (VAT/GST/LGPD rules), live exchange-rate tracking, and per-region rounding/psychological-pricing rules. This is slow, error-prone, and rarely maintained. Velo automates this end-to-end via an API + rules engine + dashboard.

### 1.3 Scope
Velo will provide:
1. A **Translation API** (`/v1/translate`) that takes a base price + currency and returns a localized price with tax treatment applied.
2. A **Rules Engine** letting a company define which currencies/regions/regulations apply and how (rounding rules, tax-inclusive vs exclusive, psychological pricing).
3. **Billing-platform Integrations** (Stripe Billing, Chargebee, Recurly) to sync plans/prices so translation stays in sync with the source of truth.
4. A **Dashboard** (Integrations, Rules, Preview, Activity) for configuration, live preview, and audit/monitoring.
5. An **Activity Log** of every translation API call for audit, debugging, and billing/usage metering.
6. **API key management** for authenticating customer (SaaS company) requests.

### 1.4 Out of Scope (v1)
- Automatic detection of visitor location on the client's website (Velo returns data; the client site decides how to detect the visitor — IP geolocation is a stretch goal, not core v1).
- Full legal/tax filing or remittance (Velo only tells the client what tax rate/label to display — it does not collect or remit tax).
- Payment processing itself (Stripe/Chargebee/Recurly remain the payment processors; Velo only reads plan/price data from them).
- Multi-language text translation of marketing copy (Velo only translates **numbers, currency, and compliance labels**, not page copy).

### 1.5 Definitions & Abbreviations
| Term | Meaning |
|---|---|
| SRS | Software Requirements Specification |
| Base Price | The company's original price, in its home currency (e.g., $29/mo) |
| Translated Price | The localized price after currency + tax + rounding rules |
| Tax Region | A jurisdiction with a defined tax regime (EU VAT, India GST, Brazil LGPD-linked tax rules, etc.) |
| Rule Set | A saved configuration mapping currencies → regulations → rounding behavior |
| Connector | An integration module that talks to an external billing platform |
| Activity Log | Immutable record of every API call made against a customer's account |
| Org | A customer company using Velo (tenant) |

### 1.6 References
- Mockup: `app.html` (four-tab dashboard: Integrations, Rules, Preview, Activity)
- Idea card: Ideas AI by @levelsio

---

## 2. Overall Description

### 2.1 Product Perspective
Velo is a **multi-tenant SaaS product**. Each customer ("Org") signs up, connects one or more billing platforms, defines translation rules, and calls Velo's REST API from their own pricing page (client-side or server-side) to fetch localized prices in real time. Velo itself is not embedded UI on the client's site — it is an API + a Velo-hosted admin dashboard.

### 2.2 Product Functions (Summary)
1. Org & user account management (multi-tenant).
2. API key issuance/rotation ("New Key" button in mockup header).
3. Connect/sync billing integrations (Stripe, Chargebee, Recurly).
4. Define and save pricing translation Rule Sets (currency groups + regulation + rounding).
5. Live Preview of translated price side-by-side with original.
6. Serve real-time translation via public API (`/v1/translate`).
7. Log and display Activity (endpoint, region, status, timestamp).
8. Deploy rule changes ("Save & Deploy") with versioning.

### 2.3 User Classes and Characteristics
| User Class | Description | Technical Level |
|---|---|---|
| Org Admin | Owner of a Velo account; manages integrations, rules, API keys | Non-technical to semi-technical (marketing/growth/finance ops) |
| Developer | Integrates the `/v1/translate` API into the client's own pricing page | Technical |
| Velo Internal Admin | Platform-level admin (support/ops) — v1 optional, can be stubbed | Technical |

### 2.4 Operating Environment
- Dashboard: modern web browsers (Chrome, Edge, Firefox, Safari), responsive down to tablet width.
- API: consumed server-side or client-side (CORS-enabled) by customer web apps, any language.
- Hosting: cloud (containerized), region-aware deployment recommended for latency (EU + US + APAC edge, stretch goal).

### 2.5 Design & Implementation Constraints
- Must expose a stable, versioned public REST API (`/v1/...`).
- Exchange rates and tax rates must be refreshed on a schedule, not hardcoded.
- Rule changes must be deployable without downtime ("Save & Deploy" implies a build/deploy pipeline or a hot-reloadable rules cache).
- All monetary calculations must use fixed-point/decimal arithmetic — never floating point — to avoid rounding errors.

### 2.6 Assumptions and Dependencies
- Availability of a third-party currency exchange-rate API (e.g., a live FX rates provider).
- Availability of a tax-rate reference dataset per country (VAT/GST rates), refreshed periodically.
- Customer already has an account with at least one supported billing platform (Stripe, Chargebee, or Recurly) for the Integrations module to be useful; the Rules/Preview/API modules can work with manually entered prices too.

---

## 3. System Features (Functional Requirements)

Each feature is numbered `FR-<module>-<n>` for traceability.

### 3.1 Module: Authentication & API Key Management
- **FR-AUTH-1**: System shall allow an Org Admin to sign up and create an Org.
- **FR-AUTH-2**: System shall support login via email/password (and optionally OAuth — stretch).
- **FR-AUTH-3**: System shall let an Org generate one or more API keys ("New Key" button), each scoped to the Org.
- **FR-AUTH-4**: System shall let an Org revoke/rotate an API key without affecting other keys.
- **FR-AUTH-5**: System shall require a valid API key (header-based) on every call to `/v1/*` public endpoints.
- **FR-AUTH-6**: System shall rate-limit API calls per key.

### 3.2 Module: Integrations (Tab 1 in mockup)
- **FR-INT-1**: System shall let an Org connect to Stripe Billing via OAuth or restricted API key.
- **FR-INT-2**: System shall let an Org connect to Chargebee via API key + site name.
- **FR-INT-3**: System shall let an Org connect to Recurly via API key.
- **FR-INT-4**: System shall display connection status per integration: `Live`, `Syncing`, `Error`, `Disconnected`.
- **FR-INT-5**: System shall display "Last sync" time per integration.
- **FR-INT-6**: System shall periodically (and on-demand via "Configure") pull the Org's plans/prices from each connected billing platform.
- **FR-INT-7**: System shall normalize plan/price data from all three providers into one internal schema (see §5).
- **FR-INT-8**: On sync failure, system shall log the error and surface it in the Integrations table (status = Error) and in Activity.

### 3.3 Module: Rules Engine (Tab 2 in mockup)
- **FR-RULE-1**: System shall let an Org select one or more target currency groups (e.g., "EUR, GBP, JPY, AUD" or "BRL, INR, MXN") to translate into.
- **FR-RULE-2**: System shall let an Org select a Regulation profile per target region (e.g., "EU VAT + GDPR", "India GST", "Brazil LGPD").
- **FR-RULE-3**: System shall let an Org configure whether displayed price is tax-inclusive or tax-exclusive.
- **FR-RULE-4**: System shall let an Org configure rounding strategy (e.g., round to nearest whole unit, nearest .99, nearest .00).
- **FR-RULE-5**: System shall let an Org configure "psychological pricing" adjustment (optional charm pricing, e.g., 34.80 → 34.99) as a toggle.
- **FR-RULE-6**: System shall version every Rule Set; "Save & Deploy" creates a new active version and keeps prior versions in history.
- **FR-RULE-7**: System shall validate a Rule Set before deploy (e.g., currency code validity, regulation exists) and block deploy on validation failure with a clear error.
- **FR-RULE-8**: On successful deploy, system shall show a confirmation with the deploy duration (mockup shows "Rules deployed in 42s" toast).
- **FR-RULE-9**: System shall apply the most recently deployed active Rule Set to all subsequent `/v1/translate` calls immediately (no redeploy of client apps required).

### 3.4 Module: Preview (Tab 3 in mockup)
- **FR-PRV-1**: System shall let an Org pick one of its synced plans (or manually enter a price) to preview.
- **FR-PRV-2**: System shall show the Original price (base currency, plan name, billing interval) side-by-side with the Translated price.
- **FR-PRV-3**: Translated price panel shall show: target currency, computed amount, tax label (e.g., "incl. 20% VAT"), and compliance note (e.g., "GDPR compliant").
- **FR-PRV-4**: System shall provide a "Refresh translation" action that recomputes the preview using the latest exchange rate and active Rule Set.
- **FR-PRV-5**: System shall let the Org switch the target region/currency in preview to check multiple regions without leaving the tab.

### 3.5 Module: Public Translation API
- **FR-API-1**: System shall expose `POST /v1/translate` accepting: source amount, source currency, target currency (or target country/region), plan identifier (optional).
- **FR-API-2**: System shall return: translated amount, currency code, applicable tax rate/label, rounding applied, regulation notes, and the Rule Set version used.
- **FR-API-3**: System shall support `GET /v1/translate` (or `/v1/prices/{plan_id}`) for the common case of "give me this plan's price in this currency" using saved plan data (no need to pass raw amount).
- **FR-API-4**: System shall respond within a defined SLA (see NFR-PERF).
- **FR-API-5**: System shall cache exchange rates internally (not call the FX provider on every request) with a defined refresh interval (e.g., hourly).
- **FR-API-6**: System shall return clear, structured error codes for: invalid API key, unsupported currency pair, missing plan, rate-limit exceeded.

### 3.6 Module: Activity (Tab 4 in mockup)
- **FR-ACT-1**: System shall log every call to `/v1/*` endpoints: timestamp, endpoint, target region/country, response status.
- **FR-ACT-2**: System shall display the Activity table sorted by most recent first.
- **FR-ACT-3**: System shall allow filtering Activity by date range, endpoint, region, and status (success/error).
- **FR-ACT-4**: System shall retain Activity logs for a defined period (e.g., 90 days on standard plan) and allow export (CSV) — stretch for v1.
- **FR-ACT-5**: System shall aggregate Activity into simple usage metrics (calls today, calls this month) for potential future billing/metering.

### 3.7 Module: Dashboard Shell / Navigation
- **FR-NAV-1**: System shall present four primary views as tabs: Integrations, Rules, Preview, Activity (matches mockup).
- **FR-NAV-2**: System shall show the active Org name in the header.
- **FR-NAV-3**: Header shall expose a global "New Key" action reachable from any tab.

---

## 4. External Interface Requirements

### 4.1 User Interface Requirements (derived from mockup)
- Single-page app shell with top header (logo, org name, New Key button) and tab navigation.
- Integrations view: table of connected apps with Status badge (green = Live, blue = Syncing), Last Sync column, Configure action.
- Rules view: two-column form (Currencies selector, Regulations selector) + primary "Save & Deploy" button; on save, show a transient bottom-center toast confirming deployment.
- Preview view: two side-by-side cards (Original vs Translated), Translated card visually emphasized (accent border/background), plus "Refresh translation" action.
- Activity view: table of Time, Endpoint, Region, Status (green status pill for success codes).
- Consistent design language: rounded cards, subtle borders, accent blue (`#0066FF`), status pill badges (green = success/live, blue = in-progress).
- Fully responsive down to tablet width; graceful stacking of the two-column grid on narrow screens.

### 4.2 API Interfaces (External, Outbound — Velo calling third parties)
- **Stripe Billing API** — read Products/Prices/Plans.
- **Chargebee API** — read Plans/Item Prices.
- **Recurly API** — read Plans/Pricing.
- **Currency Exchange Rate Provider** — live/historical FX rates (e.g., a provider such as exchangerate.host, Open Exchange Rates, or Fixer — final choice left to implementation, must support all target currencies).
- **Tax/VAT Rate Reference Data** — a maintained dataset or API for VAT (EU), GST (India), and similar regimes (e.g., a VAT-rates API/service) — final provider choice left to implementation.

### 4.3 API Interfaces (Internal/Public — third parties calling Velo)
- `POST /v1/translate`
- `GET /v1/prices/{plan_id}`
- `GET /v1/integrations`
- `POST /v1/integrations/{provider}/connect`
- `POST /v1/rules`
- `GET /v1/rules/active`
- `GET /v1/activity`
- `POST /v1/keys`
- `DELETE /v1/keys/{id}`

(Exact request/response payload schemas to be finalized during API design phase — see §6 for field-level data model that will back these payloads.)

### 4.4 Hardware Interfaces
None beyond standard server/cloud compute; no special hardware required.

---

## 5. Data Model (Logical Entities)

| Entity | Key Fields | Notes |
|---|---|---|
| **Org** | id, name, created_at, plan_tier | Tenant root |
| **User** | id, org_id, email, password_hash, role | role: admin / developer |
| **APIKey** | id, org_id, key_hash, label, created_at, last_used_at, revoked_at | Never store raw key after issuance |
| **Integration** | id, org_id, provider (stripe/chargebee/recurly), status, credentials_ref, last_synced_at | Credentials stored in a secrets vault, not plain DB column |
| **Plan** (normalized) | id, org_id, integration_id, external_plan_id, name, base_amount, base_currency, billing_interval | Populated by sync |
| **RuleSet** | id, org_id, version, currencies[], regulation_profile, tax_mode (inclusive/exclusive), rounding_strategy, psychological_pricing (bool), is_active, created_at | Versioned; only one active per Org |
| **RegulationProfile** | code (EU_VAT_GDPR, INDIA_GST, BRAZIL_LGPD, ...), display_name, applicable_countries[] | Reference/config table |
| **ExchangeRateCache** | base_currency, target_currency, rate, fetched_at | Refreshed on schedule |
| **TaxRateReference** | country_code, tax_type (VAT/GST/...), rate, effective_date | Refreshed periodically |
| **ActivityLog** | id, org_id, api_key_id, endpoint, region, status_code, created_at, latency_ms | Append-only |

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **NFR-PERF-1**: `/v1/translate` median response time ≤ 150 ms; p95 ≤ 400 ms (assuming cached FX/tax data).
- **NFR-PERF-2**: Dashboard views shall load within 2 seconds on broadband.
- **NFR-PERF-3**: Rule deploy shall complete and become active within 60 seconds (matches mockup's "42s" example).

### 6.2 Scalability
- **NFR-SCALE-1**: System shall support multi-tenant horizontal scaling of the API layer independent of the dashboard.
- **NFR-SCALE-2**: Exchange rate and tax data caching shall be shared across all Orgs (not per-tenant) to minimize third-party API cost.

### 6.3 Security
- **NFR-SEC-1**: All traffic over HTTPS/TLS only.
- **NFR-SEC-2**: API keys stored as one-way hashes; raw key shown to user only once at creation.
- **NFR-SEC-3**: Billing-platform credentials (Stripe/Chargebee/Recurly) stored in an encrypted secrets store, never in plaintext in the primary database.
- **NFR-SEC-4**: Role-based access control between Org Admin and Developer roles.
- **NFR-SEC-5**: Full audit trail via Activity Log; logs are append-only/immutable.
- **NFR-SEC-6**: Rate limiting and abuse protection on all public endpoints.

### 6.4 Compliance
- **NFR-COMP-1**: Tax logic shall be configurable per regulation profile (EU VAT, India GST, Brazil-related rules, extensible to more) — Velo provides computed values and labels; legal responsibility for correctness/filing remains with the customer, and this shall be stated in the product's terms.
- **NFR-COMP-2**: Personal data handling (Org/User accounts) shall follow GDPR-style data-subject rights (access, export, deletion) at least for EU-based customers.

### 6.5 Reliability & Availability
- **NFR-REL-1**: Target uptime 99.9% for the public API.
- **NFR-REL-2**: If the live FX/tax provider is unavailable, system shall serve the last successfully cached rate rather than failing the request, with a flag indicating "stale rate used."

### 6.6 Usability
- **NFR-USE-1**: Dashboard shall require no training for an Org Admin to connect an integration and deploy a first Rule Set within 5 minutes (matches the product's core promise).

### 6.7 Maintainability
- **NFR-MAINT-1**: Regulation profiles and tax rates shall be data-driven/config-driven, not hardcoded in application logic, so new regions can be added without code changes to the core translation engine.

---

## 7. System Architecture (High-Level, Logical)

**Components:**
1. **Dashboard (Frontend SPA)** — renders the four tabs; talks only to Velo's internal/admin API (authenticated by session, not public API key).
2. **Admin/Internal API service** — powers the dashboard: Org/User management, Integrations CRUD, RuleSet CRUD, Activity queries.
3. **Public Translation API service** — the customer-facing, API-key-authenticated `/v1/*` surface; optimized for low latency; reads from the Rules cache and Exchange/Tax cache.
4. **Integration Connectors** — one module per billing provider (Stripe/Chargebee/Recurly), each implementing a common "fetch plans" interface; run as scheduled sync jobs plus on-demand triggers.
5. **Rules Engine / Translation Engine** — pure calculation module: given (amount, base currency, target currency, active RuleSet, tax rate reference), returns translated amount + labels. Must be deterministic and independently unit-testable.
6. **Rates & Tax Data Sync Service** — scheduled jobs that refresh ExchangeRateCache and TaxRateReference from external providers.
7. **Activity Logger** — async, non-blocking write path so logging never slows down the translation response.
8. **Primary Database** — stores Org, User, Integration metadata, Plan, RuleSet, RegulationProfile.
9. **Cache Layer** — in-memory/distributed cache for exchange rates, tax rates, and the currently active RuleSet per Org (to keep `/v1/translate` fast).
10. **Secrets Vault** — stores third-party API credentials.
11. **Job Queue** — for async sync jobs (integration pulls, rate refreshes) so the UI ("Configure", "Save & Deploy") isn't blocked on slow external calls.

**Data flow (translation request):** Client app → Public API (auth by API key) → Cache lookup (active RuleSet + FX rate + tax rate) → Translation Engine computes result → Response returned → Activity Logger writes log asynchronously.

**Data flow (rule deploy):** Dashboard → Admin API validates RuleSet → new version saved (is_active=true, prior version is_active=false) → Cache invalidated/updated → toast confirmation returned to dashboard.

---

## 8. Regulation Profiles (Initial Set, from mockup)

| Profile Code | Display Name | Notes |
|---|---|---|
| EU_VAT_GDPR | EU VAT + GDPR | Tax-inclusive display typical; VAT rate varies by EU member state |
| INDIA_GST | India GST | GST rate depends on product/service classification |
| BRAZIL_LGPD | Brazil LGPD | Primarily a data-privacy regulation; pair with applicable Brazilian tax rules for price display |

This table is intentionally extensible — adding a new profile should require only a new config row, not a code change (see NFR-MAINT-1).

---

## 9. Testing Requirements

- **Unit tests** for the Translation Engine covering: currency conversion math, rounding strategies, tax-inclusive vs exclusive calculation, psychological pricing toggle.
- **Integration tests** for each billing connector against sandbox/test accounts (Stripe test mode, Chargebee test site, Recurly sandbox).
- **Contract tests** for the public API request/response schema.
- **Load testing** for `/v1/translate` to validate NFR-PERF targets.
- **Security testing**: API key auth bypass attempts, rate-limit verification, secrets-at-rest checks.

---

## 10. Deployment & Environments

- Recommended environments: `local`, `staging`, `production`.
- Public API and Dashboard/Admin API should be independently deployable/scalable services (even if built as one codebase initially).
- Scheduled jobs (rate/tax sync, integration sync) should run on a job scheduler independent of the request/response path.
- Configuration (regulation profiles, supported currencies, rate provider endpoints) should be environment-variable or config-file driven, not hardcoded.

---

## 11. Technology Stack & Library Installation

> The final choice between the Node.js and Python stacks should be made once and used consistently. Below are both viable options with installation commands, for Antigravity/the build agent to choose one.

### 11.1 Option A — Node.js / TypeScript Stack

**Backend (API + Admin service)**
```
npm init -y
npm install express cors helmet dotenv
npm install zod                     # request/response schema validation
npm install pg                      # PostgreSQL client
npm install ioredis                 # Redis cache client
npm install bullmq                  # job queue for sync/refresh jobs
npm install jsonwebtoken bcrypt     # auth
npm install axios                   # outbound HTTP calls (FX/tax/billing APIs)
npm install stripe                  # Stripe SDK
npm install pino pino-pretty        # structured logging
npm install --save-dev typescript ts-node @types/node @types/express
npm install --save-dev jest ts-jest @types/jest supertest
```

**Frontend (Dashboard)**
```
npm create vite@latest velo-dashboard -- --template react-ts
cd velo-dashboard
npm install
npm install axios
npm install @tanstack/react-query
npm install react-router-dom
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 11.2 Option B — Python Stack

**Backend (API + Admin service)**
```
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install fastapi uvicorn[standard]
pip install pydantic
pip install sqlalchemy psycopg2-binary alembic     # ORM + migrations for PostgreSQL
pip install redis
pip install celery                  # job queue for sync/refresh jobs
pip install python-jose passlib[bcrypt]             # auth
pip install httpx                   # outbound HTTP calls
pip install stripe                  # Stripe SDK
pip install python-dotenv
pip install pytest pytest-asyncio httpx
```

**Frontend (Dashboard)** — same as Option A's frontend commands (frontend stack is independent of backend language choice).

### 11.3 Infrastructure / Supporting Services
```
# PostgreSQL (primary database) and Redis (cache) — run via Docker for local dev
docker pull postgres:16
docker pull redis:7

# Optional: local dev orchestration
# docker-compose (no install needed if Docker Desktop already includes Compose v2)
```

### 11.4 Third-Party Accounts Needed (no install, but required before build)
- Stripe account (test mode) + API keys
- Chargebee test site + API key
- Recurly sandbox + API key
- Account with a currency exchange-rate data provider
- Access to a VAT/GST tax-rate reference source

---

## 12. Constraints & Assumptions Recap
- Monetary values must always be handled as decimal/fixed-point, never binary float.
- Exchange rates and tax rates are external data — the system must degrade gracefully (serve last-cached value) if a provider is temporarily unavailable.
- v1 targets three billing connectors only (Stripe, Chargebee, Recurly); architecture should allow adding more connectors later without redesigning the core Rules/Translation Engine.

## 13. Future Enhancements (Explicitly Post-v1)
- IP/geo-based auto-detection of visitor region on the client's page.
- Additional billing connectors (Paddle, Lemon Squeezy, custom billing).
- A/B testing of psychological pricing variants.
- Usage-based billing for Velo itself (metering via Activity Log).
- CSV export and webhook notifications for rule deploys and sync failures.
- Multi-region edge deployment of the Translation API for lower global latency.

## 14. Glossary
See §1.5 (Definitions & Abbreviations).

---
*End of SRS.*
