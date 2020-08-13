from os import linesep
import re

def parse_title(title):
    """Parse paper title."""
    return title.replace(linesep, "").replace("  ", " ")

def parse_links(links, link_type='pdf'):
    """Loop over links and extract hrefs to pdf and arXiV abstract.

    parse links
    related & title = pdf --> pdf
    related & title = doi --> doi
    alternate --> abstract
    """
    for link in links:
        if link.rel == 'alternate' and link_type == 'abs':
            return link.href
        if link.rel == 'related':
            if link.title == 'pdf' and link_type == 'pdf':
                return link.href
            if link.title == 'doi' and link_type == 'doi':
                return link.href

    return None

def parse_authors(authors):
    """Convert authors from freeparser output to list."""
    return [au.name for au in authors]

def parse_cats(cats):
    """Convert categories from freeparser output to list."""
    return [cat.term for cat in cats]

def tag_suitable(paper, rule):
    """Check if paper is suitable with a tag rule.

    :param      paper:  The paper
    :type       paper:  paper JSON entry
    :param      rule:    The tag rule
    :type       rule:    re rule for tag assignment
    """
    # recursion end
    if rule == 'True':
        return True
    if rule == 'False':
        return False

    rule_outside_curly = ''.join(re.findall(r'(.*?)\{.*?\}', rule))
    # # parse brackets () outtside {}
    if '(' in rule_outside_curly:
        start_pos = re.search(r"(^|\}[&|])(\()", rule).start(2)
        end_pos = re.search(r"\}(\))", rule).start(1)
        condition = str(tag_suitable(paper, rule[start_pos+1:end_pos]))
        new_rule = rule[0:start_pos] + condition + rule[end_pos+1:]
        return tag_suitable(paper, new_rule)

    # parse logic AND
    # while '&' outside {} exists
    if '&' in rule_outside_curly:
        fst, scd, before_fst, after_scd = separate_rules(rule, '&')
        condition = str(tag_suitable(paper, fst) and tag_suitable(paper, scd))
        new_rule = before_fst + condition + after_scd
        return tag_suitable(paper, new_rule)

    # parse logic OR
    if '|' in rule_outside_curly:
        fst, scd, before_fst, after_scd = separate_rules(rule, '|')
        condition = str(tag_suitable(paper, fst) or tag_suitable(paper, scd))
        new_rule = before_fst + condition + after_scd
        return tag_suitable(paper, new_rule)

    # parse simple conditions ti/abs/au
    res = re.search(r'^(ti|abs|au)\{.*?\}', rule)
    if res:
        return parse_simple_rule(paper, rule, res.group(1))

    return False

def separate_rules(rule, sign):
    """Split two parts of the rule with sign."""
    sign_pos = re.search(r"\{.*?\}(%s).*\{.*?\}" % re.escape(sign),
                         rule).start(1)

    fst = (re.search(r'.*\{(.*?)(&|\||$)',
                     rule[:sign_pos][::-1]
                     ).group(0))[::-1]

    scd = rule[sign_pos+1:].split('}')[0] + '}'

    fst_start = sign_pos - len(fst)
    scd_end = sign_pos + len(scd)

    return fst, scd, rule[0:fst_start], rule[scd_end+2:]

def parse_simple_rule(paper, rule, prefix):
    """Parse simple rules as ti/au/abs."""
    rule_dict = {'ti': 'title',
                 'au': 'author',
                 'abs': 'abstract'
                 }
    if prefix not in rule_dict:
        raise ValueError('Prefix is unknown')

    condition = re.search(r'.*%s{(.*)}.*' % prefix, rule).group(1)
    search_target = paper[rule_dict[prefix]]
    # in case of author the target is a list
    if isinstance(search_target, list):
        search_target = ', '.join(paper['author'])

    if re.search(condition,
                 search_target,
                 flags=re.IGNORECASE
                 ) is None:
        return False
    return True
