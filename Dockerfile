FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Single worker (multiple threads) on purpose: quiz/teaching session state is
# held in-process (app.py), so it is NOT shared across worker processes. Running
# >1 worker would make the quiz submit/complete flow 404 non-deterministically.
# To scale horizontally, move that state into a shared store (Redis/DB) first.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "8", "app:app"]
