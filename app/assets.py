from flask_assets import Environment, Bundle

def compile_layout_assets(app):
    """Compile asssets explicetely for layout."""
    assets = Environment(app)
    Environment.auto_build = True
    Environment.debug = False
    # Stylesheets Bundle
    less_bundle = Bundle(
        'src/less/layout.less',
        filters='less,cssmin',
        output='dist/css/layout.css',
        extra={'rel': 'stylesheet/less'}
    )
    # JavaScript Bundle
    js_bundle = Bundle(
        'src/js/alert.js',
        filters='jsmin',
        output='dist/js/main.min.js'
    )
    # Register assets
    assets.register('less_all', less_bundle)
    assets.register('js_all', js_bundle)
    # Build assets in development mode
    if app.config['DEBUG']:
        less_bundle.build(force=True)
        js_bundle.build()

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
        'src/js/alert.js',
        'src/js/cookie.js',
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



def compile_assets(app):
    """Compile all app assets."""
    compile_layout_assets(app)
    compile_paper_assets(app)
