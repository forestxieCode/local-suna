# 常见错误快速修复手册

## 错误 1: tool_calls 相关错误

### 🐛 错误信息
```
InternalError.Algo.InvalidParameter: messages with role "tool" must be a 
response to a preceeding message with "tool_calls".
```

### ⚡ 快速修复
已修复！查看详细说明：
- **ERROR_FIX.md** - 完整说明
- **QUICK_FIX.md** - 快速参考

### ✅ 修复内容
1. `core/llm.py` - Message 类支持 Function Calling 字段
2. `core/agent.py` - 使用 `msg.to_dict()` 转换消息

### 🧪 验证
```bash
python test_message_fix.py
python test_full_flow.py
```

---

## 错误 2: StopIteration 错误

### 🐛 错误信息
```
❌ 错误: generator raised StopIteration
RuntimeError: generator raised StopIteration
```

### ⚡ 快速修复
已修复！查看详细说明：
- **STOPITERATION_FIX.md** - 完整说明

### 原因
生成器函数中使用了 `return value`（Python 3.7+ 不允许）

### ✅ 修复内容
`core/llm.py` - LLM.chat() 方法
- **移除**: `return full_content`
- **结果**: 函数自然结束

### 🧪 验证
```bash
python test_stopiteration_fix.py
```

---

## 错误 3: Docker 相关错误

### 🐛 可能的错误
```
Docker daemon not running
Cannot connect to Docker
```

### ⚡ 解决方案

**Windows**:
```bash
# 启动 Docker Desktop
# 或通过服务启动 Docker
```

**Linux**:
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

**验证**:
```bash
docker version
docker ps
```

---

## 错误 4: API Key 相关错误

### 🐛 可能的错误
```
Invalid API key
Authentication failed
```

### ⚡ 解决方案

1. 检查 `.env` 文件：
```bash
cat .env
# 应该包含: DASHSCOPE_API_KEY=sk-xxxxx
```

2. 确认 API Key 有效：
```bash
# 登录阿里云百炼控制台检查
https://dashscope.console.aliyun.com/
```

3. 重新设置：
```bash
echo "DASHSCOPE_API_KEY=sk-your-new-key" > .env
```

---

## 错误 5: 依赖安装问题

### 🐛 可能的错误
```
ModuleNotFoundError: No module named 'xxx'
ImportError: cannot import name 'xxx'
```

### ⚡ 解决方案

```bash
# 重新安装依赖
pip install -r requirements.txt

# 或使用特定版本
pip install -r requirements.txt --force-reinstall

# 清理缓存重装
pip cache purge
pip install -r requirements.txt
```

---

## 错误 6: 配置文件问题

### 🐛 可能的错误
```
Config file not found
Invalid configuration
```

### ⚡ 解决方案

1. 检查 `config.yaml` 是否存在
2. 验证 YAML 格式：
```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

3. 恢复默认配置（如果损坏）

---

## 诊断工具

### 🔍 消息格式诊断
```bash
python diagnose.py
```

### 🔍 核心功能验证
```bash
python verify_features.py
```

### 🔍 工具系统测试
```bash
python test_tools.py
```

### 🔍 完整测试套件
```bash
python test_message_fix.py      # Message 类测试
python test_full_flow.py         # 完整流程测试
python test_stopiteration_fix.py # StopIteration 测试
```

---

## 快速检查清单

运行前检查：
- [ ] Docker 是否运行？ `docker version`
- [ ] API Key 是否设置？ `cat .env`
- [ ] 依赖是否安装？ `pip list | grep dashscope`
- [ ] 配置文件是否存在？ `ls config.yaml`

如果都正常：
```bash
python run.py
```

---

## 获取帮助

### 📖 文档索引

| 文档 | 内容 |
|-----|------|
| **README.md** | 完整使用指南 |
| **QUICKSTART.md** | 5分钟快速开始 |
| **ERROR_FIX.md** | tool_calls 错误修复 |
| **STOPITERATION_FIX.md** | StopIteration 错误修复 |
| **FEATURES.md** | 核心功能详解 |
| **QUICK_FIX.md** | 快速修复参考 |

### 🧪 测试文件

| 文件 | 用途 |
|-----|------|
| **diagnose.py** | 消息格式诊断 |
| **verify_features.py** | 核心功能验证 |
| **test_tools.py** | 工具系统测试 |
| **test_message_fix.py** | Message 类测试 |
| **test_full_flow.py** | 完整流程测试 |
| **test_stopiteration_fix.py** | StopIteration 测试 |

---

## 仍然有问题？

1. **查看日志**: 检查终端输出的详细错误信息
2. **运行诊断**: `python diagnose.py`
3. **检查文档**: 查看对应的 *_FIX.md 文件
4. **重启环境**: 重新启动 Docker 和 Python 环境

---

最后更新：2026-02-01
