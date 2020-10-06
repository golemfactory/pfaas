FROM python:3.8-slim

RUN mkdir /golem && mkdir /golem/input && mkdir /golem/output
COPY runner.py /golem
VOLUME /golem/input /golem/output
