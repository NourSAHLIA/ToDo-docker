FROM python:3.11-slim-bullseye

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY App.py .
EXPOSE 5000
CMD ["python", "App.py"]