"""Settings management: settings page and settings changes."""

from json import loads, dumps
import logging

from flask import Blueprint, render_template, session, \
request, current_app
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
    # WARNING Do I really need prefs in session
    # How much it affect db load?
    session['cats'] = current_user.arxiv_cat
    return dumps({'success':True}), 201

@settings_bp.route('/mod_tag', methods=['POST'])
@login_required
def mod_tag():
    """Apply tag changes."""
    new_tags = []
    # Fix key break with ampersand
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
            logging.info("Creating new tag %s", tag['name'])
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
            logging.info('Old user %r', new_tag.user_id)
        # if tag was modified
        if tag.get('mod'):
            update_tag(new_tag, tag)

        current_user.tags.append(new_tag)
        session['tags'].append({'id': new_tag.id,
                                'name': new_tag.name,
                                'rule': new_tag.rule,
                                'color': new_tag.color,
                                'bookmark': new_tag.bookmark,
                                'email': new_tag.email,
                                'public': new_tag.public
                                })

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
    # WARNING Do I really need prefs in session
    # How much it affect db load?
    session['pref'] = loads(current_user.pref)
    return dumps({'success':True}), 201


def update_tag(old_tag, tag):
    """Update Tag record in database."""
    old_tag.name = tag['name']
    old_tag.rule = tag['rule']
    old_tag.color = tag['color']
    old_tag.bookmark = tag['bookmark']
    old_tag.email = tag['email']
    old_tag.public = tag['public']

def load_prefs():
    """Load preferences from DB to session."""
    if not current_user.is_authenticated:
        return
    # if 'cats' not in session:
    session['cats'] = current_user.arxiv_cat

    # read tags
    # if 'tags' not in session:
    session['tags'] = []
    for tag in current_user.tags:
        session['tags'].append({'id': tag.id,
                                'name': tag.name,
                                'rule': tag.rule,
                                'color': tag.color,
                                'bookmark': tag.bookmark,
                                'email': tag.email,
                                'public': tag.public
                                })


    # read preferences
    # if 'pref' not in session:
    if "NoneType" not in str(type(current_user.pref)):
        session['pref'] = loads(current_user.pref)