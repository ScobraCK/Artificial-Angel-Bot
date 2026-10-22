FROM python:3.15-slim

RUN apt-get -y update && apt-get -y upgrade
RUN pip install --upgrade --no-cache-dir "pip>=26.2.2" certifi

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "aabot.main"]
