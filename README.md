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
To run server locally with Docker, build and run the image with

```bash
docker-compose build && docker-compose up
```

The website is accesible with a browser at `http://0.0.0.0:8000/`

The bulk paper download for the last month could be triggered with 
`http://0.0.0.0:8000/load_papers?token=test_token`
