/**
 * AkshareDatafeed - klinecharts pro 数据适配器
 * 连接前端图表与后端 API
 */
class AkshareDatafeed {
    constructor() {
        this.apiBase = '/api';
    }

    /**
     * 搜索期货品种
     * @param {string} search - 搜索关键词
     * @returns {Promise<Array>} 品种列表
     */
    async searchSymbols(search) {
        try {
            const url = search
                ? `${this.apiBase}/symbols?q=${encodeURIComponent(search)}`
                : `${this.apiBase}/symbols`;

            const response = await this._fetchWithErrorHandling(url);

            if (!response.ok) {
                throw new Error(`搜索失败: ${response.status}`);
            }

            const symbols = await response.json();

            // 转换为 klinecharts pro 格式
            return symbols.map(s => ({
                ...s,
                fullCode: `${s.exchange}.${s.ticker}`,
            }));
        } catch (error) {
            console.error('搜索品种失败:', error);
            this._showError(`搜索品种失败: ${error.message}`);
            return [];
        }
    }

    /**
     * 获取历史 K 线数据
     * @param {SymbolInfo} symbol - 品种信息对象 { ticker, exchange, ... }
     * @param {Period} period - 周期对象 { multiplier, timespan, text }
     * @param {number} from - 开始时间戳 (毫秒)
     * @param {number} to - 结束时间戳 (毫秒)
     * @returns {Promise<Array>} K 线数据数组
     */
    async getHistoryKLineData(symbol, period, from, to) {
        try {
            // 从对象中提取值
            const symbolCode = symbol.ticker;  // 从对象获取 ticker
            const periodCode = period.text;    // 使用 text 字段 (如 '1d')

            // 构建查询参数
            const params = new URLSearchParams({
                symbol: symbolCode,
                period: periodCode
            });

            if (from) {
                params.append('from', from);
            }
            if (to) {
                params.append('to', to);
            }

            const url = `${this.apiBase}/history?${params.toString()}`;
            const response = await this._fetchWithErrorHandling(url);

            if (!response.ok) {
                throw new Error(`获取历史数据失败: ${response.status}`);
            }

            const data = await response.json();

            // 数据已经在后端转换为正确格式，直接返回
            return data;
        } catch (error) {
            console.error('获取历史数据失败:', error);
            this._showError(`获取历史数据失败: ${error.message}`);
            return [];
        }
    }

    /**
     * 订阅实时数据
     * 注意: 当前版本不实现实时订阅，仅作为接口占位
     * @param {SymbolInfo} symbol - 品种信息对象
     * @param {Period} period - 周期对象
     * @param {Function} callback - 数据回调函数
     * @returns {Promise<void>}
     */
    async subscribe(symbol, period, callback) {
        const symbolCode = symbol.ticker;
        const periodCode = period.text;
        console.log(`订阅请求: ${symbolCode} (${periodCode}) - 功能待实现`);
        return Promise.resolve();
    }

    /**
     * 取消订阅
     * @param {SymbolInfo} symbol - 品种信息对象
     * @param {Period} period - 周期对象
     * @returns {Promise<void>}
     */
    async unsubscribe(symbol, period) {
        const symbolCode = symbol.ticker;
        const periodCode = period.text;
        console.log(`取消订阅: ${symbolCode} (${periodCode})`);
        return Promise.resolve();
    }

    /**
     * 带错误处理的请求方法
     * @param {string} url - 请求 URL
     * @param {RequestInit} options - 请求选项
     * @returns {Promise<Response>}
     */
    async _fetchWithErrorHandling(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            return response;
        } catch (error) {
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('无法连接到服务器，请检查网络连接');
            }
            throw error;
        }
    }

    /**
     * 显示错误信息
     * @param {string} message - 错误信息
     */
    _showError(message) {
        const errorBanner = document.getElementById('chart-error');
        if (errorBanner) {
            errorBanner.textContent = message;
            errorBanner.style.display = 'flex';

            // 5秒后自动隐藏
            setTimeout(() => {
                errorBanner.style.display = 'none';
            }, 5000);
        }
    }
}

// 导出为全局变量
window.AkshareDatafeed = AkshareDatafeed;
