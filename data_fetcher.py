"""
期货数据获取模块

使用 akshare 获取期货历史数据，支持多周期分析
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FuturesDataFetcher:
    """期货数据获取器"""

    def __init__(self):
        self.akshare = None
        self._init_akshare()

    def _init_akshare(self):
        """初始化 akshare"""
        try:
            import akshare as ak
            self.akshare = ak
            logger.info("akshare 初始化成功")
        except ImportError:
            raise ImportError("请先安装 akshare: pip install akshare")

    def get_future_data(
        self,
        symbol: str = "rb888",
        period: str = "day",
        days: int = 120,
        adjust: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取期货历史数据

        Args:
            symbol: 期货品种代码，如 "rb888" (螺纹钢主力连续)
            period: 周期，支持 day/60min/15min/5min
            days: 获取天数（用于日线，分钟线会自动计算条数）
            adjust: 复权类型

        Returns:
            标准化的 DataFrame，包含列: date, open, high, low, close, volume
        """
        if not self.akshare:
            raise RuntimeError("akshare 未初始化")

        try:
            # 转换期货品种代码为新浪格式
            sina_symbol = self._convert_to_sina_symbol(symbol)

            logger.info(f"正在获取 {symbol} 期货数据，周期: {period}")

            if period == "day":
                df = self._get_daily_data(sina_symbol, symbol, days)
            elif period in ["60min", "60m", "1h"]:
                df = self._get_minute_data(sina_symbol, symbol, "60", days)
            elif period in ["15min", "15m"]:
                df = self._get_minute_data(sina_symbol, symbol, "15", days)
            elif period in ["5min", "5m"]:
                df = self._get_minute_data(sina_symbol, symbol, "5", days)
            else:
                raise ValueError(f"不支持的周期: {period}")

            if df is None or df.empty:
                logger.error(f"获取 {symbol} 数据失败")
                return pd.DataFrame()

            # 标准化列名
            df = self._standardize_columns(df)

            # 过滤数据范围
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)

            logger.info(f"成功获取 {len(df)} 条 {symbol} {period} 数据")
            return df

        except Exception as e:
            logger.error(f"获取 {symbol} 数据失败: {e}")
            raise

    def _get_daily_data(self, sina_symbol: str, symbol: str, days: int) -> pd.DataFrame:
        """获取日线数据"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days * 2)

        df = self.akshare.futures_zh_daily_sina(symbol=sina_symbol)

        if df is None or df.empty:
            # 尝试东方财富接口
            logger.warning("新浪接口失败，尝试东方财富接口...")
            try:
                em_symbol = self._convert_to_em_symbol(symbol)
                df = self.akshare.futures_hist_em(
                    symbol=em_symbol,
                    period="daily",
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d")
                )
            except Exception as e:
                logger.error(f"备用接口也失败: {e}")
                return pd.DataFrame()

        return df

    def _get_minute_data(self, sina_symbol: str, symbol: str, period: str, days: int) -> pd.DataFrame:
        """获取分钟线数据"""
        try:
            df = self.akshare.futures_zh_minute_sina(symbol=sina_symbol, period=period)

            if df is None or df.empty:
                logger.error(f"获取 {period} 分钟数据失败")
                return pd.DataFrame()

            # 根据天数过滤数据
            # 估算需要的数据条数
            if period == "5":
                # 每天5分钟约54条（日盘39条 + 夜盘15条）
                limit = days * 54
            elif period == "15":
                # 每天15分钟约18条
                limit = days * 18
            elif period == "60":
                # 每天60分钟约4-5条
                limit = days * 5
            else:
                limit = days * 50

            return df.tail(limit)

        except Exception as e:
            logger.error(f"获取分钟数据失败: {e}")
            return pd.DataFrame()

    def get_multi_period_data(
        self,
        symbol: str = "rb888",
        days: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """
        获取多周期数据

        Args:
            symbol: 期货品种代码
            days: 获取天数

        Returns:
            包含多个周期数据的字典
        """
        periods = {
            '5min': '5min',
            '15min': '15min',
            '60min': '60min',
            'day': 'day'
        }

        result = {}
        for key, period in periods.items():
            try:
                df = self.get_future_data(symbol=symbol, period=period, days=days)
                if not df.empty:
                    result[key] = df
                else:
                    logger.warning(f"获取 {period} 数据失败")
            except Exception as e:
                logger.error(f"获取 {period} 数据出错: {e}")

        return result

    def _convert_to_sina_symbol(self, symbol: str) -> str:
        """将期货品种代码转换为新浪格式"""
        symbol = symbol.upper()

        code_mapping = {
            'RB888': 'RB0',   # 螺纹钢
            'HC888': 'HC0',   # 热卷
            'AU888': 'AU0',   # 黄金
            'AG888': 'AG0',   # 白银
            'CU888': 'CU0',   # 铜
            'AL888': 'AL0',   # 铝
            'ZN888': 'ZN0',   # 锌
            'NI888': 'NI0',   # 镍
            'SN888': 'SN0',   # 锡
            'SC888': 'SC0',   # 原油
            'FU888': 'FU0',   # 燃料油
            'A888': 'A0',     # 豆一
            'M888': 'M0',     # 豆粕
            'Y888': 'Y0',     # 豆油
            'P888': 'P0',     # 棕榈油
            'C888': 'C0',     # 玉米
            'CS888': 'CS0',   # 玉米淀粉
            'JD888': 'JD0',   # 鸡蛋
            'PP888': 'PP0',   # PP
            'L888': 'L0',     # L
            'V888': 'V0',     # PVC
            'EG888': 'EG0',   # 乙二醇
            'MA888': 'MA0',   # 甲醇
            'TA888': 'TA0',   # PTA
            'RU888': 'RU0',   # 橡胶
            'IF888': 'IF0',   # 沪深300
            'IH888': 'IH0',   # 上证50
            'IC888': 'IC0',   # 中证500
        }

        if symbol in code_mapping:
            return code_mapping[symbol]

        if len(symbol) == 6 and symbol.endswith('888'):
            base_code = symbol[:3]
            return f"{base_code}0"

        return symbol

    def _convert_to_em_symbol(self, symbol: str) -> str:
        """将期货品种代码转换为东方财富格式"""
        name_mapping = {
            'RB888': '螺纹钢主连',
            'HC888': '热卷主连',
            'AU888': '沪金主连',
            'AG888': '沪银主连',
            'CU888': '沪铜主连',
            'AL888': '沪铝主连',
            'ZN888': '沪锌主连',
            'NI888': '沪镍主连',
            'SN888': '沪锡主连',
            'SC888': '原油主连',
            'FU888': '燃料油主连',
            'A888': '豆一主连',
            'M888': '豆粕主连',
            'Y888': '豆油主连',
            'P888': '棕榈油主连',
            'C888': '玉米主连',
            'JD888': '鸡蛋主连',
            'PP888': 'PP主连',
            'L888': 'L主连',
            'V888': 'PVC主连',
            'EG888': '乙二醇主连',
            'MA888': '甲醇主连',
            'TA888': 'PTA主连',
            'RU888': '橡胶主连',
            'IF888': '沪深300主连',
            'IH888': '上证50主连',
            'IC888': '中证500主连',
        }

        symbol_upper = symbol.upper()
        return name_mapping.get(symbol_upper, symbol)

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名为统一格式"""
        if df.empty:
            return df

        column_mapping = {
            '日期': 'date', '时间': 'date', 'time': 'date', 'Day': 'date',
            'day': 'date', 'datetime': 'date',
            '开盘': 'open', 'Open': 'open', 'open': 'open',
            '最高': 'high', 'High': 'high', 'high': 'high',
            '最低': 'low', 'Low': 'low', 'low': 'low',
            '收盘': 'close', 'Close': 'close', 'close': 'close',
            '成交量': 'volume', 'Volume': 'volume', 'volume': 'volume',
            'vol': 'volume', '持仓量': 'volume',
            '成交额': 'amount', 'Amount': 'amount', 'amount': 'amount',
            'turnover': 'amount', '持仓额': 'amount',
        }

        df = df.rename(columns=column_mapping)

        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"数据缺少必需列: {missing_columns}, 现有列: {list(df.columns)}")

        if 'date' not in df.columns:
            df = df.reset_index()
            df = df.rename(columns={'index': 'date'})

        result_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        if 'amount' in df.columns:
            result_columns.append('amount')

        df = df[result_columns]

        return df


def fetch_future_data(symbol: str = "rb888", period: str = "day", days: int = 120) -> pd.DataFrame:
    """快捷函数：获取期货数据"""
    fetcher = FuturesDataFetcher()
    return fetcher.get_future_data(symbol=symbol, period=period, days=days)


if __name__ == "__main__":
    # 测试数据获取
    logging.basicConfig(level=logging.INFO)

    # 测试多周期获取
    fetcher = FuturesDataFetcher()

    print("\n=== 测试多周期数据获取 ===\n")

    multi_data = fetcher.get_multi_period_data("rb888", days=10)

    for period, df in multi_data.items():
        print(f"{period}: {len(df)} 条数据")
        print(df.head(2))
        print()
