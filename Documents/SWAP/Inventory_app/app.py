import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <h1>🎉 Inventory App is Live!</h1>
    <p>Successfully deployed and running on production server.</p>
    <p>Ready for your inventory management system!</p>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)