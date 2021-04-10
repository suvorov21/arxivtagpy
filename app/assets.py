"""JS ans CSS bundles generator."""

from flask_assets import Environment, Bundle

def compile_layout_assets(app):
    """Compile asssets explicetely for layout."""
    assets = Environment(app)
    Environment.auto_build = True
    Environment.debug = False
    # Light theme
    vars_bundle = Bundle(
        'src/less/vars.less',
        filters='less,cssmin',
        output='dist/css/vars.css',
        extra={'rel': 'stylesheet/less'}
    )

    assets.register('vars', vars_bundle)
    # Dark theme
    vars_dark_bundle = Bundle(
        'src/less/vars_dark.less',
        filters='less,cssmin',
        output='dist/css/vars_dark.css',
        extra={'rel': 'stylesheet/less'}
    )

    assets.register('vars_dark', vars_dark_bundle)

    less_bundle = Bundle(
        'src/less/layout.less',
        filters='less,cssmin',
        output='dist/css/layout.css',
        extra={'rel': 'stylesheet/less'}
    )

    assets.register('layout', less_bundle)

    # Build assets in development mode
    if app.config['DEBUG']:
        vars_bundle.build(force=True)
        vars_dark_bundle.build(force=True)
        less_bundle.build(force=True)

def compile_paper_assets(app):
    """Compile asssets explicetely for paper representation."""
    assets = Environment(app)
    Environment.auto_build = True
    Environment.debug = False
    # Stylesheets Bundle
    less_bundle = Bundle(
        'src/less/layout.less',
        'src/less/papers.less',
        filters='less,cssmin',
        output='dist/css/papers.css',
        extra={'rel': 'stylesheet/less'}
    )
    # JavaScript Bundle
    js_bundle = Bundle(
        'src/js/cookie.js',
        'src/js/paper_basic.js',
        'src/js/papers.js',
        filters='jsmin',
        output='dist/js/papers.min.js'
    )

    # Register assets
    assets.register('less_all', less_bundle)
    assets.register('js_all', js_bundle)
    # Build assets in development mode
    if app.config['DEBUG']:
        less_bundle.build(force=True)
        js_bundle.build()

def compile_settings_assets(app):
    """Compile asssets explicetely for settings page."""
    assets = Environment(app)
    Environment.auto_build = True
    Environment.debug = False
    # Stylesheets Bundle
    less_bundle = Bundle(
        'src/less/layout.less',
        'src/less/settings.less',
        filters='less,cssmin',
        output='dist/css/settings.css',
        extra={'rel': 'stylesheet/less'}
    )
    # JavaScript Bundle
    js_bundle = Bundle(
        'src/js/allCatsArray.js',
        'src/js/cookie.js',
        'src/js/settings.js',
        'src/js/jquery.wheelcolorpicker.js',
        filters='jsmin',
        output='dist/js/settings.min.js'
    )

    # Register assets
    assets.register('less_all', less_bundle)
    assets.register('js_all', js_bundle)
    # Build assets in development mode
    if app.config['DEBUG']:
        less_bundle.build(force=True)
        js_bundle.build()

def compile_bookshelf_assets(app):
    """Compile boockshelf assets."""
    assets = Environment(app)
    Environment.auto_build = True
    Environment.debug = False

    # JavaScript Bundle
    js_bundle = Bundle(
        'src/js/allCatsArray.js',
        'src/js/cookie.js',
        'src/js/paper_basic.js',
        'src/js/bookshelf.js',
        filters='jsmin',
        output='dist/js/bookshelf.min.js'
    )

    assets.register('js_all', js_bundle)
    # Build assets in development mode
    if app.config['DEBUG']:
        js_bundle.build()



def compile_assets(app):
    """Compile all app assets."""
    compile_layout_assets(app)
    compile_paper_assets(app)
    compile_settings_assets(app)
    compile_bookshelf_assets(app)
