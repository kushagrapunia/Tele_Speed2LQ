FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Leads Excel file + dedupe state persist here — mount a volume at /app/data
# if you want lead data to survive container restarts/redeploys.
CMD ["python", "-m", "app.main"]
