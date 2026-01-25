#!/usr/bin/env python3
"""批量回测脚本 - 支持多个品种"""

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import FuturesAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 要回测的品种列表
SYMBOLS = ['RB2605', 'HC2605', 'I2605', 'JM2605']
DAYS = 30  # 获取天数
# 使用脚本所在目录作为输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

def batch_analyze():
    """批量执行回测分析"""
    start_time = datetime.now()
    results = {}

    # 创建分析器
    analyzer = FuturesAnalyzer(output_dir=OUTPUT_DIR)

    for symbol in SYMBOLS:
        logger.info(f"\n{'='*60}")
        logger.info(f"开始分析 {symbol} ({list(SYMBOLS).index(symbol)+1}/{len(SYMBOLS)})")
        logger.info(f"{'='*60}\n")

        try:
            result = analyzer.analyze(
                symbol=symbol.lower(),
                days=DAYS,
                save_chart=True,
                save_report=True
            )
            results[symbol] = result

            if result.get('success'):
                logger.info(f"✓ {symbol} 分析成功")
            else:
                logger.error(f"✗ {symbol} 分析失败: {result.get('error')}")

        except Exception as e:
            logger.error(f"✗ {symbol} 分析异常: {e}")
            results[symbol] = {'success': False, 'error': str(e)}

    # 生成汇总索引页面
    logger.info("\n生成汇总索引页面...")
    generate_index_html(results, OUTPUT_DIR)

    # 打印汇总结果
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*60}")
    print(f"{'批量回测完成':^60}")
    print(f"{'='*60}")
    print(f"总耗时: {elapsed:.2f}秒\n")

    for symbol, result in results.items():
        status = "✓ 成功" if result.get('success') else "✗ 失败"
        print(f"  {symbol}: {status}")
        if result.get('chart_html_path'):
            print(f"    图表: {result['chart_html_path']}")
        if result.get('report_path'):
            print(f"    报告: {result['report_path']}")

def generate_index_html(results, output_dir):
    """生成汇总索引页面"""
    # 品种名称映射
    symbol_names = {
        'RB2605': '螺纹钢 2605',
        'HC2605': '热卷 2605',
        'I2605': '铁矿 2605',
        'JM2605': '焦煤 2605',
    }

    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>期货回测报告汇总</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #eee;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 40px;
            font-size: 0.9rem;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        .card:hover {
            transform: translateY(-4px);
            border-color: rgba(0, 212, 255, 0.3);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 16px;
        }
        .card-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #00d4ff, #7c3aed);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: bold;
            margin-right: 16px;
        }
        .card-title {
            font-size: 1.3rem;
            font-weight: 600;
        }
        .card-links {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .card-link {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            text-decoration: none;
            color: #ccc;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }
        .card-link:hover {
            background: rgba(0, 212, 255, 0.1);
            border-color: rgba(0, 212, 255, 0.3);
            color: #00d4ff;
        }
        .card-link .icon {
            margin-right: 10px;
            font-size: 1.1rem;
        }
        .status-success {
            color: #4ade80;
        }
        .status-failed {
            color: #ef4444;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            color: #666;
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 期货回测报告汇总</h1>
        <p class="subtitle">RB2605 · HC2605 · I2605 · JM2605</p>

        <div class="grid">
"""

    for symbol in SYMBOLS:
        result = results.get(symbol, {})
        success = result.get('success', False)
        symbol_lower = symbol.lower()
        status_class = 'status-success' if success else 'status-failed'
        status_text = '✓ 分析成功' if success else '✗ 分析失败'

        html_content += f"""
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">{symbol[:2]}</div>
                    <div>
                        <div class="card-title">{symbol_names.get(symbol, symbol)}</div>
                        <div class="{status_class}" style="font-size: 0.85rem; margin-top: 4px;">{status_text}</div>
                    </div>
                </div>
                <div class="card-links">
"""

        if success:
            html_content += f"""
                    <a href="{symbol_lower}_chart.html" class="card-link" target="_blank">
                        <span class="icon">📈</span>
                        <span>K线图表</span>
                    </a>
                    <a href="{symbol_lower}_report.html" class="card-link" target="_blank">
                        <span class="icon">📄</span>
                        <span>HTML报告</span>
                    </a>
                    <a href="{symbol_lower}_report.txt" class="card-link" target="_blank">
                        <span class="icon">📝</span>
                        <span>文本报告</span>
                    </a>
"""
        else:
            html_content += f"""
                    <div class="card-link" style="opacity: 0.5;">
                        <span class="icon">⚠️</span>
                        <span>{result.get('error', '数据获取失败')}</span>
                    </div>
"""

        html_content += """
                </div>
            </div>
"""

    html_content += f"""
        </div>

        <div class="footer">
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 8px;">期货回测系统 © 2026</p>
        </div>
    </div>
</body>
</html>
"""

    # 写入索引文件
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"索引页面已生成: {index_path}")

if __name__ == "__main__":
    batch_analyze()
