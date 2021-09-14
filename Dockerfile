FROM python:3.9.5-slim-buster

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends netcat  && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /usr/src/app/
COPY .env_example /usr/src/app/.env

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

RUN apk add --update nodejs nodejs-npm
RUN cd app/static/src/ || return \
    npm install \
    npm run build

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
