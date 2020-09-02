from json import dumps
from urllib.parse import quote
from typing import List, Dict, Tuple

def render_cats(cats: Tuple[str], n_cats: Tuple[int]) -> str:
    """Display the checkboxes, categories labels and counters."""
    parent = ''
    for num, cat in enumerate(cats):
        content = add_tag('input',
                          typed='checkbox',
                          name=f'check-cat-{num}',
                          cl='check-cat',
                          tag_content='checked',
                          self_closed=True,)
        text = add_tag('div',
                       cl='menu-line-left item-cat',
                       name=f'cat-label-{num}',
                       content=cat
                       )
        counter = add_tag('div',
                          cl='menu-line-right',
                          name=f'cat-count-{num}',
                          content=str(n_cats[num])
                         )

        parent += add_tag('div',
                          cl='menu-item',
                          name=f'item-cat-{num}',
                          content=content+text+counter
                          )
    return parent

def render_tags(tags: Dict, n_tags: Tuple[int]) -> str:
    """Render tags to HTNL divs."""
    parent = ''
    for num, tag in enumerate(tags):
        content = add_tag('div',
                          cl='tag-label menu-line-left',
                          name=f'tag-label-{num}',
                          content=rf'{tag["name"]}',
                          style=f'background-color: {tag["color"]}; margin: 0'
                          )

        counter = add_tag('div',
                          cl='menu-line-right',
                          name=f'tag-count-{num}',
                          content=str(n_tags[num])
                         )

        parent += add_tag('div',
                          cl='menu-item',
                          name=f'item-cat-{num}',
                          content=content+counter)
    return parent


def render_title(date_type: int = 0) -> str:
    """Put the date type in the title text."""
    if date_type == 0:
        return 'Papers for today'
    if date_type == 1:
        return 'Papers for this week'
    if date_type == 2:
        return 'Papers for this month'
    if date_type == 3:
        return 'Papers since your last visit'
    return 'Papers'

def render_papers(papers: Dict) -> str:
    """Convert papers dict to JSON string."""

    # cross-fingered nobody will use 1000 tags
    # otherwise I'm in trouble
    papers['content'] = sorted(papers['content'],
                               key=lambda t: t['tags'] if len(t['tags'])>0 else [1000])

    for paper in papers['content']:
        if paper.get('author') and len(paper['author']) > 4:
            paper['author'] = paper['author'][:4]
            paper['author'].append('et al')

        # Put submit date only if updated
        if paper.get('date_sub') \
        and paper.get('date_sub') != paper.get('date_up'):
            paper['date_sub'] = paper['date_sub'].strftime('%d %B %Y')
        else:
            paper['date_sub'] = None

        if paper.get('date_up'):
            paper['date_up'] = paper['date_up'].strftime('%d %B %Y')

    # TODO think about the best way to encode JSON
    # quote may be exaggerated
    return quote(dumps(papers['content']))

# TODO replace with kwargs
def add_tag(tag, cl='', name='', href='', target='', content='',
           self_closed=False, tag_content='', typed='', style='',
           value=''):
    """Add HTML tag."""
    output = f'<{tag}'
    if cl != '':
        output += f' class="{cl}"'
    if name != '':
        output += f' id="{name}"'
    if href != '':
        output += f' href="{href}"'
    if target != '':
        output += f' target="{target}"'
    if typed != '':
        output += f' type="{typed}"'
    if style:
        output += f' style="{style}"'
    if value:
        output += f' value="{value}"'
    if tag_content:
        output += f' {tag_content}'

    output += '/>' if self_closed else f'>{content}</{tag}>'

    return output
