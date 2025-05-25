from flask import Flask
from flask_session import Session
from flask_cors import CORS
import os
from blueprint.order import order
from blueprint.session import auth

# 初始化 Flask 應用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', "your_secret_key_here")
app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('PERMANENT_SESSION_LIFETIME', 3600))
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'filesystem')
app.config['SESSION_COOKIE_NAME'] = os.getenv('SESSION_COOKIE_NAME', 'session')
app.config['SESSION_COOKIE_HTTPONLY'] = True
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)  # 允許跨域請求
Session(app)

# router
app.register_blueprint(order, url_prefix='/')
app.register_blueprint(auth, url_prefix='/auth')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)