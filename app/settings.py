"""Settings management: settings page and settings changes."""

from json import loads, dumps

import logging

from flask import Blueprint, render_template, session, request, \
    current_app, redirect, url_for, flash
from flask_login import current_user, login_required

from .model import db, Tag, PaperList
from .utils import cast_args_to_dict

settings_bp = Blueprint(
    'settings_bp',
    __name__,
    template_folder='templates',
    static_folder='frontend'
)

SET_PAGE = 'settings_bp.settings_page'


@settings_bp.route('/settings')
@login_required
def settings_page():
    """Settings page."""
    load_prefs()
    page = 'cat'
    if 'page' in request.args:
        page = request.args['page']

    data = default_data()
    data['page'] = page

    if page == 'cat':
        data['cats'] = session['cats']
    elif page == 'bookshelf':
        paper_lists = PaperList.query.filter_by(user_id=current_user.id
                                                ).order_by(PaperList.order).all()
        data['lists'] = [{'id': paper_list.id,
                          'name': paper_list.name
                          } for paper_list in paper_lists]

    elif page == 'tag':
        data['tags'] = dumps(session['tags'])
        data['verified_email'] = current_user.verified_email
    elif page == 'pref':
        data['pref'] = dumps(session['pref'])
        data['verified_email'] = current_user.verified_email
        data['pass'] = current_user.pasw is not None
        data['email'] = current_user.email
        data['orcid'] = current_user.orcid
    else:
        return redirect(url_for(SET_PAGE,
                                page='cat'
                                ))

    return render_template('settings.jinja2',
                           data=data
                           )


@settings_bp.route('/mod_cat', methods=['POST'])
@login_required
def mod_cat():
    """Apply category changes."""
    new_cats = cast_args_to_dict(request.form.to_dict().keys())
    current_user.arxiv_cat = new_cats
    db.session.commit()
    session['cats'] = current_user.arxiv_cat
    return dumps({'success': True}), 201


@settings_bp.route('/mod_tag', methods=['POST'])
@login_required
def mod_tag():
    """Apply tag changes."""
    args = request.form.to_dict().keys()
    return modify_settings(args,
                           Tag,
                           new_tag,
                           update_tag,
                           current_user.tags
                           )


@settings_bp.route('/mod_lists', methods=['POST'])
@login_required
def mod_list():
    """Modify paper lists."""
    args = request.form.to_dict().keys()
    return modify_settings(args,
                           PaperList,
                           new_list,
                           update_list,
                           current_user.lists
                           )


@settings_bp.route('/add_list', methods=['POST'])
@login_required
def add_list():
    """Add a new paper list."""
    args = cast_args_to_dict(request.form.to_dict().keys())[0]

    if args['name'] == '':
        logging.error('Error during list add. Request %r', args)
        return dumps({'success': False}), 422

    n_list = PaperList(name=args['name'],
                       order=999,
                       not_seen=0
                       )

    current_user.lists.append(n_list)
    db.session.commit()
    return dumps({'success': True}), 201


@settings_bp.route('/mod_pref', methods=['POST'])
@login_required
def mod_pref():
    """Apply preference changes."""
    new_pref = []
    for arg in request.form.to_dict().keys():
        new_pref = arg

    if not new_pref:
        return dumps({'success': False}), 204

    current_user.pref = str(new_pref)
    db.session.commit()
    session['pref'] = loads(current_user.pref)
    return dumps({'success': True}), 201


@settings_bp.route('/noEmail', methods=["POST"])
@login_required
def no_email():
    """Unsubscribe from all the tag emails."""
    tags = Tag.query.filter_by(user_id=current_user.id).all()

    for tag in tags:
        tag.email = False

    db.session.commit()
    flash('Successfully unsubscribed from all tag emails.')
    return redirect(url_for(SET_PAGE, page='pref'))


def new_tag(tag, order):
    """Create new Tag object."""
    db_tag = Tag(name=tag['name'],
                 rule=tag['rule'],
                 color=tag['color'],
                 order=order,
                 bookmark=tag['bookmark'],
                 email=tag['email'],
                 public=tag['public']
                 )
    return db_tag


def new_list(n_list, order):
    """Create new PaperList object."""
    db_list = PaperList(name=n_list['name'],
                        order=order,
                        not_seen=0
                        )
    return db_list


def modify_settings(args, db_class, new_db_object, update, set_place):
    """
    Single function for settings modifications.

    args:           request.form.to_dict().keys()
    db_class:       database class for the given setting: tag, PaperList, etc.
    new_db_object:  function to create a new DB object
    update:         function to update the DB record
    set_place:      settings relation. E.g. current_user.tags
    """
    new_settings = cast_args_to_dict(args)

    settings = db_class.query.filter_by(user_id=current_user.id
                                        ).order_by(db_class.order).all()
    # save the old version wo delete unused options later
    old_set_id = {setting.id for setting in settings}
    new_set_id = set()
    for order, new_set in enumerate(new_settings):
        new_set_id.add(new_set['id'])
        # create a new object
        if new_set['id'] == -1:
            db_set = new_db_object(new_set, order)
            set_place.append(db_set)
        else:
            # find this list for user
            db_set = db_class.query.filter_by(id=new_set['id']).first()

        update(db_set, new_set, order)

    # delete "unused" lists
    to_delete = old_set_id - new_set_id
    for del_list in to_delete:
        db_class.query.filter_by(id=del_list).delete()

    db.session.commit()
    return dumps({'success': True}), 201


def update_tag(old_tag: Tag, tag: Tag, order: int):
    """Update Tag record in database."""
    old_tag.name = tag['name']
    old_tag.rule = tag['rule']
    old_tag.color = tag['color']
    old_tag.bookmark = tag['bookmark']
    old_tag.email = tag['email']
    old_tag.public = tag['public']
    old_tag.order = order


def update_list(old_list: PaperList, up_list: PaperList, order: int):
    """Update PaperList db record."""
    old_list.name = up_list['name']
    old_list.order = order


def tag_to_dict(tag: Tag) -> dict:
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

    user_id = current_user.id

    session['cats'] = current_user.arxiv_cat

    # read tags
    session['tags'] = []
    tags = Tag.query.filter_by(user_id=user_id).order_by(Tag.order).all()
    for tag in tags:
        session['tags'].append(tag_to_dict(tag))

    # read preferences
    session['pref'] = loads(current_user.pref)


def default_data():
    """Get default template render params."""
    data = dict()
    data['version'] = current_app.config['VERSION']
    data['sentry'] = ''
    if current_app.config['SENTRY_HOOK']:
        data['sentry'] = 'long'
        data['sentry_dsn'] = current_app.config['SENTRY_HOOK']
        data['sentry_key'] = current_app.config['SENTRY_HOOK'].split('//')[1].split('@')[0]
    if 'pref' in session:
        data['theme'] = session['pref'].get('theme')
        data['math_jax'] = session['pref'].get('tex')
    return data
