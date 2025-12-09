FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

ENV FLASK_APP=yacut_async \
    FLASK_ENV=production

EXPOSE 5000

CMD ["gunicorn", "yacut_async:app", "--bind", "0.0.0.0:5000"]