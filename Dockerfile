FROM python:3.11.0a5-slim-buster

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends netcat  && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /usr/src/app/
COPY .env_example /usr/src/app/.env

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt

RUN apt update && \
    apt install curl -y && \
    curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    apt install -y nodejs

RUN cd app/frontend/src/ || return \
    npm install \
    npm run build

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
