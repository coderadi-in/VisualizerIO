'''coderadi'''

# ? Importing libraries
from flask import Flask, redirect, url_for, flash
from dotenv import load_dotenv
import os
from extensions import *

# ? Importing routers
from routers.router import router
from routers.api import api
from routers.auth import auth
from routers.project import project
from routers.team import team
from routers.docs import docs
from routers.app import app
from routers.admin import admin

# ! Loading environment variables
load_dotenv('.venv/vars.env')

# ! Building server
server = Flask(__name__)
server.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
server.config['SQLALCHEMY_TRACK_MODIFIACTIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFIACTIONS')
server.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
server.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
server.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
server.config['MAIL_USE_TLS'] = os.getenv('TLS')
server.config['MAIL_USE_SSL'] = os.getenv('SSL')
server.config['MAIL_USERNAME'] = os.getenv('ADMIN_EMAIL')
server.config['MAIL_PASSWORD'] = os.getenv('ADMIN_PASS')
server.config['MAIL_DEFAULT_SENDER'] = os.getenv('ADMIN_EMAIL')
server.config['SCHEDULER_API_ENABLED'] = os.getenv('SCHEDULER_API_ENABLED')
server.wsgi_app = ProxyFix(server.wsgi_app, x_proto=1, x_host=1)

# ! Binding extensions
bind_extensions(server)
init_oauth(server)
worker.start()

# ! Binding routers
server.register_blueprint(router)
server.register_blueprint(api)
server.register_blueprint(auth)
server.register_blueprint(project)
server.register_blueprint(team)
server.register_blueprint(docs)
server.register_blueprint(app)
server.register_blueprint(admin)

# * Change passwords scheduler
@worker.task('interval', id="Change password", days=3)
def change_password():
    with server.app_context():
        for setting in UserSettings.query.filter(
            UserSettings.password_rotation == True
        ).all():
            set_random_pass(setting.user_id)

# * Delete app notifications
@worker.task('interval', id="Delete app notifications", days=15)
def delete_app_notifications():
    with server.app_context():
        for notification in Notification.query.filter_by(recv=0).all():
            db.session.delete(notification)
            db.session.commit()

# * 401 error handler
@server.errorhandler(401)
def unauthorized_(error):
    flash("Login required", "warning")
    return redirect(url_for('auth.signup'))