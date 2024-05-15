FROM python:3.12

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y --no-install-recommends ffmpeg

WORKDIR /app
COPY requirement.txt /app/requirement.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD python3 ./main.py
