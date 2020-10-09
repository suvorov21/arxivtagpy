# arXiv tagger
A server and a web-page for friendly monitoring of the paper submissions at [arXiv](https://arxiv.org/).

Main features:
1. Select a date range of submissions: today/this week/this month/**since your last visit**
2. Add **any number of arXiv sections** and further toggle them easily with checkboxes
3. Create **tags with rules for title, abstract, and author**. You can use logical operators (or/and), regular expressions, TeX formulas in rules. View the most interesting papers on top!
4. **Sort the papers** with tags, submission dates, categories.
5. All your preferences: categories, tags, checkboxes are saved and will be used on your next visit.

You can briefly look through the design concept at [GitLab pages](https://suvorov21.gitlab.io/arXivTag/).

The screen shot of the web-page is provided below:

![Website](./doc/website_half.png)


## Development
To run server locally

```bash
git clone https://gitlab.com/suvorov21/arxivtagpy.git
cd arxivtagpy
virtualemv v_arxiv
python3 -m pip install -r requirements.txt
```

After installation you can run a server in a dev mode with `./launch_dev.py`.
