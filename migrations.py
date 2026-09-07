from app import app, db
from flask_migrate import upgrade, migrate, init, stamp

def init_db():
    with app.app_context():
        # Initialize migrations
        init()
        # Create a stamp for the current database state
        stamp()
        # Create initial migration
        migrate()
        # Apply the migration
        upgrade()

if __name__ == '__main__':
    init_db()