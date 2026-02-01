# 错误修复说明（完整版）

## 🐛 错误信息

```
InternalError.Algo.InvalidParameter: messages with role "tool" must be a 
response to a preceeding message with "tool_calls".
```

## 📝 错误含义

这是**阿里云百炼（DashScope）API** 的错误，表示：

- 消息历史中有 `role="tool"` 的消息（工具执行结果）
- 但它前面的消息**没有包含 `tool_calls` 字段**
- 或者 `tool_calls` 的格式不正确

## 🔍 根本原因（两个问题）

### ❌ 问题 1: Message 类不支持 Function Calling

**旧的 Message 类**：

```python
# core/llm.py - 旧版本
class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}
        # ❌ 只返回 role 和 content，丢失 tool_calls、tool_call_id 等字段
```

### ❌ 问题 2: Agent 消息转换时丢失字段

**旧的 _call_llm_with_tools 方法**：

```python
# core/agent.py - 旧版本
def _call_llm_with_tools(self, messages: List[Message]) -> Dict[str, Any]:
    # ❌ 手动构建字典，只包含 role 和 content
    messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]
    # 即使 Message 对象有 tool_calls，这里也丢失了！
```

**结果**：发送给 API 的消息格式：

```python
# assistant 消息（应该有 tool_calls）
{
    "role": "assistant",
    "content": "我来执行"
    # ❌ 缺少 tool_calls 字段
}

# tool 消息
{
    "role": "tool",
    "content": "结果"
    # ❌ 缺少 tool_call_id 和 name 字段
}
```

API 收到后发现 `tool` 消息前面的 `assistant` 消息没有 `tool_calls`，于是报错。

---

## ✅ 完整修复方案

### 修复 1: 升级 Message 类

```python
# core/llm.py - 新版本
class Message:
    """消息类 - 支持 Function Calling"""
    def __init__(self, role: str, content: str = "", 
                 tool_calls: Optional[List[Dict]] = None, 
                 tool_call_id: Optional[str] = None, 
                 name: Optional[str] = None):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls      # ✅ 新增
        self.tool_call_id = tool_call_id  # ✅ 新增
        self.name = name                  # ✅ 新增
    
    def to_dict(self) -> Dict[str, Any]:
        result = {"role": self.role}
        
        if self.content:
            result["content"] = self.content
        
        # ✅ 保留所有 Function Calling 字段
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        
        if self.name:
            result["name"] = self.name
        
        return result
```

### 修复 2: 使用 to_dict() 转换消息

```python
# core/agent.py - 新版本
def _call_llm_with_tools(self, messages: List[Message]) -> Dict[str, Any]:
    """调用 LLM（带工具支持）"""
    # ✅ 使用 to_dict() 保留所有字段
    messages_dict = [msg.to_dict() for msg in messages]
    
    # 准备工具定义
    tools = []
    if self.enable_function_calling:
        functions = self._get_tool_functions()
        tools = [{"type": "function", "function": func} for func in functions]
    
    # 调用 API
    response = Generation.call(
        model=config.llm_model,
        messages=messages_dict,  # ✅ 现在包含完整字段
        tools=tools if tools else None,
        ...
    )
```

### 修复 3: 正确创建消息

```python
# core/agent.py - 创建 assistant 消息
self.messages.append(Message(
    role="assistant",
    content=assistant_message_content,
    tool_calls=tool_calls  # ✅ 作为参数传递
))

# 创建 tool 消息
self.messages.append(Message(
    role="tool",
    content=result.output,
    tool_call_id=tool_call_id,  # ✅ 作为参数传递
    name=function_name          # ✅ 作为参数传递
))
```

---

## 🧪 验证修复

### 运行测试脚本

```bash
# 测试 1: Message 类基础功能
python test_message_fix.py

# 测试 2: 完整消息流程
python test_full_flow.py
```

### 预期输出

```
✅ 所有测试通过！Message 格式符合阿里云百炼 API 要求
✅ 所有测试通过！Function Calling 消息格式完全正确
```

---

## 📊 修复对比

| 项目 | 之前（错误） | 现在（正确） |
|-----|-------------|-------------|
| **Message 类** | 只支持 role + content | 支持所有 Function Calling 字段 |
| **to_dict()** | 只返回 role 和 content | 返回完整字段（tool_calls 等） |
| **消息转换** | `{"role": msg.role, "content": msg.content}` | `msg.to_dict()` |
| **tool_calls** | ❌ 丢失 | ✅ 保留 |
| **tool_call_id** | ❌ 丢失 | ✅ 保留 |
| **API 兼容性** | ❌ 报错 | ✅ 正常工作 |

---

## 🎯 正确的 Function Calling 流程

```
1. 用户消息
   → {"role": "user", "content": "计算1+1"}

2. Assistant 消息（带 tool_calls）
   → {
       "role": "assistant",
       "content": "我来计算",
       "tool_calls": [{"id": "call_123", ...}]  ← 独立字段
     }

3. Tool 消息（工具结果）
   → {
       "role": "tool",
       "content": "2",
       "tool_call_id": "call_123",  ← 对应上面的 id
       "name": "calculate"
     }

4. Assistant 消息（最终回复）
   → {"role": "assistant", "content": "结果是2"}
```

**关键点**：
- ✅ tool_calls 必须是 assistant 消息的**独立字段**
- ✅ tool 消息必须有 **tool_call_id** 和 **name** 字段
- ✅ tool_call_id 必须与前面的 tool_calls[].id **一一对应**
- ✅ 使用 `msg.to_dict()` 而不是手动构建字典

---

## 📝 修改的文件

### ✅ core/llm.py
- Message 类增加 `tool_calls`、`tool_call_id`、`name` 参数
- `to_dict()` 方法返回完整字段

### ✅ core/agent.py  
- `_call_llm_with_tools()` 使用 `msg.to_dict()` 转换
- 创建消息时正确传递 Function Calling 字段

### ✅ 测试文件
- `test_message_fix.py` - Message 类测试
- `test_full_flow.py` - 完整流程测试

---

## 🔧 如何避免类似错误

### 1. 始终使用 to_dict()

```python
# ✅ 正确
messages_dict = [msg.to_dict() for msg in messages]

# ❌ 错误 - 会丢失字段
messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]
```

### 2. 调试时打印消息格式

```python
# 发送 API 前检查
for msg in messages:
    print(msg.to_dict())
    
# 检查：
# - role="tool" 前面是否有 role="assistant"
# - assistant 是否有 tool_calls
# - tool_call_id 是否匹配
```

### 3. 使用类型提示

```python
from typing import List, Dict, Optional, Any

def to_dict(self) -> Dict[str, Any]:  # 明确返回类型
    ...
```

---

## ✅ 修复完成

**所有问题已解决！**

**修改的文件**：
- ✅ `core/llm.py` - Message 类完整支持 Function Calling
- ✅ `core/agent.py` - 消息转换使用 to_dict()

**测试验证**：
- ✅ `test_message_fix.py` - 通过
- ✅ `test_full_flow.py` - 通过

**现在可以正常使用**：
```bash
python run.py
```

Function Calling 功能完全正常！🎉
