# AI Customer Intelligence Engine

🚀 **A Production-Ready SaaS Platform for Real-Time Sentiment & Trend Intelligence**

Transform customer feedback from public review sources into actionable business insights using state-of-the-art NLP and LLMs.

---

## ✨ Key Features

-   **🎯 Multi-Source Ingestion:** Scrape reviews from URLs, upload CSVs, or paste raw text.
-   **🎭 Sentiment Intelligence:** Uses RoBERTa-based NLP to classify sentiment with high precision.
-   **🔥 Pressure Radar:** Automatically detects trending complaints before they become PR crises.
-   **💎 Aspect Intelligence (New):** LLM-powered extraction of specific business aspects (e.g., Price, Service) and their sentiment.
-   **🤖 Executive Briefs:** LLM-powered (Gemini) summaries of key business trends.
-   **📡 Auto-Sync Watchlist (New):** Background scheduler to monitor competition or brand reviews 24/7.
-   **📊 Premium Dashboard:** Stunning glassmorphism UI with real-time metrics, trend charts, and word clouds.
-   **☁️ Cloud Native:** Seamlessly integrated with Supabase for persistent data and Hugging Face for deployment.

---

## 🏗️ Architecture

```text
├── config/              # Centralized settings & logging
├── data/
│   └── migrations/      # Supabase SQL migrations
├── src/
│   ├── ingestion/       # Scrapers (httpx, BeautifulSoup)
│   ├── processing/      # Pipeline orchestration
│   ├── intelligence/    # NLP Models (RoBERTa, Gemini)
│   ├── database/        # Supabase Client (Singleton Pattern)
│   ├── automation/      # APScheduler Workers
│   └── presentation/    # Streamlit Glassmorphism UI
└── tests/               # Pytest Suite (Mocked for CI)
```

---

## 🛠️ Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/Adithya0805/AI-Customer-Intelligence-Engine.git
cd AI-Customer-Intelligence-Engine
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file from `.env.example`:
```env
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
SUPABASE_SERVICE_KEY=your_service_role_key
GEMINI_API_KEY=your_gemini_key
ENVIRONMENT=production
```

### 3. Run Locally
```bash
streamlit run src/presentation/app.py
```

---

## 🚀 Roadmap

### Phase 1: Stable MVP (Completed)
- [x] Hardened generic scraper with retries
- [x] RoBERTa sentiment analysis integration
- [x] Glassmorphism dashboard foundation
- [x] Basic Supabase persistence

### Phase 2: Advanced Intelligence (Current)
- [x] **Aspect-Based Sentiment:** Extract deep insights (Price, Support, etc.)
- [x] **Auto-Sync Scheduler:** 24/7 monitoring via APScheduler
- [x] **Adaptive Clustering:** Silhouette-score optimized topic grouping
- [x] **Executive Brief History:** Persistent AI summaries in database

### Phase 3: Enterprise Scale (Upcoming)
- [ ] Multi-tenant authentication (Clerk/Supabase Auth)
- [ ] Multi-source connectors (Amazon, Play Store, Twitter)
- [ ] Custom LLM training for industry-specific sentiment
- [ ] Exportable executive PDF reports

---

## 🛡️ License
MIT License - See [LICENSE](LICENSE) for details.
