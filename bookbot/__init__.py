from enum import IntEnum
import os

from flask import Flask

# noinspection PyTypeChecker
Weekdays = IntEnum(
    'Weekdays', 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday')


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'bookbot.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    @app.template_filter()
    def get_day_string(day) -> str:
        # noinspection PyCallingNonCallable
        return Weekdays(int(day)+1).name

    # register the database commands
    from bookbot import db
    db.init_app(app)

    # apply the blueprints to the app
    from bookbot import auth, bookbot
    app.register_blueprint(auth.bp)
    app.register_blueprint(bookbot.bp)

    app.add_url_rule('/', endpoint='index')

    return app
