"""
技术指标计算模块

提供常用的技术分析指标计算，包括:
- 移动平均线 (MA, EMA)
- MACD
- RSI
- 布林带 (BOLL)
- KDJ
- ATR

参考 TradingAgents-CN 项目的实现
"""

from typing import Optional, Dict, List
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算类"""

    @staticmethod
    def ma(close: pd.Series, n: int, min_periods: int = 1) -> pd.Series:
        """
        计算移动平均线 (Moving Average)

        Args:
            close: 收盘价序列
            n: 周期
            min_periods: 最小周期数

        Returns:
            移动平均线序列
        """
        return close.rolling(window=int(n), min_periods=min_periods).mean()

    @staticmethod
    def ema(close: pd.Series, n: int) -> pd.Series:
        """
        计算指数移动平均线 (Exponential Moving Average)

        Args:
            close: 收盘价序列
            n: 周期

        Returns:
            指数移动平均线序列
        """
        return close.ewm(span=int(n), adjust=False).mean()

    @staticmethod
    def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """
        计算MACD指标 (Moving Average Convergence Divergence)

        Args:
            close: 收盘价序列
            fast: 快线周期，默认12
            slow: 慢线周期，默认26
            signal: 信号线周期，默认9

        Returns:
            包含 dif, dea, macd_hist 的 DataFrame
        """
        dif = TechnicalIndicators.ema(close, fast) - TechnicalIndicators.ema(close, slow)
        dea = dif.ewm(span=int(signal), adjust=False).mean()
        hist = dif - dea
        return pd.DataFrame({
            "dif": dif,
            "dea": dea,
            "macd_hist": hist
        })

    @staticmethod
    def rsi(close: pd.Series, n: int = 14, method: str = 'ema') -> pd.Series:
        """
        计算RSI指标 (Relative Strength Index)

        Args:
            close: 收盘价序列
            n: 周期，默认14
            method: 计算方法 ('ema', 'sma', 'china')

        Returns:
            RSI序列 (0-100)
        """
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        if method == 'ema':
            avg_gain = gain.ewm(alpha=1 / float(n), adjust=False).mean()
            avg_loss = loss.ewm(alpha=1 / float(n), adjust=False).mean()
        elif method == 'sma':
            avg_gain = gain.rolling(window=int(n), min_periods=1).mean()
            avg_loss = loss.rolling(window=int(n), min_periods=1).mean()
        elif method == 'china':
            avg_gain = gain.ewm(com=int(n) - 1, adjust=True).mean()
            avg_loss = loss.ewm(com=int(n) - 1, adjust=True).mean()
        else:
            raise ValueError(f"不支持的RSI计算方法: {method}")

        rs = avg_gain / (avg_loss.replace(0, np.nan))
        rsi_val = 100 - (100 / (1 + rs))
        return rsi_val

    @staticmethod
    def boll(close: pd.Series, n: int = 20, k: float = 2.0, min_periods: int = 1) -> pd.DataFrame:
        """
        计算布林带指标 (Bollinger Bands)

        Args:
            close: 收盘价序列
            n: 周期，默认20
            k: 标准差倍数，默认2.0
            min_periods: 最小周期数

        Returns:
            包含 boll_mid, boll_upper, boll_lower 的 DataFrame
        """
        mid = close.rolling(window=int(n), min_periods=min_periods).mean()
        std = close.rolling(window=int(n), min_periods=min_periods).std()
        upper = mid + k * std
        lower = mid - k * std
        return pd.DataFrame({
            "boll_mid": mid,
            "boll_upper": upper,
            "boll_lower": lower
        })

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
        """
        计算ATR指标 (Average True Range)

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            n: 周期，默认14

        Returns:
            ATR序列
        """
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low).abs(),
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ], axis=1).max(axis=1)
        return tr.rolling(window=int(n), min_periods=int(n)).mean()

    @staticmethod
    def kdj(high: pd.Series, low: pd.Series, close: pd.Series,
            n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """
        计算KDJ指标

        Args:
            high: 最高价序列
            low: 最低价序列
            close: 收盘价序列
            n: RSV周期，默认9
            m1: K值平滑周期，默认3
            m2: D值平滑周期，默认3

        Returns:
            包含 kdj_k, kdj_d, kdj_j 的 DataFrame
        """
        lowest_low = low.rolling(window=int(n), min_periods=int(n)).min()
        highest_high = high.rolling(window=int(n), min_periods=int(n)).max()
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.replace([np.inf, -np.inf], np.nan)

        # 按经典公式递推
        k = pd.Series(np.nan, index=close.index)
        d = pd.Series(np.nan, index=close.index)
        alpha_k = 1 / float(m1)
        alpha_d = 1 / float(m2)
        last_k = 50.0
        last_d = 50.0

        for i in range(len(close)):
            rv = rsv.iloc[i]
            if np.isnan(rv):
                k.iloc[i] = np.nan
                d.iloc[i] = np.nan
                continue
            curr_k = (1 - alpha_k) * last_k + alpha_k * rv
            curr_d = (1 - alpha_d) * last_d + alpha_d * curr_k
            k.iloc[i] = curr_k
            d.iloc[i] = curr_d
            last_k, last_d = curr_k, curr_d

        j = 3 * k - 2 * d
        return pd.DataFrame({
            "kdj_k": k,
            "kdj_d": d,
            "kdj_j": j
        })

    @staticmethod
    def add_all_indicators(df: pd.DataFrame, rsi_style: str = 'international') -> pd.DataFrame:
        """
        为DataFrame添加所有常用技术指标

        Args:
            df: 包含价格数据的DataFrame，需有 close, high, low 列
            rsi_style: RSI计算风格 ('international' 或 'china')

        Returns:
            添加了技术指标的DataFrame（原地修改）
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame缺少收盘价列: close")

        # 移动平均线
        df['ma5'] = TechnicalIndicators.ma(df['close'], 5, min_periods=1)
        df['ma10'] = TechnicalIndicators.ma(df['close'], 10, min_periods=1)
        df['ma20'] = TechnicalIndicators.ma(df['close'], 20, min_periods=1)
        df['ma60'] = TechnicalIndicators.ma(df['close'], 60, min_periods=1)

        # RSI指标
        if rsi_style == 'china':
            df['rsi6'] = TechnicalIndicators.rsi(df['close'], 6, method='china')
            df['rsi12'] = TechnicalIndicators.rsi(df['close'], 12, method='china')
            df['rsi24'] = TechnicalIndicators.rsi(df['close'], 24, method='china')
            df['rsi14'] = TechnicalIndicators.rsi(df['close'], 14, method='sma')
            df['rsi'] = df['rsi12']
        else:
            df['rsi'] = TechnicalIndicators.rsi(df['close'], 14, method='ema')

        # MACD
        macd_df = TechnicalIndicators.macd(df['close'], fast=12, slow=26, signal=9)
        df['macd_dif'] = macd_df['dif']
        df['macd_dea'] = macd_df['dea']
        df['macd'] = macd_df['macd_hist'] * 2

        # 布林带
        boll_df = TechnicalIndicators.boll(df['close'], n=20, k=2.0, min_periods=1)
        df['boll_mid'] = boll_df['boll_mid']
        df['boll_upper'] = boll_df['boll_upper']
        df['boll_lower'] = boll_df['boll_lower']

        # KDJ
        if all(col in df.columns for col in ['high', 'low', 'close']):
            kdj_df = TechnicalIndicators.kdj(df['high'], df['low'], df['close'])
            df['kdj_k'] = kdj_df['kdj_k']
            df['kdj_d'] = kdj_df['kdj_d']
            df['kdj_j'] = kdj_df['kdj_j']

        return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    快捷函数：为DataFrame添加所有技术指标

    Args:
        df: 包含 OHLCV 数据的 DataFrame

    Returns:
        添加了指标的 DataFrame
    """
    return TechnicalIndicators.add_all_indicators(df.copy())


# 导出信号检测函数
def detect_signals(df: pd.DataFrame) -> Dict[str, str]:
    """
    检测交易信号

    Args:
        df: 包含指标数据的 DataFrame

    Returns:
        信号字典
    """
    signals = {}

    if df.empty:
        return signals

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    # 均线信号
    if 'ma5' in df.columns and 'ma20' in df.columns:
        if pd.notna(last['ma5']) and pd.notna(last['ma20']):
            if last['ma5'] > last['ma20'] and prev['ma5'] <= prev['ma20']:
                signals['ma_cross'] = '金叉（MA5上穿MA20）'
            elif last['ma5'] < last['ma20'] and prev['ma5'] >= prev['ma20']:
                signals['ma_cross'] = '死叉（MA5下穿MA20）'

    # MACD信号
    if 'macd_dif' in df.columns and 'macd_dea' in df.columns:
        if pd.notna(last['macd_dif']) and pd.notna(last['macd_dea']):
            if last['macd_dif'] > last['macd_dea'] and prev['macd_dif'] <= prev['macd_dea']:
                signals['macd_cross'] = 'MACD金叉'
            elif last['macd_dif'] < last['macd_dea'] and prev['macd_dif'] >= prev['macd_dea']:
                signals['macd_cross'] = 'MACD死叉'

    # RSI信号
    if 'rsi' in df.columns:
        if pd.notna(last['rsi']):
            if last['rsi'] > 70:
                signals['rsi'] = f'RSI超买 ({last["rsi"]:.1f})'
            elif last['rsi'] < 30:
                signals['rsi'] = f'RSI超卖 ({last["rsi"]:.1f})'

    # KDJ信号
    if 'kdj_k' in df.columns and 'kdj_d' in df.columns:
        if pd.notna(last['kdj_k']) and pd.notna(last['kdj_d']):
            if last['kdj_k'] > last['kdj_d'] and prev['kdj_k'] <= prev['kdj_d']:
                signals['kdj_cross'] = 'KDJ金叉'
            elif last['kdj_k'] < last['kdj_d'] and prev['kdj_k'] >= prev['kdj_d']:
                signals['kdj_cross'] = 'KDJ死叉'

    # 布林带信号
    if 'boll_upper' in df.columns and 'boll_lower' in df.columns:
        if pd.notna(last['close']) and pd.notna(last['boll_upper']):
            if last['close'] > last['boll_upper']:
                signals['boll'] = '突破布林带上轨'
            elif last['close'] < last['boll_lower']:
                signals['boll'] = '跌破布林带下轨'

    return signals


if __name__ == "__main__":
    # 测试指标计算
    import sys
    sys.path.append('..')
    from data_fetcher import fetch_future_data

    logging.basicConfig(level=logging.INFO)

    df = fetch_future_data("rb888", days=60)
    df = add_indicators(df)

    print("\n添加指标后的数据:")
    print(df[['date', 'close', 'ma5', 'ma20', 'rsi', 'macd']].tail())

    print("\n检测到的信号:")
    signals = detect_signals(df)
    for key, value in signals.items():
        print(f"  {key}: {value}")
