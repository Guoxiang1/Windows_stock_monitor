"""
股票行情悬浮窗主程序
"""
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import threading
import time
from api_client import NetEaseFinanceAPI
from kline_chart import KLineChart

class StockMonitor:
    """股票监控悬浮窗主类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("股票行情监控")
        
        # 加载配置
        self.config_file = "config.json"
        self.load_config()
        
        # API客户端
        self.api = NetEaseFinanceAPI()
        
        # 当前显示模式：'quote'(行情), 'kline'(K线)
        self.display_mode = 'quote'
        
        # 当前选中的股票索引
        self.current_stock_index = 0
        
        # 数据更新线程控制
        self.is_running = True
        self.update_thread = None
        
        # 初始化界面
        self.setup_ui()
        
        # 设置窗口属性
        self.apply_window_settings()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 开始数据更新
        self.start_update_thread()
    
    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # 默认配置
            self.config = {
                "stocks": [
                    {"code": "000001", "name": "上证指数", "market": "sh"}
                ],
                "settings": {
                    "topmost": True,
                    "refresh_interval": 2,
                    "window_width": 400,
                    "window_height": 300
                }
            }
            self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口大小
        width = self.config['settings'].get('window_width', 400)
        height = self.config['settings'].get('window_height', 300)
        self.root.geometry(f"{width}x{height}")
        
        # 主容器
        self.main_frame = tk.Frame(self.root, bg='#1e1e1e')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部工具栏
        self.create_toolbar()
        
        # 内容区域（使用Frame容器来切换显示）
        self.content_frame = tk.Frame(self.main_frame, bg='#1e1e1e')
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建行情显示区域
        self.create_quote_view()
        
        # K线图容器（初始隐藏）
        self.kline_frame = None
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = tk.Frame(self.main_frame, bg='#2d2d2d', height=40)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # 股票选择下拉框
        self.stock_var = tk.StringVar()
        stock_options = [f"{s['name']} ({s['code']})" for s in self.config['stocks']]
        if stock_options:
            self.stock_var.set(stock_options[0])
        
        self.stock_combo = ttk.Combobox(toolbar, textvariable=self.stock_var, 
                                        values=stock_options, state='readonly', width=15)
        self.stock_combo.pack(side=tk.LEFT, padx=5, pady=5)
        self.stock_combo.bind('<<ComboboxSelected>>', self.on_stock_changed)
        
        # 切换K线按钮
        self.toggle_btn = tk.Button(toolbar, text="切换K线", command=self.toggle_display_mode,
                                    bg='#3d3d3d', fg='white', relief=tk.FLAT, padx=10)
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_btn = tk.Button(toolbar, text="刷新", command=self.refresh_data,
                               bg='#3d3d3d', fg='white', relief=tk.FLAT, padx=10)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 管理按钮
        manage_btn = tk.Button(toolbar, text="管理", command=self.open_manage_window,
                              bg='#3d3d3d', fg='white', relief=tk.FLAT, padx=10)
        manage_btn.pack(side=tk.LEFT, padx=5)
        
        # 置顶复选框
        self.topmost_var = tk.BooleanVar(value=self.config['settings'].get('topmost', True))
        topmost_check = tk.Checkbutton(toolbar, text="置顶", variable=self.topmost_var,
                                      command=self.toggle_topmost, bg='#2d2d2d', fg='white',
                                      selectcolor='#3d3d3d', activebackground='#2d2d2d',
                                      activeforeground='white')
        topmost_check.pack(side=tk.RIGHT, padx=5)
    
    def create_quote_view(self):
        """创建行情显示视图"""
        self.quote_frame = tk.Frame(self.content_frame, bg='#1e1e1e')
        self.quote_frame.pack(fill=tk.BOTH, expand=True)
        
        # 股票名称和代码
        self.name_label = tk.Label(self.quote_frame, text="加载中...", 
                                   font=('Arial', 16, 'bold'), bg='#1e1e1e', fg='white')
        self.name_label.pack(pady=10)
        
        # 当前价格
        self.price_label = tk.Label(self.quote_frame, text="--", 
                                    font=('Arial', 32, 'bold'), bg='#1e1e1e', fg='white')
        self.price_label.pack(pady=5)
        
        # 涨跌幅和涨跌额
        self.change_label = tk.Label(self.quote_frame, text="-- (--)", 
                                     font=('Arial', 14), bg='#1e1e1e', fg='white')
        self.change_label.pack(pady=5)
        
        # 详细信息框架
        detail_frame = tk.Frame(self.quote_frame, bg='#1e1e1e')
        detail_frame.pack(pady=20, fill=tk.X, padx=20)
        
        # 左侧信息
        left_frame = tk.Frame(detail_frame, bg='#1e1e1e')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.open_label = tk.Label(left_frame, text="今开: --", 
                                   font=('Arial', 10), bg='#1e1e1e', fg='#888888', anchor='w')
        self.open_label.pack(fill=tk.X)
        
        self.high_label = tk.Label(left_frame, text="最高: --", 
                                   font=('Arial', 10), bg='#1e1e1e', fg='#888888', anchor='w')
        self.high_label.pack(fill=tk.X, pady=5)
        
        self.volume_label = tk.Label(left_frame, text="成交量: --", 
                                     font=('Arial', 10), bg='#1e1e1e', fg='#888888', anchor='w')
        self.volume_label.pack(fill=tk.X)
        
        # 右侧信息
        right_frame = tk.Frame(detail_frame, bg='#1e1e1e')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.yestclose_label = tk.Label(right_frame, text="昨收: --", 
                                        font=('Arial', 10), bg='#1e1e1e', fg='#888888', anchor='w')
        self.yestclose_label.pack(fill=tk.X)
        
        self.low_label = tk.Label(right_frame, text="最低: --", 
                                  font=('Arial', 10), bg='#1e1e1e', fg='#888888', anchor='w')
        self.low_label.pack(fill=tk.X, pady=5)
        
        self.turnover_label = tk.Label(right_frame, text="成交额: --", 
                                       font=('Arial', 10), bg='#1e1e1e', fg='#888888', anchor='w')
        self.turnover_label.pack(fill=tk.X)
        
        # 更新时间
        self.time_label = tk.Label(self.quote_frame, text="更新时间: --", 
                                   font=('Arial', 9), bg='#1e1e1e', fg='#666666')
        self.time_label.pack(side=tk.BOTTOM, pady=5)
    
    def toggle_display_mode(self):
        """切换显示模式（行情/K线）"""
        if self.display_mode == 'quote':
            self.display_mode = 'kline'
            self.toggle_btn.config(text="显示行情")
            self.show_kline()
        else:
            self.display_mode = 'quote'
            self.toggle_btn.config(text="切换K线")
            self.show_quote()
    
    def show_quote(self):
        """显示行情"""
        if self.kline_frame:
            self.kline_frame.pack_forget()
        self.quote_frame.pack(fill=tk.BOTH, expand=True)
        self.refresh_data()
    
    def show_kline(self):
        """显示K线图"""
        self.quote_frame.pack_forget()
        
        if not self.kline_frame:
            self.kline_frame = tk.Frame(self.content_frame, bg='#1e1e1e')
        
        self.kline_frame.pack(fill=tk.BOTH, expand=True)
        
        # 获取当前股票信息
        stock = self.config['stocks'][self.current_stock_index]
        
        # 加载K线数据
        self.load_kline_data(stock['code'], stock['market'])
    
    def load_kline_data(self, code, market):
        """加载K线数据"""
        # 清空现有内容
        for widget in self.kline_frame.winfo_children():
            widget.destroy()
        
        # 显示加载提示
        loading_label = tk.Label(self.kline_frame, text="加载K线数据中...", 
                                font=('Arial', 12), bg='#1e1e1e', fg='white')
        loading_label.pack(expand=True)
        
        # 在新线程中加载数据
        def load_data():
            kline_data = self.api.get_kline_data(code, market, days=30)
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self.display_kline(kline_data))
        
        threading.Thread(target=load_data, daemon=True).start()
    
    def display_kline(self, kline_data):
        """显示K线图"""
        # 清空现有内容
        for widget in self.kline_frame.winfo_children():
            widget.destroy()
        
        if not kline_data:
            error_label = tk.Label(self.kline_frame, text="无法获取K线数据", 
                                  font=('Arial', 12), bg='#1e1e1e', fg='red')
            error_label.pack(expand=True)
            return
        
        # 创建K线图
        chart = KLineChart(self.kline_frame, kline_data, bg='#1e1e1e')
        chart.pack(fill=tk.BOTH, expand=True)
    
    def refresh_data(self):
        """刷新数据"""
        if not self.config['stocks']:
            return
        
        stock = self.config['stocks'][self.current_stock_index]
        data = self.api.get_realtime_data(stock['code'], stock['market'])
        
        if data:
            self.update_quote_display(data)
    
    def update_quote_display(self, data):
        """更新行情显示"""
        if self.display_mode != 'quote':
            return
        
        # 更新名称
        self.name_label.config(text=f"{data['name']} ({data['code']})")
        
        # 更新价格
        price = data['price']
        self.price_label.config(text=f"{price:.2f}")
        
        # 更新涨跌幅
        percent = data['percent']
        updown = data['updown']
        
        # 根据涨跌设置颜色
        if percent > 0:
            color = '#ff4d4f'  # 红色（上涨）
            sign = '+'
        elif percent < 0:
            color = '#52c41a'  # 绿色（下跌）
            sign = ''
        else:
            color = 'white'
            sign = ''
        
        self.price_label.config(fg=color)
        self.change_label.config(text=f"{sign}{updown:.2f} ({sign}{percent:.2f}%)", fg=color)
        
        # 更新详细信息
        self.open_label.config(text=f"今开: {data['open']:.2f}")
        self.high_label.config(text=f"最高: {data['high']:.2f}")
        self.low_label.config(text=f"最低: {data['low']:.2f}")
        self.yestclose_label.config(text=f"昨收: {data['yestclose']:.2f}")
        
        # 格式化成交量和成交额
        volume = data['volume']
        turnover = data['turnover']
        
        if volume >= 100000000:
            volume_str = f"{volume/100000000:.2f}亿"
        elif volume >= 10000:
            volume_str = f"{volume/10000:.2f}万"
        else:
            volume_str = f"{volume:.0f}"
        
        if turnover >= 100000000:
            turnover_str = f"{turnover/100000000:.2f}亿"
        elif turnover >= 10000:
            turnover_str = f"{turnover/10000:.2f}万"
        else:
            turnover_str = f"{turnover:.0f}"
        
        self.volume_label.config(text=f"成交量: {volume_str}")
        self.turnover_label.config(text=f"成交额: {turnover_str}")
        
        # 更新时间
        self.time_label.config(text=f"更新时间: {data['time']}")
    
    def on_stock_changed(self, event):
        """股票选择改变事件"""
        selected = self.stock_combo.current()
        self.current_stock_index = selected
        
        if self.display_mode == 'quote':
            self.refresh_data()
        else:
            stock = self.config['stocks'][self.current_stock_index]
            self.load_kline_data(stock['code'], stock['market'])
    
    def toggle_topmost(self):
        """切换置顶状态"""
        topmost = self.topmost_var.get()
        self.root.attributes('-topmost', topmost)
        self.config['settings']['topmost'] = topmost
        self.save_config()
    
    def apply_window_settings(self):
        """应用窗口设置"""
        # 设置置顶
        topmost = self.config['settings'].get('topmost', True)
        self.root.attributes('-topmost', topmost)
    
    def open_manage_window(self):
        """打开股票管理窗口"""
        ManageWindow(self.root, self)
    
    def start_update_thread(self):
        """启动数据更新线程（每2秒自动刷新当前行情）"""
        def update_loop():
            while self.is_running:
                if self.display_mode == 'quote':
                    self.root.after(0, self.refresh_data)
                
                # 固定2秒刷新间隔
                time.sleep(2)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def on_closing(self):
        """窗口关闭事件"""
        self.is_running = False
        self.root.destroy()
    
    def run(self):
        """运行程序"""
        self.root.mainloop()


class ManageWindow:
    """股票管理窗口"""
    
    def __init__(self, parent, monitor):
        self.monitor = monitor
        self.window = tk.Toplevel(parent)
        self.window.title("股票管理")
        self.window.geometry("500x400")
        self.window.transient(parent)
        
        self.setup_ui()
        self.load_stocks()
    
    def setup_ui(self):
        """设置界面"""
        # 列表框
        list_frame = tk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # 按钮框架
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(btn_frame, text="添加股票", command=self.add_stock).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="删除股票", command=self.delete_stock).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def load_stocks(self):
        """加载股票列表"""
        self.listbox.delete(0, tk.END)
        for stock in self.monitor.config['stocks']:
            self.listbox.insert(tk.END, f"{stock['name']} ({stock['code']}) - {stock['market'].upper()}")
    
    def add_stock(self):
        """添加股票"""
        AddStockDialog(self.window, self)
    
    def delete_stock(self):
        """删除股票"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的股票")
            return
        
        index = selection[0]
        stock = self.monitor.config['stocks'][index]
        
        if messagebox.askyesno("确认", f"确定要删除 {stock['name']} 吗？"):
            del self.monitor.config['stocks'][index]
            self.monitor.save_config()
            self.load_stocks()
            self.update_monitor()
    
    def update_monitor(self):
        """更新监控器"""
        # 更新下拉框
        stock_options = [f"{s['name']} ({s['code']})" for s in self.monitor.config['stocks']]
        self.monitor.stock_combo['values'] = stock_options
        
        if stock_options:
            self.monitor.stock_combo.current(0)
            self.monitor.current_stock_index = 0
            self.monitor.refresh_data()
        else:
            self.monitor.stock_var.set("")


