/**
 * ChartApp - klinecharts pro 应用初始化和管理
 */
class ChartApp {
    constructor() {
        this.chart = null;
        this.datafeed = null;
        this.currentSymbol = 'RB2505'; // 默认品种
        this.currentPeriod = '1d'; // 默认周期
    }

    /**
     * 初始化应用
     */
    async init() {
        try {
            console.log('初始化 ChartApp...');

            // 初始化 datafeed
            this.datafeed = new AkshareDatafeed();

            // 显示加载状态
            this._showLoading('正在初始化图表...');

            // 创建图表实例
            await this._createChart();

            // 加载初始数据
            await this._loadInitialData();

            // 隐藏加载状态
            this._hideLoading();

            // 更新连接状态
            this._updateStatus('connected', '已连接');

            console.log('ChartApp 初始化完成');
        } catch (error) {
            console.error('初始化失败:', error);
            this._hideLoading();
            this._showError(`初始化失败: ${error.message}`);
            this._updateStatus('error', '连接失败');
        }
    }

    /**
     * 创建图表实例
     */
    async _createChart() {
        const chartContainer = document.getElementById('chart');
        if (!chartContainer) {
            throw new Error('找不到图表容器');
        }

        // 检查 klinechartspro 是否可用
        if (typeof klinechartspro === 'undefined') {
            throw new Error('klinechartspro 库未加载');
        }

        // 创建图表配置
        const config = {
            container: chartContainer,
            styles: {
                candle: {
                    type: 'candle_solid',
                    bar: {
                        upColor: '#26a69a',
                        downColor: '#ef5350',
                        noChangeColor: '#888888'
                    },
                    tooltip: {
                        showRule: 'always',
                        showType: 'standard',
                        labels: ['时间: ', '开: ', '高: ', '低: ', '收: ', '成交量: '],
                        text: {
                            size: 12,
                            color: '#D9D9D9'
                        }
                    },
                    priceMark: {
                        show: true,
                        high: {
                            show: true,
                            color: '#26a69a',
                            textSize: 10
                        },
                        low: {
                            show: true,
                            color: '#ef5350',
                            textSize: 10
                        },
                        last: {
                            show: true,
                            upColor: '#26a69a',
                            downColor: '#ef5350',
                            noChangeColor: '#888888',
                            text: {
                                show: true,
                                size: 12
                            }
                        }
                    }
                },
                indicator: {
                    tooltip: {
                        showRule: 'always',
                        showType: 'standard',
                        text: {
                            size: 12,
                            color: '#D9D9D9'
                        }
                    }
                },
                xAxis: {
                    show: true,
                    axisLine: {
                        show: true,
                        color: '#888888'
                    },
                    tickLine: {
                        show: true,
                        length: 5,
                        color: '#888888'
                    },
                    tickText: {
                        show: true,
                        color: '#D9D9D9',
                        size: 12
                    }
                },
                yAxis: {
                    show: true,
                    position: 'right',
                    axisLine: {
                        show: true,
                        color: '#888888'
                    },
                    tickLine: {
                        show: true,
                        length: 5,
                        color: '#888888'
                    },
                    tickText: {
                        show: true,
                        color: '#D9D9D9',
                        size: 12
                    }
                },
                grid: {
                    show: true,
                    horizontal: {
                        show: true,
                        size: 1,
                        color: '#292929',
                        style: 'dashed'
                    },
                    vertical: {
                        show: true,
                        size: 1,
                        color: '#292929',
                        style: 'dashed'
                    }
                },
                crosshair: {
                    show: true,
                    horizontal: {
                        show: true,
                        line: {
                            show: true,
                            style: 'dashed',
                            dashValue: [4, 2],
                            size: 1,
                            color: '#888888'
                        },
                        text: {
                            show: true,
                            color: '#D9D9D9',
                            size: 12,
                            backgroundColor: '#505050'
                        }
                    },
                    vertical: {
                        show: true,
                        line: {
                            show: true,
                            style: 'dashed',
                            dashValue: [4, 2],
                            size: 1,
                            color: '#888888'
                        },
                        text: {
                            show: true,
                            color: '#D9D9D9',
                            size: 12,
                            backgroundColor: '#505050'
                        }
                    }
                },
                layout: {
                    background: {
                        type: 'solid',
                        color: '#1a1a1a'
                    },
                    textColor: '#D9D9D9'
                }
            },
            locale: 'zh-CN',
            timeframe: '1D',
            customApi: {
                getDatafeed: () => this.datafeed
            }
        };

        // 使用 klinechartspro 创建图表
        this.chart = klinechartspro.KLineChartPro.init(config);
        console.log('图表实例已创建');
    }

    /**
     * 加载初始数据
     */
    async _loadInitialData() {
        try {
            // 计算时间范围 - 最近3个月
            const to = Date.now();
            const from = to - (90 * 24 * 60 * 60 * 1000);

            // 获取历史数据
            const klineData = await this.datafeed.getHistoryKLineData(
                this.currentSymbol,
                this.currentPeriod,
                from,
                to
            );

            if (klineData.length === 0) {
                throw new Error('没有获取到数据');
            }

            // 设置图表数据
            this.chart.applyNewData(klineData);
            console.log(`已加载 ${klineData.length} 条 K 线数据`);
        } catch (error) {
            console.error('加载初始数据失败:', error);
            throw error;
        }
    }

    /**
     * 显示加载状态
     * @param {string} message - 加载提示信息
     */
    _showLoading(message = '正在加载...') {
        const loadingOverlay = document.getElementById('loading');
        if (loadingOverlay) {
            const loadingText = loadingOverlay.querySelector('p');
            if (loadingText) {
                loadingText.textContent = message;
            }
            loadingOverlay.classList.remove('hidden');
        }
    }

    /**
     * 隐藏加载状态
     */
    _hideLoading() {
        const loadingOverlay = document.getElementById('loading');
        if (loadingOverlay) {
            loadingOverlay.classList.add('hidden');
        }
    }

    /**
     * 显示错误信息
     * @param {string} message - 错误信息
     */
    _showError(message) {
        const errorBanner = document.getElementById('chart-error');
        if (errorBanner) {
            errorBanner.innerHTML = `
                <span>${message}</span>
                <button class="close-btn" onclick="this.parentElement.style.display='none'">&times;</button>
            `;
            errorBanner.style.display = 'flex';

            // 10秒后自动隐藏
            setTimeout(() => {
                errorBanner.style.display = 'none';
            }, 10000);
        }
    }

    /**
     * 更新连接状态
     * @param {string} status - 状态 ('connecting', 'connected', 'error')
     * @param {string} text - 状态文本
     */
    _updateStatus(status, text) {
        const statusIndicator = document.getElementById('status');
        if (!statusIndicator) return;

        const statusDot = statusIndicator.querySelector('.status-dot');
        const statusText = statusIndicator.querySelector('.status-text');

        if (statusText) {
            statusText.textContent = text;
        }

        if (statusDot) {
            statusDot.classList.remove('connected', 'error');

            if (status === 'connected') {
                statusDot.classList.add('connected');
            } else if (status === 'error') {
                statusDot.classList.add('error');
            }
        }
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM 加载完成，初始化应用...');
    const app = new ChartApp();
    app.init().catch(error => {
        console.error('应用初始化失败:', error);
    });
});
