from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Ensure the instance folder exists
    instance_path = os.path.join(os.getcwd(), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    
    # Configure the SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "data.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Set the secret key
    app.config['SECRET_KEY'] = '5ccb1761f0250a6a3325df84174e94be'  # Replace with your actual secret key
    
    db.init_app(app)
    migrate.init_app(app, db)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        # Create tables only if the database does not exist
        if not os.path.exists(os.path.join(instance_path, 'data.db')):
            db.create_all()

    return app
