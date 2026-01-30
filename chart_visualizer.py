"""
K线图可视化数据生成模块

生成与 klinecharts 前端库兼容的数据格式，并创建HTML查看器
支持多周期切换和报告显示
使用 klinecharts 9.8 技术栈
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class ChartConfig:
    """图表配置常量"""

    # 支持的周期
    SUPPORTED_PERIODS = ['5min', '15min', '60min', 'day']

    # 周期显示名称映射
    PERIOD_NAMES = {
        '5min': '5分钟',
        '15min': '15分钟',
        '60min': '60分钟',
        'day': '日线'
    }

    # 默认最大数据点数
    DEFAULT_MAX_POINTS = 500

    # 图表尺寸配置
    CHART_HEIGHT = 600
    INDICATOR_HEIGHT = 80

    # 颜色配置（红涨绿跌）
    UP_COLOR = '#ef5350'
    DOWN_COLOR = '#26a69a'
    NO_CHANGE_COLOR = '#888888'

    # 主题色配置
    DARK_THEME_COLORS = {
        'background': '#0f0f23',
        'grid': '#2a2a3e',
        'text': '#d9d9d9',
        'border': '#2a2a3e',
        'hover_bg': '#2a2a3e',
        'hover_text': '#e94560',
        'scrollbar_track': '#1a1a2e',
        'scrollbar_thumb': '#e94560'
    }

    LIGHT_THEME_COLORS = {
        'background': '#ffffff',
        'grid': '#e0e0e0',
        'text': '#2c3e50',
        'border': '#d0d0d0',
        'hover_bg': '#e0e0e0',
        'hover_text': '#c41e3a',
        'scrollbar_track': '#f0f0f0',
        'scrollbar_thumb': '#c41e3a'
    }


class StyleConfig:
    """样式配置类 - 消除暗色/浅色主题的重复代码"""

    @staticmethod
    def get_base_candle_styles() -> Dict[str, Any]:
        """获取基础蜡烛图样式配置"""
        return {
            'type': 'candle_solid',
            'bar': {
                'upColor': ChartConfig.UP_COLOR,
                'downColor': ChartConfig.DOWN_COLOR,
                'noChangeColor': ChartConfig.NO_CHANGE_COLOR,
                'upBorderColor': ChartConfig.UP_COLOR,
                'downBorderColor': ChartConfig.DOWN_COLOR,
                'noChangeBorderColor': ChartConfig.NO_CHANGE_COLOR,
                'upWickColor': ChartConfig.UP_COLOR,
                'downWickColor': ChartConfig.DOWN_COLOR,
                'noChangeWickColor': ChartConfig.NO_CHANGE_COLOR
            }
        }

    @staticmethod
    def get_tooltip_config(text_color: str) -> Dict[str, Any]:
        """获取 tooltip 配置"""
        return {
            'showRule': 'always',
            'showType': 'standard',
            'custom': [
                {'title': '时间', 'value': '{time}'},
                {'title': '开', 'value': '{open}'},
                {'title': '高', 'value': '{high}'},
                {'title': '低', 'value': '{low}'},
                {'title': '收', 'value': '{close}'},
                {'title': '成交量', 'value': '{volume}'}
            ],
            'text': {
                'size': 12,
                'color': text_color
            }
        }

    @staticmethod
    def get_price_mark_config() -> Dict[str, Any]:
        """获取价格标记配置"""
        return {
            'show': True,
            'high': {
                'show': True,
                'color': ChartConfig.UP_COLOR,
                'textSize': 10
            },
            'low': {
                'show': True,
                'color': ChartConfig.DOWN_COLOR,
                'textSize': 10
            },
            'last': {
                'show': True,
                'upColor': ChartConfig.UP_COLOR,
                'downColor': ChartConfig.DOWN_COLOR,
                'noChangeColor': ChartConfig.NO_CHANGE_COLOR,
                'line': {
                    'show': True,
                    'style': 'dashed',
                    'dashedValue': [4, 4],
                    'size': 1
                },
                'text': {
                    'show': True,
                    'style': 'fill',
                    'size': 12,
                    'color': '#ffffff'
                }
            }
        }

    @staticmethod
    def get_grid_config(color: str) -> Dict[str, Any]:
        """获取网格配置"""
        return {
            'show': True,
            'horizontal': {
                'show': True,
                'size': 1,
                'color': color,
                'style': 'dashed',
                'dashedValue': [2, 2]
            },
            'vertical': {
                'show': True,
                'size': 1,
                'color': color,
                'style': 'dashed',
                'dashedValue': [2, 2]
            }
        }

    @staticmethod
    def get_indicator_config(text_color: str) -> Dict[str, Any]:
        """获取指标配置"""
        return {
            'ohlc': {
                'upColor': f'rgba(239, 83, 80, 0.7)',
                'downColor': f'rgba(38, 166, 154, 0.7)',
                'noChangeColor': '#888888'
            },
            'bars': [{
                'style': 'fill',
                'borderStyle': 'solid',
                'borderSize': 1,
                'upColor': f'rgba(239, 83, 80, 0.7)',
                'downColor': f'rgba(38, 166, 154, 0.7)',
                'noChangeColor': '#888888'
            }],
            'lines': [
                {'style': 'solid', 'smooth': False, 'size': 1, 'color': '#FF9600'},
                {'style': 'solid', 'smooth': False, 'size': 1, 'color': '#935EBD'},
                {'style': 'solid', 'smooth': False, 'size': 1, 'color': '#2196F3'}
            ],
            'tooltip': {
                'showRule': 'always',
                'showType': 'standard',
                'showName': True,
                'showParams': True,
                'text': {
                    'size': 12,
                    'color': text_color
                }
            }
        }

    @staticmethod
    def get_axis_config(text_color: str) -> Dict[str, Any]:
        """获取坐标轴配置"""
        return {
            'show': True,
            'size': 'auto',
            'axisLine': {'show': True, 'color': '#888888', 'size': 1},
            'tickText': {'show': True, 'color': text_color, 'size': 12},
            'tickLine': {'show': True, 'size': 1, 'length': 3, 'color': '#888888'}
        }

    @staticmethod
    def get_crosshair_config() -> Dict[str, Any]:
        """获取十字光标配置"""
        return {
            'show': True,
            'horizontal': {
                'show': True,
                'line': {'show': True, 'style': 'dashed', 'dashedValue': [4, 2], 'size': 1, 'color': '#888888'},
                'text': {'show': True, 'style': 'fill', 'color': '#ffffff', 'size': 12, 'backgroundColor': '#686D76'}
            },
            'vertical': {
                'show': True,
                'line': {'show': True, 'style': 'dashed', 'dashedValue': [4, 2], 'size': 1, 'color': '#888888'},
                'text': {'show': True, 'style': 'fill', 'color': '#ffffff', 'size': 12, 'backgroundColor': '#686D76'}
            }
        }

    @classmethod
    def get_dark_styles(cls) -> Dict[str, Any]:
        """获取暗色主题完整样式配置"""
        return {
            'grid': cls.get_grid_config(ChartConfig.DARK_THEME_COLORS['grid']),
            'candle': {
                **cls.get_base_candle_styles(),
                'tooltip': cls.get_tooltip_config(ChartConfig.DARK_THEME_COLORS['text']),
                'priceMark': cls.get_price_mark_config()
            },
            'indicator': cls.get_indicator_config(ChartConfig.DARK_THEME_COLORS['text']),
            'xAxis': cls.get_axis_config(ChartConfig.DARK_THEME_COLORS['text']),
            'yAxis': {**cls.get_axis_config(ChartConfig.DARK_THEME_COLORS['text']), 'position': 'right'},
            'crosshair': cls.get_crosshair_config()
        }

    @classmethod
    def get_light_styles(cls) -> Dict[str, Any]:
        """获取浅色主题完整样式配置"""
        return {
            'grid': cls.get_grid_config(ChartConfig.LIGHT_THEME_COLORS['grid']),
            'candle': {
                **cls.get_base_candle_styles(),
                'tooltip': cls.get_tooltip_config(ChartConfig.LIGHT_THEME_COLORS['text']),
                'priceMark': cls.get_price_mark_config()
            },
            'indicator': cls.get_indicator_config(ChartConfig.LIGHT_THEME_COLORS['text']),
            'xAxis': cls.get_axis_config(ChartConfig.LIGHT_THEME_COLORS['text']),
            'yAxis': {**cls.get_axis_config(ChartConfig.LIGHT_THEME_COLORS['text']), 'position': 'right'},
            'crosshair': cls.get_crosshair_config()
        }


class ChartDataConverter:
    """数据转换器 - 处理数据到 klinecharts 格式的转换"""

    @staticmethod
    def convert_timestamp(ts) -> Optional[int]:
        """将时间戳转换为毫秒级时间戳

        Returns:
            int or None: 返回毫秒级时间戳，无效时间戳返回 None
        """
        if pd.isna(ts):
            logger.warning("Invalid timestamp encountered (NaN), skipping record")
            return None

        try:
            if isinstance(ts, str):
                dt = pd.to_datetime(ts)
            elif isinstance(ts, (pd.Timestamp, datetime)):
                dt = ts
            else:
                logger.warning(f"Invalid timestamp type: {type(ts)}, skipping record")
                return None

            return int(dt.timestamp() * 1000)
        except Exception as e:
            logger.warning(f"Timestamp conversion error: {e}, skipping record")
            return None

    @classmethod
    def convert_to_kline_format(cls, df: pd.DataFrame, max_points: int = None) -> List[Dict[str, Any]]:
        """
        转换数据为 klinecharts 兼容格式

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            max_points: 最大数据点数，None 表示使用默认值

        Returns:
            klinecharts 9.8 格式的对象数组
        """
        if max_points is None:
            max_points = ChartConfig.DEFAULT_MAX_POINTS

        if df.empty:
            return []

        kline_data = []

        for _, row in df.iterrows():
            timestamp = cls.convert_timestamp(row.get('date', row.name))
            if timestamp is None:
                continue

            item = {
                'timestamp': timestamp,
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'volume': float(row['volume']) if pd.notna(row['volume']) else None
            }

            if any(item[k] is not None for k in ['open', 'high', 'low', 'close']):
                kline_data.append(item)

        if len(kline_data) > max_points:
            kline_data = kline_data[-max_points:]

        return kline_data


class ChartDataGenerator:
    """K线图数据生成器"""

    def __init__(self):
        pass

    def _convert_timestamp(self, ts) -> Optional[int]:
        """将时间戳转换为毫秒级时间戳（向后兼容方法）"""
        return ChartDataConverter.convert_timestamp(ts)

    def generate_kline_data(self, df: pd.DataFrame, max_points: int = None) -> List[Dict[str, Any]]:
        """
        生成 klinecharts 兼容的K线数据

        klinecharts 9.8 数据格式: 对象数组
        每个对象包含: timestamp, open, high, low, close, volume

        Args:
            df: 包含 OHLCV 数据的 DataFrame
            max_points: 最大数据点数，None 表示使用默认值

        Note:
            NaN 值将被转换为 None (JavaScript null)，而非 0
            时间戳无效的记录将被跳过
        """
        if max_points is None:
            max_points = ChartConfig.DEFAULT_MAX_POINTS

        if df.empty:
            return []

        kline_data = []

        for _, row in df.iterrows():
            timestamp = self._convert_timestamp(row.get('date', row.name))
            if timestamp is None:
                continue  # 跳过时间戳无效的记录

            item = {
                'timestamp': timestamp,
                'open': float(row['open']) if pd.notna(row['open']) else None,
                'high': float(row['high']) if pd.notna(row['high']) else None,
                'low': float(row['low']) if pd.notna(row['low']) else None,
                'close': float(row['close']) if pd.notna(row['close']) else None,
                'volume': float(row['volume']) if pd.notna(row['volume']) else None
            }

            # 只有当至少有一个有效价格数据时才添加
            if any(item[k] is not None for k in ['open', 'high', 'low', 'close']):
                kline_data.append(item)

        # 只返回最近的数据，避免数据量过大
        if len(kline_data) > max_points:
            kline_data = kline_data[-max_points:]

        return kline_data

    def generate_full_chart_data(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """生成完整的图表数据包"""
        kline_data = self.generate_kline_data(df)

        return {
            'symbol': symbol,
            'dataCount': len(kline_data),
            'kline': kline_data
        }

    def generate_html_viewer(
        self,
        chart_data: Dict[str, Any],
        report_data: Dict[str, Any],
        output_path: str = "chart_viewer.html"
    ) -> None:
        """
        生成独立的HTML查看器
        包含多周期切换功能和报告显示
        使用 klinecharts 9.8 API

        Args:
            chart_data: 包含所有周期数据的字典 {'5min': data, '15min': data, ...}
            report_data: 包含所有周期报告的字典
            output_path: 输出路径
        """
        symbol = chart_data.get('symbol', 'unknown')

        # 准备各周期的K线数据
        periods_data = {}

        for period in ChartConfig.SUPPORTED_PERIODS:
            if period in chart_data and not chart_data[period].empty:
                periods_data[period] = json.dumps(
                    self.generate_kline_data(chart_data[period]),
                    ensure_ascii=False
                )

        # 准备报告HTML内容
        report_html = self._generate_report_html(report_data, symbol)

        # 获取生成时间
        generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 使用 .format() 方法生成HTML
        html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{0} 多周期K线图</title>
    <script src="klinecharts.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        /* 暗色主题（默认） */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e0e0e0;
            transition: all 0.3s ease;
        }}

        body.light-theme {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
            color: #2c3e50;
        }}

        .container {{
            max-width: 1800px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}

        .header-left {{
            flex: 1;
        }}

        .header h1 {{
            color: #e94560;
            font-size: 28px;
            margin-bottom: 5px;
        }}

        body.light-theme .header h1 {{
            color: #c41e3a;
        }}

        .header p {{
            color: #888;
            font-size: 14px;
        }}

        body.light-theme .header p {{
            color: #666;
        }}

        .header .generation-time {{
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }}

        body.light-theme .header .generation-time {{
            color: #888;
        }}

        /* 主题切换按钮 */
        .theme-toggle {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .theme-btn {{
            padding: 8px 16px;
            border: 1px solid #e94560;
            background: transparent;
            color: #e94560;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }}

        .theme-btn:hover {{
            background: #e94560;
            color: #fff;
        }}

        body.light-theme .theme-btn {{
            border-color: #c41e3a;
            color: #c41e3a;
        }}

        body.light-theme .theme-btn:hover {{
            background: #c41e3a;
            color: #fff;
        }}

        .main-content {{
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 20px;
        }}

        .chart-section {{
            background: #0f0f23;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }}

        body.light-theme .chart-section {{
            background: #ffffff;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .report-section {{
            background: #0f0f23;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            max-height: 800px;
            overflow-y: auto;
            transition: all 0.3s ease;
        }}

        body.light-theme .report-section {{
            background: #ffffff;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .report-section::-webkit-scrollbar {{
            width: 8px;
        }}

        .report-section::-webkit-scrollbar-track {{
            background: #1a1a2e;
            border-radius: 4px;
        }}

        body.light-theme .report-section::-webkit-scrollbar-track {{
            background: #f0f0f0;
        }}

        .report-section::-webkit-scrollbar-thumb {{
            background: #e94560;
            border-radius: 4px;
        }}

        body.light-theme .report-section::-webkit-scrollbar-thumb {{
            background: #c41e3a;
        }}

        .period-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}

        .period-tab {{
            padding: 10px 20px;
            background: #1a1a2e;
            border: 1px solid #2a2a3e;
            border-radius: 8px;
            cursor: pointer;
            color: #888;
            transition: all 0.3s;
            font-size: 14px;
        }}

        body.light-theme .period-tab {{
            background: #f0f0f0;
            border-color: #d0d0d0;
        }}

        .period-tab:hover {{
            background: #2a2a3e;
            color: #e94560;
        }}

        body.light-theme .period-tab:hover {{
            background: #e0e0e0;
            color: #c41e3a;
        }}

        .period-tab.active {{
            background: #e94560;
            color: #fff;
            border-color: #e94560;
        }}

        body.light-theme .period-tab.active {{
            background: #c41e3a;
            border-color: #c41e3a;
        }}

        .indicator-toggles {{
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }}

        .indicator-toggle {{
            padding: 8px 16px;
            background: #1a1a2e;
            border: 1px solid #2a2a3e;
            border-radius: 8px;
            cursor: pointer;
            color: #888;
            transition: all 0.3s;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        body.light-theme .indicator-toggle {{
            background: #f0f0f0;
            border-color: #d0d0d0;
        }}

        .indicator-toggle:hover {{
            background: #2a2a3e;
            color: #e94560;
        }}

        body.light-theme .indicator-toggle:hover {{
            background: #e0e0e0;
            color: #c41e3a;
        }}

        .indicator-toggle.active {{
            background: #26a69a;
            color: #fff;
            border-color: #26a69a;
        }}

        body.light-theme .indicator-toggle.active {{
            background: #26a69a;
            border-color: #26a69a;
        }}

        .indicator-toggle .checkbox {{
            width: 16px;
            height: 16px;
            border: 2px solid currentColor;
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .indicator-toggle.active .checkbox::after {{
            content: '✓';
            font-size: 12px;
        }}

        #chart {{
            width: 100%;
            height: 600px;
        }}

        .info {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }}

        .info-item {{
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 10px;
            text-align: center;
        }}

        body.light-theme .info-item {{
            background: rgba(0,0,0,0.05);
        }}

        .info-item .label {{
            color: #888;
            font-size: 12px;
            margin-bottom: 5px;
        }}

        .info-item .value {{
            color: #e94560;
            font-size: 18px;
            font-weight: bold;
        }}

        body.light-theme .info-item .value {{
            color: #c41e3a;
        }}

        .report-section h2 {{
            color: #e94560;
            font-size: 20px;
            margin-bottom: 15px;
            border-bottom: 1px solid #2a2a3e;
            padding-bottom: 10px;
        }}

        body.light-theme .report-section h2 {{
            color: #c41e3a;
            border-bottom-color: #d0d0d0;
        }}

        .report-section h3 {{
            color: #26a69a;
            font-size: 16px;
            margin-top: 15px;
            margin-bottom: 10px;
        }}

        .report-section p {{
            color: #aaa;
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 8px;
        }}

        body.light-theme .report-section p {{
            color: #555;
        }}

        .report-section ul {{
            margin-left: 20px;
            margin-bottom: 10px;
        }}

        .report-section li {{
            color: #aaa;
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 5px;
        }}

        body.light-theme .report-section li {{
            color: #555;
        }}

        .trend-up {{
            color: #ef5350;
        }}

        .trend-down {{
            color: #26a69a;
        }}

        .trend-neutral {{
            color: #888;
        }}

        .support-line {{
            color: #26a69a;
        }}

        .resistance-line {{
            color: #ef5350;
        }}

        .error {{
            color: #ef5350;
            text-align: center;
            padding: 20px;
            background: rgba(239, 83, 80, 0.1);
            border-radius: 8px;
            margin: 20px;
        }}

        @media (max-width: 1200px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>📈 {0} 多周期技术分析图表</h1>
                <p>5分钟 · 15分钟 · 60分钟 · 日线 | 实时切换</p>
                <p class="generation-time">生成时间: {6}</p>
            </div>
            <div class="theme-toggle">
                <button class="theme-btn" id="theme-toggle-btn">🌙 暗色主题</button>
            </div>
        </div>

        <div class="main-content">
            <!-- 左侧图表区域 -->
            <div class="chart-section">
                <div class="period-tabs">
                    <div class="period-tab" data-period="5min">5分钟</div>
                    <div class="period-tab" data-period="15min">15分钟</div>
                    <div class="period-tab" data-period="60min">60分钟</div>
                    <div class="period-tab active" data-period="day">日线</div>
                </div>

                <!-- 指标切换按钮 -->
                <div class="indicator-toggles">
                    <div class="indicator-toggle active" data-indicator="VOL">
                        <span class="checkbox"></span>
                        <span>成交量</span>
                    </div>
                    <div class="indicator-toggle active" data-indicator="MACD">
                        <span class="checkbox"></span>
                        <span>MACD</span>
                    </div>
                    <div class="indicator-toggle" data-indicator="KDJ">
                        <span class="checkbox"></span>
                        <span>KDJ</span>
                    </div>
                </div>

                <div class="info">
                    <div class="info-item">
                        <div class="label">品种代码</div>
                        <div class="value">{0}</div>
                    </div>
                    <div class="info-item">
                        <div class="label">当前周期</div>
                        <div class="value" id="current-period">日线</div>
                    </div>
                    <div class="info-item">
                        <div class="label">数据条数</div>
                        <div class="value" id="data-count">-</div>
                    </div>
                </div>

                <div id="chart"></div>
                <div id="error-msg" class="error" style="display:none;"></div>
            </div>

            <!-- 右侧报告区域 -->
            <div class="report-section">
                {1}
            </div>
        </div>
    </div>

    <script>
        // 各周期K线数据
        const periodData = {{
            '5min': {2},
            '15min': {3},
            '60min': {4},
            'day': {5}
        }};

        // 当前选中的周期
        let currentPeriod = 'day';
        let chart = null;
        let isDarkTheme = true;
        let indicators = {{}};

        // 指标状态（默认显示成交量和 MACD）
        let indicatorStates = {{
            'VOL': true,
            'MACD': true,
            'KDJ': false
        }};

        // 暗色主题样式配置 - 红涨绿跌（中国习惯）
        const darkStyles = {{
            grid: {{
                show: true,
                horizontal: {{
                    show: true,
                    size: 1,
                    color: '#2a2a3e',
                    style: 'dashed',
                    dashedValue: [2, 2]
                }},
                vertical: {{
                    show: true,
                    size: 1,
                    color: '#2a2a3e',
                    style: 'dashed',
                    dashedValue: [2, 2]
                }}
            }},
            candle: {{
                type: 'candle_solid',
                bar: {{
                    upColor: '#ef5350',           // 上涨红色
                    downColor: '#26a69a',         // 下跌绿色
                    noChangeColor: '#888888',
                    upBorderColor: '#ef5350',     // 上涨边框红色
                    downBorderColor: '#26a69a',   // 下跌边框绿色
                    noChangeBorderColor: '#888888',
                    upWickColor: '#ef5350',       // 上涨影线红色
                    downWickColor: '#26a69a',     // 下跌影线绿色
                    noChangeWickColor: '#888888'
                }},
                tooltip: {{
                    showRule: 'always',
                    showType: 'standard',
                    custom: [
                        {{ title: '时间', value: '{{time}}' }},
                        {{ title: '开', value: '{{open}}' }},
                        {{ title: '高', value: '{{high}}' }},
                        {{ title: '低', value: '{{low}}' }},
                        {{ title: '收', value: '{{close}}' }},
                        {{ title: '成交量', value: '{{volume}}' }}
                    ],
                    text: {{
                        size: 12,
                        color: '#d9d9d9'
                    }}
                }},
                priceMark: {{
                    show: true,
                    high: {{
                        show: true,
                        color: '#ef5350',
                        textSize: 10
                    }},
                    low: {{
                        show: true,
                        color: '#26a69a',
                        textSize: 10
                    }},
                    last: {{
                        show: true,
                        upColor: '#ef5350',
                        downColor: '#26a69a',
                        noChangeColor: '#888888',
                        line: {{
                            show: true,
                            style: 'dashed',
                            dashedValue: [4, 4],
                            size: 1
                        }},
                        text: {{
                            show: true,
                            style: 'fill',
                            size: 12,
                            color: '#ffffff'
                        }}
                    }}
                }}
            }},
            indicator: {{
                ohlc: {{
                    upColor: 'rgba(239, 83, 80, 0.7)',
                    downColor: 'rgba(38, 166, 154, 0.7)',
                    noChangeColor: '#888888'
                }},
                bars: [{{
                    style: 'fill',
                    borderStyle: 'solid',
                    borderSize: 1,
                    upColor: 'rgba(239, 83, 80, 0.7)',
                    downColor: 'rgba(38, 166, 154, 0.7)',
                    noChangeColor: '#888888'
                }}],
                lines: [
                    {{ style: 'solid', smooth: false, size: 1, color: '#FF9600' }},
                    {{ style: 'solid', smooth: false, size: 1, color: '#935EBD' }},
                    {{ style: 'solid', smooth: false, size: 1, color: '#2196F3' }}
                ],
                tooltip: {{
                    showRule: 'always',
                    showType: 'standard',
                    showName: true,
                    showParams: true,
                    text: {{
                        size: 12,
                        color: '#d9d9d9'
                    }}
                }}
            }},
            xAxis: {{
                show: true,
                size: 'auto',
                axisLine: {{ show: true, color: '#888888', size: 1 }},
                tickText: {{ show: true, color: '#d9d9d9', size: 12 }},
                tickLine: {{ show: true, size: 1, length: 3, color: '#888888' }}
            }},
            yAxis: {{
                show: true,
                size: 'auto',
                position: 'right',
                axisLine: {{ show: true, color: '#888888', size: 1 }},
                tickText: {{ show: true, color: '#d9d9d9', size: 12 }},
                tickLine: {{ show: true, size: 1, length: 3, color: '#888888' }}
            }},
            crosshair: {{
                show: true,
                horizontal: {{
                    show: true,
                    line: {{ show: true, style: 'dashed', dashedValue: [4, 2], size: 1, color: '#888888' }},
                    text: {{ show: true, style: 'fill', color: '#ffffff', size: 12, backgroundColor: '#686D76' }}
                }},
                vertical: {{
                    show: true,
                    line: {{ show: true, style: 'dashed', dashedValue: [4, 2], size: 1, color: '#888888' }},
                    text: {{ show: true, style: 'fill', color: '#ffffff', size: 12, backgroundColor: '#686D76' }}
                }}
            }}
        }};

        // 浅色主题样式配置 - 红涨绿跌（中国习惯）
        const lightStyles = {{
            grid: {{
                show: true,
                horizontal: {{
                    show: true,
                    size: 1,
                    color: '#e0e0e0',
                    style: 'dashed',
                    dashedValue: [2, 2]
                }},
                vertical: {{
                    show: true,
                    size: 1,
                    color: '#e0e0e0',
                    style: 'dashed',
                    dashedValue: [2, 2]
                }}
            }},
            candle: {{
                type: 'candle_solid',
                bar: {{
                    upColor: '#ef5350',           // 上涨红色
                    downColor: '#26a69a',         // 下跌绿色
                    noChangeColor: '#888888',
                    upBorderColor: '#ef5350',     // 上涨边框红色
                    downBorderColor: '#26a69a',   // 下跌边框绿色
                    noChangeBorderColor: '#888888',
                    upWickColor: '#ef5350',       // 上涨影线红色
                    downWickColor: '#26a69a',     // 下跌影线绿色
                    noChangeWickColor: '#888888'
                }},
                tooltip: {{
                    showRule: 'always',
                    showType: 'standard',
                    custom: [
                        {{ title: '时间', value: '{{time}}' }},
                        {{ title: '开', value: '{{open}}' }},
                        {{ title: '高', value: '{{high}}' }},
                        {{ title: '低', value: '{{low}}' }},
                        {{ title: '收', value: '{{close}}' }},
                        {{ title: '成交量', value: '{{volume}}' }}
                    ],
                    text: {{
                        size: 12,
                        color: '#2c3e50'
                    }}
                }},
                priceMark: {{
                    show: true,
                    high: {{
                        show: true,
                        color: '#ef5350',
                        textSize: 10
                    }},
                    low: {{
                        show: true,
                        color: '#26a69a',
                        textSize: 10
                    }},
                    last: {{
                        show: true,
                        upColor: '#ef5350',
                        downColor: '#26a69a',
                        noChangeColor: '#888888',
                        line: {{
                            show: true,
                            style: 'dashed',
                            dashedValue: [4, 4],
                            size: 1
                        }},
                        text: {{
                            show: true,
                            style: 'fill',
                            size: 12,
                            color: '#ffffff'
                        }}
                    }}
                }}
            }},
            indicator: {{
                ohlc: {{
                    upColor: 'rgba(239, 83, 80, 0.7)',
                    downColor: 'rgba(38, 166, 154, 0.7)',
                    noChangeColor: '#888888'
                }},
                bars: [{{
                    style: 'fill',
                    borderStyle: 'solid',
                    borderSize: 1,
                    upColor: 'rgba(239, 83, 80, 0.7)',
                    downColor: 'rgba(38, 166, 154, 0.7)',
                    noChangeColor: '#888888'
                }}],
                lines: [
                    {{ style: 'solid', smooth: false, size: 1, color: '#FF9600' }},
                    {{ style: 'solid', smooth: false, size: 1, color: '#935EBD' }},
                    {{ style: 'solid', smooth: false, size: 1, color: '#2196F3' }}
                ],
                tooltip: {{
                    showRule: 'always',
                    showType: 'standard',
                    showName: true,
                    showParams: true,
                    text: {{
                        size: 12,
                        color: '#2c3e50'
                    }}
                }}
            }},
            xAxis: {{
                show: true,
                size: 'auto',
                axisLine: {{ show: true, color: '#888888', size: 1 }},
                tickText: {{ show: true, color: '#2c3e50', size: 12 }},
                tickLine: {{ show: true, size: 1, length: 3, color: '#888888' }}
            }},
            yAxis: {{
                show: true,
                size: 'auto',
                position: 'right',
                axisLine: {{ show: true, color: '#888888', size: 1 }},
                tickText: {{ show: true, color: '#2c3e50', size: 12 }},
                tickLine: {{ show: true, size: 1, length: 3, color: '#888888' }}
            }},
            crosshair: {{
                show: true,
                horizontal: {{
                    show: true,
                    line: {{ show: true, style: 'dashed', dashedValue: [4, 2], size: 1, color: '#888888' }},
                    text: {{ show: true, style: 'fill', color: '#ffffff', size: 12, backgroundColor: '#686D76' }}
                }},
                vertical: {{
                    show: true,
                    line: {{ show: true, style: 'dashed', dashedValue: [4, 2], size: 1, color: '#888888' }},
                    text: {{ show: true, style: 'fill', color: '#ffffff', size: 12, backgroundColor: '#686D76' }}
                }}
            }}
        }};

        // 初始化图表 - 使用 klinecharts 9.8 API
        function initChart() {{
            try {{
                // klinecharts 9.8 初始化方式
                chart = klinecharts.init('chart', {{
                    styles: darkStyles,
                    layout: [
                        {{
                            type: 'candle',
                            content: [],
                            options: {{ id: 'candle_pane' }}
                        }}
                    ]
                }});

                // 创建 MA 指标（在蜡烛图中显示）
                chart.createIndicator('MA', true, {{ id: 'candle_pane' }});

                // 根据默认状态创建指标
                if (indicatorStates['VOL']) {{
                    indicators['VOL'] = chart.createIndicator('VOL', false, {{ height: 80 }});
                }}
                if (indicatorStates['MACD']) {{
                    indicators['MACD'] = chart.createIndicator('MACD', false, {{ height: 80 }});
                }}
                if (indicatorStates['KDJ']) {{
                    indicators['KDJ'] = chart.createIndicator('KDJ', false, {{ height: 80 }});
                }}

                // 加载初始数据
                const data = periodData['day'];
                if (data && data.length > 0) {{
                    chart.applyNewData(data);
                }}

                console.log('✅ K线图表加载成功 (klinecharts 9.8)');
            }} catch (error) {{
                console.error('❌ K线图表加载失败:', error);
                showError('图表加载失败: ' + error.message);
            }}
        }}

        // 切换主题
        function toggleTheme() {{
            isDarkTheme = !isDarkTheme;
            const body = document.body;
            const btn = document.getElementById('theme-toggle-btn');

            if (isDarkTheme) {{
                body.classList.remove('light-theme');
                btn.textContent = '🌙 暗色主题';
                if (chart) {{
                    chart.setStyles(darkStyles);
                }}
            }} else {{
                body.classList.add('light-theme');
                btn.textContent = '☀️ 浅色主题';
                if (chart) {{
                    chart.setStyles(lightStyles);
                }}
            }}
        }}

        // 切换指标显示
        function toggleIndicator(indicatorName) {{
            if (!chart) return;

            const btn = document.querySelector(`.indicator-toggle[data-indicator="${{indicatorName}}"]`);

            if (indicatorStates[indicatorName]) {{
                // 隐藏指标
                if (indicators[indicatorName]) {{
                    try {{
                        chart.removeIndicator(indicators[indicatorName]);
                    }} catch (e) {{
                        console.warn('移除指标失败:', e);
                    }}
                    delete indicators[indicatorName];
                }}
                indicatorStates[indicatorName] = false;
            }} else {{
                // 显示指标 - 先检查是否已存在
                if (indicators[indicatorName]) {{
                    console.warn('指标已存在，跳过创建');
                    return;
                }}
                indicators[indicatorName] = chart.createIndicator(indicatorName, false, {{ height: 80 }});
                indicatorStates[indicatorName] = true;
            }}

            // 更新按钮状态
            if (btn) {{
                if (indicatorStates[indicatorName]) {{
                    btn.classList.add('active');
                }} else {{
                    btn.classList.remove('active');
                }}
            }}
        }}

        // 恢复指标状态（用于切换周期后）
        function restoreIndicators() {{
            if (!chart) return;

            // 清除所有已跟踪的指标实例（不包括MA，它始终显示）
            for (let key in indicators) {{
                if (indicators[key]) {{
                    try {{
                        chart.removeIndicator(indicators[key]);
                    }} catch (e) {{
                        console.warn('清除指标失败:', e);
                    }}
                }}
            }}
            indicators = {{}};

            // MA指标始终显示，重新创建
            chart.createIndicator('MA', true, {{ id: 'candle_pane' }});

            // 根据当前状态重新创建指标
            if (indicatorStates['VOL']) {{
                indicators['VOL'] = chart.createIndicator('VOL', false, {{ height: 80 }});
            }}
            if (indicatorStates['MACD']) {{
                indicators['MACD'] = chart.createIndicator('MACD', false, {{ height: 80 }});
            }}
            if (indicatorStates['KDJ']) {{
                indicators['KDJ'] = chart.createIndicator('KDJ', false, {{ height: 80 }});
            }}
        }}

        // 加载指定周期数据
        function loadPeriodData(period) {{
            if (!chart) return;

            const data = periodData[period];
            if (!data || data.length === 0) {{
                showError('暂无' + getPeriodName(period) + '数据');
                return;
            }}

            currentPeriod = period;

            // klinecharts 9.8: 使用 applyNewData 加载新数据
            chart.applyNewData(data);

            // 恢复指标状态
            restoreIndicators();

            document.getElementById('data-count').textContent = data.length;
            document.getElementById('current-period').textContent = getPeriodName(period);

            // 更新报告内容
            updateReport(period);
        }}

        // 获取周期中文名
        function getPeriodName(period) {{
            const names = {{
                '5min': '5分钟',
                '15min': '15分钟',
                '60min': '60分钟',
                'day': '日线'
            }};
            return names[period] || period;
        }}

        // 更新报告内容
        function updateReport(period) {{
            // 隐藏所有周期报告，但保持支撑压力位可见
            document.querySelectorAll('.period-report').forEach(el => {{
                if (el.id !== 'report-support') {{
                    el.style.display = 'none';
                }}
            }});

            // 确保支撑压力位始终可见
            const supportReport = document.getElementById('report-support');
            if (supportReport) {{
                supportReport.style.display = 'block';
            }}

            // 显示当前周期报告
            const currentReport = document.getElementById('report-' + period);
            if (currentReport) {{
                currentReport.style.display = 'block';
            }}
        }}

        // 显示错误
        function showError(message) {{
            const errorMsg = document.getElementById('error-msg');
            errorMsg.textContent = message;
            errorMsg.style.display = 'block';
            document.getElementById('chart').style.display = 'none';
        }}

        // 周期切换事件
        document.querySelectorAll('.period-tab').forEach(tab => {{
            tab.addEventListener('click', function() {{
                const period = this.getAttribute('data-period');

                // 更新Tab样式
                document.querySelectorAll('.period-tab').forEach(t => {{
                    t.classList.remove('active');
                }});
                this.classList.add('active');

                // 加载新周期数据
                loadPeriodData(period);
            }});
        }});

        // 指标切换事件
        document.querySelectorAll('.indicator-toggle').forEach(toggle => {{
            const indicatorName = toggle.getAttribute('data-indicator');

            // 设置初始状态
            if (indicatorStates[indicatorName]) {{
                toggle.classList.add('active');
            }} else {{
                toggle.classList.remove('active');
            }}

            toggle.addEventListener('click', function() {{
                toggleIndicator(indicatorName);
            }});
        }});

        // 主题切换事件
        document.getElementById('theme-toggle-btn').addEventListener('click', toggleTheme);

        // 响应式
        window.addEventListener('resize', () => {{
            if (chart) {{
                chart.resize();
            }}
        }});

        // 页面加载完成后初始化
        window.addEventListener('DOMContentLoaded', initChart);
    </script>
</body>
</html>'''.format(
            symbol,
            report_html,
            periods_data.get('5min', '[]'),
            periods_data.get('15min', '[]'),
            periods_data.get('60min', '[]'),
            periods_data.get('day', '[]'),
            generation_time  # 新增：报告生成时间
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

        # 复制 klinecharts.min.js 到 output 目录
        import shutil
        source_js = os.path.join(os.path.dirname(__file__), 'static', 'lib', 'klinecharts.min.js')
        target_js = os.path.join(os.path.dirname(output_path), 'klinecharts.min.js')
        if os.path.exists(source_js):
            shutil.copy2(source_js, target_js)
            logger.info(f"JS文件已复制: {target_js}")

        logger.info(f"HTML查看器已生成: {output_path}")

    def _generate_report_html(self, report_data: Dict[str, Any], symbol: str) -> str:
        """生成报告HTML内容"""
        html_parts = []

        # 添加标题
        html_parts.append(f'<h2>📊 {symbol} 技术分析报告</h2>')

        # 首先显示支撑阻力（所有周期通用）
        if 'support_resistance' in report_data:
            sr = report_data['support_resistance']
            html_parts.append('''
            <div class="period-report" id="report-support" style="display: block;">
                <h3>🎯 支撑压力位</h3>
            ''')

            current_price = sr.get('current_price', 0)
            html_parts.append(f'<p><strong>当前价格:</strong> {current_price:.2f}</p>')

            if sr.get('resistance_levels'):
                html_parts.append('<p><strong>上方压力位（阻力）:</strong></p><ul>')
                for i, r in enumerate(sr['resistance_levels'][:3], 1):
                    distance = ((r - current_price) / current_price * 100) if current_price > 0 else 0
                    html_parts.append(f'<li class="resistance-line">R{i}: {r:.2f} ({distance:+.2f}%)</li>')
                html_parts.append('</ul>')

            if sr.get('support_levels'):
                html_parts.append('<p><strong>下方支撑位:</strong></p><ul>')
                for i, s in enumerate(sr['support_levels'][:3], 1):
                    distance = ((current_price - s) / current_price * 100) if current_price > 0 else 0
                    html_parts.append(f'<li class="support-line">S{i}: {s:.2f} ({-distance:.2f}%)</li>')
                html_parts.append('</ul>')

            html_parts.append('</div>')

        # 各周期报告 - 使用 ChartConfig 中的周期配置
        for period in reversed(ChartConfig.SUPPORTED_PERIODS):
            if period not in report_data:
                continue

            period_name = ChartConfig.PERIOD_NAMES.get(period, period)
            data = report_data[period]

            html_parts.append(f'''
            <div class="period-report" id="report-{period}" style="display: {'block' if period == 'day' else 'none'};">
                <h3>{period_name}分析</h3>
            ''')

            # 趋势分析
            if 'trend' in data:
                trend = data['trend']
                # 修改颜色：红色=上涨，绿色=下跌
                trend_class = 'trend-up' if trend == 'uptrend' else 'trend-down' if trend == 'downtrend' else 'trend-neutral'
                trend_text = {'uptrend': '📈 上升', 'downtrend': '📉 下降', 'sideways': '➡️ 震荡'}.get(trend, trend)
                html_parts.append(f'<p class="{trend_class}"><strong>趋势:</strong> {trend_text}</p>')

            # 均线分析
            if 'ma_trend' in data and data['ma_trend']:
                ma = data['ma_trend']
                if ma.get('signal'):
                    html_parts.append(f'<p><strong>均线:</strong> {ma["signal"]}</p>')

            # MACD分析
            if 'macd_trend' in data and data['macd_trend']:
                macd = data['macd_trend']
                if macd.get('signal'):
                    html_parts.append(f'<p><strong>MACD:</strong> {macd["signal"]}</p>')

            # KDJ分析
            if 'kdj_trend' in data and data['kdj_trend']:
                kdj = data['kdj_trend']
                if kdj.get('signal'):
                    html_parts.append(f'<p><strong>KDJ:</strong> {kdj["signal"]}</p>')

            # 技术指标数值
            if 'indicators' in data:
                ind = data['indicators']
                html_parts.append('<p><strong>技术指标:</strong></p><ul>')

                if ind.get('ma5'):
                    html_parts.append(f'<li>MA5: {ind["ma5"]:.2f}</li>')
                if ind.get('ma10'):
                    html_parts.append(f'<li>MA10: {ind["ma10"]:.2f}</li>')
                if ind.get('ma20'):
                    html_parts.append(f'<li>MA20: {ind["ma20"]:.2f}</li>')

                if ind.get('macd') is not None:
                    macd_val = ind['macd']
                    status = '红柱' if macd_val > 0 else '绿柱'
                    html_parts.append(f'<li>MACD: {macd_val:.2f} ({status})</li>')

                if ind.get('kdj_k'):
                    k_val = ind['kdj_k']
                    k_status = '超买' if k_val > 80 else '超卖' if k_val < 20 else '正常'
                    html_parts.append(f'<li>KDJ: {k_val:.2f} ({k_status})</li>')

                if ind.get('rsi'):
                    rsi_val = ind['rsi']
                    rsi_status = '超买' if rsi_val > 70 else '超卖' if rsi_val < 30 else '正常'
                    html_parts.append(f'<li>RSI: {rsi_val:.2f} ({rsi_status})</li>')

                html_parts.append('</ul>')

            # K线形态
            if 'patterns' in data and data['patterns']:
                html_parts.append('<p><strong>K线形态:</strong></p><ul>')
                for pattern in data['patterns'][:5]:  # 最多显示5个
                    signal_icon = '🔴' if pattern['signal'] == 'bullish' else '🟢' if pattern['signal'] == 'bearish' else '⚪'
                    html_parts.append(f'<li>{signal_icon} {pattern["pattern"]}</li>')
                html_parts.append('</ul>')

            html_parts.append('</div>')

        return ''.join(html_parts)

    def generate_html_report(
        self,
        symbol: str,
        text_report: str,
        output_path: str
    ) -> None:
        """
        生成HTML格式的技术分析报告

        Args:
            symbol: 品种代码
            text_report: 文本报告内容
            output_path: 输出路径
        """
        # 将文本报告转换为HTML格式
        html_content = text_report.replace('\n', '<br>\n')

        # 转义特殊字符
        import html as html_module
        html_content = html_module.escape(html_content)

        # 恢复换行标签
        html_content = html_content.replace('&lt;br&gt;', '<br>')

        # 构建HTML文档
        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{symbol.upper()} 技术分析报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #e0e0e0;
            line-height: 1.8;
            transition: all 0.3s ease;
        }}
        body.light-theme {{
            background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
            color: #2c3e50;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(15, 15, 35, 0.8);
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }}
        body.light-theme .container {{
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .header h1 {{
            color: #e94560;
            font-size: 28px;
        }}
        body.light-theme .header h1 {{
            color: #c41e3a;
        }}
        .theme-toggle button {{
            padding: 8px 16px;
            border: 1px solid #e94560;
            background: transparent;
            color: #e94560;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }}
        body.light-theme .theme-toggle button {{
            border-color: #c41e3a;
            color: #c41e3a;
        }}
        .theme-toggle button:hover {{
            background: #e94560;
            color: #fff;
        }}
        body.light-theme .theme-toggle button:hover {{
            background: #c41e3a;
            color: #fff;
        }}
        .back-link {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .back-link a {{
            color: #e94560;
            text-decoration: none;
            padding: 10px 20px;
            border: 1px solid #e94560;
            border-radius: 8px;
            transition: all 0.3s;
        }}
        body.light-theme .back-link a {{
            color: #c41e3a;
            border-color: #c41e3a;
        }}
        .back-link a:hover {{
            background: #e94560;
            color: #fff;
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        body.light-theme .subtitle {{
            color: #666;
        }}
        .report-content {{
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-family: 'Courier New', monospace;
            font-size: 14px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        body.light-theme .report-content {{
            background: rgba(0, 0, 0, 0.02);
            border-color: rgba(0, 0, 0, 0.1);
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 {symbol.upper()} 技术分析报告</h1>
            <div class="theme-toggle">
                <button id="theme-toggle-btn">🌙 暗色主题</button>
            </div>
        </div>
        <p class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div class="report-content">{html_content}</div>
        <div class="footer">
            <p>期货技术分析系统 © 2026</p>
        </div>
    </div>
    <script>
        let isDarkTheme = true;
        function toggleTheme() {{
            isDarkTheme = !isDarkTheme;
            const body = document.body;
            const btn = document.getElementById('theme-toggle-btn');
            if (isDarkTheme) {{
                body.classList.remove('light-theme');
                btn.textContent = '🌙 暗色主题';
            }} else {{
                body.classList.add('light-theme');
                btn.textContent = '☀️ 浅色主题';
            }}
        }}
        document.getElementById('theme-toggle-btn').addEventListener('click', toggleTheme);
    </script>
</body>
</html>'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

        logger.info(f"HTML报告已生成: {output_path}")

    def save_chart_data(self, chart_data: Dict[str, Any], filepath: str) -> None:
        """保存图表数据到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)
        logger.info(f"图表数据已保存到: {filepath}")


def generate_chart_data(symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
    """快捷函数：生成图表数据"""
    generator = ChartDataGenerator()
    return generator.generate_full_chart_data(symbol, df)


if __name__ == "__main__":
    # 测试图表数据生成
    import sys
    sys.path.append('..')
    from data_fetcher import fetch_future_data
    from indicators import add_indicators

    logging.basicConfig(level=logging.INFO)

    symbol = "rb888"
    df = fetch_future_data(symbol, period="day", days=60)
    df = add_indicators(df)

    # 生成图表数据
    generator = ChartDataGenerator()
    chart_data = generator.generate_full_chart_data(symbol, df)

    print(f"\nK线数据条数: {len(chart_data['kline'])}")
    print(f"首条数据: {chart_data['kline'][0]}")

    # 保存数据
    import os
    output_dir = "/Users/mystryl/Documents/Quant/futures_backtest/output"
    os.makedirs(output_dir, exist_ok=True)

    generator.save_chart_data(chart_data, f"{output_dir}/{symbol}_chart.json")

    # 生成HTML查看器
    generator.generate_html_viewer(chart_data, {}, f"{output_dir}/{symbol}_chart.html")

    print(f"\n数据已保存到 {output_dir}/")
