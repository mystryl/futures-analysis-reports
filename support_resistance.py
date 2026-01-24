"""
支撑位和阻力位计算模块

使用多种方法计算支撑位和阻力位
"""

from typing import List, Dict, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class SupportResistanceAnalyzer:
    """支撑位和阻力位分析器"""

    def __init__(self, window: int = 20, tolerance: float = 0.005):
        """
        初始化分析器

        Args:
            window: 检测窗口大小
            tolerance: 价格容差比例（用于合并相近的支撑/阻力位）
        """
        self.window = window
        self.tolerance = tolerance

    def find_pivot_points(self, df: pd.DataFrame) -> Tuple[List[float], List[float]]:
        """
        寻找转折点（波峰和波谷）

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            (阻力位列表, 支撑位列表)
        """
        if len(df) < self.window * 2:
            return [], []

        resistance_levels = []
        support_levels = []

        for i in range(self.window, len(df) - self.window):
            # 检测波峰（阻力位）
            current_high = df.iloc[i]['high']
            is_peak = True

            for j in range(i - self.window, i + self.window + 1):
                if j == i:
                    continue
                if df.iloc[j]['high'] >= current_high:
                    is_peak = False
                    break

            if is_peak:
                resistance_levels.append(current_high)

            # 检测波谷（支撑位）
            current_low = df.iloc[i]['low']
            is_trough = True

            for j in range(i - self.window, i + self.window + 1):
                if j == i:
                    continue
                if df.iloc[j]['low'] <= current_low:
                    is_trough = False
                    break

            if is_trough:
                support_levels.append(current_low)

        # 合并相近的价位
        resistance_levels = self._merge_levels(resistance_levels)
        support_levels = self._merge_levels(support_levels)

        return resistance_levels, support_levels

    def _merge_levels(self, levels: List[float]) -> List[float]:
        """合并相近的价位"""
        if not levels:
            return []

        # 排序
        sorted_levels = sorted(levels, reverse=True)

        # 合并相近价位
        merged = []
        for level in sorted_levels:
            if not merged:
                merged.append(level)
            else:
                # 检查是否与已有价位相近
                is_near = False
                for i, existing in enumerate(merged):
                    avg_price = (level + existing) / 2
                    if abs(level - existing) / avg_price < self.tolerance:
                        # 合并为平均值
                        merged[i] = (existing + level) / 2
                        is_near = True
                        break

                if not is_near:
                    merged.append(level)

        return sorted(merged, reverse=True)

    def find_fibonacci_levels(
        self,
        df: pd.DataFrame,
        trend: str = "auto"
    ) -> Dict[str, List[float]]:
        """
        计算斐波那契回调位

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            trend: 趋势方向 "up"/"down"/"auto"

        Returns:
            斐波那契价位字典
        """
        if len(df) < 10:
            return {}

        # 自动判断趋势
        if trend == "auto":
            start_price = df.iloc[0]['close']
            end_price = df.iloc[-1]['close']
            trend = "up" if end_price > start_price else "down"

        # 找到最近一段显著行情的起点和终点
        lookback = min(60, len(df))
        recent_df = df.tail(lookback)

        high = recent_df['high'].max()
        low = recent_df['low'].min()
        diff = high - low

        # 斐波那契回调比例
        fib_ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]

        levels = {}
        if trend == "up":
            # 上升趋势：从低点向上回调
            for ratio in fib_ratios:
                level_name = f"fib_{ratio*100:.1f}%"
                levels[level_name] = low + diff * ratio
        else:
            # 下降趋势：从高点向下回调
            for ratio in fib_ratios:
                level_name = f"fib_{ratio*100:.1f}%"
                levels[level_name] = high - diff * ratio

        return levels

    def find_pivot_points_simplified(
        self,
        df: pd.DataFrame,
        num_levels: int = 5
    ) -> Tuple[List[float], List[float]]:
        """
        简化的支撑位和阻力位计算（基于近期高低点）

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            num_levels: 返回的支撑/阻力位数量

        Returns:
            (阻力位列表, 支撑位列表)
        """
        if df.empty:
            return [], []

        # 使用不同窗口计算
        windows = [5, 10, 20, 40]
        all_resistance = []
        all_support = []

        for window in windows:
            if len(df) < window * 2:
                continue

            # 近期最高点和最低点
            recent_high = df.tail(window * 2)['high'].max()
            recent_low = df.tail(window * 2)['low'].min()

            all_resistance.append(recent_high)
            all_support.append(recent_low)

        # 去重并排序
        resistance_set = set(all_resistance)
        support_set = set(all_support)

        resistance_levels = sorted(resistance_set, reverse=True)[:num_levels]
        support_levels = sorted(support_set)[:num_levels]

        return resistance_levels, support_levels

    def get_current_price_position(
        self,
        current_price: float,
        resistance_levels: List[float],
        support_levels: List[float]
    ) -> Dict[str, any]:
        """
        获取当前价格在支撑/阻力位中的位置

        Args:
            current_price: 当前价格
            resistance_levels: 阻力位列表
            support_levels: 支撑位列表

        Returns:
            位置分析字典
        """
        result = {
            'current_price': current_price,
            'nearest_resistance': None,
            'nearest_support': None,
            'resistance_distance': None,
            'support_distance': None,
            'position': 'middle'
        }

        if resistance_levels:
            # 找到最近的上方阻力位
            above_resistance = [r for r in resistance_levels if r > current_price]
            if above_resistance:
                nearest_resistance = min(above_resistance)
                result['nearest_resistance'] = nearest_resistance
                result['resistance_distance'] = (nearest_resistance - current_price) / current_price * 100

        if support_levels:
            # 找到最近的下方支撑位
            below_support = [s for s in support_levels if s < current_price]
            if below_support:
                nearest_support = max(below_support)
                result['nearest_support'] = nearest_support
                result['support_distance'] = (current_price - nearest_support) / current_price * 100

        # 判断价格位置
        if result['resistance_distance'] and result['support_distance']:
            if result['resistance_distance'] < result['support_distance']:
                result['position'] = 'near_resistance'
            else:
                result['position'] = 'near_support'
        elif result['resistance_distance']:
            result['position'] = 'near_resistance'
        elif result['support_distance']:
            result['position'] = 'near_support'

        return result

    def analyze_comprehensive(
        self,
        df: pd.DataFrame
    ) -> Dict[str, any]:
        """
        综合分析支撑位和阻力位

        Args:
            df: 包含 OHLCV 数据的 DataFrame

        Returns:
            综合分析结果
        """
        if df.empty:
            return {}

        current_price = df.iloc[-1]['close']

        # 方法1：转折点法
        resistance_pivot, support_pivot = self.find_pivot_points_simplified(df)

        # 方法2：斐波那契回调位
        fib_levels = self.find_fibonacci_levels(df)

        # 当前价格位置
        price_position = self.get_current_price_position(
            current_price,
            resistance_pivot,
            support_pivot
        )

        return {
            'current_price': current_price,
            'resistance_levels': resistance_pivot[:3],  # 前3个阻力位
            'support_levels': support_pivot[:3],        # 前3个支撑位
            'fibonacci_levels': fib_levels,
            'price_position': price_position,
            'analysis': self._generate_support_resistance_text(
                current_price,
                resistance_pivot[:3],
                support_pivot[:3],
                price_position
            )
        }

    def _generate_support_resistance_text(
        self,
        current_price: float,
        resistance_levels: List[float],
        support_levels: List[float],
        price_position: Dict[str, any]
    ) -> str:
        """生成支撑阻力分析文本"""
        lines = []

        lines.append(f"当前价格: {current_price:.2f}")

        if resistance_levels:
            lines.append(f"\n上方阻力位:")
            for i, r in enumerate(resistance_levels, 1):
                lines.append(f"  R{i}: {r:.2f}")

        if support_levels:
            lines.append(f"\n下方支撑位:")
            for i, s in enumerate(support_levels, 1):
                lines.append(f"  S{i}: {s:.2f}")

        # 价格位置分析
        position_text = {
            'near_resistance': '价格接近阻力位，注意压力',
            'near_support': '价格接近支撑位，关注反弹',
            'middle': '价格处于中间区域'
        }

        position = price_position.get('position', 'middle')
        lines.append(f"\n位置判断: {position_text.get(position, position)}")

        return '\n'.join(lines)


def analyze_support_resistance(df: pd.DataFrame) -> Dict[str, any]:
    """快捷函数：分析支撑位和阻力位"""
    analyzer = SupportResistanceAnalyzer()
    return analyzer.analyze_comprehensive(df)


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.append('..')
    from data_fetcher import fetch_future_data

    logging.basicConfig(level=logging.INFO)

    df = fetch_future_data("rb888", period="day", days=60)

    analyzer = SupportResistanceAnalyzer()
    result = analyzer.analyze_comprehensive(df)

    print("\n=== 支撑位和阻力位分析 ===\n")
    print(result['analysis'])
