# Copyright 2026 Windows Stock Monitor Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
K线图绘制模块
使用matplotlib在tkinter中绘制K线图
"""
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from datetime import datetime

class KLineChart(tk.Frame):
    """K线图组件"""
    
    def __init__(self, parent, kline_data, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.kline_data = kline_data
        self.setup_chart()
    
    def setup_chart(self):
        """设置图表"""
        # 设置matplotlib中文字体和样式
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建图表
        self.figure = Figure(figsize=(6, 4), dpi=80, facecolor='#1e1e1e')
        self.ax = self.figure.add_subplot(111)
        
        # 设置背景色
        self.ax.set_facecolor('#1e1e1e')
        self.figure.patch.set_facecolor('#1e1e1e')
        
        # 绘制K线
        self.draw_kline()
        
        # 创建画布
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def draw_kline(self):
        """绘制K线图"""
        if not self.kline_data:
            return
        
        # 准备数据
        dates = []
        opens = []
        closes = []
        highs = []
        lows = []
        
        for item in self.kline_data:
            # 解析日期
            date_str = item['date']
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                try:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                except:
                    continue
            
            dates.append(date_obj)
            opens.append(item['open'])
            closes.append(item['close'])
            highs.append(item['high'])
            lows.append(item['low'])
        
        if not dates:
            return
        
        # 绘制K线
        width = 0.6
        
        for i in range(len(dates)):
            # 判断涨跌
            if closes[i] >= opens[i]:
                # 上涨或平盘 - 红色
                color = '#ff4d4f'
                body_color = '#ff4d4f'
            else:
                # 下跌 - 绿色
                color = '#52c41a'
                body_color = '#52c41a'
            
            # 绘制上下影线
            self.ax.plot([i, i], [lows[i], highs[i]], color=color, linewidth=1)
            
            # 绘制实体
            height = abs(closes[i] - opens[i])
            bottom = min(opens[i], closes[i])
            
            rect = Rectangle((i - width/2, bottom), width, height,
                           facecolor=body_color, edgecolor=color, linewidth=1)
            self.ax.add_patch(rect)
        
        # 设置x轴标签
        if len(dates) > 10:
            # 如果数据点太多，只显示部分日期
            step = len(dates) // 10
            x_ticks = list(range(0, len(dates), step))
            x_labels = [dates[i].strftime('%m-%d') for i in x_ticks]
        else:
            x_ticks = list(range(len(dates)))
            x_labels = [d.strftime('%m-%d') for d in dates]
        
        self.ax.set_xticks(x_ticks)
        self.ax.set_xticklabels(x_labels, rotation=45, ha='right', color='white', fontsize=8)
        
        # 设置y轴标签颜色
        self.ax.tick_params(axis='y', colors='white', labelsize=8)
        
        # 设置网格
        self.ax.grid(True, alpha=0.2, color='#444444', linestyle='--', linewidth=0.5)
        
        # 设置边框颜色
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#444444')
        
        # 设置标题
        self.ax.set_title('日K线图', color='white', fontsize=10, pad=10)
        
        # 设置y轴标签
        self.ax.set_ylabel('价格', color='white', fontsize=9)
        
        # 自动调整布局
        self.figure.tight_layout()
    
    def update_data(self, kline_data):
        """更新数据"""
        self.kline_data = kline_data
        self.ax.clear()
        self.draw_kline()
        self.canvas.draw()

if __name__ == "__main__":
    # 测试代码
    root = tk.Tk()
    root.title("K线图测试")
    root.geometry("800x600")
    
    # 模拟数据
    test_data = [
        {'date': '2024-01-01', 'open': 100, 'close': 105, 'high': 107, 'low': 98, 'volume': 1000000},
        {'date': '2024-01-02', 'open': 105, 'close': 103, 'high': 108, 'low': 102, 'volume': 1200000},
        {'date': '2024-01-03', 'open': 103, 'close': 110, 'high': 112, 'low': 101, 'volume': 1500000},
        {'date': '2024-01-04', 'open': 110, 'close': 108, 'high': 113, 'low': 107, 'volume': 1300000},
        {'date': '2024-01-05', 'open': 108, 'close': 112, 'high': 115, 'low': 106, 'volume': 1400000},
    ]
    
    chart = KLineChart(root, test_data, bg='#1e1e1e')
    chart.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
