#!/usr/bin/env python3
"""
AgentScope Backend v2 交互式体验脚本

使用方法:
    python demo_v2.py

功能:
    1. 创建示例 traces
    2. 查询和过滤
    3. 父子 trace 关系
    4. 对比分析
    5. 查看指标
"""

import requests
import json
from datetime import datetime
from typing import Optional

BASE_URL = "http://localhost:8000"


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def print_json(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def check_health():
    """检查服务健康状态"""
    print_section("服务健康检查")
    resp = requests.get(f"{BASE_URL}/api/health")
    if resp.status_code == 200:
        print("✅ 服务运行正常")
        print_json(resp.json())
        return True
    else:
        print(f"❌ 服务异常: {resp.status_code}")
        return False


def create_sample_traces():
    """创建示例 traces"""
    print_section("创建示例 Traces")
    
    now = datetime.now().isoformat()
    
    # 创建父 trace (主 Agent)
    parent = {
        "id": "demo-parent-001",
        "name": "客户服务主代理",
        "tags": ["demo", "customer-service", "parent"],
        "start_time": now,
        "status": "success",
        "input_query": "客户询问订单 #12345 的退款状态",
        "output_result": "退款已批准，将在 3-5 个工作日内退回",
        "steps": [
            {"id": "s1", "type": "input", "content": "接收客户查询", "timestamp": now, "latency_ms": 10},
            {"id": "s2", "type": "llm_call", "content": "理解客户意图", "timestamp": now, "tokens_input": 50, "tokens_output": 30, "latency_ms": 800},
        ],
        "total_latency_ms": 2500.0,
        "total_tokens": 200,
        "cost_estimate": 0.005,
        "child_trace_ids": ["demo-child-001", "demo-child-002"],
    }
    
    resp = requests.post(f"{BASE_URL}/api/traces", json=parent)
    if resp.status_code == 200:
        print("✅ 父 trace 创建成功")
    else:
        print(f"❌ 创建失败: {resp.text}")
        return
    
    # 创建子 trace 1 (搜索 Agent)
    child1 = {
        "id": "demo-child-001",
        "name": "订单搜索代理",
        "tags": ["demo", "search", "child"],
        "start_time": now,
        "status": "success",
        "input_query": "搜索订单 #12345",
        "output_result": "订单找到: 金额 $99.99, 日期 2024-03-15",
        "parent_trace_id": "demo-parent-001",
        "steps": [
            {"id": "s1", "type": "tool_call", "content": "查询订单数据库", "timestamp": now, "latency_ms": 300},
        ],
        "total_latency_ms": 350.0,
        "cost_estimate": 0.001,
    }
    
    resp = requests.post(f"{BASE_URL}/api/traces", json=child1)
    if resp.status_code == 200:
        print("✅ 子 trace 1 (搜索) 创建成功")
    
    # 创建子 trace 2 (退款验证 Agent)
    child2 = {
        "id": "demo-child-002",
        "name": "退款验证代理",
        "tags": ["demo", "validation", "child"],
        "start_time": now,
        "status": "success",
        "input_query": "验证订单 #12345 退款资格",
        "output_result": "符合退款条件，购买时间在 30 天内",
        "parent_trace_id": "demo-parent-001",
        "steps": [
            {"id": "s1", "type": "memory_read", "content": "读取退款政策", "timestamp": now, "latency_ms": 50},
            {"id": "s2", "type": "reasoning", "content": "分析购买日期", "timestamp": now, "latency_ms": 100},
        ],
        "total_latency_ms": 200.0,
        "cost_estimate": 0.0015,
    }
    
    resp = requests.post(f"{BASE_URL}/api/traces", json=child2)
    if resp.status_code == 200:
        print("✅ 子 trace 2 (验证) 创建成功")
    
    # 创建一些额外的 traces 用于过滤演示
    for i in range(3):
        trace = {
            "id": f"demo-extra-{i:03d}",
            "name": f"额外 Trace {i}",
            "tags": ["demo", "extra"],
            "start_time": now,
            "status": "success" if i < 2 else "error",
            "input_query": f"查询 {i}",
            "output_result": f"结果 {i}",
            "steps": [],
            "total_latency_ms": 100.0 + i * 50,
        }
        requests.post(f"{BASE_URL}/api/traces", json=trace)
    
    print("✅ 额外 traces 创建成功")


def query_traces():
    """查询 traces"""
    print_section("查询 Traces")
    
    # 查询所有
    resp = requests.get(f"{BASE_URL}/api/traces?limit=10")
    if resp.status_code == 200:
        data = resp.json()
        print(f"📊 总计 {data['pagination']['total']} 个 traces")
        print(f"   当前返回 {len(data['traces'])} 个")
        for t in data['traces'][:3]:
            print(f"   - {t['id']}: {t['name']} [{t['status']}]")
    
    # 按状态过滤
    print("\n🔍 按状态过滤 (success):")
    resp = requests.get(f"{BASE_URL}/api/traces?status=success")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   找到 {len(data['traces'])} 个成功的 traces")
    
    # 按标签过滤
    print("\n🏷️  按标签过滤 (child):")
    resp = requests.get(f"{BASE_URL}/api/traces?tag=child")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   找到 {len(data['traces'])} 个子 agent traces")


def show_relations():
    """展示父子关系"""
    print_section("父子 Trace 关系")
    
    # 获取子 traces
    resp = requests.get(f"{BASE_URL}/api/traces/demo-parent-001/children")
    if resp.status_code == 200:
        data = resp.json()
        print(f"👨‍👧‍👦 父 trace 'demo-parent-001' 有 {data['count']} 个子 traces:")
        for child in data['children']:
            print(f"   - {child['id']}: {child['name']}")
    
    # 获取父 trace
    print("\n👆 子 trace 'demo-child-001' 的父 trace:")
    resp = requests.get(f"{BASE_URL}/api/traces/demo-child-001/parent")
    if resp.status_code == 200:
        data = resp.json()
        if data.get('parent'):
            print(f"   - {data['parent']['id']}: {data['parent']['name']}")
        else:
            print("   无父 trace")


def compare_demo():
    """对比演示"""
    print_section("Trace 对比分析")
    
    resp = requests.post(f"{BASE_URL}/api/traces/compare", json={
        "trace_id_1": "demo-child-001",
        "trace_id_2": "demo-child-002"
    })
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"📊 对比 'demo-child-001' vs 'demo-child-002':")
        print(f"   延迟差: {data['latency_diff_ms']:.1f}ms")
        print(f"   Token 差: {data['tokens_diff']}")
        print(f"   成本差: ${data['cost_diff']:.4f}")
        print(f"   状态变化: {data['status_changed']}")


