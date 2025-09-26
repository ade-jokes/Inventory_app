import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Inventory App is Running!</h1><p>Deployment successful on Railway.</p>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)