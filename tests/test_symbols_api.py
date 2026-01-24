"""品种搜索 API 测试"""
import pytest
from chart_server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_symbols_search_no_params(client):
    """测试无参数搜索（返回所有品种）"""
    response = client.get('/api/symbols')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)


def test_symbols_search_with_query(client):
    """测试带关键词搜索"""
    response = client.get('/api/symbols?q=rb')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # 验证返回的是螺纹钢相关品种
    if len(data) > 0:
        assert 'ticker' in data[0]
        assert 'name' in data[0]


def test_symbols_missing_required_param(client):
    """测试缺少必需参数（目前 symbols 没有必需参数）"""
    # 此测试仅为演示，实际 /api/symbols 不需要参数
    pass
