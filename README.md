[![Codacy](https://app.codacy.com/project/badge/Grade/eea7048694ce444b8f1f1329cbc010d6)](https://www.codacy.com/manual/suvorov21/arxivtagpy?utm_source=gitlab.com&amp;utm_medium=referral&amp;utm_content=suvorov21/arxivtagpy&amp;utm_campaign=Badge_Grade)
[![Coverage](https://app.codacy.com/project/badge/Coverage/eea7048694ce444b8f1f1329cbc010d6)](https://www.codacy.com/gl/suvorov21/arxivtagpy/dashboard?utm_source=gitlab.com&utm_medium=referral&utm_content=suvorov21/arxivtagpy&utm_campaign=Badge_Coverage)
[![Deploy](https://gitlab.com/suvorov21/arxivtagpy/badges/master/pipeline.svg?key_text=deploy)](https://gitlab.com/suvorov21/arxivtagpy/-/commits/master)
[![Dev_test](https://gitlab.com/suvorov21/arxivtagpy/badges/develop/pipeline.svg?key_text=dev_test)](https://gitlab.com/suvorov21/arxivtagpy/-/commits/develop)

# arXiv tag
A server and a [web-page](https://arxivtag.tk) for friendly monitoring of the paper submissions at [arXiv](https://arxiv.org/).

Main features:
1. Select a date range of submissions: today/this week/this month/**since your last visit**. Check easily what submissions you have been already overviewed. 
2. Add any number of arXiv sections and further toggle them easily with check boxes.
3. Create **tags with rules for keywords in title, abstract, and author list**. One can use logical operators (or/and), regular expressions, and TeX formulas. View the most interesting papers on top!
4. Papers suitable with a given tag are **bookmarked automatically**.
5. Email notifications are send when the paper suitable with a given tag is submitted.
6. Dark and light theme of the website.

## Development

### Docker run

To run server locally with Docker, build and run the image with

```bash
docker-compose build && docker-compose up
```

The website is accesible with a browser at `http://0.0.0.0:8000/`

The bulk paper download for the last month could be triggered with 
`http://0.0.0.0:8000/load_papers?token=test_token`


### Python venv

Server can be run without Docker, just with a system python. The python3 >= 3.6 is required.

To do so, create the virtual environment
```bash
python3 -m venv varxiv
. varxiv/bin/activate
pip install -r requirements.txt
```

The server can be run in the dev mode with

```bash
./launch_dev.py
```

The website access is the same as for the Docker run.

