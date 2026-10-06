# Velo — Pricing Translation API & Admin Dashboard

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18.0-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6?logo=typescript&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)

**Velo** is an enterprise-grade Pricing Translation API and Admin Dashboard designed for SaaS platforms, global e-commerce, and multi-regional billing engines. It automatically converts base pricing into localized currencies while accounting for regional tax regulations (EU VAT, India GST, Brazil LGPD), custom psychological pricing strategies (charm rounding), and real-time exchange rates.

---

## 🌟 Key Features

- ⚡ **High-Performance Translation Engine**: Converts plans and dynamic checkout prices in `< 42ms` median latency with fallback rate caching.
- 🌍 **Regional Tax & Compliance Studio**: Built-in compliance profiles for EU VAT, India GST, Brazil LGPD, and US Sales Tax with support for tax-inclusive or tax-exclusive price rendering.
- 🧠 **Psychological Pricing Rules**: Configurable charm rounding strategies (`.99`, `.95`, nearest integer) to maximize localized checkout conversion rates.
- 🔄 **Unified Billing Connectors**: Pre-built connectors for **Stripe**, **Chargebee**, and **Recurly** normalizing multi-provider subscription plans into a single schema.
- 📊 **Real-time Activity Audit Monitor**: Live stream of API requests, response latencies, execution statuses, and audit trail logs.
- 🛡️ **Dual Security Architecture**: API-key bearer authentication for public translation endpoints and session-based authentication for the administrative management dashboard.
- 💎 **Obsidian Glassmorphism Dashboard**: Modern, responsive dashboard UI built with React 18, Vite, and custom CSS styling.

---

## 🏗️ Tech Stack & Architecture

### Backend
- **Framework**: Python 3.12 + FastAPI
- **Database**: SQLite / PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Background Tasks & Caching**: Celery + Redis / In-Memory Fallback Cache
- **Testing**: Pytest (100% core test coverage across auth, rules engine, public API, and sync components)

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Vanilla CSS (Obsidian dark glassmorphism theme)
- **State & Router**: Modern React Hooks & Context API

### Infrastructure
- **Containerization**: Docker & Docker Compose (`docker-compose.yml`)

---

## 📸 Dashboard UI & Feature Walkthrough

### 1. Dashboard Home & Hero Metrics
Provides an instant overview of edge node statuses, active currency translations, median API response latency, total synced plans, and currently deployed rule versions.

![Dashboard Home](https://raw.githubusercontent.com/KuldeepShivajiraoGheghate/Velo-Pricing-Translation-API-/main/docs/velo_dashboard_home.png)

---

### 2. Rules Engine & Regulation Studio
Configure regional compliance rules, target currency groups, tax calculation modes (inclusive vs. exclusive), and charm rounding parameters with one-click deployment.

![Rules Engine](https://raw.githubusercontent.com/KuldeepShivajiraoGheghate/Velo-Pricing-Translation-API-/main/docs/velo_rules_deployed.png)

---

### 3. Live Preview Studio
Side-by-side translation workspace allowing developers to test base prices against target currencies, regional tax profiles, and rounding rules in real time.

![Live Preview Studio](https://raw.githubusercontent.com/KuldeepShivajiraoGheghate/Velo-Pricing-Translation-API-/main/docs/velo_preview_studio.png)

---

### 4. Real-Time Activity Monitor
Live audit log monitoring all incoming `/v1/translate` API requests, execution status codes, response times, and payload breakdowns.

![Activity Monitor](https://raw.githubusercontent.com/KuldeepShivajiraoGheghate/Velo-Pricing-Translation-API-/main/docs/velo_activity_monitor.png)

---

### 5. Billing Integrations Manager
Connect and manage live sync pipelines with **Stripe**, **Chargebee**, and **Recurly** billing providers.

![Billing Integrations](https://raw.githubusercontent.com/KuldeepShivajiraoGheghate/Velo-Pricing-Translation-API-/main/docs/velo_integrations.png)

---

### 6. API Key Management
Issue, inspect, and revoke production and sandbox API keys with fine-grained organization scoping.

![API Key Generator](https://raw.githubusercontent.com/KuldeepShivajiraoGheghate/Velo-Pricing-Translation-API-/main/docs/velo_api_key_generated.png)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+ and `npm`
- Git

---

### 1. Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
The API server will run at `http://localhost:8000`. Swagger documentation will be available at `http://localhost:8000/docs`.

---

### 2. Frontend Setup

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
The dashboard UI will be available at `http://localhost:5173`.

---

### 3. Running with Docker Compose

You can launch both the backend and frontend simultaneously using Docker:

```bash
docker-compose up --build
```

---

## 🧪 Running Automated Tests

The repository includes comprehensive automated test suites covering all phases of development.

```bash
cd backend
pytest
```

---

## 🔌 Core API Reference

### Public API (`/v1`) — Authenticated via `X-API-Key`

#### `POST /v1/translate`
Translates a single price or checkout payload into the target regional format.

**Request Payload:**
```json
{
  "amount": 199.00,
  "base_currency": "USD",
  "target_currency": "EUR",
  "country_code": "DE",
  "rule_set_id": "rule_default_01"
}
```

**Response:**
```json
{
  "status": "success",
  "translated_price": {
    "original_amount": 199.00,
    "original_currency": "USD",
    "target_currency": "EUR",
    "exchange_rate": 0.92,
    "tax_rate": 0.19,
    "tax_amount": 34.78,
    "final_display_price": "217.99",
    "currency_symbol": "€",
    "rule_set_version": "v1.4.0"
  },
  "latency_ms": 18
}
```

---

### Admin API (`/admin`) — Session Authenticated

- `GET /admin/integrations`: Returns connected billing platforms and sync status.
- `POST /admin/rules`: Creates or updates pricing translation rule sets.
- `GET /admin/activity`: Fetches activity logs for audit and monitoring.
- `POST /auth/api-keys`: Generates new API keys for customer orgs.

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── alembic/                # Database migrations
│   ├── app/
│   │   ├── activity_logging/   # Asynchronous audit log generator
│   │   ├── admin_api/          # Dashboard administrative API routes
│   │   ├── auth/               # User authentication & API key middleware
│   │   ├── config/             # Static tax, currency, and profile configs
│   │   ├── core/               # Security, settings, and DB engine
│   │   ├── integrations/       # Stripe, Chargebee, Recurly connectors
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── public_api/         # Dynamic price translation endpoints
│   │   ├── rates_sync/         # Foreign exchange & tax rate sync workers
│   │   └── rules_engine/       # Calculation engine & psychological rounding
│   ├── tests/                  # Automated pytest test suites
│   ├── alembic.ini
│   └── requirements.txt
├── frontend/
│   ├── src/                    # React components and dashboard tabs
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── INSTRUCTIONS.md
└── SRS_Velo_Pricing_Translation_API.md
```

---

## 📜 License

This project is open-source under the [MIT License](LICENSE).
