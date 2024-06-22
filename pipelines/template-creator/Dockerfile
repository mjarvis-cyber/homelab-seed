FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    qemu-utils \
    jq

RUN pip install paramiko \
    requests \
    scp

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
