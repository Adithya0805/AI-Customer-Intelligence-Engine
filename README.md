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
## Deployment (Production Hosting)

To make this tool available publicly for anyone to use, you have two excellent free options:

### Option 1: Hugging Face Spaces (Recommended for ML apps)
Since this app uses HuggingFace `transformers` (RoBERTa), Hugging Face Spaces is the most stable free host.
1. Create a free account at [Hugging Face](https://huggingface.co/).
2. Click **New Space** -> Select **Streamlit** as the Space SDK.
3. You can connect your GitHub repository directly, or push your code using Git.
4. The space will automatically install `requirements.txt` and run `app.py`.

### Option 2: Streamlit Community Cloud (Easiest)
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **New app** and select your repository (`Adithya0805/AI-Customer-Intelligence-Engine`).
3. Set the Main file path to `src/presentation/app.py`.
4. Click **Deploy!**
*(Note: Streamlit cloud has a 1GB RAM limit on the free tier, which might be tight when the AI model loads into memory).*
