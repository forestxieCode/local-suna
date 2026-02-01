# Kortix CLI - 轻量级 AI Agent 命令行工具

<div align="center">

**🤖 简洁 · 强大 · 易用**

专为中国用户优化的 AI Agent CLI 工具

支持阿里云百炼 · Docker 沙箱代码执行 · 命令行交互

</div>

---

## ✨ 特性

- ✅ **极简设计** - 只保留核心功能，去除所有冗余
- ✅ **一条命令启动** - `python run.py` 即可开始对话
- ✅ **阿里云百炼集成** - 使用国内高质量 LLM，无需翻墙
- ✅ **代码执行** - Docker 沙箱安全执行 Python 代码
- ✅ **流式输出** - 实时显示 AI 回复，体验流畅
- ✅ **对话历史** - 自动保存对话记录
- ✅ **零配置** - 只需一个 API Key 即可使用

## 📦 快速开始

### 1. 前置要求

- **Python 3.8+**
- **Docker** (用于代码执行沙箱)
- **阿里云百炼 API Key** ([获取地址](https://dashscope.console.aliyun.com/))

### 2. 安装依赖

```bash
cd kortix-cli
pip install -r requirements.txt
```

### 3. 配置 API Key

**方法一：环境变量**（推荐）
```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env，填入你的 API Key
DASHSCOPE_API_KEY=sk-your-api-key-here
```

**方法二：修改配置文件**
```yaml
# 编辑 config.yaml
llm:
  api_key: sk-your-api-key-here
```

### 4. 运行

```bash
python run.py
```

## 🎮 使用示例

```bash
$ python run.py

╔═══════════════════════════════════════════════════════════╗
║              🤖 Kortix AI Agent CLI                       ║
║         轻量级 AI 助手 - 对话 + 代码执行                   ║
╚═══════════════════════════════════════════════════════════╝

✅ LLM: dashscope (qwen-turbo)
✅ 沙箱: 已启用 (Docker)
✅ 对话历史: 保存到文件

You: 你好，请介绍一下你自己

Agent: 你好！我是 Kortix AI Agent，一个智能助手。我可以帮你：
1. 回答问题和提供建议
2. 编写和执行 Python 代码
...

You: 帮我写一个 Python 脚本，计算斐波那契数列前 10 项

Agent: 好的，我来帮你写一个计算斐波那契数列的脚本：

```python
def fibonacci(n):
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib[:n]

result = fibonacci(10)
print("斐波那契数列前 10 项:")
for i, num in enumerate(result):
    print(f"F({i}) = {num}")
```

[执行 python 代码...]
✅ 代码执行成功

输出:
斐波那契数列前 10 项:
F(0) = 0
F(1) = 1
F(2) = 1
F(3) = 2
F(4) = 3
F(5) = 5
F(6) = 8
F(7) = 13
F(8) = 21
F(9) = 34

You: exit
👋 再见！
```

## 🔧 配置说明

### config.yaml

```yaml
# LLM 配置
llm:
  provider: dashscope       # LLM 提供商（固定为 dashscope）
  api_key: ${DASHSCOPE_API_KEY}  # API Key（从环境变量读取）
  model: qwen-turbo         # 模型选择
  temperature: 0.7          # 温度参数（0-1）
  max_tokens: 2000          # 最大生成 token 数

# Docker 沙箱配置
sandbox:
  enabled: true             # 是否启用沙箱
  image: python:3.11-slim   # Docker 镜像
  timeout: 60               # 超时时间（秒）
  memory_limit: 512         # 内存限制（MB）

# 对话历史配置
history:
  save_to_file: true        # 是否保存历史
  file_path: ./conversations/  # 保存路径
  max_messages: 50          # 最大历史消息数
```

### 可用模型

| 模型 | 说明 | 价格 |
|------|------|------|
| `qwen-turbo` | 经济型，适合日常对话 | ¥2/百万tokens |
| `qwen-plus` | 平衡型，性能更好 | ¥4/百万tokens |
| `qwen-max` | 最强性能 | ¥40/百万tokens |
| `qwen-long` | 长文本，支持100万tokens上下文 | ¥0.5/百万tokens |

## 💡 命令参考

### 交互式命令

在运行 `python run.py` 后，可以使用以下命令：

- `help` - 显示帮助信息
- `reset` - 重置对话历史
- `save` - 手动保存对话历史
- `status` - 显示系统状态
- `exit` / `quit` - 退出程序

### 命令行参数

```bash
python run.py --help           # 显示帮助
python run.py --config custom.yaml  # 使用自定义配置
python run.py --debug          # 启用调试模式
```

## 📂 项目结构

```
kortix-cli/
├── run.py                  # CLI 入口
├── config.yaml             # 配置文件
├── requirements.txt        # 依赖列表
├── .env.example            # 环境变量示例
├── .gitignore
├── README.md
├── core/                   # 核心模块
│   ├── __init__.py
│   ├── agent.py            # Agent 核心逻辑
│   ├── llm.py              # LLM 接口（阿里云百炼）
│   ├── sandbox.py          # Docker 沙箱
│   └── utils/              # 工具类
│       ├── config.py       # 配置管理
│       └── logger.py       # 日志管理
└── conversations/          # 对话历史（自动创建）
```

## 🧪 测试

### 测试 LLM

```bash
cd core
python llm.py
```

### 测试 Docker 沙箱

```bash
cd core
python sandbox.py
```

### 测试 Agent

```bash
cd core
python agent.py
```

## 🔍 常见问题

### Q1: 提示 "未设置 DASHSCOPE_API_KEY"

**A:** 请按以下步骤设置 API Key：

1. 访问 https://dashscope.console.aliyun.com/ 获取 API Key
2. 创建 `.env` 文件：`cp .env.example .env`
3. 编辑 `.env`，填入你的 API Key

### Q2: Docker 相关错误

**A:** 确保 Docker 已安装并正在运行：

```bash
# 检查 Docker 状态
docker version

# Windows: 启动 Docker Desktop
# Linux: sudo systemctl start docker
```

### Q3: 首次运行很慢

**A:** 首次运行时需要拉取 Docker 镜像（约 100MB），请耐心等待。后续运行会很快。

### Q4: 如何更换模型？

**A:** 编辑 `config.yaml`，修改 `llm.model` 字段：

```yaml
llm:
  model: qwen-max  # 改为更强的模型
```

### Q5: 如何禁用代码执行？

**A:** 编辑 `config.yaml`：

```yaml
sandbox:
  enabled: false  # 禁用沙箱
```

## 📊 性能对比

| 指标 | 原项目 | 简化版 | 改善 |
|-----|-------|--------|------|
| 文件数 | 500+ | 15 | **-97%** |
| 依赖数 | 100+ | 10 | **-90%** |
| 启动时间 | ~30s | <2s | **15x 更快** |
| 内存占用 | ~2GB | ~100MB | **-95%** |
| 配置项 | 50+ | 1 个 API Key | **极简** |

## 🛠️ 开发

### 添加新工具

在 `core/agent.py` 中添加新的 `Tool` 类：

```python
class CustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="custom_tool",
            description="自定义工具说明"
        )
    
    def execute(self, **kwargs) -> str:
        # 实现工具逻辑
        return "工具执行结果"
```

### 扩展功能

- 支持更多 LLM 提供商（编辑 `core/llm.py`）
- 添加更多编程语言支持（编辑 `core/sandbox.py`）
- 自定义系统提示词（编辑 `core/agent.py` 中的 `_build_system_prompt`）

## 📝 更新日志

### v1.0.0 (2026-02-01)

- ✅ 初始版本发布
- ✅ 支持阿里云百炼 LLM
- ✅ Docker 沙箱代码执行
- ✅ 命令行交互界面
- ✅ 对话历史管理

## 📄 许可证

Apache-2.0 License

## 🙏 致谢

本项目是从 [Kortix Suna](https://github.com/kortix-ai/suna) 项目简化而来，专为中国用户优化。

---

**有问题或建议？欢迎反馈！** 🎉
