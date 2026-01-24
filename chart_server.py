"""
Flask 图表服务器
期货 K 线图表应用的主入口
"""

from flask import Flask, render_template, send_from_directory
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 Flask 应用
app = Flask(__name__,
            static_folder='static',
            template_folder='templates')

# 注册 API 蓝图
from api import register_blueprints
register_blueprints(app)

# 路由定义
@app.route('/')
def index():
    """主页面"""
    return send_from_directory('static', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """静态文件服务"""
    return send_from_directory('static', path)


if __name__ == '__main__':
    logger.info("启动 Flask 服务器: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)
