FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    jq

RUN pip install cryptography \
    paramiko \
    requests \
    scp

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
