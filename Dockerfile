FROM python:3.10-buster

WORKDIR /api

COPY requirements.txt /api

RUN pip install -r requirements.txt

COPY . /api

RUN chmod a+x /api/script_sh/*.sh
