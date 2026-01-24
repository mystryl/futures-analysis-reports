"""
Flask 图表服务器
期货 K 线图表应用的主入口
"""

from flask import Flask, render_template

def create_app():
    """应用工厂函数"""
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    # 注册蓝图（将在后续任务中添加）
    # from api import chart_bp
    # app.register_blueprint(chart_bp)

    @app.route('/')
    def index():
        """主页路由"""
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
