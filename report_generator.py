"""
完整技术分析报告生成模块

生成详细的技术分析报告，包含多周期分析、形态识别、支撑阻力等
"""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TechnicalReportGenerator:
    """技术分析报告生成器"""

    def __init__(self):
        pass

    def generate_full_report(
        self,
        symbol: str,
        multi_period_data: Dict[str, pd.DataFrame],
        multi_period_analysis: Dict[str, Dict[str, any]],
        support_resistance: Dict[str, any],
        patterns: Dict[str, List[Dict[str, any]]]
    ) -> str:
        """
        生成完整的技术分析报告

        Args:
            symbol: 期货品种代码
            multi_period_data: 多周期数据
            multi_period_analysis: 多周期趋势分析结果
            support_resistance: 支撑阻力分析结果
            patterns: 各周期形态识别结果

        Returns:
            完整的技术分析报告文本
        """
        report_lines = []

        # 报告标题
        report_lines.append("=" * 70)
        report_lines.append(f"【{symbol} 期货技术分析报告】".center(70))
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(70))
        report_lines.append("=" * 70)
        report_lines.append("")

        # 1. 当前价格信息
        report_lines.extend(self._generate_price_section(symbol, multi_period_data))
        report_lines.append("")

        # 2. 多周期趋势分析
        report_lines.extend(self._generate_trend_section(multi_period_analysis))
        report_lines.append("")

        # 3. 支撑位和阻力位分析
        report_lines.extend(self._generate_support_resistance_section(support_resistance))
        report_lines.append("")

        # 4. K线形态分析
        report_lines.extend(self._generate_pattern_section(patterns))
        report_lines.append("")

        # 5. 技术指标分析
        report_lines.extend(self._generate_indicators_section(multi_period_data, multi_period_analysis))
        report_lines.append("")

        # 6. 综合判断与操作建议
        report_lines.extend(self._generate_conclusion_section(multi_period_analysis, support_resistance))
        report_lines.append("")

        # 7. 风险提示
        report_lines.extend(self._generate_risk_warning())

        return '\n'.join(report_lines)

    def _generate_price_section(
        self,
        symbol: str,
        multi_period_data: Dict[str, pd.DataFrame]
    ) -> List[str]:
        """生成价格信息部分"""
        lines = []
        lines.append("┏" + "━" * 68 + "┓")
        lines.append("┃" + " 【当前价格信息】 ".center(66) + "┃")
        lines.append("┗" + "━" * 68 + "┛")
        lines.append("")

        # 获取日线最新数据
        day_df = multi_period_data.get('day')
        if not day_df.empty:
            latest = day_df.iloc[-1]
            current_price = latest['close']

            # 计算涨跌
            if len(day_df) > 1:
                prev = day_df.iloc[-2]
                price_change = current_price - prev['close']
                price_change_pct = (price_change / prev['close']) * 100

                if price_change >= 0:
                    change_text = f"+{price_change:.2f} (+{price_change_pct:.2f}%) 🔺"
                else:
                    change_text = f"{price_change:.2f} ({price_change_pct:.2f}%) 🔻"

                lines.append(f"  品种代码: {symbol}")
                lines.append(f"  最新价格: {current_price:.2f}")
                lines.append(f"  涨跌情况: {change_text}")
                lines.append(f"  最高价: {latest['high']:.2f}")
                lines.append(f"  最低价: {latest['low']:.2f}")
                lines.append(f"  成交量: {int(latest['volume']):,}")

        return lines

    def _generate_trend_section(
        self,
        multi_period_analysis: Dict[str, Dict[str, any]]
    ) -> List[str]:
        """生成趋势分析部分"""
        lines = []
        lines.append("┏" + "━" * 68 + "┓")
        lines.append("┃" + " 【多周期趋势分析】 ".center(66) + "┃")
        lines.append("┗" + "━" * 68 + "┛")
        lines.append("")

        period_names = {
            'day': '日线',
            '60min': '60分钟',
            '15min': '15分钟'
        }

        for period_key in ['day', '60min', '15min']:
            if period_key not in multi_period_analysis:
                continue

            analysis = multi_period_analysis[period_key]
            period_name = period_names.get(period_key, period_key)

            # 趋势图标
            trend = analysis.get('trend', 'unknown')
            trend_icons = {
                'uptrend': '📈 上升',
                'downtrend': '📉 下降',
                'sideways': '➡️ 震荡',
                'unknown': '❓ 不明'
            }

            lines.append(f"  【{period_name}】")
            lines.append(f"    趋势: {trend_icons.get(trend, trend)}")

            # 均线分析
            ma_analysis = analysis.get('ma_trend', {})
            if ma_analysis.get('signal'):
                lines.append(f"    均线: {ma_analysis['signal']}")

            # MACD分析
            macd_analysis = analysis.get('macd_trend', {})
            if macd_analysis.get('signal'):
                lines.append(f"    MACD: {macd_analysis['signal']}")

            # KDJ分析
            kdj_analysis = analysis.get('kdj_trend', {})
            if kdj_analysis.get('signal'):
                lines.append(f"    KDJ: {kdj_analysis['signal']}")

            lines.append("")

        return lines

    def _generate_support_resistance_section(
        self,
        support_resistance: Dict[str, any]
    ) -> List[str]:
        """生成支撑阻力部分"""
        lines = []
        lines.append("┏" + "━" * 68 + "┓")
        lines.append("┃" + " 【支撑位与阻力位】 ".center(66) + "┃")
        lines.append("┗" + "━" * 68 + "┛")
        lines.append("")

        current_price = support_resistance.get('current_price', 0)
        lines.append(f"  当前价格: {current_price:.2f}")
        lines.append("")

        # 阻力位
        resistance_levels = support_resistance.get('resistance_levels', [])
        if resistance_levels:
            lines.append("  🔴 上方阻力位:")
            for i, r in enumerate(resistance_levels, 1):
                distance = ((r - current_price) / current_price * 100) if current_price > 0 else 0
                lines.append(f"    R{i}: {r:.2f} (距离 {distance:+.2f}%)")

        lines.append("")

        # 支撑位
        support_levels = support_resistance.get('support_levels', [])
        if support_levels:
            lines.append("  🟢 下方支撑位:")
            for i, s in enumerate(support_levels, 1):
                distance = ((current_price - s) / current_price * 100) if current_price > 0 else 0
                lines.append(f"    S{i}: {s:.2f} (距离 {-distance:.2f}%)")

        lines.append("")

        # 价格位置判断
        price_position = support_resistance.get('price_position', {})
        position = price_position.get('position', '')

        position_text = {
            'near_resistance': '⚠️ 价格接近阻力位，注意上方压力',
            'near_support': '✅ 价格接近支撑位，关注反弹机会',
            'middle': '⏺️ 价格处于中间区域'
        }

        if position:
            lines.append(f"  位置判断: {position_text.get(position, position)}")

        return lines

    def _generate_pattern_section(
        self,
        patterns: Dict[str, List[Dict[str, any]]]
    ) -> List[str]:
        """生成K线形态部分"""
        lines = []
        lines.append("┏" + "━" * 68 + "┓")
        lines.append("┃" + " 【K线形态分析】 ".center(66) + "┃")
        lines.append("┗" + "━" * 68 + "┛")
        lines.append("")

        period_names = {
            'day': '日线',
            '60min': '60分钟',
            '15min': '15分钟'
        }

        has_patterns = False

        for period_key in ['day', '60min', '15min']:
            if period_key not in patterns or not patterns[period_key]:
                continue

            has_patterns = True
            period_name = period_names.get(period_key, period_key)
            period_patterns = patterns[period_key]

            # 只显示重要形态（双根和三根）
            important_patterns = [p for p in period_patterns if p['type'] in ['double', 'triple']]

            if important_patterns:
                lines.append(f"  【{period_name}】")
                for p in important_patterns[:3]:  # 最多显示3个
                    signal_icon = '🟢' if p['signal'] == 'bullish' else '🔴' if p['signal'] == 'bearish' else '⚪'
                    lines.append(f"    {signal_icon} {p['pattern']}")

                lines.append("")

        if not has_patterns:
            lines.append("  暂未检测到明显K线形态")

        return lines

    def _generate_indicators_section(
        self,
        multi_period_data: Dict[str, pd.DataFrame],
        multi_period_analysis: Dict[str, Dict[str, any]]
    ) -> List[str]:
        """生成技术指标部分"""
        lines = []
        lines.append("┏" + "━" * 68 + "┓")
        lines.append("┃" + " 【关键技术指标】 ".center(66) + "┃")
        lines.append("┗" + "━" * 68 + "┛")
        lines.append("")

        # 使用日线数据展示指标
        day_df = multi_period_data.get('day')
        if day_df.empty:
            return lines

        latest = day_df.iloc[-1]

        # 均线指标
        lines.append("  📊 均线指标:")
        if 'ma5' in day_df.columns and pd.notna(latest.get('ma5')):
            lines.append(f"    MA5:  {latest['ma5']:.2f}")
        if 'ma10' in day_df.columns and pd.notna(latest.get('ma10')):
            lines.append(f"    MA10: {latest['ma10']:.2f}")
        if 'ma20' in day_df.columns and pd.notna(latest.get('ma20')):
            lines.append(f"    MA20: {latest['ma20']:.2f}")
        if 'ma60' in day_df.columns and pd.notna(latest.get('ma60')):
            lines.append(f"    MA60: {latest['ma60']:.2f}")

        lines.append("")

        # MACD指标
        lines.append("  📊 MACD指标:")
        if 'macd_dif' in day_df.columns and pd.notna(latest.get('macd_dif')):
            macd_value = latest.get('macd', 0)
            macd_status = '红柱' if macd_value > 0 else '绿柱'
            lines.append(f"    DIF:  {latest['macd_dif']:.2f}")
            lines.append(f"    DEA:  {latest['macd_dea']:.2f}")
            lines.append(f"    MACD: {macd_value:.2f} ({macd_status})")

        lines.append("")

        # KDJ指标
        lines.append("  📊 KDJ指标:")
        if 'kdj_k' in day_df.columns and pd.notna(latest.get('kdj_k')):
            k_value = latest['kdj_k']
            k_status = '超买' if k_value > 80 else '超卖' if k_value < 20 else '正常'
            lines.append(f"    K:   {k_value:.2f} ({k_status})")
            lines.append(f"    D:   {latest['kdj_d']:.2f}")
            lines.append(f"    J:   {latest['kdj_j']:.2f}")

        lines.append("")

        # RSI指标
        if 'rsi' in day_df.columns and pd.notna(latest.get('rsi')):
            rsi_value = latest['rsi']
            rsi_status = '超买' if rsi_value > 70 else '超卖' if rsi_value < 30 else '正常'
            lines.append(f"  📊 RSI指标: {rsi_value:.2f} ({rsi_status})")

        return lines

    def _generate_conclusion_section(
        self,
        multi_period_analysis: Dict[str, Dict[str, any]],
        support_resistance: Dict[str, any]
    ) -> List[str]:
        """生成综合判断部分"""
        lines = []
        lines.append("┏" + "━" * 68 + "┓")
        lines.append("┃" + " 【综合判断与操作建议】 ".center(66) + "┃")
        lines.append("┗" + "━" * 68 + "┛")
        lines.append("")

        # 统计各周期趋势
        trends = []
        for analysis in multi_period_analysis.values():
            trend = analysis.get('trend', 'unknown')
            if trend != 'unknown':
                trends.append(trend)

        uptrend_count = sum(1 for t in trends if t == 'uptrend')
        downtrend_count = sum(1 for t in trends if t == 'downtrend')
        sideways_count = sum(1 for t in trends if t == 'sideways')

        # 趋势共振判断
        if uptrend_count >= 2:
            lines.append("  📈 多周期趋势共振: 看涨")
            lines.append("     → 日线、60分钟、15分钟中至少2个周期呈上升趋势")
            lines.append("")
            lines.append("  💡 操作建议:")
            lines.append("     • 逢低做多为主")
            lines.append("     • 关注支撑位附近机会")
            lines.append("     • 设置合理止损")

        elif downtrend_count >= 2:
            lines.append("  📉 多周期趋势共振: 看跌")
            lines.append("     → 日线、60分钟、15分钟中至少2个周期呈下降趋势")
            lines.append("")
            lines.append("  💡 操作建议:")
            lines.append("     • 高空为主，谨慎做多")
            lines.append("     • 关注阻力位附近机会")
            lines.append("     • 注意反弹风险")

        else:
            lines.append("  ➡️ 多周期趋势分化: 方向不明")
            lines.append("     → 各周期趋势不一致，等待明确信号")
            lines.append("")
            lines.append("  💡 操作建议:")
            lines.append("     • 观望为主，等待方向明确")
            lines.append("     • 可做区间操作")
            lines.append("     • 严格控制仓位")

        lines.append("")
        lines.append("  🎯 关键价位:")

        # 添加关键价位
        current_price = support_resistance.get('current_price', 0)
        resistance_levels = support_resistance.get('resistance_levels', [])
        support_levels = support_resistance.get('support_levels', [])

        if resistance_levels:
            lines.append(f"     上方阻力: {resistance_levels[0]:.2f}")
        if support_levels:
            lines.append(f"     下方支撑: {support_levels[0]:.2f}")
        lines.append(f"     当前价格: {current_price:.2f}")

        return lines

    def _generate_risk_warning(self) -> List[str]:
        """生成风险提示"""
        lines = []
        lines.append("┏" + "━" * 68 + "┓")
        lines.append("┃" + " 【风险提示】 ".center(66) + "┃")
        lines.append("┗" + "━" * 68 + "┛")
        lines.append("")
        lines.append("  ⚠️ 本报告仅供参考，不构成投资建议")
        lines.append("  ⚠️ 期货交易风险较高，入市需谨慎")
        lines.append("  ⚠️ 建议结合基本面分析和其他技术方法综合判断")
        lines.append("  ⚠️ 严格控制风险，合理设置止损止盈")
        lines.append("")
        lines.append("=" * 70)

        return lines


def generate_technical_report(
    symbol: str,
    multi_period_data: Dict[str, pd.DataFrame],
    multi_period_analysis: Dict[str, Dict[str, any]],
    support_resistance: Dict[str, any],
    patterns: Dict[str, List[Dict[str, any]]]
) -> str:
    """快捷函数：生成完整技术分析报告"""
    generator = TechnicalReportGenerator()
    return generator.generate_full_report(
        symbol, multi_period_data, multi_period_analysis,
        support_resistance, patterns
    )
