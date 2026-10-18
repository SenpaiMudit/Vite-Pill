import os
import sys

# Ensure root directory and vite_pill package are on sys.path
function_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(function_dir, '..', '..'))
vite_pill_dir = os.path.join(root_dir, 'vite_pill')

for p in [root_dir, vite_pill_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import serverless_wsgi
from vite_pill.app import app


def handler(event, context):
    """AWS Lambda / Netlify Serverless handler for Flask application."""
    return serverless_wsgi.handle_request(app, event, context)
