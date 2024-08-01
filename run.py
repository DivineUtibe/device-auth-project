from app import create_app, db
from flask_migrate import Migrate
import os

app = create_app()
migrate = Migrate(app, db)

def initialize_database():
    with app.app_context():
        if not os.path.exists('instance/data.db'):
            # Only create tables if the database does not exist
            db.create_all()
            print("Database tables created successfully.")
        else:
            print("Database already exists. Run migrations to update the schema.")

if __name__ == '__main__':
    initialize_database()  # Run this to initialize the database
    app.run(debug=True)
