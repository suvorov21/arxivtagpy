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

def render_cats(cats):
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
                          content='0'
                         )

        parent += add_tag('div',
                          cl='menu-item',
                          name=f'item-cat-{num}',
                          content=content+text+counter)


    return parent

def render_tags(tags):
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
                          content='0'
                         )

        parent += add_tag('div',
                          cl='menu-item',
                          name=f'item-cat-{num}',
                          content=content+counter)
    return parent

def cut_author(authors, n_author=4):
    """String with author list limited to n_author.

    Arguments:
    :param      n_author:  Number of authors to print
    :type       n_author:  int
    """
    if len(authors) > n_author:
        authors = authors[:n_author+1]
        authors.append('et al')
        return authors
    return authors
