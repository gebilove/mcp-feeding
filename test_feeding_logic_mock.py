import sys
from types import ModuleType
import os
import datetime

# Set test DB path
# Set test DB path
import os
os.environ["FEEDING_DB_PATH"] = "/tmp/test_feeding.db"

# --- MOCKING INFRASTRUCTURE ---
# 这是一个模拟模块，用来在没有安装 fastmcp 的情况下测试业务逻辑
# It mocks the 'fastmcp' library so we can call the functions directly.
mock_fastmcp = ModuleType("fastmcp")

class MockFastMCP:
    def __init__(self, name):
        self.name = name
    
    def tool(self):
        # Return a decorator that just returns the function
        def decorator(func):
            return func
        return decorator
    
    def on_startup(self, func):
        return func
    
    def run(self, transport="stdio"):
        print(f"MockFastMCP '{self.name}' started on {transport}")

mock_fastmcp.FastMCP = MockFastMCP
sys.modules["fastmcp"] = mock_fastmcp

# --- END MOCKING ---

# Import the server code (which thinks it's importing real fastmcp)
import feeding_server

print(f"DEBUG: feeding_server.DB_FILE = {feeding_server.DB_FILE}")

# Initialize/Reset DB for testing
if os.path.exists(feeding_server.DB_FILE):
    os.remove(feeding_server.DB_FILE)
feeding_server.init_db()

print("=== 🧪 开始测试喂养服务逻辑 (Mock Mode) ===")

# Test 1: Record Feeding
print("\n👉 测试 1: 记录喂奶 (150ml)")
res = feeding_server.record_feeding(150, "formula")
print(f"   结果: {res}")

# Test 2: Record Another
print("\n👉 测试 2: 记录第二次喂奶 (200ml)")
feeding_server.record_feeding(200, "formula")
print(f"   已执行记录动作")

# Test 3: Daily Summary
print("\n👉 测试 3: 获取今日统计")
summary = feeding_server.get_daily_summary()
print(f"   统计结果: {summary}")

# Verification
expected_vol = 350
if summary['total_volume_ml'] == expected_vol:
    print(f"\n✅ 验证通过: 总量正确 ({expected_vol}ml)")
else:
    print(f"\n❌ 验证失败: 预期 {expected_vol}ml, 实际 {summary['total_volume_ml']}ml")


print("\n--- 换尿布测试 ---")

# Test 5: Record Diaper Change
print("\n👉 测试 5: 记录换尿布 (pee)")
res = feeding_server.record_diaper_change("pee")
print(f"   结果: {res}")

# Test 6: Record Diaper Change (poop)
print("\n👉 测试 6: 记录换尿布 (poop)")
feeding_server.record_diaper_change("poop")
print(f"   已执行记录动作")

# Test 7: Record Diaper Change (both)
print("\n👉 测试 7: 记录换尿布 (both)")
feeding_server.record_diaper_change("both")
print(f"   已执行记录动作")

# Test 8: Diaper Summary
print("\n👉 测试 8: 获取今日尿布统计")
diaper_summary = feeding_server.get_daily_diaper_summary()
print(f"   统计结果: {diaper_summary}")

if diaper_summary['total_changes'] == 3 and diaper_summary['counts'].get('pee') == 1:
     print(f"\n✅ 验证通过: 尿布统计正确")
else:
     print(f"\n❌ 验证失败: 尿布统计错误 {diaper_summary}")

# Test 9: Last Diaper Change Info
print("\n👉 测试 9: 查看最后一次尿布信息")
last_info = feeding_server.get_last_diaper_change_info()
print(f"   结果: {last_info}")
if 'minutes_since' in last_info:
    print(f"   ✅ 验证通过: 成功获取时间差 ({last_info['description']})")
else:
    print(f"   ❌ 验证失败: {last_info}")

# Cleanup
if os.path.exists(feeding_server.DB_FILE):
    os.remove(feeding_server.DB_FILE)
print("\n=== 测试完成 ===")
