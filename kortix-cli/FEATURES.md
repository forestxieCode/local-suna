# 核心功能详解

## 🎯 三大核心功能

### 1. ✅ 沙箱环境隔离

**完全支持** - 基于 Docker 容器的安全执行环境

#### 技术实现
```python
# core/sandbox.py
class DockerSandbox:
    - 每次代码执行在独立的 Docker 容器中
    - 容器有独立的文件系统、进程空间、网络
    - 执行完成后自动清理容器
    - 内存和 CPU 资源限制
```

#### 安全特性
- ✅ **完全隔离** - 代码运行在独立容器，不影响主机
- ✅ **资源限制** - 内存限制（默认512MB）、超时控制（默认60秒）
- ✅ **自动清理** - 执行后自动删除容器，不留痕迹
- ✅ **网络控制** - 可配置是否允许网络访问

#### 使用示例
```python
You: 写一个 Python 代码读取系统信息

Agent: 🔧 [使用工具: execute_python]
       
import platform
print(f"系统: {platform.system()}")
print(f"Python: {platform.python_version()}")

✅ 执行成功（在 Docker 容器中）
输出:
系统: Linux  # 容器内的系统
Python: 3.11.x
```

#### 验证方法
```bash
python verify_features.py
# 会测试：
# - Docker 容器隔离
# - 危险代码安全执行
# - 资源限制
# - 自动清理
```

---

### 2. ✅ 复杂多步骤自动化

**完全支持** - 基于 Function Calling 的智能工具协作

#### 技术实现
```python
# core/agent.py
class Agent:
    - Function Calling - AI 自动选择工具
    - 多轮对话循环（最多5轮）
    - 工具结果自动传递
    - 智能任务分解
```

#### 自动化能力
- ✅ **任务分解** - AI 自动将复杂任务拆分为多个步骤
- ✅ **工具组合** - 自动选择和组合多个工具
- ✅ **结果传递** - 前一步的结果自动传递给下一步
- ✅ **智能决策** - 根据执行结果调整后续步骤

#### 执行流程
```
用户请求
    ↓
AI 分析任务
    ↓
步骤1: 调用工具A → 获得结果1
    ↓
步骤2: 基于结果1，调用工具B → 获得结果2
    ↓
步骤3: 基于结果1+2，调用工具C → 获得结果3
    ↓
最终总结并回复用户
```

#### 使用示例

**示例 1: 数据处理流程**
```
You: 搜索"Python教程"，把前3个结果保存到文件，然后统计字数

Agent 自动执行:
🔧 步骤1: search(query="Python教程")
   → 获得搜索结果

🔧 步骤2: write_file(path="results.txt", content="...")
   → 保存结果

🔧 步骤3: execute_python(code="统计字数代码")
   → 统计: 共1234个字

✅ 完成！已搜索、保存并统计。
```

**示例 2: 文件分析**
```
You: 读取所有txt文件，找出最长的一个，创建摘要

Agent 自动执行:
🔧 步骤1: list_files()
   → 找到: file1.txt, file2.txt, file3.txt

🔧 步骤2: read_file("file1.txt")
   → 长度: 1000字

🔧 步骤3: read_file("file2.txt")
   → 长度: 2000字

🔧 步骤4: read_file("file3.txt")
   → 长度: 1500字

🔧 步骤5: write_file("summary.txt", content="最长的是file2.txt...")
   → 创建摘要

✅ 完成！file2.txt 最长（2000字），已创建摘要。
```

**示例 3: 计算+保存流程**
```
You: 计算从1到100的平方和，结果保存到result.txt

Agent 自动执行:
🔧 步骤1: execute_python(code="sum([i**2 for i in range(1,101)])")
   → 结果: 338350

🔧 步骤2: write_file(path="result.txt", content="338350")
   → 已保存

✅ 完成！计算结果338350已保存到result.txt
```

#### 配置
```yaml
# config.yaml
llm:
  enable_function_calling: true  # 启用
  model: qwen-plus  # 推荐 plus 或 max（更好的 function calling）
```

---

### 3. ✅ 实时流式响应

**完全支持** - 边思考边输出，即时反馈

#### 技术实现
```python
# core/agent.py
def chat(self, user_input: str, stream: bool = True):
    for chunk in response:
        yield chunk  # 实时返回每个片段
```

#### 流式特性
- ✅ **即时响应** - 首个字符在1-2秒内返回
- ✅ **边想边说** - AI 思考过程实时显示
- ✅ **工具执行可见** - 工具调用过程实时展示
- ✅ **降低等待感** - 用户不需要等待完整响应

