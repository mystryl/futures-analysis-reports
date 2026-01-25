"""品种搜索 API"""
from flask import Blueprint, request, jsonify
import akshare as ak
from api.utils import handle_akshare_error
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# 获取当前日期，格式为 YYYYMMDD
CURRENT_DATE = datetime.now().strftime("%Y%m%d")

symbols_bp = Blueprint('symbols', __name__)


def get_exchange_from_symbol(symbol):
    """根据合约代码判断交易所"""
    symbol_upper = symbol.upper()

    # 中国金融期货交易所
    if symbol_upper.startswith(('IF', 'IH', 'IC', 'IM', 'TS', 'TF', 'T', 'TL')):
        return 'CFFEX'

    # 上海期货交易所
    shfe_symbols = ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'WR',
                    'BU', 'HC', 'FU', 'RU', 'SP', 'SS', 'AO', 'BR']
    if any(symbol_upper.startswith(s) for s in shfe_symbols):
        return 'SHFE'

    # 上海国际能源交易中心
    ine_symbols = ['SC', 'NR', 'LU', 'BC', 'EC']
    if any(symbol_upper.startswith(s) for s in ine_symbols):
        return 'INE'

    # 郑州商品交易所
    czce_symbols = ['CF', 'SR', 'TA', 'WH', 'JR', 'LR', 'RI', 'PM', 'RM', 'RS', 'OI',
                    'MA', 'FG', 'ZC', 'CY', 'AP', 'CJ', 'UR', 'SA', 'PF', 'PK', 'SH', 'PX']
    if any(symbol_upper.startswith(s) for s in czce_symbols):
        return 'CZCE'

    # 大连商品交易所
    dce_symbols = ['A', 'B', 'M', 'Y', 'P', 'C', 'CS', 'L', 'V', 'PP', 'JD', 'J', 'JM',
                   'I', 'FB', 'BB', 'EG', 'RR', 'EB', 'PG', 'LH']
    if any(symbol_upper.startswith(s) for s in dce_symbols):
        return 'DCE'

    # 广州期货交易所
    gfex_symbols = ['SI', 'LC']
    if any(symbol_upper.startswith(s) for s in gfex_symbols):
        return 'GFEX'

    # 默认返回未知
    return 'UNKNOWN'


