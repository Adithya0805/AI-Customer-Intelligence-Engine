FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy project files
COPY . .

# Expose ports for both Streamlit and FastAPI
EXPOSE 7860
EXPOSE 8000

# Entrypoint script to handle multiple modes
RUN echo '#!/bin/bash\n\
if [ "$MODE" = "api" ]; then\n\
  uvicorn src.api.main:app --host 0.0.0.0 --port 8000\n\
elif [ "$MODE" = "worker" ]; then\n\
  python -m src.automation.worker\n\
else\n\
  streamlit run src/presentation/app.py --server.port=7860 --server.address=0.0.0.0\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
