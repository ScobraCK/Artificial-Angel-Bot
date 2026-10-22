FROM python:3.15-slim

RUN apt-get -y update && apt-get -y upgrade

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "aabot.main"]