def show_metrics():
    """展示指标"""
    print_section("实时指标")
    
    resp = requests.get(f"{BASE_URL}/api/metrics/realtime")
    if resp.status_code == 200:
        data = resp.json()
        print(f"📈 实时指标:")
        print(f"   总 traces: {data['total_traces']}")
        print(f"   成功率: {data['success_rate']*100:.1f}%")
        print(f"   平均延迟: {data['avg_latency_ms']:.1f}ms")
        print(f"   总 tokens: {data['total_tokens']}")
        print(f"   总成本: ${data['total_cost']:.4f}")
    
    print("\n📊 存储统计:")
    resp = requests.get(f"{BASE_URL}/api/stats")
    if resp.status_code == 200:
        data = resp.json()
        print(f"   后端: {data['backend']}")
        print(f"   总 traces: {data['total_traces']}")
        print(f"   存储大小: {data['storage_size_bytes']} bytes")


def show_timeline():
    """展示时间线"""
    print_section("时间线分析")
    
    resp = requests.get(f"{BASE_URL}/api/traces/demo-parent-001/timeline")
    if resp.status_code == 200:
        data = resp.json()
        print(f"⏱️  Trace 'demo-parent-001' 时间线:")
        print(f"   总步骤: {data['total_steps']}")
        print(f"   步骤类型: {data['step_types']}")
        print(f"   总延迟: {data['total_latency_ms']}ms")
        print("\n   详细时间线:")
        for item in data['timeline'][:5]:
            print(f"   - {item['type']}: {item['latency_ms']}ms (累计: {item['cumulative_latency_ms']}ms)")


def interactive_menu():
    """交互式菜单"""
    while True:
        print("\n" + "="*60)
        print("  AgentScope Backend v2 体验菜单")
        print("="*60)
        print("  1. 检查服务健康")
        print("  2. 创建示例数据")
        print("  3. 查询 Traces")
        print("  4. 父子关系展示")
        print("  5. 对比分析")
        print("  6. 查看指标")
        print("  7. 时间线分析")
        print("  8. 运行全部演示")
        print("  0. 退出")
        print("="*60)
        
        choice = input("\n请选择操作 [0-8]: ").strip()
        
        if choice == '1':
            check_health()
        elif choice == '2':
            create_sample_traces()
        elif choice == '3':
            query_traces()
        elif choice == '4':
            show_relations()
        elif choice == '5':
            compare_demo()
        elif choice == '6':
            show_metrics()
        elif choice == '7':
            show_timeline()
        elif choice == '8':
            run_all_demos()
        elif choice == '0':
            print("\n感谢体验 AgentScope Backend v2!")
            break
        else:
            print("无效选择，请重试")


def run_all_demos():
    """运行全部演示"""
    if not check_health():
        return
    
    create_sample_traces()
    query_traces()
    show_relations()
    compare_demo()
    show_metrics()
    show_timeline()
    
    print_section("演示完成")
    print("✅ 全部演示已完成！")
    print(f"\n您可以访问 http://localhost:8000 查看 API 文档")


def main():
    print("\n" + "="*60)
    print("  AgentScope Backend v2 体验脚本")
    print("="*60)
    print(f"\nAPI 地址: {BASE_URL}")
    
    # 检查服务
    try:
        resp = requests.get(f"{BASE_URL}/api/health", timeout=3)
        if resp.status_code == 200:
            print("✅ 服务已连接")
        else:
            print(f"⚠️  服务返回异常状态: {resp.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到 {BASE_URL}")
        print("   请确保 Backend v2 已启动:")
        print("   cd backend && python main_v2.py")
        return
    
    interactive_menu()


if __name__ == "__main__":
    main()
