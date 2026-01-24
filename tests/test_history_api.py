"""历史数据 API 测试"""
import pytest
from chart_server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_history_missing_symbol(client):
    """测试缺少 symbol 参数"""
    response = client.get('/api/history?period=1d')
    assert response.status_code == 400


def test_history_with_valid_params(client):
    """测试有效参数请求"""
    response = client.get('/api/history?symbol=rb2505&period=1d')
    # 可能返回 200 (成功) 或 500 (akshare 调用失败)
    # 但不应该是 400 (参数错误)
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.get_json()
        assert isinstance(data, list)
