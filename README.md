# arXiv tagger
A server and a [web-page](https://arxivtag.herokuapp.com/) for friendly monitoring of the paper submissions at [arXiv](https://arxiv.org/).

Main features:
1. Select a date range of submissions: today/this week/this month/**since your last visit**
2. Add **any number of arXiv sections** and further toggle them easily with checkboxes
3. Create **tags with rules for title, abstract, and author**. You can use logical operators (or/and), regular expressions, TeX formulas in rules. View the most interesting papers on top!
4. **Sort the papers** with tags, submission dates, categories.

The project is deployed at [Heroku](https://arxivtag.herokuapp.com/).

You can briefly look through the design concept at [GitLab pages](https://suvorov21.gitlab.io/arXivTag/). (!This is **not** a project web-page, just a design layout)

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

After installation you can run a server in a dev mode with `./launch_dev.py`.
