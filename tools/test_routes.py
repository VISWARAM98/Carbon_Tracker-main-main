import sys
import os
# ensure project root is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create a test user if not exists
    email = 'test@example.com'
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email)
        user.set_password('test123')
        db.session.add(user)
        db.session.commit()
        print('Created test user')
    else:
        print('Test user exists')

# Use test client to login and fetch dashboard_home
with app.test_client() as c:
    # Login
    resp = c.post('/login', data={'email': 'test@example.com', 'password': 'test123'}, follow_redirects=True)
    print('Login status:', resp.status_code)
    # After login, attempt to access dashboard_home
    resp2 = c.get('/dashboard_home')
    print('dashboard_home status:', resp2.status_code)
    # Show start of response data
    data = resp2.get_data(as_text=True)
    print('--- response start ---')
    print(data[:2000])
    print('--- response end ---')
