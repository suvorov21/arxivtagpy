# arXiv tagger
A server and a web-page for friendly monitoring of the paper submissions at [arXiv](https://arxiv.org/).

Main features:
1. Select a date range of submissions: today/this week/this month/**since your last visit**
2. Add any number of arXiv section and further toggle them easily with check boxes
3. Create tags with rules for title, abstract, and author. Complicated logic with OR/AND and LaTeX is supported. View the most interesting papers on top!
4. Sort the papers with tags, submission dates
5. All your preferences: categories, tags, checkboxes, sorting mehtod are saved and will be used at your next visit.

You can briefly look through the design concept at [GitLab pages](https://suvorov21.gitlab.io/arXivTag/). Keep in mind, this is just a conceptual layout, the dynamical load of papers is not possible, as well as category and tags management. You need to download the whole package and to run the server. However, you can get an impression of the basic functions, toggle check-boxes, etc.

The screen shot of the web-page is provided below:

![Website](./doc/website_half.png)


## Installation

At the moment only developer installation is available. The user-friendly rpm/deb/dmg *may* come later. The basic requerments is python > 3.6. To install the package run:

```bash
git clone https://gitlab.com/suvorov21/arXivTag.git
cd arXivTag
python3 -m pip install .
```

After installation you can run a server and a website with `./launcher.sh`. The server can be stopped with a `kill -9` command, the exact particular command will be shown in the terminal.

In case of any problems you can run the server and a browser manually with

```bash
cd arXivTag
python3 server.py
```
and open the provided link (e.g. http://127.0.0.1:8880/) with a browser.