#### 输出示例

**非流式（传统方式）**
```
You: 帮我分析这个数据

[等待10秒...]

Agent: 我已经完成了分析，结果是... [一次性显示完整内容]
```

**流式（新方式）✨**
```
You: 帮我分析这个数据

Agent: 我来
       帮你
       分析
       这个
       数据
       
🔧 [使用工具: execute_python]
       
✅ 执行
   成功
   
   结果
   显示
   ...
```

#### 使用场景

1. **长回复**
   - 传统: 等待10秒，一次性显示
   - 流式: 1秒开始显示，边想边输出

2. **工具调用**
   - 传统: 等待所有工具执行完
   - 流式: 实时显示每个工具的执行

3. **复杂任务**
   ```
   Agent: 好的，我来处理这个任务
   
   🔧 [使用工具: search]
   ✅ 搜索完成，找到5条结果
   
   🔧 [使用工具: execute_python]
   ✅ 分析完成
   
   🔧 [使用工具: write_file]
   ✅ 文件已保存
   
   完成！我已经搜索、分析并保存了结果...
   ```

#### 性能对比
```
首次响应时间（TTFB）:
  非流式: ~5-10秒
  流式:   ~1-2秒   ⚡ 快5-10倍

用户体验:
  非流式: ⏳ 长时间等待，不知道在做什么
  流式:   ✨ 即时反馈，看到进度，更有参与感
```

---

## 🧪 功能验证

### 运行验证脚本
```bash
python verify_features.py
```

### 预期输出
```
==============================================================
测试 1: Docker 沙箱环境隔离
==============================================================
✅ Docker 沙箱已初始化
✅ 沙箱执行成功！
✅ 验证：代码在完全隔离的 Docker 容器中执行

==============================================================
测试 2: 复杂多步骤自动化（Function Calling）
==============================================================
✅ Agent 已初始化
✅ 多步骤自动化完成！
   - 执行步骤数: 3
   - 调用的工具: ['calculate', 'write_file', 'read_file']
   - 是否自动协作: ✅ 是

==============================================================
测试 3: 实时流式响应
==============================================================
✅ 流式响应测试完成！
   - 接收到的块数: 156
   - 首个块延迟: 1.23秒
   - 总耗时: 3.45秒
   - 是否实时: ✅ 是

==============================================================
验证结果总结
==============================================================
沙箱环境隔离: ✅ 支持
多步骤自动化: ✅ 支持
实时流式响应: ✅ 支持

🎉 所有核心功能验证通过！
```

---

## 📊 技术栈

### 沙箱隔离
- Docker SDK for Python
- 容器资源限制
- 自动容器管理

### 多步骤自动化
- 阿里云百炼 Function Calling API
- Tool Registry 系统
- 多轮对话管理

### 流式响应
- Generator/Iterator 模式
- 实时 yield 输出
- 非阻塞 I/O

---

## 🎯 最佳实践

### 1. 沙箱使用
```yaml
# config.yaml
sandbox:
  enabled: true
  timeout: 60      # 根据任务调整
  memory_limit: 512  # 根据需要调整
```

### 2. 多步骤任务
```python
# 清晰描述任务步骤
You: "请做以下事情：
     1. 搜索Python教程
     2. 保存前3个结果到文件
     3. 统计总字数"

# AI 会自动分解并执行
```

### 3. 流式体验
```python
# run.py 中默认启用
for chunk in agent.chat(user_input, stream=True):
    print(chunk, end='', flush=True)
```

---

## 🔧 故障排查

### 沙箱问题
```bash
# 检查 Docker
docker version

# 检查镜像
docker images | grep python

# 手动测试
python core/sandbox.py
```

### Function Calling 问题
```yaml
# 确保使用支持的模型
llm:
  model: qwen-plus  # 或 qwen-max
  enable_function_calling: true
```

### 流式响应慢
```yaml
# 调整模型
llm:
  model: qwen-turbo  # 更快但能力稍弱
```

---

## ✨ 总结

Kortix CLI v2.0 完整支持：

1. ✅ **沙箱环境隔离**
   - Docker 容器完全隔离
   - 安全执行任意代码
   - 自动资源管理

2. ✅ **复杂多步骤自动化**
   - AI 智能任务分解
   - 自动工具组合
   - 多轮协作执行

3. ✅ **实时流式响应**
   - 即时首次响应
   - 边想边输出
   - 更好的用户体验

**立即验证**: `python verify_features.py`
