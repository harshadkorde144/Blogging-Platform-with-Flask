FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FLASK_APP=wsgi.py
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -m appuser && mkdir -p /data && chown -R appuser /app /data
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')" || exit 1
# Apply DB migrations, then start Gunicorn
CMD ["sh", "-c", "flask db upgrade && gunicorn --bind 0.0.0.0:8000 --workers 3 --access-logfile - wsgi:app"]