@symbols_bp.route('/symbols', methods=['GET'])
@handle_akshare_error
def search_symbols():
    """
    搜索期货品种
    参数: q (可选) - 搜索关键词
    返回: SymbolInfo[] 数组
    """
    query = request.args.get('q', '').strip()

    try:
        # 合并多个交易所的期货品种信息
        all_symbols = []

        # 获取上海期货交易所的合约信息
        try:
            df_shfe = ak.futures_contract_info_shfe(date=CURRENT_DATE)
            if not df_shfe.empty:
                for _, row in df_shfe.iterrows():
                    contract = row.get('合约代码', '')
                    if contract:
                        # 提取品种代码（合约代码的前2-3位大写字母）
                        symbol_code = ''.join([c for c in contract if c.isalpha()]).upper()
                        all_symbols.append({
                            'ticker': symbol_code,
                            'name': contract,  # 使用合约代码作为名称
                            'shortName': symbol_code,
                            'exchange': 'SHFE',
                            'market': 'futures',
                            'priceCurrency': 'CNY',
                            'type': 'future'
                        })
        except Exception as e:
            logger.warning(f"Failed to fetch SHFE contract info: {e}")

        # 获取大连商品交易所的合约信息
        try:
            df_dce = ak.futures_contract_info_dce()
            if not df_dce.empty:
                for _, row in df_dce.iterrows():
                    variety = row.get('品种', '')
                    contract = row.get('合约代码', '')
                    if variety and contract:
                        all_symbols.append({
                            'ticker': variety.upper(),
                            'name': variety,
                            'shortName': variety.upper(),
                            'exchange': 'DCE',
                            'market': 'futures',
                            'priceCurrency': 'CNY',
                            'type': 'future'
                        })
        except Exception as e:
            logger.warning(f"Failed to fetch DCE contract info: {e}")

        # 获取郑州商品交易所的合约信息
        try:
            df_czce = ak.futures_contract_info_czce(date=CURRENT_DATE)
            if not df_czce.empty:
                for _, row in df_czce.iterrows():
                    product_code = row.get('产品代码', '')
                    product_name = row.get('产品名称', '')
                    if product_code and product_name:
                        # 去掉"期货"等后缀
                        name = product_name.replace('期货', '').replace('连续', '').strip()
                        all_symbols.append({
                            'ticker': product_code.upper(),
                            'name': name,
                            'shortName': product_code.upper(),
                            'exchange': 'CZCE',
                            'market': 'futures',
                            'priceCurrency': 'CNY',
                            'type': 'future'
                        })
        except Exception as e:
            logger.warning(f"Failed to fetch CZCE contract info: {e}")

        # 获取中国金融期货交易所的合约信息
        try:
            df_cffex = ak.futures_contract_info_cffex(date=CURRENT_DATE)
            if not df_cffex.empty:
                for _, row in df_cffex.iterrows():
                    variety = row.get('品种', '')
                    contract = row.get('合约代码', '')
                    if variety and contract:
                        all_symbols.append({
                            'ticker': variety.upper(),
                            'name': variety,
                            'shortName': variety.upper(),
                            'exchange': 'CFFEX',
                            'market': 'futures',
                            'priceCurrency': 'CNY',
                            'type': 'future'
                        })
        except Exception as e:
            logger.warning(f"Failed to fetch CFFEX contract info: {e}")

        # 获取上海国际能源交易中心的合约信息
        try:
            df_ine = ak.futures_contract_info_ine(date=CURRENT_DATE)
            if not df_ine.empty:
                for _, row in df_ine.iterrows():
                    contract = row.get('合约代码', '')
                    if contract:
                        # 提取品种代码
                        symbol_code = ''.join([c for c in contract if c.isalpha()]).upper()
                        all_symbols.append({
                            'ticker': symbol_code,
                            'name': contract,
                            'shortName': symbol_code,
                            'exchange': 'INE',
                            'market': 'futures',
                            'priceCurrency': 'CNY',
                            'type': 'future'
                        })
        except Exception as e:
            logger.warning(f"Failed to fetch INE contract info: {e}")

        # 获取广州期货交易所的合约信息
        try:
            df_gfex = ak.futures_contract_info_gfex()
            if not df_gfex.empty:
                for _, row in df_gfex.iterrows():
                    variety = row.get('品种', '')
                    contract = row.get('合约代码', '')
                    if variety and contract:
                        all_symbols.append({
                            'ticker': variety.upper(),
                            'name': variety,
                            'shortName': variety.upper(),
                            'exchange': 'GFEX',
                            'market': 'futures',
                            'priceCurrency': 'CNY',
                            'type': 'future'
                        })
        except Exception as e:
            logger.warning(f"Failed to fetch GFEX contract info: {e}")

        # 去重
        seen = set()
        unique_symbols = []
        for symbol in all_symbols:
            key = (symbol['ticker'], symbol['exchange'])
            if key not in seen:
                seen.add(key)
                unique_symbols.append(symbol)

        # 如果有搜索关键词，过滤结果
        if query:
            filtered_symbols = []
            for symbol in unique_symbols:
                ticker = symbol.get('ticker', '').lower()
                name = symbol.get('name', '').lower()
                if query.lower() in ticker or query.lower() in name:
                    filtered_symbols.append(symbol)
            return jsonify(filtered_symbols)

        return jsonify(unique_symbols)

    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        # 如果所有方法都失败，返回一些常用的期货品种作为fallback
        fallback_symbols = [
            {'ticker': 'RB', 'name': '螺纹钢', 'shortName': 'RB', 'exchange': 'SHFE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'CU', 'name': '铜', 'shortName': 'CU', 'exchange': 'SHFE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'AL', 'name': '铝', 'shortName': 'AL', 'exchange': 'SHFE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'AU', 'name': '黄金', 'shortName': 'AU', 'exchange': 'SHFE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'M', 'name': '豆粕', 'shortName': 'M', 'exchange': 'DCE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'Y', 'name': '豆油', 'shortName': 'Y', 'exchange': 'DCE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'CF', 'name': '棉花', 'shortName': 'CF', 'exchange': 'CZCE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'SR', 'name': '白糖', 'shortName': 'SR', 'exchange': 'CZCE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'IF', 'name': '沪深300指数', 'shortName': 'IF', 'exchange': 'CFFEX', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
            {'ticker': 'SC', 'name': '原油', 'shortName': 'SC', 'exchange': 'INE', 'market': 'futures', 'priceCurrency': 'CNY', 'type': 'future'},
        ]

        if query:
            filtered_fallback = [s for s in fallback_symbols
                               if query.lower() in s['ticker'].lower() or query.lower() in s['name'].lower()]
            return jsonify(filtered_fallback)

        return jsonify(fallback_symbols)
