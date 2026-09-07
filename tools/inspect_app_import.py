import sys, os, traceback
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import app
    print('Imported app module successfully')
    print('attrs:', [a for a in dir(app) if a in ('app','db','User','Emission')])
except Exception as e:
    print('Import failed:')
    traceback.print_exc()
