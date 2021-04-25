FROM alpine:latest as arxiv_dev

RUN apk add python3-dev postgresql postgresql-dev \
    py3-wheel py3-pip chromium chromium-chromedriver

RUN apk add gcc musl-dev libffi-dev make g++ nodejs nodejs-npm
RUN npm install -g less

ENV POSTGRES_DB arxiv_test
ENV POSTGRES_USER runner
ENV POSTGRES_PASSWORD tester
ENV POSTGRES_HOST_AUTH_METHOD trust

ENV DATABASE_URL_TEST postgresql://runner:tester@postgres:5432/arxiv_test
ENV FLASK_RUN_HOST=0.0.0.0
ENV TOKEN test_token

COPY requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

FROM arxiv_dev as arxiv_run

COPY . .
RUN flask assets build
CMD ["gunicorn", \
    "--workers=2", \
    "--worker-connections=1000", \
    "--worker-class=gevent" \
    "-t 300" \
    "-b 0.0.0.0:8000" \
    "wsgi:app"]
