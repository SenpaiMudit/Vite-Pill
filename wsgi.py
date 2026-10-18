import os
import sys

# Ensure vite_pill module and directory are discoverable
current_dir = os.path.dirname(os.path.abspath(__file__))
vite_pill_dir = os.path.join(current_dir, 'vite_pill')
if vite_pill_dir not in sys.path:
    sys.path.insert(0, vite_pill_dir)

from vite_pill.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
