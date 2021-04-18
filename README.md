# arXiv tagger
A server and a [web-page](https://arxivtag.tk) for friendly monitoring of the paper submissions at [arXiv](https://arxiv.org/).

Main features:
1. Select a date range of submissions: today/this week/this month/**since your last visit**
2. Add **any number of arXiv sections** and further toggle them easily with checkboxes
3. Create **tags with rules for title, abstract, and author**. You can use logical operators (or/and), regular expressions, TeX formulas in rules. View the most interesting papers on top!
4. **Sort the papers** with tags, submission dates, categories.
5. Dark and light theme of the website

## Development
To run server locally

The package requires NPM less package

1. install NODE.js
2. `npm install less`

Then the package could be cloned and installed

```bash
git clone https://gitlab.com/suvorov21/arxivtagpy.git
cd arxivtagpy
virtualenv varxiv
source varxiv/bin/activate
python3 -m pip install -r requirements.txt
```

PostgreSQL database should be setup and the connection information provided in .env file. See .env_example for more configurations.

After installation you can run a server in a dev mode with `./launch_dev.py`.
