FROM python:3.7.4
MAINTAINER S-PRO

ENV PYTHONUNBUFFERED 1

COPY app /app
COPY requirements.txt /app/requirements.txt
COPY docker/start.sh /app/start.sh

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["/docker/start.sh"]
