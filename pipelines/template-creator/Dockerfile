FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    qemu-utils \
    jq

RUN pip install -r pipelines/template-creator/requirements.txt

COPY . /app
WORKDIR /app

CMD ["python", "main.py"]
