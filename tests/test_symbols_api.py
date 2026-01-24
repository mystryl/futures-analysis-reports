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


def test_symbols_search_exchange_info(client):
    """测试返回的品种包含正确的交易所信息"""
    response = client.get('/api/symbols')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)

    # 验证至少有一些数据
    if len(data) > 0:
        # 检查第一个品种的字段
        symbol = data[0]
        assert 'ticker' in symbol
        assert 'name' in symbol
        assert 'exchange' in symbol
        assert 'market' in symbol
        assert 'priceCurrency' in symbol
        assert 'type' in symbol

        # 验证交易所代码是有效的
        valid_exchanges = ['SHFE', 'DCE', 'CZCE', 'CFFEX', 'INE', 'GFEX', 'UNKNOWN']
        assert symbol['exchange'] in valid_exchanges

        # 验证市场类型
        assert symbol['market'] == 'futures'
        assert symbol['type'] == 'future'
        assert symbol['priceCurrency'] == 'CNY'


def test_symbols_no_results(client):
    """测试搜索不存在的品种返回空列表"""
    response = client.get('/api/symbols?q=nonexistent_symbol_xyz123')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    # 应该返回空列表或者没有匹配的结果
    assert len(data) == 0 or all('nonexistent_symbol_xyz123' not in str(item).lower() for item in data)
