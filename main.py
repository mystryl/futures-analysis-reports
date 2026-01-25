#!/usr/bin/env python3
"""
期货K线自动分析主程序

整合数据获取、指标计算、形态识别、趋势分析、支撑阻力、报告生成和可视化功能
支持多周期分析（15分钟、60分钟、日线）
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional
import pandas as pd

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_fetcher import FuturesDataFetcher
from indicators import TechnicalIndicators
from pattern_recognizer import KLinePatternRecognizer
from support_resistance import SupportResistanceAnalyzer
from trend_analyzer import TrendAnalyzer
from report_generator import TechnicalReportGenerator
from chart_visualizer import ChartDataGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FuturesAnalyzer:
    """期货K线自动分析器（支持多周期分析）"""

    def __init__(self, output_dir: str = "output"):
        """
        初始化分析器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 初始化各个模块
        self.data_fetcher = FuturesDataFetcher()
        self.pattern_recognizer = KLinePatternRecognizer()
        self.support_analyzer = SupportResistanceAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.report_generator = TechnicalReportGenerator()
        self.chart_generator = ChartDataGenerator()

        logger.info("期货K线自动分析器初始化完成")

    def analyze(
        self,
        symbol: str = "rb888",
        days: int = 30,
        save_chart: bool = True,
        save_report: bool = True
    ) -> dict:
        """
        执行完整的多周期分析流程

        Args:
            symbol: 期货品种代码
            days: 获取天数
            save_chart: 是否保存图表数据
            save_report: 是否保存报告

        Returns:
            分析结果字典
        """
        logger.info(f"开始分析 {symbol}...")
        start_time = datetime.now()

        # 1. 获取多周期数据
        logger.info("1/7 获取多周期数据...")
        multi_period_data = self.data_fetcher.get_multi_period_data(symbol=symbol, days=days)

        if not multi_period_data:
            logger.error(f"获取 {symbol} 数据失败")
            return {
                'success': False,
                'error': '数据获取失败',
                'symbol': symbol
            }

        data_summary = ", ".join([f"{k}:{len(v)}条" for k, v in multi_period_data.items()])
        logger.info(f"获取到 {data_summary}")

        # 2. 计算技术指标（所有周期）
        logger.info("2/7 计算技术指标...")
        for period, df in multi_period_data.items():
            multi_period_data[period] = TechnicalIndicators.add_all_indicators(df)
            logger.info(f"  {period}: 添加指标完成")

        # 3. 多周期趋势分析
        logger.info("3/7 多周期趋势分析...")
        multi_period_analysis = {}
        period_names = {'5min': '5分钟', '15min': '15分钟', '60min': '60分钟', 'day': '日线'}
        for period, df in multi_period_data.items():
            analysis = self.trend_analyzer.analyze_trend(df, period_names.get(period, period))
            multi_period_analysis[period] = analysis
            logger.info(f"  {period}: {analysis.get('trend', 'unknown')}")

        # 4. 支撑位和阻力位分析（使用日线数据）
        logger.info("4/7 支撑阻力分析...")
        day_df = multi_period_data.get('day', pd.DataFrame())
        support_resistance = self.support_analyzer.analyze_comprehensive(day_df)
        logger.info(f"  阻力位: {len(support_resistance.get('resistance_levels', []))}个")
        logger.info(f"  支撑位: {len(support_resistance.get('support_levels', []))}个")

        # 5. K线形态识别（所有周期）
        logger.info("5/7 K线形态识别...")
        all_patterns = {}
        for period, df in multi_period_data.items():
            patterns = self.pattern_recognizer.get_recent_patterns(df, n=10)
            all_patterns[period] = patterns
            logger.info(f"  {period}: 识别到 {len(patterns)} 个形态")

        # 6. 生成完整技术分析报告
        logger.info("6/7 生成技术分析报告...")
        full_report = self.report_generator.generate_full_report(
            symbol,
            multi_period_data,
            multi_period_analysis,
            support_resistance,
            all_patterns
        )

        # 打印报告预览
        logger.info("\n" + "=" * 70)
        logger.info("【技术分析报告预览】")
        logger.info("=" * 70)
        for line in full_report.split('\n')[:30]:  # 显示前30行
            logger.info(line)
        if len(full_report.split('\n')) > 30:
            logger.info("... (更多内容请查看保存的报告文件)")

        # 7. 生成图表数据（所有周期）
        chart_data = None
        if save_chart:
            logger.info("7/7 生成图表数据...")

            # 准备图表数据：包含所有周期的DataFrame
            chart_data = {'symbol': symbol}
            for period, df in multi_period_data.items():
                chart_data[period] = df

            # 准备报告数据
            report_data = {}
            for period, analysis in multi_period_analysis.items():
                report_data[period] = {
                    'trend': analysis.get('trend'),
                    'ma_trend': analysis.get('ma_trend', {}),
                    'macd_trend': analysis.get('macd_trend', {}),
                    'kdj_trend': analysis.get('kdj_trend', {}),
                    'patterns': all_patterns.get(period, [])
                }

                # 添加技术指标数值
                df = multi_period_data[period]
                if not df.empty:
                    latest = df.iloc[-1]
                    report_data[period]['indicators'] = {
                        'ma5': latest.get('ma5'),
                        'ma10': latest.get('ma10'),
                        'ma20': latest.get('ma20'),
                        'macd': latest.get('macd'),
                        'kdj_k': latest.get('kdj_k'),
                        'rsi': latest.get('rsi')
                    }

            # 添加支撑阻力数据
            report_data['support_resistance'] = support_resistance

            # 生成HTML查看器
            chart_html_path = os.path.join(self.output_dir, f"{symbol}_chart.html")
            self.chart_generator.generate_html_viewer(chart_data, report_data, chart_html_path)

            logger.info(f"  图表已保存: {chart_html_path}")

        # 保存报告（同时保存 TXT 和 HTML 格式）
        report_txt_path = None
        report_html_path = None
        if save_report:
            # 保存文本格式
            report_txt_path = os.path.join(self.output_dir, f"{symbol}_report.txt")
            with open(report_txt_path, 'w', encoding='utf-8') as f:
                f.write(full_report)
            logger.info(f"  文本报告已保存: {report_txt_path}")

            # 保存 HTML 格式
            report_html_path = os.path.join(self.output_dir, f"{symbol}_report.html")
            self.chart_generator.generate_html_report(symbol, full_report, report_html_path)

        # 计算耗时
        elapsed = (datetime.now() - start_time).total_seconds()

        # 返回结果
        result = {
            'success': True,
            'symbol': symbol,
            'data_summary': data_summary,
            'full_report': full_report,
            'chart_html_path': os.path.join(self.output_dir, f"{symbol}_chart.html") if save_chart else None,
            'report_txt_path': report_txt_path,
            'report_html_path': report_html_path,
            'elapsed_time': elapsed
        }

        logger.info(f"分析完成! 耗时: {elapsed:.2f}秒")
        return result

    def print_result(self, result: dict) -> None:
        """打印分析结果"""
        print("\n" + "=" * 70)
        print(f"{'期货K线自动分析报告':^70}")
        print("=" * 70)

        if not result.get('success'):
            print(f"\n❌ 分析失败: {result.get('error', '未知错误')}")
            return

        print(f"\n📊 品种: {result['symbol']}")
        print(f"📅 数据: {result.get('data_summary', '')}")
        print(f"⏱️  耗时: {result.get('elapsed_time', 0):.2f}秒")

        # 打印完整报告
        if result.get('full_report'):
            print("\n" + result['full_report'])

        print("\n" + "=" * 70)
        print("📁 输出文件:")
        if result.get('chart_html_path'):
            print(f"  📊 K线图: {result['chart_html_path']}")
        if result.get('report_path'):
            print(f"  📄 分析报告: {result['report_path']}")
        print("=" * 70 + "\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="期货K线自动分析工具（支持多周期）")
    parser.add_argument(
        'symbol',
        nargs='?',
        default='eg2605',
        help='期货品种代码 (默认: rb888 螺纹钢)'
    )
    parser.add_argument(
        '-d', '--days',
        type=int,
        default=30,
        help='获取天数 (默认: 30)'
    )
    parser.add_argument(
        '-o', '--output',
        default='output',
        help='输出目录 (默认: output)'
    )
    parser.add_argument(
        '--no-chart',
        action='store_true',
        help='不生成图表'
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='不保存报告'
    )

    args = parser.parse_args()

    # 创建分析器
    analyzer = FuturesAnalyzer(output_dir=args.output)

    # 执行分析
    result = analyzer.analyze(
        symbol=args.symbol,
        days=args.days,
        save_chart=not args.no_chart,
        save_report=not args.no_report
    )

    # 打印结果
    analyzer.print_result(result)

    # 返回退出码
    return 0 if result.get('success') else 1


if __name__ == "__main__":
    sys.exit(main())
