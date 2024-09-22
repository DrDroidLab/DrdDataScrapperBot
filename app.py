import os
from flask import Flask
from flask_migrate import Migrate
from persistance.models import db
from routes.app_router import app_blueprint
from routes.google_router import google_blueprint
from routes.slack_router import slack_blueprint

class Config:
    SECRET_KEY = os.getenv('FLASK_APP_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = f'postgresql://{os.getenv("PG_DB_USERNAME")}:{os.getenv("PG_DB_PASSWORD")}@{os.getenv("PG_DB_HOSTNAME")}/{os.getenv("PG_DB_NAME")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    Migrate(app, db)

    # Register all blueprints
    app.register_blueprint(app_blueprint, url_prefix='/app')
    app.register_blueprint(slack_blueprint, url_prefix='/slack')
    app.register_blueprint(google_blueprint, url_prefix='/google')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=False)
