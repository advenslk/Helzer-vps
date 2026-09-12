FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml ./
COPY helzer ./helzer
COPY main.py ./main.py
RUN pip install --no-cache-dir .

CMD ["python", "main.py"]
