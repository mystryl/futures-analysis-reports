"""历史 K 线数据 API"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import pandas as pd
from services.cache import cache
from api.utils import handle_akshare_error, validate_required, ApiError
import logging

logger = logging.getLogger(__name__)

history_bp = Blueprint('history', __name__)


def _convert_to_kline_format(df):
    """转换 DataFrame 为 klinecharts 格式"""
    kline_data = []
    for _, row in df.iterrows():
        item = {
            'timestamp': int(row['timestamp']),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
            'volume': float(row['volume'])
        }
        kline_data.append(item)
    return kline_data


@history_bp.route('/history', methods=['GET'])
@handle_akshare_error
def get_history():
    """
    获取历史 K 线数据
    参数:
        - symbol: 品种代码 (如 "rb2505")
        - period: 周期 ("5m", "15m", "1h", "1d")
        - from: 开始时间戳 (毫秒)
        - to: 结束时间戳 (毫秒)
    返回: KLineData[] 数组
    """
    params = request.args

    # 参数验证
    validate_required(params, ['symbol'])

    symbol = params.get('symbol')
    period = params.get('period', '1d')
    from_ts = int(params.get('from', 0))
    to_ts = int(params.get('to', int(datetime.now().timestamp() * 1000)))

    # 周期映射
    period_map = {
        '5m': '5',
        '15m': '15',
        '1h': '60',
        '1d': 'daily'
    }

    if period not in period_map:
        raise ApiError(f"不支持的周期: {period}，支持的周期: {', '.join(period_map.keys())}", 400)

    # 尝试从缓存获取
    cache_key_params = {
        'symbol': symbol,
        'period': period,
        'from': from_ts,
        'to': to_ts
    }
    cached = cache.get('history', **cache_key_params)
    if cached:
        return jsonify(cached)

    # 调用 akshare 获取数据
    import akshare as ak

    if period == '1d':
        # 日线数据使用 futures_zh_daily_sina
        # symbol 需要是品种代码加0，如 RB0
        df = ak.futures_zh_daily_sina(symbol=symbol)
    else:
        # 分钟数据使用 futures_zh_minute_sina
        ak_period = period_map[period]
        df = ak.futures_zh_minute_sina(symbol=symbol, period=ak_period)

    # 数据处理
    if period == '1d':
        # 日线数据列名是 'date'
        df['timestamp'] = pd.to_datetime(df['date'])
    else:
        # 分钟数据列名是 'datetime'
        df['timestamp'] = pd.to_datetime(df['datetime'])

    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    # 转换时间戳
    df['timestamp'] = df['timestamp'].apply(lambda x: int(x.timestamp() * 1000))

    # 过滤时间范围
    if from_ts > 0:
        df = df[df['timestamp'] >= from_ts]
    if to_ts > 0:
        df = df[df['timestamp'] <= to_ts]

    # 转换格式
    kline_data = _convert_to_kline_format(df)

    # 写入缓存
    cache.set('history', kline_data, **cache_key_params)

    return jsonify(kline_data)
