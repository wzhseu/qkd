from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    # 创建Flask应用实例
    app = Flask(__name__, 
                static_folder='../frontend/dist',
                template_folder='../frontend/dist')
    
    # 配置数据库
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'gateway_data', 'quantum_gateway.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'quantum-gateway-secret-key-2024'
    
    # 启用CORS
    CORS(app)
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        # 导入模型
        from gateway_app import models
        # 创建所有表
        db.create_all()
        print(f"[Database] Initialized at: {db_path}")
    
    return app
