from flask import Flask
from app.routes.api.upcoming import upcoming_api
from app.routes.api.predict import predict_api
from app.routes.api.fighter_search import fighter_search_api
from app.routes.api.head_to_head import head_to_head_api
from app.routes.api.fighter_data import fighter_data_api
from app.routes.api.run_command import run_command_api
from app.routes.home import home_bp
from app.routes.predict import predict_bp
from app.routes.admin import admin_bp
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')

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
    app.register_blueprint(head_to_head_api, url_prefix='/api')
    app.register_blueprint(fighter_data_api, url_prefix='/api')
    app.register_blueprint(run_command_api, url_prefix='/api')
    app.register_blueprint(home_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(admin_bp)
    
    return app