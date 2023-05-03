import os
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from config import Config
from flask import Flask
from flask.helpers import get_root_path
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_required
from flask_mail import Mail
from flask_bootstrap import Bootstrap

# sets a database and its migration
db = SQLAlchemy()
migrate = Migrate()
# sets a logging service
login = LoginManager()
# to forces users to login, it needs to know
# what is the view function that handles logins
login.login_view = 'auth.login'
# send emails to users
mail = Mail()
# css framework
bootstrap = Bootstrap()


def create_app(config_class=Config):
    # create a flask instance
    app = Flask(__name__)

    # call configs values from Config class
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # the code above creates a SMTPHandler instance to only reports errors
    # and finally attaches it to the app.logger object from Flask
    if not app.debug:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or \
                    app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'],
                          app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='FinData Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

            # make log files
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/findata.log',
                                               maxBytes=10240,
                                               backupCount=10)
            # includes timestamp, logging level, message and
            # source file and line number from where the log entry originated
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('FinData startup')

    return app

# imports files that uses server
# its stays at bottom to avoid circular imports
from app import models
