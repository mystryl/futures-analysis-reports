"""
K线形态识别模块

识别常见的K线形态，包括:
- 单根K线形态: 十字星、锤子线、流星线、大阳线、大阴线
- 双根K线形态: 阳包阴、阴包阳、曙光初现、乌云盖顶
- 多根K线形态: 吞噬形态、早晨之星、黄昏之星、三连阳/阴
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class KLinePatternRecognizer:
    """K线形态识别器"""

    def __init__(self, body_threshold: float = 0.5, shadow_threshold: float = 0.3):
        """
        初始化识别器

        Args:
            body_threshold: 实体比例阈值（用于判断十字星等）
            shadow_threshold: 影线比例阈值
        """
        self.body_threshold = body_threshold
        self.shadow_threshold = shadow_threshold

    def _calculate_body_info(self, row: pd.Series) -> Dict[str, float]:
        """计算K线实体信息"""
        open_price = row['open']
        close_price = row['close']
        high_price = row['high']
        low_price = row['low']

        body_size = abs(close_price - open_price)
        total_range = high_price - low_price

        if total_range == 0:
            return {
                'body_size': 0,
                'total_range': 0,
                'body_ratio': 0,
                'upper_shadow': 0,
                'lower_shadow': 0,
                'upper_shadow_ratio': 0,
                'lower_shadow_ratio': 0,
                'is_bullish': close_price > open_price,
                'is_bearish': close_price < open_price
            }

        upper_shadow = high_price - max(open_price, close_price)
        lower_shadow = min(open_price, close_price) - low_price

        return {
            'body_size': body_size,
            'total_range': total_range,
            'body_ratio': body_size / total_range,
            'upper_shadow': upper_shadow,
            'lower_shadow': lower_shadow,
            'upper_shadow_ratio': upper_shadow / total_range,
            'lower_shadow_ratio': lower_shadow / total_range,
            'is_bullish': close_price > open_price,
            'is_bearish': close_price < open_price
        }

    def recognize_single_pattern(self, row: pd.Series) -> Optional[str]:
        """
        识别单根K线形态

        Args:
            row: 单行数据，包含 open, high, low, close

        Returns:
            形态名称或None
        """
        info = self._calculate_body_info(row)

        # 十字星 - 实体很小
        if info['body_ratio'] < self.body_threshold:
            if info['upper_shadow_ratio'] > self.shadow_threshold and \
               info['lower_shadow_ratio'] > self.shadow_threshold:
                return "十字星（长上下影）"
            else:
                return "十字星"

        # 锤子线 - 下影线长，实体小，上影线短
        if info['lower_shadow_ratio'] > 2 * info['body_ratio'] and \
           info['upper_shadow_ratio'] < self.shadow_threshold:
            if info['is_bullish']:
                return "锤子线（看涨）"
            else:
                return "上吊线（看跌）"

        # 流星线 - 上影线长，实体小，下影线短
        if info['upper_shadow_ratio'] > 2 * info['body_ratio'] and \
           info['lower_shadow_ratio'] < self.shadow_threshold:
            if info['is_bullish']:
                return "流星线（看跌）"
            else:
                return "倒锤子（看涨）"

        # 大阳线
        if info['is_bullish'] and info['body_ratio'] > 0.7:
            return "大阳线"

        # 大阴线
        if info['is_bearish'] and info['body_ratio'] > 0.7:
            return "大阴线"

        # 中阳线
        if info['is_bullish'] and info['body_ratio'] > 0.5:
            return "中阳线"

        # 中阴线
        if info['is_bearish'] and info['body_ratio'] > 0.5:
            return "中阴线"

        # 小阳线
        if info['is_bullish']:
            return "小阳线"

        # 小阴线
        if info['is_bearish']:
            return "小阴线"

        return None

    def recognize_double_pattern(self, prev_row: pd.Series, curr_row: pd.Series) -> Optional[str]:
        """
        识别双根K线形态

        Args:
            prev_row: 前一根K线
            curr_row: 当前K线

        Returns:
            形态名称或None
        """
        prev_info = self._calculate_body_info(prev_row)
        curr_info = self._calculate_body_info(curr_row)

        # 阳包阴 - 前阴后阳，阳线实体完全包含阴线
        if prev_info['is_bearish'] and curr_info['is_bullish']:
            if curr_row['close'] > prev_row['open'] and curr_row['open'] < prev_row['close']:
                return "阳包阴（看涨）"

        # 阴包阳 - 前阳后阴，阴线实体完全包含阳线
        if prev_info['is_bullish'] and curr_info['is_bearish']:
            if curr_row['close'] < prev_row['open'] and curr_row['open'] > prev_row['close']:
                return "阴包阳（看跌）"

        # 曙光初现 - 前阴后阳，阳线收盘价深入阴线实体
        if prev_info['is_bearish'] and curr_info['is_bullish']:
            prev_body_mid = (prev_row['open'] + prev_row['close']) / 2
            if curr_row['close'] > prev_body_mid and curr_row['open'] < prev_row['close']:
                return "曙光初现（看涨）"

        # 乌云盖顶 - 前阳后阴，阴线收盘价深入阳线实体
        if prev_info['is_bullish'] and curr_info['is_bearish']:
            prev_body_mid = (prev_row['open'] + prev_row['close']) / 2
            if curr_row['close'] < prev_body_mid and curr_row['open'] > prev_row['close']:
                return "乌云盖顶（看跌）"

        return None

    def recognize_triple_pattern(self, df: pd.DataFrame, index: int) -> Optional[str]:
        """
        识别三根K线形态

        Args:
            df: 完整数据
            index: 当前K线索引

        Returns:
            形态名称或None
        """
        if index < 2:
            return None

        row1 = df.iloc[index - 2]
        row2 = df.iloc[index - 1]
        row3 = df.iloc[index]

        info1 = self._calculate_body_info(row1)
        info2 = self._calculate_body_info(row2)
        info3 = self._calculate_body_info(row3)

        # 早晨之星 - 底部反转形态
        # 第一根阴线，第二根小实体（可阳可阴），第三根阳线
        if info1['is_bearish'] and info3['is_bullish']:
            if info2['body_ratio'] < self.body_threshold:
                if row3['close'] > (row1['open'] + row1['close']) / 2:
                    return "早晨之星（看涨）"

        # 黄昏之星 - 顶部反转形态
        # 第一根阳线，第二根小实体（可阳可阴），第三根阴线
        if info1['is_bullish'] and info3['is_bearish']:
            if info2['body_ratio'] < self.body_threshold:
                if row3['close'] < (row1['open'] + row1['close']) / 2:
                    return "黄昏之星（看跌）"

        # 三连阳 - 红三兵
        if info1['is_bullish'] and info2['is_bullish'] and info3['is_bullish']:
            if all([info1['body_ratio'] > 0.4, info2['body_ratio'] > 0.4, info3['body_ratio'] > 0.4]):
                if row3['close'] > row1['close']:
                    return "红三兵（看涨）"

        # 三连阴 - 三只乌鸦
        if info1['is_bearish'] and info2['is_bearish'] and info3['is_bearish']:
            if all([info1['body_ratio'] > 0.4, info2['body_ratio'] > 0.4, info3['body_ratio'] > 0.4]):
                if row3['close'] < row1['close']:
                    return "三只乌鸦（看跌）"

        return None

    def analyze_patterns(self, df: pd.DataFrame) -> List[Dict[str, any]]:
        """
        分析整个数据序列的K线形态

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            形态列表，每个元素包含索引、日期、形态名称、类型
        """
        patterns = []

        for i in range(len(df)):
            row = df.iloc[i]
            date = row['date'] if 'date' in df.columns else i

            # 单根K线形态
            single_pattern = self.recognize_single_pattern(row)
            if single_pattern:
                patterns.append({
                    'index': i,
                    'date': date,
                    'pattern': single_pattern,
                    'type': 'single',
                    'signal': self._get_pattern_signal(single_pattern)
                })

            # 双根K线形态
            if i > 0:
                double_pattern = self.recognize_double_pattern(df.iloc[i-1], row)
                if double_pattern:
                    patterns.append({
                        'index': i,
                        'date': date,
                        'pattern': double_pattern,
                        'type': 'double',
                        'signal': self._get_pattern_signal(double_pattern)
                    })

            # 三根K线形态
            triple_pattern = self.recognize_triple_pattern(df, i)
            if triple_pattern:
                patterns.append({
                    'index': i,
                    'date': date,
                    'pattern': triple_pattern,
                    'type': 'triple',
                    'signal': self._get_pattern_signal(triple_pattern)
                })

        return patterns

    def _get_pattern_signal(self, pattern: str) -> str:
        """根据形态名称判断信号类型"""
        bullish_keywords = ['看涨', '锤子', '早晨', '红三兵', '曙光']
        bearish_keywords = ['看跌', '上吊', '黄昏', '乌鸦', '乌云']

        for keyword in bullish_keywords:
            if keyword in pattern:
                return 'bullish'

        for keyword in bearish_keywords:
            if keyword in pattern:
                return 'bearish'

        return 'neutral'

    def get_recent_patterns(self, df: pd.DataFrame, n: int = 5) -> List[Dict[str, any]]:
        """
        获取最近 n 天的K线形态

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            n: 返回最近多少天的形态

        Returns:
            最近的形态列表
        """
        all_patterns = self.analyze_patterns(df)
        # 按索引排序，返回最近的 n 个
        sorted_patterns = sorted(all_patterns, key=lambda x: x['index'], reverse=True)
        return sorted_patterns[:n]


def recognize_patterns(df: pd.DataFrame) -> List[Dict[str, any]]:
    """
    快捷函数：识别K线形态

    Args:
        df: 包含 OHLCV 数据的 DataFrame

    Returns:
        形态列表
    """
    recognizer = KLinePatternRecognizer()
    return recognizer.analyze_patterns(df)


def format_patterns_summary(patterns: List[Dict[str, any]]) -> str:
    """
    格式化形态摘要

    Args:
        patterns: 形态列表

    Returns:
        格式化的摘要字符串
    """
    if not patterns:
        return "未检测到明显形态"

    summary_parts = []

    # 统计信号类型
    bullish_count = sum(1 for p in patterns if p['signal'] == 'bullish')
    bearish_count = sum(1 for p in patterns if p['signal'] == 'bearish')

    if bullish_count > bearish_count:
        summary_parts.append(f"整体偏看涨（{bullish_count}个看涨形态 vs {bearish_count}个看跌形态）")
    elif bearish_count > bullish_count:
        summary_parts.append(f"整体偏看跌（{bearish_count}个看跌形态 vs {bullish_count}个看涨形态）")
    else:
        summary_parts.append(f"多空平衡（各{bullish_count}个形态）")

    # 列出最近的重要形态
    important_patterns = [p for p in patterns[:3] if p['type'] in ['double', 'triple']]
    if important_patterns:
        pattern_names = [p['pattern'] for p in important_patterns]
        summary_parts.append(f"最近形态: {', '.join(pattern_names)}")

    return '；'.join(summary_parts)


if __name__ == "__main__":
    # 测试形态识别
    import sys
    sys.path.append('..')
    from data_fetcher import fetch_future_data
    from indicators import add_indicators

    logging.basicConfig(level=logging.INFO)

    df = fetch_future_data("rb888", days=60)
    df = add_indicators(df)

    recognizer = KLinePatternRecognizer()

    print("\n=== K线形态识别测试 ===\n")

    # 获取最近的形态
    recent_patterns = recognizer.get_recent_patterns(df, n=10)

    print(f"检测到 {len(recent_patterns)} 个近期形态:\n")
    for p in recent_patterns:
        print(f"  [{p['date']}] {p['pattern']} ({p['type']})")

    print(f"\n摘要: {format_patterns_summary(recent_patterns)}")
