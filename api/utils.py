"""API 工具模块 - 错误处理和参数验证"""
from functools import wraps
from flask import jsonify
import logging

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """API 错误基类"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload


def handle_api_error(error):
    """统一错误响应格式"""
    response = {
        'error': error.message,
        'code': error.status_code
    }
    if error.payload:
        response.update(error.payload)
    logger.error(f"API Error: {error.message}")
    return jsonify(response), error.status_code


def validate_required(params, required_fields):
    """验证必需参数"""
    missing = [f for f in required_fields if f not in params or not params[f]]
    if missing:
        raise ApiError(f"缺少必需参数: {', '.join(missing)}", 400)


def handle_akshare_error(func):
    """处理 akshare 调用异常"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiError:
            # ApiError 应该由 Flask 的错误处理器处理
            raise
        except ValueError as e:
            raise ApiError(f"数据格式错误: {str(e)}", 400)
        except ConnectionError as e:
            raise ApiError("网络连接失败，请检查网络", 503)
        except Exception as e:
            logger.exception("akshare 调用异常")
            raise ApiError(f"数据获取失败: {str(e)}", 500)
    return wrapper
