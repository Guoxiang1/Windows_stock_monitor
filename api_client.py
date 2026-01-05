"""
东方财富API客户端
支持获取股票实时行情和历史K线数据
"""
import requests
import json
from datetime import datetime, timedelta
import random

class NetEaseFinanceAPI:
    """财经API客户端类（使用东方财富API）"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://quote.eastmoney.com/'
        }
        
        # 期货代码映射表 (用户代码 -> (市场ID, 东方财富代码, 名称))
        self.futures_map = {
            'XAUUSD': ('122', 'XAU', '黄金/美元'),
            'XAU': ('122', 'XAU', '黄金/美元'),
            'XAGUSD': ('122', 'XAG', '白银/美元'),
            'XAG': ('122', 'XAG', '白银/美元'),
            'CL': ('113', 'cl', 'WTI原油'),
            'NG': ('113', 'ng', '天然气'),
            'GC': ('113', 'gc', 'COMEX黄金'),
            'SI': ('113', 'si', 'COMEX白银')
        }
    
    def get_eastmoney_code(self, code, market):
        """
        获取东方财富的股票代码格式
        market: sh(上证), sz(深证), us(美股), hf(期货)
        """
        market = market.lower()
        
        if market == 'sh':
            # 上证：1.代码
            if code.startswith('6'):
                return f'1.{code}'
            else:
                return f'1.{code}'  # 指数也用1
        elif market == 'sz':
            # 深证：0.代码
            return f'0.{code}'
        elif market == 'us':
            # 美股：105.代码
            return f'105.{code.upper()}'
        elif market == 'hf':
            # 期货：使用映射表
            code_upper = code.upper()
            if code_upper in self.futures_map:
                market_id, real_code, _ = self.futures_map[code_upper]
                return f'{market_id}.{real_code}'
            return f'113.{code.lower()}'
        else:
            return f'1.{code}'
    
    def get_futures_name(self, code):
        """获取期货中文名称"""
        code_upper = code.upper()
        if code_upper in self.futures_map:
            _, _, name = self.futures_map[code_upper]
            return name
        return code
    
    def get_realtime_data(self, code, market='sh'):
        """
        获取实时行情数据
        code: 股票代码
        market: 市场类型
        """
        try:
            market = market.lower()
            
            # 所有市场统一使用东方财富API
            secid = self.get_eastmoney_code(code, market)
            
            # 东方财富实时行情API
            url = f"http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'secid': secid,
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f107,f152,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171',
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'cb': 'jQuery'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                text = response.text
                # 移除jQuery回调函数包装
                if text.startswith('jQuery'):
                    text = text[text.index('(') + 1:text.rindex(')')]
                
                data = json.loads(text)
                
                if data.get('data'):
                    stock_data = data['data']
                    
                    # 获取字段值
                    name = stock_data.get('f58', '')  # 名称
                    
                    # 如果是期货且名称为空，使用映射表中的名称
                    if not name and market == 'hf':
                        name = self.get_futures_name(code)
                    
                    price = stock_data.get('f43', 0) / 100  # 最新价（需要除以100）
                    yestclose = stock_data.get('f60', 0) / 100  # 昨收
                    open_price = stock_data.get('f46', 0) / 100  # 开盘
                    high = stock_data.get('f44', 0) / 100  # 最高
                    low = stock_data.get('f45', 0) / 100  # 最低
                    volume = stock_data.get('f47', 0)  # 成交量（手）
                    turnover = stock_data.get('f48', 0)  # 成交额（元）
                    percent = stock_data.get('f170', 0) / 100  # 涨跌幅
                    
                    # 计算涨跌额
                    updown = price - yestclose
                    
                    # 获取时间
                    time_str = datetime.now().strftime('%H:%M:%S')
                    
                    return {
                        'code': code,
                        'name': name,
                        'price': price,
                        'percent': percent,
                        'updown': updown,
                        'open': open_price,
                        'high': high,
                        'low': low,
                        'yestclose': yestclose,
                        'volume': volume * 100,  # 转换为股
                        'turnover': turnover,
                        'time': time_str,
                        'market': market
                    }
            
            return None
        except Exception as e:
            print(f"获取实时数据失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_kline_data(self, code, market='sh', days=30):
        """
        获取K线数据
        code: 股票代码
        market: 市场类型
        days: 获取天数
        """
        try:
            market = market.lower()
            
            # 期货市场使用新浪全球期货API
            if market == 'hf':
                return self._get_futures_kline(code, days)
            
            # A股使用腾讯财经API
            if market == 'sh':
                stock_code = f'sh{code}'
            elif market == 'sz':
                stock_code = f'sz{code}'
            else:
                # 美股暂时使用模拟数据
                print(f"警告: {market}市场暂不支持K线数据，使用模拟数据")
                return self._generate_mock_kline_data(days)
            
            # 腾讯财经K线数据API
            url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {
                'param': f'{stock_code},day,,,{days},'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('code') == 0 and data.get('data'):
                    # 获取股票代码的数据
                    stock_data = data['data'].get(stock_code)
                    
                    if stock_data and 'day' in stock_data:
                        klines = stock_data['day']
                        kline_list = []
                        
                        for kline in klines:
                            # 格式：[日期, 开盘, 收盘, 最高, 最低, 成交量]
                            if len(kline) >= 6:
                                kline_list.append({
                                    'date': kline[0],  # 日期
                                    'open': float(kline[1]),  # 开盘价
                                    'close': float(kline[2]),  # 收盘价
                                    'high': float(kline[3]),  # 最高价
                                    'low': float(kline[4]),  # 最低价
                                    'volume': float(kline[5])  # 成交量
                                })
                        
                        if kline_list:
                            return kline_list
            
            # 如果获取失败，返回模拟数据
            print(f"警告: 无法获取K线数据，使用模拟数据")
            return self._generate_mock_kline_data(days)
            
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_mock_kline_data(days)
    
    def _get_futures_kline(self, code, days=30):
        """
        获取期货K线数据（使用新浪全球期货API）
        """
        try:
            # 转换代码格式
            code_upper = code.upper()
            
            # 检查是否在映射表中，获取实际代码
            if code_upper in self.futures_map:
                # 对于映射表中的代码，使用特定格式
                # XAU/XAUUSD -> XAU, XAGUSD/XAG -> XAG 等
                symbol_map = {
                    'XAUUSD': 'XAU',
                    'XAU': 'XAU',
                    'XAGUSD': 'XAG', 
                    'XAG': 'XAG',
                    'CL': 'CL',
                    'NG': 'NG',
                    'GC': 'GC',
                    'SI': 'SI'
                }
                symbol = symbol_map.get(code_upper, code_upper)
            else:
                symbol = code_upper
            
            # 新浪全球期货K线API
            url = f"https://stock2.finance.sina.com.cn/futures/api/jsonp.php/var%20_{symbol}_data=/GlobalFuturesService.getGlobalFuturesDailyKLine"
            params = {
                'symbol': symbol,
                '_': '1'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                text = response.text
                
                # 解析JSONP响应
                import re
                match = re.search(r'var _[A-Z]+_data=\((.+)\);', text)
                
                if match:
                    import json
                    data = json.loads(match.group(1))
                    
                    if data:
                        kline_list = []
                        # 只取最近days天的数据
                        for item in data[-days:]:
                            kline_list.append({
                                'date': item['date'],
                                'open': float(item['open']),
                                'close': float(item['close']),
                                'high': float(item['high']),
                                'low': float(item['low']),
                                'volume': float(item.get('volume', 0))
                            })
                        
                        if kline_list:
                            print(f"成功获取 {len(kline_list)} 条期货K线数据")
                            return kline_list
            
            print(f"警告: 无法获取期货K线数据，使用模拟数据")
            return self._generate_mock_kline_data(days)
            
        except Exception as e:
            print(f"获取期货K线数据失败: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_mock_kline_data(days)
    
    def get_intraday_data(self, code, market='sh'):
        """
        获取分时数据（使用K线最后一天数据模拟）
        """
        try:
            # 对于期货，从新浪获取
            if market.lower() == 'hf':
                return self._generate_intraday_from_kline(code, market)
            
            # A股从腾讯API获取分时数据
            # 由于分时API复杂，这里用简化版本
            return self._generate_intraday_from_kline(code, market)
            
        except Exception as e:
            print(f"获取分时数据失败: {e}")
            return []
    
    def _generate_intraday_from_kline(self, code, market):
        """从K线数据生成分时数据"""
        try:
            kline = self.get_kline_data(code, market, days=2)
            if not kline or len(kline) < 2:
                return []
            
            latest = kline[-1]
            yestclose = kline[-2]['close']
            
            # 生成240个分时点（4小时交易，每分钟一个点）
            intraday_data = []
            open_p = latest['open']
            close_p = latest['close']
            high_p = latest['high']
            low_p = latest['low']
            
            for i in range(240):
                # 简单线性插值
                ratio = i / 240
                price = open_p + (close_p - open_p) * ratio
                # 添加随机波动
                price += random.uniform(-5, 5)
                price = max(low_p, min(high_p, price))
                
                # 计算时间
                hour = 9 + (i + 30) // 60
                minute = (i + 30) % 60
                if hour >= 12:
                    hour += 1
                if hour >= 15:
                    break
                    
                time_str = f"{hour:02d}:{minute:02d}"
                
                intraday_data.append({
                    'time': time_str,
                    'price': round(price, 2),
                    'yestclose': yestclose
                })
            
            return intraday_data
        except:
            return []
    
    def _generate_mock_kline_data(self, days=30):
        """生成模拟K线数据用于演示"""
        kline_list = []
        base_price = 3000
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
            
            # 简单的随机波动
            change = random.uniform(-50, 50)
            base_price += change
            
            open_price = base_price
            close_price = base_price + random.uniform(-20, 20)
            high_price = max(open_price, close_price) + random.uniform(0, 30)
            low_price = min(open_price, close_price) - random.uniform(0, 30)
            
            kline_list.append({
                'date': date,
                'open': round(open_price, 2),
                'close': round(close_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'volume': random.randint(1000000, 5000000)
            })
        
        return kline_list

if __name__ == "__main__":
    # 测试代码
    api = NetEaseFinanceAPI()
    
    # 测试实时数据
    print("测试上证指数实时数据:")
    data = api.get_realtime_data('000001', 'sh')
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("获取失败")
    
    print("\n测试深证成指实时数据:")
    data = api.get_realtime_data('399001', 'sz')
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # 测试期货数据
    print("\n测试黄金期货实时数据:")
    data = api.get_realtime_data('XAUUSD', 'hf')
    if data:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("获取失败")
    
    # 测试A股K线数据
    print("\n测试A股K线数据:")
    kline = api.get_kline_data('000001', 'sh', days=5)
    if kline:
        print(f"获取到 {len(kline)} 条K线数据")
        for k in kline[-3:]:  # 只显示最后3天
            print(k)
    
    # 测试期货K线数据
    print("\n测试黄金期货K线数据:")
    kline = api.get_kline_data('XAU', 'hf', days=5)
    if kline:
        print(f"获取到 {len(kline)} 条K线数据")
        for k in kline:  # 显示所有5天数据
            print(k)
