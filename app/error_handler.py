"""Catch HTTP errors."""

import logging
import traceback

from werkzeug.exceptions import HTTPException

from flask import render_template, abort, current_app, request, flash, redirect, url_for
from flask_wtf.csrf import CSRFError

from .settings import default_data


ERROR_TEMPLATE = 'error_main.jinja2'


@current_app.errorhandler(CSRFError)
def handle_csrf_error(error):
    """CSRF token error handler."""
    if 'expired' in error.description:
        return render_template(ERROR_TEMPLATE,
                               line1='Your session is expired.',
                               line2='Please, resubmit the form.',
                               img='clock',
                               data=default_data()
                               ), 400
    if 'is missing' in error.description:
        flash('ERROR! Internal error occurred. Please submit the form again')
        return redirect(url_for('main_bp.root'))

    logging.error('CSRFError: %s', error.description)
    return abort(500)


@current_app.errorhandler(Exception)
def handle_exception(error):
    """Error handler."""
    if isinstance(error, HTTPException):
        logging.info('HTTP error %r', error)
        if error.code in (404, 405):
            pref = 'http'
            line2 = f'Go to <a href="{pref}://{request.headers.get("Host")}">main page</a>'
            return render_template(ERROR_TEMPLATE,
                                   line1='Page not found',
                                   line2=line2,
                                   img='error',
                                   data=default_data()
                                   ), error.code
        logging.error('Unhandled HTTP error: %r', error)
        return error
    logging.error('General error was fired: %r', error)
    logging.error(traceback.format_exc())
    line1 = 'arXiv tag was suddenly broken while processing your request.'
    line2 = 'We are notified and investigating the issue. Sorry for the inconvenience.'
    pref = 'http'
    line2 += f'<br>Go to <a href="{pref}://{request.headers.get("Host")}">main page</a>'
    return render_template(ERROR_TEMPLATE,
                           line1=line1,
                           line2=line2,
                           img='error',
                           data=default_data()
                           ), 500


@current_app.route('/error', methods=['GET'])
def error_path():
    """Error tester endpoint."""
    return 1/0
