"""
K线图可视化数据生成模块

生成与 klinecharts 前端库兼容的数据格式，并创建HTML查看器
支持多周期切换和报告显示
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class ChartDataGenerator:
    """K线图数据生成器"""

    def __init__(self):
        pass

    def _convert_timestamp(self, ts) -> int:
        """将时间戳转换为毫秒级时间戳"""
        if pd.isna(ts):
            return int(datetime.now().timestamp() * 1000)

        if isinstance(ts, str):
            dt = pd.to_datetime(ts)
        elif isinstance(ts, (pd.Timestamp, datetime)):
            dt = ts
        else:
            return int(datetime.now().timestamp() * 1000)

        return int(dt.timestamp() * 1000)

    def generate_kline_data(self, df: pd.DataFrame, max_points: int = 500) -> List[Dict[str, Any]]:
        """
        生成 klinecharts 兼容的K线数据

        klinecharts 9.x/10.x 数据格式: 对象数组
        每个对象包含: timestamp, open, high, low, close, volume
        """
        if df.empty:
            return []

        kline_data = []

        for _, row in df.iterrows():
            item = {
                'timestamp': self._convert_timestamp(row.get('date', row.name)),
                'open': float(row['open']) if pd.notna(row['open']) else 0,
                'high': float(row['high']) if pd.notna(row['high']) else 0,
                'low': float(row['low']) if pd.notna(row['low']) else 0,
                'close': float(row['close']) if pd.notna(row['close']) else 0,
                'volume': float(row['volume']) if pd.notna(row['volume']) else 0
            }
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

        Args:
            chart_data: 包含所有周期数据的字典 {'5min': data, '15min': data, ...}
            report_data: 包含所有周期报告的字典
            output_path: 输出路径
        """
        symbol = chart_data.get('symbol', 'unknown')

        # 准备各周期的K线数据
        periods_data = {}
        period_names = {
            '5min': '5分钟',
            '15min': '15分钟',
            '60min': '60分钟',
            'day': '日线'
        }

        for period in ['5min', '15min', '60min', 'day']:
            if period in chart_data and not chart_data[period].empty:
                periods_data[period] = json.dumps(
                    self.generate_kline_data(chart_data[period]),
                    ensure_ascii=False
                )

        # 获取默认周期数据（15分钟）
        default_data = periods_data.get('15min', periods_data.get('day', '[]'))

        # 准备报告HTML内容
        report_html = self._generate_report_html(report_data, symbol)

        # 读取本地 klinecharts.min.js 内容
        script_dir = os.path.dirname(os.path.abspath(__file__))
        js_path = os.path.join(script_dir, 'output', 'klinecharts.min.js')

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
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #e0e0e0;
        }}
        .container {{
            max-width: 1800px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #e94560;
            font-size: 28px;
            margin-bottom: 5px;
        }}
        .header p {{
            color: #888;
            font-size: 14px;
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
        }}
        .report-section {{
            background: #0f0f23;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            max-height: 800px;
            overflow-y: auto;
        }}
        .report-section::-webkit-scrollbar {{
            width: 8px;
        }}
        .report-section::-webkit-scrollbar-track {{
            background: #1a1a2e;
            border-radius: 4px;
        }}
        .report-section::-webkit-scrollbar-thumb {{
            background: #e94560;
            border-radius: 4px;
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
        .period-tab:hover {{
            background: #2a2a3e;
            color: #e94560;
        }}
        .period-tab.active {{
            background: #e94560;
            color: #fff;
            border-color: #e94560;
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
        .report-section h2 {{
            color: #e94560;
            font-size: 20px;
            margin-bottom: 15px;
            border-bottom: 1px solid #2a2a3e;
            padding-bottom: 10px;
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
        .trend-up {{
            color: #26a69a;
        }}
        .trend-down {{
            color: #ef5350;
        }}
        .trend-neutral {{
            color: #888;
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
            <h1>📈 {0} 多周期技术分析图表</h1>
            <p>5分钟 · 15分钟 · 60分钟 · 日线 | 实时切换</p>
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

        // 初始化图表
        function initChart() {{
            try {{
                // 使用 klinecharts 9.x 正确的初始化方式
                chart = klinecharts.init('chart', {{
                    styles: {{
                        candle: {{
                            type: 'candle_solid',
                            bar: {{
                                upColor: '#ef5350',      // 上涨红色
                                downColor: '#26a69a',    // 下跌绿色
                                noChangeColor: '#888888'
                            }},
                            tooltip: {{
                                showRule: 'always',
                                showType: 'standard',
                                labels: ['时间: ', '开: ', '高: ', '低: ', '收: ', '涨跌幅: '],
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
                                    text: {{
                                        show: true,
                                        size: 12
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});

                // 创建技术指标窗口
                chart.createIndicator('MA', false, {{ id: 'candle_pane' }});
                chart.createIndicator('VOL', false, {{ height: 80 }});
                chart.createIndicator('MACD', false, {{ height: 80 }});

                loadPeriodData('day');
                console.log('✅ K线图表加载成功');
            }} catch (error) {{
                console.error('❌ K线图表加载失败:', error);
                showError('图表加载失败: ' + error.message);
            }}
        }}

        // 加载指定周期数据
        function loadPeriodData(period) {{
            const data = periodData[period];
            if (!data || data.length === 0) {{
                showError('暂无' + getPeriodName(period) + '数据');
                return;
            }}

            chart.applyNewData(data);
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
            // 隐藏所有周期报告，显示当前周期报告
            document.querySelectorAll('.period-report').forEach(el => {{
                el.style.display = 'none';
            }});
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
                currentPeriod = period;
                loadPeriodData(period);
            }});
        }});

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
            periods_data.get('day', '[]')
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

        logger.info(f"HTML查看器已生成: {output_path}")

    def _generate_report_html(self, report_data: Dict[str, Any], symbol: str) -> str:
        """生成报告HTML内容"""
        html_parts = []

        # 添加标题
        html_parts.append(f'<h2>📊 {symbol} 技术分析报告</h2>')

        # 各周期报告
        period_names = {
            'day': '日线',
            '60min': '60分钟',
            '15min': '15分钟',
            '5min': '5分钟'
        }

        for period in ['day', '60min', '15min', '5min']:
            if period not in report_data:
                continue

            period_name = period_names.get(period, period)
            data = report_data[period]

            html_parts.append(f'''
            <div class="period-report" id="report-{period}" style="display: {'block' if period == 'day' else 'none'};">
                <h3>{period_name}分析</h3>
            ''')

            # 趋势分析
            if 'trend' in data:
                trend = data['trend']
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
                    signal_icon = '🟢' if pattern['signal'] == 'bullish' else '🔴' if pattern['signal'] == 'bearish' else '⚪'
                    html_parts.append(f'<li>{signal_icon} {pattern["pattern"]}</li>')
                html_parts.append('</ul>')

            html_parts.append('</div>')

        # 支撑阻力（只在日线显示）
        if 'support_resistance' in report_data:
            sr = report_data['support_resistance']
            html_parts.append('''
            <div class="period-report" id="report-support" style="display: block;">
                <h3>支撑阻力</h3>
            ''')

            current_price = sr.get('current_price', 0)
            html_parts.append(f'<p><strong>当前价格:</strong> {current_price:.2f}</p>')

            if sr.get('resistance_levels'):
                html_parts.append('<p><strong>上方阻力位:</strong></p><ul>')
                for i, r in enumerate(sr['resistance_levels'][:3], 1):
                    distance = ((r - current_price) / current_price * 100) if current_price > 0 else 0
                    html_parts.append(f'<li>R{i}: {r:.2f} ({distance:+.2f}%)</li>')
                html_parts.append('</ul>')

            if sr.get('support_levels'):
                html_parts.append('<p><strong>下方支撑位:</strong></p><ul>')
                for i, s in enumerate(sr['support_levels'][:3], 1):
                    distance = ((current_price - s) / current_price * 100) if current_price > 0 else 0
                    html_parts.append(f'<li>S{i}: {s:.2f} ({-distance:.2f}%)</li>')
                html_parts.append('</ul>')

            html_parts.append('</div>')

        return ''.join(html_parts)

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
