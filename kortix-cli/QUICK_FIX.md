# 快速修复参考

## 🐛 错误
```
InternalError.Algo.InvalidParameter: messages with role "tool" must be a 
response to a preceeding message with "tool_calls".
```

## ⚡ 快速修复

### ✅ 已修复的文件
1. **core/llm.py** - Message 类支持 Function Calling
2. **core/agent.py** - 使用 `msg.to_dict()` 转换消息

### 🧪 验证修复
```bash
# 方法 1: 运行测试
python test_message_fix.py
python test_full_flow.py

# 方法 2: 诊断消息格式
python diagnose.py
```

### ✅ 核心修复点

#### 1. Message 类必须支持这些字段
```python
Message(
    role="assistant",
    content="...",
    tool_calls=[...]      # ✅ 用于 assistant
)

Message(
    role="tool",
    content="...",
    tool_call_id="...",   # ✅ 用于 tool
    name="..."            # ✅ 用于 tool
)
```

#### 2. 转换消息时必须用 to_dict()
```python
# ✅ 正确
messages_dict = [msg.to_dict() for msg in messages]

# ❌ 错误 - 会丢失 tool_calls 等字段
messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]
```

## 📋 检查清单

运行前检查：
- [ ] Message 类有 `tool_calls`、`tool_call_id`、`name` 参数
- [ ] `to_dict()` 返回这些字段
- [ ] 使用 `msg.to_dict()` 而不是手动构建字典
- [ ] 运行 `python test_full_flow.py` 确认通过

## 🔍 如何调试

### 打印消息查看格式
```python
# 在 _call_llm_with_tools() 中添加
messages_dict = [msg.to_dict() for msg in messages]
print("发送给 API 的消息:")
for msg in messages_dict:
    print(msg)
```

### 使用诊断工具
```python
from diagnose import diagnose_messages

messages_dict = [msg.to_dict() for msg in messages]
diagnose_messages(messages_dict)
```

## 📖 详细文档
- **ERROR_FIX.md** - 完整错误说明和修复步骤
- **test_message_fix.py** - Message 类测试
- **test_full_flow.py** - 完整流程测试
- **diagnose.py** - 消息格式诊断工具

## ✅ 现在应该可以正常运行了
```bash
python run.py
```
