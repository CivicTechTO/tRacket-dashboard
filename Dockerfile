# syntax=docker/dockerfile:1.4
FROM python:3.8.6-slim-buster as builder

WORKDIR /usr/src/project/

COPY requirements.txt /
RUN pip install -r /requirements.txt


FROM builder AS dev-builder

ARG TOKEN
ENV TOKEN=$TOKEN

# install make and pre-commit
RUN <<EOF
apt-get update -y
apt-get update 
apt-get install make
apt-get install -y git
EOF

EXPOSE 8888
EXPOSE 8501

ENTRYPOINT [ "bash" ]



FROM builder AS prod-builder

ARG TOKEN
ENV TOKEN=$TOKEN

WORKDIR /usr/src/project/app

RUN useradd -m myuser
USER myuser

ADD --chown=myuser ./app /usr/src/project/app/

EXPOSE 8501

CMD gunicorn --bind 0.0.0.0:$PORT app:server