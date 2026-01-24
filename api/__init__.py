"""API 蓝图模块"""
from flask import Blueprint
from api.utils import handle_api_error, ApiError

# 导入蓝图
from api.symbols import symbols_bp
from api.history import history_bp

# 注册错误处理器
def register_blueprints(app):
    """注册所有蓝图到 Flask 应用"""
    app.register_blueprint(symbols_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api')

    # 注册全局错误处理器
    app.register_error_handler(ApiError, handle_api_error)
