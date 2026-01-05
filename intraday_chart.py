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
分时图绘制模块
"""
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class IntradayChart(tk.Frame):
    """分时图组件"""
    
    def __init__(self, parent, intraday_data, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.intraday_data = intraday_data
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
        
        # 绘制分时图
        self.draw_intraday()
        
        # 创建画布
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def draw_intraday(self):
        """绘制分时图"""
        if not self.intraday_data:
            return
        
        # 提取数据
        prices = [item['price'] for item in self.intraday_data]
        yestclose = self.intraday_data[0]['yestclose']
        
        # 绘制价格曲线
        self.ax.plot(range(len(prices)), prices, color='#2196F3', linewidth=1.5)
        
        # 绘制昨收平线
        self.ax.axhline(y=yestclose, color='#888888', linestyle='--', linewidth=0.8, alpha=0.5)
        
        # 填充涨跌区域
        for i in range(len(prices)):
            if prices[i] > yestclose:
                self.ax.fill_between([i, i+1] if i < len(prices)-1 else [i], yestclose, prices[i], 
                                    color='#ff4d4f', alpha=0.1)
            else:
                self.ax.fill_between([i, i+1] if i < len(prices)-1 else [i], prices[i], yestclose,
                                    color='#52c41a', alpha=0.1)
        
        # 设置x轴标签（时间）
        if len(self.intraday_data) > 10:
            step = len(self.intraday_data) // 6
            x_ticks = list(range(0, len(self.intraday_data), step))
            x_labels = [self.intraday_data[i]['time'] for i in x_ticks]
        else:
            x_ticks = list(range(len(self.intraday_data)))
            x_labels = [item['time'] for item in self.intraday_data]
        
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
        self.ax.set_title('分时图', color='white', fontsize=10, pad=10)
        
        # 设置y轴标签
        self.ax.set_ylabel('价格', color='white', fontsize=9)
        
        # 自动调整布局
        self.figure.tight_layout()
