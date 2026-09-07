import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import traceback
try:
    import app
    from app import app as flask_app
except Exception:
    print('Failed to import app:')
    traceback.print_exc()
    raise

with flask_app.test_client() as c:
    # Try admin login (default admin at top of app.py)
    resp = c.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    print('POST /login status:', resp.status_code)
    print('POST /login redirected to:', resp.request.path)
    # Now request dashboard
    resp2 = c.get('/dashboard')
    print('/dashboard status:', resp2.status_code)
    data = resp2.get_data(as_text=True)
    print('--- /dashboard response start ---')
    print(data[:2000])
    print('--- /dashboard response end ---')
