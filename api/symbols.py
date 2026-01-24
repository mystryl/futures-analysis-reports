"""品种搜索 API"""
from flask import Blueprint, request, jsonify
import akshare as ak
from api.utils import handle_akshare_error

symbols_bp = Blueprint('symbols', __name__)


@symbols_bp.route('/symbols', methods=['GET'])
@handle_akshare_error
def search_symbols():
    """
    搜索期货品种
    参数: q (可选) - 搜索关键词
    返回: SymbolInfo[] 数组
    """
    query = request.args.get('q', '').strip()

    # 使用 akshare 获取期货品种列表
    try:
        df = ak.futures_sina_list(sort="symbol")

        symbols = []
        for _, row in df.iterrows():
            symbol_str = str(row.get('symbol', ''))
            name_str = str(row.get('name', ''))

            # 如果有搜索关键词，过滤结果
            if query and query.lower() not in symbol_str.lower() and query.lower() not in name_str.lower():
                continue

            symbols.append({
                'ticker': symbol_str,
                'name': name_str,
                'shortName': symbol_str,
                'exchange': 'SHFE',  # 默认交易所，实际应根据品种判断
                'market': 'futures',
                'priceCurrency': 'CNY',
                'type': 'future'
            })

        return jsonify(symbols)

    except Exception as e:
        # 如果 akshare 调用失败，返回空数组
        return jsonify([])
