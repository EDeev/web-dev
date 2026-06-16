import os
import sys
sys.dont_write_bytecode = True
from app import app, init_db

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        if not os.path.exists(app.config['DATABASE']):
            init_db()
    app.run(debug=True)
