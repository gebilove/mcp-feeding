import sys
from types import ModuleType
import os

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
    
    def run(self, transport="stdio"):
        print(f"MockFastMCP '{self.name}' started on {transport}")

mock_fastmcp.FastMCP = MockFastMCP
sys.modules["fastmcp"] = mock_fastmcp

# --- END MOCKING ---

# Import the server code (which thinks it's importing real fastmcp)
import feeding_server

# Initialize/Reset DB for testing
if os.path.exists("feeding_data.db"):
    os.remove("feeding_data.db")
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

# Test 4: Recent Feedings
print("\n👉 测试 4: 查看最近记录")
recent = feeding_server.get_recent_feedings(limit=5)
for i, r in enumerate(recent):
    print(f"   [{i+1}] {r['amount_ml']}ml ({r['feeding_type']}) - {r['timestamp']}")

# Cleanup
if os.path.exists("feeding_data.db"):
    os.remove("feeding_data.db")
print("\n=== 测试完成 ===")
