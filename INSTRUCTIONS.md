# Build Instructions — Velo (Pricing Translation API)

These instructions tell the build agent (Antigravity) *how* to approach building this project. They assume `SRS_Velo_Pricing_Translation_API.md` has already been read in full and is the single source of truth for requirements. This file contains no code — only process, sequencing, conventions, and verification steps.

---

## 1. Before Starting

1. Read the full SRS document first. Do not begin building any module until the corresponding requirement section has been reviewed.
2. Confirm the technology stack choice (Node.js/TypeScript or Python, per SRS §11) before creating any project folders. Do not mix stacks.
3. Confirm which currency exchange-rate provider and which tax/VAT rate reference source will be used, since the Rates & Tax Data Sync module depends on them. If no provider is chosen yet, pause and flag this as a decision needed before Phase 3 below.
4. Create sandbox/test accounts for Stripe, Chargebee, and Recurly before starting the Integrations module — these are required for real testing, not just mocked testing.

---

## 2. Recommended Build Order (Phased)

Build in this order. Each phase should be fully working and testable before moving to the next; do not build the dashboard UI before its underlying API exists.

### Phase 1 — Foundation
- Project scaffolding for backend and frontend as two separate apps/services.
- Database schema setup for all entities listed in SRS §5.
- Org/User model, signup, login, and session handling.
- API key issuance and revocation flow.
- Basic health-check endpoint to confirm the service runs.

### Phase 2 — Rules Engine (core logic, no UI yet)
- Implement the Translation Engine as an isolated, independently testable module: given a base amount, base currency, target currency, an active Rule Set, and a tax rate, it returns a translated amount and labels.
- Implement rounding strategies and the tax-inclusive/exclusive toggle exactly as described in SRS §3.3.
- Implement psychological pricing as an optional post-processing step, not baked into the core math.
- Write this module so that it has zero dependency on the web framework — it should be callable directly for testing, and later wrapped by the API layer.

### Phase 3 — Rates & Tax Data Sync
- Implement the scheduled job that refreshes the exchange rate cache.
- Implement the scheduled job that refreshes the tax rate reference table.
- Implement the "serve last cached value on provider failure" fallback behavior described in NFR-REL-2 before moving on — this is a core reliability requirement, not an afterthought.

### Phase 4 — Public Translation API
- Implement `/v1/translate` and `/v1/prices/{plan_id}` using the Phase 2 engine and Phase 3 cached data.
- Implement API-key authentication middleware and rate limiting.
- Implement the Activity Logger as an asynchronous write path so it never adds latency to the translation response itself.
- Verify performance against the targets in SRS §6.1 before moving on.

### Phase 5 — Billing Integrations (Connectors)
- Implement the Stripe connector first (most common), then Chargebee, then Recurly.
- Each connector must be built against the same internal "normalized plan" interface described in SRS §3.2 and §5, so the Rules Engine and Preview never need to know which billing provider a plan came from.
- Implement sync status tracking (Live / Syncing / Error) and "last synced at" persistence.
- Test each connector against its respective sandbox account, not mocked data only.

### Phase 6 — Admin/Internal API for the Dashboard
- Build endpoints for: Integrations list/connect/configure, Rule Set create/list/activate, Preview computation (can reuse the Phase 2 engine directly), Activity query/filter.
- Ensure the Admin API is authenticated by user session, not by the public API key — these are two separate auth mechanisms per SRS §6.3.

### Phase 7 — Dashboard (Frontend)
- Build the shell first: header with Org name and "New Key" action, and the four-tab navigation (Integrations, Rules, Preview, Activity), matching the structure and visual language of the provided mockup (`app.html`).
- Build each tab in this order: Integrations → Rules → Preview → Activity, since each later tab depends on data produced by the earlier ones.
- Match the mockup's visual conventions: rounded cards, subtle borders, accent blue for primary actions, green/blue status pill badges, and the bottom-center toast confirmation pattern used for "Save & Deploy."
- Ensure the Rules tab blocks "Save & Deploy" and shows a clear validation error if the Rule Set is invalid, rather than allowing a silent bad deploy.
- Ensure the Preview tab's "Refresh translation" action actually recomputes using live cached data, not a static demo value.

### Phase 8 — Hardening
- Add rate limiting, input validation, and error handling across all public and admin endpoints.
- Add structured logging across backend services.
- Run through the full Testing Requirements list in SRS §9 before considering the build complete.

---

## 3. Coding & Project Conventions

- Keep the Translation Engine (Phase 2) as a self-contained module with no framework dependencies, so it can be unit tested in isolation and reused by both the public API and the dashboard's Preview feature.
- Keep regulation profiles, supported currencies, and rate-provider configuration in config/data files, not hardcoded in application logic — this is a hard requirement from SRS NFR-MAINT-1, since it is what lets new regions be added without touching core code.
- Never perform monetary arithmetic using native floating-point types; use a decimal/fixed-point approach throughout the Translation Engine and anywhere money is stored or calculated.
- Treat all third-party credentials (Stripe/Chargebee/Recurly keys) as secrets — never commit them, never log them, never store them in plaintext in the primary database.
- Every public API response should include the Rule Set version that was used to compute it, for traceability and debugging.
- Every module should be built with its corresponding automated tests before being marked complete — do not defer all testing to the end of the project.

---

## 4. Folder/Project Structure Guidance

- Keep the backend split conceptually (even if it starts as one codebase) into: `auth`, `integrations`, `rules-engine`, `rates-sync`, `public-api`, `admin-api`, `activity-logging`.
- Keep the frontend split into one component/view per tab (`Integrations`, `Rules`, `Preview`, `Activity`), plus a shared shell/layout component for the header and navigation.
- Keep configuration (currencies list, regulation profiles, provider endpoints) in a clearly separated config location, not scattered across business logic files.

---

## 5. Definition of Done (per phase)

A phase is only considered complete when:
1. Its corresponding SRS functional requirements are all satisfied.
2. Its corresponding automated tests pass.
3. It has been manually verified against the relevant tab/flow in the mockup (for UI phases) or against a real sandbox account (for integration phases).
4. No hardcoded secrets, no floating-point money math, and no bypassed authentication exist in the completed code.

---

## 6. What NOT to Do

- Do not build the dashboard UI before the underlying Admin API and data model exist.
- Do not hardcode exchange rates, tax rates, or regulation logic directly into UI components — all of this must come from the backend/config layer.
- Do not skip the "serve last cached value on provider failure" fallback — this is required, not optional, per the SRS.
- Do not mix the public API key auth (used by customer integrations) with the dashboard's session-based auth (used by Org Admins/Developers logging into Velo itself) — these must remain separate mechanisms.

---
*End of Instructions.*
