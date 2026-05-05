# AI Customer Intelligence Engine

A production-ready AI tool that transforms raw, unstructured web data into actionable business insights. Features a 4-layer architecture with a unique **Emerging Issue Detector (Pressure Feature)**.

## Architecture
1. **Ingestion Layer**: Modular scraper (httpx/Playwright + BeautifulSoup).
2. **Processing Layer**: Cleans text, handles Tamil-English code-switching via transliteration.
3. **Intelligence Layer**: Sentiment analysis (RoBERTa) and sliding-window Pressure detection.
4. **Presentation Layer**: Streamlit dashboard for real-time visualization.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. (Optional) Set environment variables:
   Copy `.env.example` to `.env` and fill in your keys if using external APIs.

## Usage

### Run the Dashboard
```bash
streamlit run src/presentation/app.py
```

### Run Pipeline via CLI
```bash
python main.py --url "https://example.com/reviews" --source generic
```

## Folder Structure
- `src/`: Core application logic (ingestion, processing, intelligence, presentation).
- `data/`: Local data storage (`raw/`, `processed/`, `alerts/`).
- `config/`: Application settings.
- `tests/`: Unit tests.
