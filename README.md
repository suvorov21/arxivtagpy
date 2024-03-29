# arXiv tag

![Release](https://gitlab.com/suvorov21/arxivtagpy/-/badges/release.svg)

[![Website arxivtag.com](https://img.shields.io/website-up-down-green-red/http/arxivtag.com.svg)](http://arxivtag.com/)
[![Deploy](https://gitlab.com/suvorov21/arxivtagpy/badges/master/pipeline.svg?key_text=deploy)](https://gitlab.com/suvorov21/arxivtagpy/-/commits/master)
[![Staging](https://gitlab.com/suvorov21/arxivtagpy/badges/develop/pipeline.svg?key_text=staging)](https://gitlab.com/suvorov21/arxivtagpy/-/commits/develop)

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=suvorov21_arxivtagpy&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=suvorov21_arxivtagpy)
[![Codacy](https://app.codacy.com/project/badge/Grade/eea7048694ce444b8f1f1329cbc010d6)](https://www.codacy.com/manual/suvorov21/arxivtagpy?utm_source=gitlab.com&amp;utm_medium=referral&amp;utm_content=suvorov21/arxivtagpy&amp;utm_campaign=Badge_Grade)
[![Coverage](https://app.codacy.com/project/badge/Coverage/eea7048694ce444b8f1f1329cbc010d6)](https://www.codacy.com/gl/suvorov21/arxivtagpy/dashboard?utm_source=gitlab.com&utm_medium=referral&utm_content=suvorov21/arxivtagpy&utm_campaign=Badge_Coverage)

Welcome to [arXivtag.com](https://arxivtag.com)!

A server and a [web-page](https://arxivtag.com) for friendly monitoring of the paper submissions at [arXiv.org](https://arxiv.org/).

![Framework flow](app/frontend/dist/img/scheme_small.png)

## Main features

1. Create **tags with rules for keywords in title, abstract, and author list**. One can use logical operators (or/and/negation), regular expressions, and TeX formulas. The paper feed is sorted based on your preferences. View the most interesting papers on top!
2. RSS feed based on the tag settings
3. Papers suitable with a given tag are **bookmarked automatically**.
4. Email notifications are sent when the paper suitable with a given tag is submitted.
5. Add any number of arXiv sections and further toggle them easily with check boxes. Control paper novelty (new/updated) and papers from the cross-categories with the checkboxes as well.
6. Select a date range of submissions: today/this week/this month/**since your last visit**. Check easily what submissions you have been already overviewed.
7. Dark and light theme of the website.
8. Authorization with ORCID

Detailed features description and screenshot gallery at [arxivtag.com](https://arxivtag.com)

## Support project

Project maintaining requires some amount of coffee and money for server hosting.
If you like the project, your support is welcome.

[![donate](https://www.paypalobjects.com/en_US/FR/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/donate/?hosted_button_id=LQKRDE4T6NU4G)

## Development

### Docker run

To run server locally with Docker, build and run the image with

```bash
docker-compose build && docker-compose up
```

The website is accessible with a browser at `http://0.0.0.0:8000/`

The bulk paper download for the last month could be triggered with
`curl -L -X POST -H "token:test_token" "http://0.0.0.0:8000/load_papers"`

### Python venv

Server can be run without Docker, just with a system python and postgres. The python3 >= 3.6 is required.

To do so, create the virtual environment

```bash
python3 -m venv varxiv
. varxiv/bin/activate
pip install -r requirements.txt
```

The Postgres DB should be installed. The DB can be created with

```bash
flask db init; flask db migrate; flask db upgrade
```

The front-end is build with npm

```bash
cd app/frontend/src/
npm install
npm run build
```

The server can be run in the dev mode with

```bash
flask run
```

The website access is the same as for the Docker run.
