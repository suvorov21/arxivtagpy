"""JS ans CSS bundles generator."""

from flask_assets import Environment, Bundle

def compile_assets(app):
    """Compile asssets."""
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
    vars_bundle.build(force=app.config['DEBUG'])
    vars_dark_bundle.build(force=app.config['DEBUG'])
    less_bundle.build(force=app.config['DEBUG'])

    paper_less_bundle = Bundle(
        'src/less/layout.less',
        'src/less/papers.less',
        filters='less,cssmin',
        output='dist/css/papers.css',
        extra={'rel': 'stylesheet/less'}
    )
    # JavaScript Bundle
    paper_js_bundle = Bundle(
        'src/js/cookie.js',
        'src/js/paper_basic.js',
        'src/js/papers.js',
        filters='jsmin',
        output='dist/js/papers.min.js'
    )

    # Register assets
    assets.register('paper_less', paper_less_bundle)
    assets.register('paper_js', paper_js_bundle)
    # Build assets in development mode
    paper_less_bundle.build(force=app.config['DEBUG'])
    paper_js_bundle.build()

    set_less_bundle = Bundle(
        'src/less/layout.less',
        'src/less/wheelcolorpicker.css',
        'src/less/settings.less',
        filters='less,cssmin',
        output='dist/css/settings.css',
        extra={'rel': 'stylesheet/less'}
    )
    # JavaScript Bundle
    set_js_bundle = Bundle(
        'src/js/allCatsArray.js',
        'src/js/cookie.js',
        'src/js/settings.js',
        'src/js/jquery.wheelcolorpicker.js',
        filters='jsmin',
        output='dist/js/settings.min.js'
    )

    # Register assets
    assets.register('settings_less', set_less_bundle)
    assets.register('settings_js', set_js_bundle)
    # Build assets in development mode
    set_less_bundle.build(force=app.config['DEBUG'])
    set_js_bundle.build()

    # JavaScript Bundle
    bookshelf_js_bundle = Bundle(
        'src/js/cookie.js',
        'src/js/paper_basic.js',
        'src/js/bookshelf.js',
        filters='jsmin',
        output='dist/js/bookshelf.min.js'
    )

    assets.register('bookshelf_js', bookshelf_js_bundle)
    # Build assets in development mode
    bookshelf_js_bundle.build()
