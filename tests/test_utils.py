"""API 工具测试"""
import pytest
import json
from flask import Flask
from api.utils import ApiError, validate_required, handle_api_error


def test_api_error_creation():
    """测试 API 错误创建"""
    error = ApiError("测试错误", 404)
    assert error.message == "测试错误"
    assert error.status_code == 404


def test_validate_required_pass():
    """测试参数验证通过"""
    params = {'symbol': 'rb2505', 'period': '1d'}
    # 不应该抛出异常
    validate_required(params, ['symbol', 'period'])


def test_validate_required_fail():
    """测试参数验证失败"""
    params = {'symbol': 'rb2505'}
    with pytest.raises(ApiError) as exc_info:
        validate_required(params, ['symbol', 'period'])

    assert '缺少必需参数' in exc_info.value.message


def test_handle_api_error():
    """测试错误处理响应"""
    # 创建 Flask 应用上下文
    app = Flask(__name__)

    with app.app_context():
        error = ApiError("未找到", 404)
        response, status = handle_api_error(error)

        assert status == 404
        # response 是 Flask Response 对象
        data = json.loads(response.get_data(as_text=True))
        assert data['error'] == "未找到"
        assert data['code'] == 404