class AddStockDialog:
    """添加股票对话框"""
    
    def __init__(self, parent, manage_window):
        self.manage_window = manage_window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("添加股票")
        self.dialog.geometry("350x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 股票代码
        tk.Label(self.dialog, text="股票代码:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.code_entry = tk.Entry(self.dialog, width=20)
        self.code_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # 股票名称
        tk.Label(self.dialog, text="股票名称:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        self.name_entry = tk.Entry(self.dialog, width=20)
        self.name_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # 市场类型
        tk.Label(self.dialog, text="市场类型:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
        self.market_var = tk.StringVar(value='sh')
        market_frame = tk.Frame(self.dialog)
        market_frame.grid(row=2, column=1, padx=10, pady=10, sticky='w')
        
        tk.Radiobutton(market_frame, text="上证(sh)", variable=self.market_var, value='sh').pack(side=tk.LEFT)
        tk.Radiobutton(market_frame, text="深证(sz)", variable=self.market_var, value='sz').pack(side=tk.LEFT)
        tk.Radiobutton(market_frame, text="美股(us)", variable=self.market_var, value='us').pack(side=tk.LEFT)
        tk.Radiobutton(market_frame, text="期货(hf)", variable=self.market_var, value='hf').pack(side=tk.LEFT)
        
        # 按钮
        btn_frame = tk.Frame(self.dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="确定", command=self.confirm, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=self.dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
    
    def confirm(self):
        """确认添加"""
        code = self.code_entry.get().strip()
        name = self.name_entry.get().strip()
        market = self.market_var.get()
        
        if not code or not name:
            messagebox.showerror("错误", "请填写完整信息")
            return
        
        # 添加到配置
        new_stock = {
            "code": code,
            "name": name,
            "market": market
        }
        
        self.manage_window.monitor.config['stocks'].append(new_stock)
        self.manage_window.monitor.save_config()
        self.manage_window.load_stocks()
        self.manage_window.update_monitor()
        
        self.dialog.destroy()
        messagebox.showinfo("成功", "股票添加成功")


if __name__ == "__main__":
    app = StockMonitor()
    app.run()
