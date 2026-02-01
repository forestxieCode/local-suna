"""诊断工具：检查 Function Calling 消息格式是否正确"""
import sys
from typing import List, Dict, Any

def diagnose_messages(messages: List[Dict[str, Any]]) -> bool:
    """
    诊断消息列表是否符合阿里云百炼 API 要求
    
    Args:
        messages: 消息字典列表
    
    Returns:
        True 如果所有检查通过，False 如果有问题
    """
    print("=" * 70)
    print("Function Calling 消息格式诊断工具")
    print("=" * 70)
    
    if not messages:
        print("\n❌ 错误: 消息列表为空")
        return False
    
    print(f"\n总共 {len(messages)} 条消息")
    
    has_error = False
    
    for i, msg in enumerate(messages):
        role = msg.get('role', '')
        print(f"\n{'='*70}")
        print(f"消息 {i+1}/{len(messages)}: role={role}")
        print(f"{'='*70}")
        
        # 检查必需字段
        if not role:
            print("❌ 错误: 缺少 role 字段")
            has_error = True
            continue
        
        # 检查 content 字段
        content = msg.get('content', '')
        if content:
            content_preview = content[:50] + "..." if len(content) > 50 else content
            print(f"✅ content: {content_preview}")
        
        # 检查 tool 消息的格式
        if role == 'tool':
            print("\n🔍 检查 tool 消息...")
            
            # 检查 1: tool 消息不能是第一条
            if i == 0:
                print("❌ 错误: tool 消息不能是第一条消息")
                has_error = True
                continue
            
            # 检查 2: 前一条必须是 assistant
            prev_msg = messages[i-1]
            prev_role = prev_msg.get('role', '')
            
            print(f"   前一条消息 role: {prev_role}")
            
            if prev_role != 'assistant':
                print(f"❌ 错误: tool 消息前必须是 assistant，当前是 {prev_role}")
                has_error = True
                continue
            
            # 检查 3: 前一条 assistant 必须有 tool_calls
            prev_tool_calls = prev_msg.get('tool_calls')
            
            if not prev_tool_calls:
                print("❌ 错误: 前一条 assistant 消息没有 tool_calls 字段")
                print(f"   前一条消息内容: {prev_msg}")
                
                # 检查是否把 tool_calls 放在 content 里了
                prev_content = prev_msg.get('content', '')
                if 'tool_calls' in prev_content:
                    print("⚠️  警告: 发现 tool_calls 在 content 字符串中！")
                    print("   这是错误的！tool_calls 应该是消息的独立字段")
                    print("   请使用 Message 类的 tool_calls 参数")
                
                has_error = True
                continue
            
            print(f"✅ 前一条 assistant 有 tool_calls ({len(prev_tool_calls)} 个)")
            
            # 检查 4: tool 消息必须有 tool_call_id
            tool_call_id = msg.get('tool_call_id')
            
            if not tool_call_id:
                print("❌ 错误: tool 消息缺少 tool_call_id 字段")
                
                # 检查是否把 tool_call_id 放在 content 里了
                if 'tool_call_id' in content:
                    print("⚠️  警告: 发现 tool_call_id 在 content 字符串中！")
                    print("   这是错误的！tool_call_id 应该是消息的独立字段")
                    print("   请使用 Message 类的 tool_call_id 参数")
                
                has_error = True
                continue
            
            print(f"✅ tool_call_id: {tool_call_id}")
            
            # 检查 5: tool_call_id 必须匹配前面的某个 tool_call
            prev_tool_call_ids = [tc.get('id') for tc in prev_tool_calls]
            
            if tool_call_id not in prev_tool_call_ids:
                print(f"❌ 错误: tool_call_id '{tool_call_id}' 不在前面的 tool_calls 中")
                print(f"   可用的 tool_call_id: {prev_tool_call_ids}")
                has_error = True
                continue
            
            print(f"✅ tool_call_id 匹配")
            
            # 检查 6: tool 消息应该有 name 字段
            name = msg.get('name')
            
            if not name:
                print("⚠️  警告: tool 消息建议包含 name 字段（函数名）")
            else:
                print(f"✅ name: {name}")
        
        # 检查 assistant 消息的 tool_calls
        elif role == 'assistant':
            tool_calls = msg.get('tool_calls')
            
            if tool_calls:
                print(f"\n✅ 包含 tool_calls: {len(tool_calls)} 个")
                
                for j, tc in enumerate(tool_calls):
                    tc_id = tc.get('id', 'N/A')
                    tc_type = tc.get('type', 'N/A')
                    func = tc.get('function', {})
                    func_name = func.get('name', 'N/A')
                    
                    print(f"   tool_call {j+1}: id={tc_id}, type={tc_type}, function={func_name}")
                    
                    # 检查 tool_call 格式
                    if not tc_id:
                        print(f"   ⚠️  警告: tool_call 缺少 id")
                    if not func_name or func_name == 'N/A':
                        print(f"   ⚠️  警告: tool_call 缺少 function.name")
    
    print(f"\n{'='*70}")
    print("诊断结果")
    print(f"{'='*70}")
    
    if has_error:
        print("\n❌ 发现错误！消息格式不符合 API 要求")
        print("\n常见问题修复方法：")
        print("1. 确保 Message 类支持 tool_calls、tool_call_id、name 参数")
        print("2. 使用 msg.to_dict() 而不是手动构建 {role, content}")
        print("3. 不要把 tool_calls 放在 content 的 JSON 字符串里")
        print("4. 确保 tool 消息前有 assistant 消息且包含 tool_calls")
        print("\n详细修复步骤请查看: ERROR_FIX.md")
        return False
    else:
        print("\n✅ 所有检查通过！消息格式符合 API 要求")
        return True

def test_diagnose():
    """测试诊断工具"""
    
    # 测试案例 1: 正确格式
    print("\n\n" + "="*70)
    print("测试案例 1: 正确的消息格式")
    print("="*70)
    
    correct_messages = [
        {"role": "user", "content": "计算1+1"},
        {
            "role": "assistant",
            "content": "好的",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "calculate", "arguments": "{}"}
                }
            ]
        },
        {
            "role": "tool",
            "content": "2",
            "tool_call_id": "call_123",
            "name": "calculate"
        },
        {"role": "assistant", "content": "结果是2"}
    ]
    
    result1 = diagnose_messages(correct_messages)
    
    # 测试案例 2: 错误格式（缺少 tool_calls）
    print("\n\n" + "="*70)
    print("测试案例 2: 错误格式（assistant 没有 tool_calls）")
    print("="*70)
    
    wrong_messages = [
        {"role": "user", "content": "计算1+1"},
        {"role": "assistant", "content": "好的"},  # ❌ 没有 tool_calls
        {
            "role": "tool",
            "content": "2",
            "tool_call_id": "call_123",
            "name": "calculate"
        }
    ]
    
    result2 = diagnose_messages(wrong_messages)
    
    # 总结
    print("\n\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"案例 1 (正确格式): {'通过' if result1 else '失败'}")
    print(f"案例 2 (错误格式): {'正确识别错误' if not result2 else '未识别错误'}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_diagnose()
    else:
        print("使用方法:")
        print("  python diagnose.py test  # 运行测试案例")
        print("  或在代码中调用 diagnose_messages(messages)")
        print()
        test_diagnose()
