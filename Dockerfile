# syntax=docker/dockerfile:1

FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt requirements.txt

COPY app/ .
RUN pip3 install -r requirements.txt

CMD gunicorn bot:app -b 0.0.0.0:9000 --access-logfile - --error-logfile -
