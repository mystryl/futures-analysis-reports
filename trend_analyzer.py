"""
多周期趋势分析模块

分析不同时间周期的趋势状态
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self):
        pass

    def analyze_trend(self, df: pd.DataFrame, period_name: str = "") -> Dict[str, any]:
        """
        分析单个周期的趋势

        Args:
            df: 包含 OHLCV 和指标数据的 DataFrame
            period_name: 周期名称（如 "日线"、"60分钟"）

        Returns:
            趋势分析结果
        """
        if df.empty or len(df) < 20:
            return {
                'period': period_name,
                'trend': 'unknown',
                'strength': 'unknown',
                'analysis': '数据不足'
            }

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        result = {
            'period': period_name,
            'current_price': float(latest['close']),
            'price_change': 0,
            'price_change_pct': 0
        }

        # 计算价格变化
        if len(df) > 1:
            result['price_change'] = float(latest['close'] - prev['close'])
            result['price_change_pct'] = float((latest['close'] - prev['close']) / prev['close'] * 100)

        # 趋势判断（基于均线）
        result['ma_trend'] = self._analyze_ma_trend(df)

        # MACD趋势
        result['macd_trend'] = self._analyze_macd_trend(df)

        # KDJ趋势
        result['kdj_trend'] = self._analyze_kdj_trend(df)

        # RSI趋势
        result['rsi_value'] = float(latest.get('rsi', 50)) if 'rsi' in df.columns and pd.notna(latest.get('rsi')) else None

        # 布林带位置
        result['boll_position'] = self._analyze_boll_position(df)

        # 综合趋势判断
        result['trend'] = self._get_overall_trend(result)
        result['strength'] = self._get_trend_strength(result)

        # 生成分析文本
        result['analysis'] = self._generate_trend_text(result)

        return result

    def _analyze_ma_trend(self, df: pd.DataFrame) -> Dict[str, str]:
        """基于均线分析趋势"""
        if len(df) < 20:
            return {'trend': 'unknown', 'signal': ''}

        latest = df.iloc[-1]

        # 检查是否有必要的均线
        if 'ma5' not in df.columns or 'ma20' not in df.columns:
            return {'trend': 'unknown', 'signal': '均线数据不足'}

        ma5 = latest.get('ma5')
        ma10 = latest.get('ma10')
        ma20 = latest.get('ma20')
        ma60 = latest.get('ma60')

        if any(pd.isna(v) for v in [ma5, ma10, ma20]):
            return {'trend': 'unknown', 'signal': '均线计算中'}

        # 均线排列
        if ma5 > ma10 > ma20:
            if ma60 and pd.notna(ma60) and ma20 > ma60:
                ma_arrangement = '多头排列'
                trend = 'strong_up'
            else:
                ma_arrangement = '短期多头'
                trend = 'up'
        elif ma5 < ma10 < ma20:
            if ma60 and pd.notna(ma60) and ma20 < ma60:
                ma_arrangement = '空头排列'
                trend = 'strong_down'
            else:
                ma_arrangement = '短期空头'
                trend = 'down'
        else:
            ma_arrangement = '均线纠缠'
            trend = 'sideways'

        # 价格与均线关系
        price = latest['close']
        if price > ma5:
            price_position = '价格站上5日线'
        elif price < ma20:
            price_position = '价格跌破20日线'
        else:
            price_position = '价格在5日和20日之间'

        return {
            'trend': trend,
            'ma_arrangement': ma_arrangement,
            'price_position': price_position,
            'signal': f'{ma_arrangement}，{price_position}'
        }

    def _analyze_macd_trend(self, df: pd.DataFrame) -> Dict[str, str]:
        """基于MACD分析趋势"""
        if 'macd_dif' not in df.columns or 'macd_dea' not in df.columns:
            return {'trend': 'unknown', 'signal': 'MACD数据不足'}

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        dif = latest.get('macd_dif')
        dea = latest.get('macd_dea')
        macd = latest.get('macd')

        if any(pd.isna(v) for v in [dif, dea, macd]):
            return {'trend': 'unknown', 'signal': 'MACD计算中'}

        # DIF与DEA关系
        if dif > dea:
            dif_dea_relation = 'DIF在DEA上方'
            if prev.get('macd_dif', 0) <= prev.get('macd_dea', 0):
                signal = 'MACD金叉（看涨）'
                trend = 'up'
            else:
                signal = 'DIF上穿DEA持续'
                trend = 'up'
        else:
            dif_dea_relation = 'DIF在DEA下方'
            if prev.get('macd_dif', 0) >= prev.get('macd_dea', 0):
                signal = 'MACD死叉（看跌）'
                trend = 'down'
            else:
                signal = 'DIF下穿DEA持续'
                trend = 'down'

        # MACD柱状图
        if macd > 0:
            macd_bar = '红柱（多头）'
        else:
            macd_bar = '绿柱（空头）'

        return {
            'trend': trend,
            'signal': signal,
            'dif_dea_relation': dif_dea_relation,
            'macd_bar': macd_bar
        }

    def _analyze_kdj_trend(self, df: pd.DataFrame) -> Dict[str, str]:
        """基于KDJ分析趋势"""
        if 'kdj_k' not in df.columns or 'kdj_d' not in df.columns:
            return {'trend': 'unknown', 'signal': 'KDJ数据不足'}

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        k = latest.get('kdj_k')
        d = latest.get('kdj_d')
        j = latest.get('kdj_j')

        if any(pd.isna(v) for v in [k, d, j]):
            return {'trend': 'unknown', 'signal': 'KDJ计算中'}

        # K值区间判断
        if k > 80:
            k_zone = '超买区（>80）'
        elif k < 20:
            k_zone = '超卖区（<20）'
        else:
            k_zone = '中性区（20-80）'

        # 金叉死叉
        if k > d:
            if prev.get('kdj_k', 0) <= prev.get('kdj_d', 0):
                signal = 'KDJ金叉'
                trend = 'up'
            else:
                signal = 'K线上穿D线持续'
                trend = 'up'
        else:
            if prev.get('kdj_k', 0) >= prev.get('kdj_d', 0):
                signal = 'KDJ死叉'
                trend = 'down'
            else:
                signal = 'K线下穿D线持续'
                trend = 'down'

        return {
            'trend': trend,
            'signal': signal,
            'k_zone': k_zone,
            'k_value': float(k),
            'd_value': float(d)
        }

    def _analyze_boll_position(self, df: pd.DataFrame) -> Dict[str, str]:
        """分析价格在布林带中的位置"""
        if 'boll_upper' not in df.columns or 'boll_lower' not in df.columns:
            return {'position': 'unknown', 'signal': '布林带数据不足'}

        latest = df.iloc[-1]
        price = latest['close']
        upper = latest.get('boll_upper')
        mid = latest.get('boll_mid')
        lower = latest.get('boll_lower')

        if any(pd.isna(v) for v in [upper, mid, lower]):
            return {'position': 'unknown', 'signal': '布林带计算中'}

        # 计算价格位置百分比
        boll_width = upper - lower
        if boll_width > 0:
            position_pct = (price - lower) / boll_width * 100
        else:
            position_pct = 50

        if price > upper:
            position = '突破上轨'
            signal = '强势突破'
        elif price < lower:
            position = '跌破下轨'
            signal = '弱势跌破'
        elif price > mid:
            position = '上轨和中轨之间'
            signal = '偏强'
        else:
            position = '中轨和下轨之间'
            signal = '偏弱'

        return {
            'position': position,
            'signal': signal,
            'position_pct': float(position_pct)
        }

    def _get_overall_trend(self, analysis: Dict[str, any]) -> str:
        """综合判断整体趋势"""
        ma_trend = analysis.get('ma_trend', {}).get('trend', 'unknown')
        macd_trend = analysis.get('macd_trend', {}).get('trend', 'unknown')
        kdj_trend = analysis.get('kdj_trend', {}).get('trend', 'unknown')

        # 统计看涨看跌
        up_count = sum([1 for t in [ma_trend, macd_trend, kdj_trend] if t in ['up', 'strong_up']])
        down_count = sum([1 for t in [ma_trend, macd_trend, kdj_trend] if t in ['down', 'strong_down']])

        if up_count >= 2:
            return 'uptrend'
        elif down_count >= 2:
            return 'downtrend'
        else:
            return 'sideways'

    def _get_trend_strength(self, analysis: Dict[str, any]) -> str:
        """判断趋势强度"""
        ma_trend = analysis.get('ma_trend', {}).get('trend', '')
        boll_pos = analysis.get('boll_position', {}).get('signal', '')

        if 'strong' in ma_trend or '突破' in boll_pos:
            return 'strong'
        elif ma_trend in ['up', 'down']:
            return 'moderate'
        else:
            return 'weak'

    def _generate_trend_text(self, analysis: Dict[str, any]) -> str:
        """生成趋势分析文本"""
        lines = []
        period = analysis.get('period', '')

        if period:
            lines.append(f"【{period}趋势分析】")

        # 当前价格
        current_price = analysis.get('current_price', 0)
        change_pct = analysis.get('price_change_pct', 0)
        lines.append(f"当前价格: {current_price:.2f} ({change_pct:+.2f}%)")

        # 综合趋势
        trend_map = {
            'uptrend': '上升趋势 📈',
            'downtrend': '下降趋势 📉',
            'sideways': '震荡整理 ➡️',
            'unknown': '趋势不明 ❓'
        }
        trend = analysis.get('trend', 'unknown')
        strength = analysis.get('strength', '')
        strength_map = {'strong': '(强势)', 'moderate': '(中等)', 'weak': '(弱势)'}
        lines.append(f"综合趋势: {trend_map.get(trend, trend)} {strength_map.get(strength, '')}")

        # 均线分析
        ma_analysis = analysis.get('ma_trend', {})
        if ma_analysis.get('signal'):
            lines.append(f"均线分析: {ma_analysis['signal']}")

        # MACD分析
        macd_analysis = analysis.get('macd_trend', {})
        if macd_analysis.get('signal'):
            lines.append(f"MACD分析: {macd_analysis['signal']}")

        # KDJ分析
        kdj_analysis = analysis.get('kdj_trend', {})
        if kdj_analysis.get('signal'):
            k_zone = kdj_analysis.get('k_zone', '')
            lines.append(f"KDJ分析: {kdj_analysis['signal']}，{k_zone}")

        # 布林带分析
        boll_analysis = analysis.get('boll_position', {})
        if boll_analysis.get('signal'):
            lines.append(f"布林带分析: {boll_analysis['signal']}")

        return '\n'.join(lines)


def analyze_multi_period_trend(
    multi_period_data: Dict[str, pd.DataFrame]
) -> Dict[str, Dict[str, any]]:
    """
    分析多周期趋势

    Args:
        multi_period_data: 多周期数据字典

    Returns:
        多周期趋势分析结果
    """
    period_names = {
        '15min': '15分钟',
        '60min': '60分钟',
        'day': '日线'
    }

    analyzer = TrendAnalyzer()
    results = {}

    for period_key, df in multi_period_data.items():
        if df.empty:
            continue

        period_name = period_names.get(period_key, period_key)
        results[period_key] = analyzer.analyze_trend(df, period_name)

    return results


def generate_multi_period_summary(multi_period_analysis: Dict[str, Dict[str, any]]) -> str:
    """生成多周期综合分析摘要"""
    lines = []
    lines.append("=" * 60)
    lines.append("多周期趋势综合分析".center(60))
    lines.append("=" * 60)
    lines.append("")

    for period_key, analysis in multi_period_analysis.items():
        if analysis.get('analysis'):
            lines.append(analysis['analysis'])
            lines.append("")

    # 综合判断
    trends = [a.get('trend', 'unknown') for a in multi_period_analysis.values()]

    uptrend_count = sum(1 for t in trends if t == 'uptrend')
    downtrend_count = sum(1 for t in trends if t == 'downtrend')

    lines.append("=" * 60)
    lines.append("【综合判断】")

    if uptrend_count > downtrend_count:
        lines.append(f"多周期共振: 看涨（{uptrend_count}个周期上涨 vs {downtrend_count}个周期下跌）")
        lines.append("操作建议: 逢低做多，注意风险控制")
    elif downtrend_count > uptrend_count:
        lines.append(f"多周期共振: 看跌（{downtrend_count}个周期下跌 vs {uptrend_count}个周期上涨）")
        lines.append("操作建议: 高空为主，注意反弹风险")
    else:
        lines.append("多周期分化: 趋势不一致，方向不明")
        lines.append("操作建议: 观望为主，等待明确信号")

    lines.append("=" * 60)

    return '\n'.join(lines)


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.append('..')
    from data_fetcher import FuturesDataFetcher

    logging.basicConfig(level=logging.INFO)

    fetcher = FuturesDataFetcher()
    multi_data = fetcher.get_multi_period_data("rb888", days=10)

    analyzer = TrendAnalyzer()

    for period, df in multi_data.items():
        from indicators import TechnicalIndicators
        df = TechnicalIndicators.add_all_indicators(df)
        result = analyzer.analyze_trend(df, period)
        print(f"\n{period} 趋势分析:")
        print(result['analysis'])
