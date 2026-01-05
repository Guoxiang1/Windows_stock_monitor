"""测试期货数据是否会更新"""
import time
from api_client import NetEaseFinanceAPI

api = NetEaseFinanceAPI()

print("=" * 50)
print("测试期货API是否返回不同数据")
print("=" * 50)

print("\n第1次调用:")
d1 = api.get_realtime_data('XAU', 'hf')
if d1:
    print(f"价格: {d1['price']}")
    print(f"时间: {d1['time']}")
    print(f"开盘: {d1['open']}")
    print(f"最高: {d1['high']}")
    print(f"最低: {d1['low']}")
else:
    print("获取失败")
    exit(1)

print("\n等待5秒...")
time.sleep(5)

print("\n第2次调用(5秒后):")
d2 = api.get_realtime_data('XAU', 'hf')
if d2:
    print(f"价格: {d2['price']}")
    print(f"时间: {d2['time']}")
    print(f"开盘: {d2['open']}")
    print(f"最高: {d2['high']}")
    print(f"最低: {d2['low']}")
else:
    print("获取失败")
    exit(1)

print("\n" + "=" * 50)
print("对比结果:")
print("=" * 50)
print(f"价格是否变化: {d1['price'] != d2['price']} (期望: False，因为使用K线收盘价)")
print(f"时间是否变化: {d1['time'] != d2['time']} (期望: True，因为使用当前时间)")
print(f"价格1: {d1['price']} -> 价格2: {d2['price']}")
print(f"时间1: {d1['time']} -> 时间2: {d2['time']}")

print("\n说明：")
print("- 期货价格来自最新K线的收盘价，一天只更新一次")
print("- 时间显示为当前系统时间，每次调用都会更新")
print("- 这是正常的，因为API返回的是日K线数据，不是实时tick数据")
