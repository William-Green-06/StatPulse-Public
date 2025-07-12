from flask import Flask
from app.routes.api.upcoming import upcoming_api
from app.routes.api.predict import predict_api
from app.routes.api.fighter_search import fighter_search_api
from app.routes.home import home_bp
from app.routes.predict import predict_bp
import os

def create_app():
    app = Flask(__name__)
    # Database credentials
    app.config['DB_NAME'] = os.getenv('DB_NAME')
    app.config['DB_USER'] = os.getenv('DB_USER')
    app.config['DB_PASS'] = os.getenv('DB_PASS')
    app.config['DB_HOST'] = os.getenv('DB_HOST', 'localhost')
    app.config['DB_PORT'] = int(os.getenv('DB_PORT', 5432))
    # Register API blueprints
    app.register_blueprint(upcoming_api, url_prefix='/api')
    app.register_blueprint(predict_api, url_prefix='/api')
    app.register_blueprint(fighter_search_api, url_prefix='/api')
    app.register_blueprint(home_bp)
    app.register_blueprint(predict_bp)
    return app