# arXiv tagger
A server and a [web-page](https://arxivtag.tk) for friendly monitoring of the paper submissions at [arXiv](https://arxiv.org/).

Main features:
1. Select a date range of submissions: today/this week/this month/**since your last visit**. Check easily what submissions you have been already overviewed. 
2. Add any number of arXiv sections and further toggle them easily with check boxes.
3. Create **tags with rules for title, abstract, and author**. You can use logical operators (or/and), regular expressions, TeX formulas in rules. View the most interesting papers on top!
4. Papers suitable with a given tag are **bookmarked automatically**.
5. Email notifications are send when the paper suitable with a given tag is submitted.
6. Dark and light theme of the website.

## Development
To run server locally with Docker, build and run the image with

```bash
docker-compose build arxiv_dev
docker-compose run -p 8000:8000 -p 5000:5000 arxiv_dev
```

Setup environment:
```bash
cd /arxivtagpy
cp .env_example .env
```

PostgreSQL database should be setup with
```bash
su - postgres
createdb -h "postgres" -U "runner" "arxiv_debug"
# pass: tester
exit
flask db stamp head; flask db migrate; flask db upgrade
````

After installation you can run a server in a dev mode with `./launch_dev.py`. And access it with a browser at `http://0.0.0.0:8000/`

The bulk paper download for the last month could be triggered with 
`http://0.0.0.0:8000/load_papers?token=test_token`
