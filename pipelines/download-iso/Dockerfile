FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    jq

RUN pip install cryptography \
    paramiko \
    requests \
    scp \
    requests-toolbelt

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
