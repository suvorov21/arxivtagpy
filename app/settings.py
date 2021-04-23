"""Settings management: settings page and settings changes."""

from json import loads, dumps
import logging
from typing import Dict

from flask import Blueprint, render_template, session, request
from flask_login import current_user, login_required

from .model import db, Tag

settings_bp = Blueprint(
    'settings_bp',
    __name__,
    template_folder='templates',
    static_folder='static'
)

@settings_bp.route('/settings')
@login_required
def settings():
    """Settings page."""
    load_prefs()
    page = 'cat'
    if 'page' in request.args:
        page = request.args['page']
    # TODO this is excessive
    # CATS and TAGS are send back for all the settings pages
    return render_template('settings.jinja2',
                           cats=session['cats'],
                           tags=dumps(session['tags']),
                           # TODO read from prefs
                           pref=dumps(session['pref']),
                           math_jax=session['pref'].get('tex'),
                           dark=session['pref'].get('dark'),
                           page=page
                           )

########### Setings change #############################################


@settings_bp.route('/mod_cat', methods=['POST'])
@login_required
def mod_cat():
    """Apply category changes."""
    new_cat = []
    new_cat = request.form.getlist("list[]")

    current_user.arxiv_cat = new_cat
    db.session.commit()
    session['cats'] = current_user.arxiv_cat
    return dumps({'success':True}), 201

@settings_bp.route('/mod_tag', methods=['POST'])
@login_required
def mod_tag():
    """Apply tag changes."""
    new_tags = []
    # FIXME Fix key break with ampersand
    for arg in request.form.to_dict().keys():
        new_tags.append(arg)

    new_tags = '&'.join(new_tags)

    if new_tags == '':
        return dumps({'success': False}), 204

    # convert to array of dict
    new_tags = loads(new_tags)

    # Rewrite user tags
    # since both reordering and tag modifications could be done
    # perform a full rewrite
    current_user.tags = []
    session['tags'] = []
    for tag in new_tags:
        # new tag creation
        if tag['id'] == -1:
            logging.debug("Creating new tag %r for user %r",
                          tag,
                          current_user
                          )
            new_tag = Tag(name=tag['name'],
                          rule=tag['rule'],
                          color=tag['color'],
                          bookmark=tag['bookmark'],
                          email=tag['email'],
                          public=tag['public']
                          )
        else:
            # tag already exists
            new_tag = Tag.query.filter_by(id=tag['id']).first()
        # if tag was modified
        if tag.get('mod'):
            update_tag(new_tag, tag)

        current_user.tags.append(new_tag)
        session['tags'].append(tag_to_dict(new_tag))

    db.session.commit()
    return dumps({'success':True}), 201

@settings_bp.route('/mod_pref', methods=['POST'])
@login_required
def mod_pref():
    """Apply preference changes."""
    new_pref = []
    for arg in request.form.to_dict().keys():
        new_pref = arg

    if new_pref == []:
        return dumps({'success': False}), 204

    current_user.pref = str(new_pref)
    db.session.commit()
    session['pref'] = loads(current_user.pref)
    return dumps({'success':True}), 201


def update_tag(old_tag: Tag, tag: Tag):
    """Update Tag record in database."""
    old_tag.name = tag['name']
    old_tag.rule = tag['rule']
    old_tag.color = tag['color']
    old_tag.bookmark = tag['bookmark']
    old_tag.email = tag['email']
    old_tag.public = tag['public']

def tag_to_dict(tag: Tag) -> Dict:
    """Transform Tag class object into dict."""
    tag_dict = {'id': tag.id,
                'name': tag.name,
                'rule': tag.rule,
                'color': tag.color,
                'bookmark': tag.bookmark,
                'email': tag.email,
                'public': tag.public
                }
    return tag_dict

def load_prefs():
    """Load preferences from DB to session."""
    if not current_user.is_authenticated:
        return

    session['cats'] = current_user.arxiv_cat

    # read tags
    session['tags'] = []
    for tag in current_user.tags:
        session['tags'].append(tag_to_dict(tag))

    # read preferences
    session['pref'] = loads(current_user.pref)
