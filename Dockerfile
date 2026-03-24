FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir --upgrade pip setuptools wheel


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .
# COPY main EXPOSE 8501 for streamlit
EXPOSE 8000
EXPOSE 5432

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]