# mandi-price-pipeline

A daily AWS pipeline that ingests India's official mandi (wholesale market) prices from data.gov.in,
cleans them with pandas, stores them as a Parquet star schema on S3, answers price questions with
Athena SQL, and writes a short weekly price advisory using a local LLM.

## Setup

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate on Linux/macOS
pip install -r requirements.txt
cp .env.example .env            # then fill in DATA_GOV_API_KEY
python -m unittest discover tests
```
