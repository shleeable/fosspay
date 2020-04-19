FROM python:3.7-buster

WORKDIR /usr/src/app

COPY . ./
RUN pip install --no-cache-dir -r requirements.txt

RUN make
