# 🚀 Kortix CLI 快速开始指南

## 5 分钟快速上手

### 步骤 1: 前置要求检查

- ✅ **Python 3.8+** 已安装
  ```bash
  python --version
  # 或
  python3 --version
  ```

- ✅ **Docker** 已安装并运行（可选，用于代码执行）
  ```bash
  docker version
  ```

- ✅ **阿里云百炼 API Key**
  - 注册地址: https://dashscope.console.aliyun.com/
  - 开通百炼服务并创建 API Key
  - 充值少量金额（建议 ¥50 起步）

---

### 步骤 2: 安装依赖

```bash
# 进入项目目录
cd kortix-cli

# 安装 Python 依赖
pip install -r requirements.txt

# 或使用 pip3
pip3 install -r requirements.txt
```

---

### 步骤 3: 配置 API Key

**方法一：使用 .env 文件（推荐）**

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件
# Windows:
notepad .env

# Linux/Mac:
nano .env
# 或
vim .env
```

在 `.env` 文件中填入你的 API Key：
```
DASHSCOPE_API_KEY=sk-your-actual-api-key-here
```

**方法二：临时环境变量**

```bash
# Windows (PowerShell)
$env:DASHSCOPE_API_KEY="sk-your-api-key"

# Linux/Mac
export DASHSCOPE_API_KEY="sk-your-api-key"
```

---

### 步骤 4: 启动运行

**方法一：使用启动脚本（推荐）**

```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

**方法二：直接运行**

```bash
# Windows
python run.py

# Linux/Mac
python3 run.py
```

---

### 步骤 5: 开始对话

启动成功后，你会看到：

```
╔═══════════════════════════════════════════════════════════╗
║              🤖 Kortix AI Agent CLI                       ║
║         轻量级 AI 助手 - 对话 + 代码执行                   ║
╚═══════════════════════════════════════════════════════════╝

✅ LLM: dashscope (qwen-turbo)
✅ 沙箱: 已启用 (Docker)
✅ 对话历史: 保存到文件

输入 'help' 查看帮助，'exit' 退出

You: 
```

现在可以开始对话了！试试以下示例：

**示例 1: 简单对话**
```
You: 你好，请介绍一下你自己
```

**示例 2: 代码执行**
```
You: 帮我写一个 Python 代码，计算 1 到 100 的和
```

**示例 3: 数据处理**
```
You: 生成 10 个随机数，并计算它们的平均值
```

---

## 💡 常用命令

在对话界面中，可以使用以下命令：

- `help` - 显示帮助信息
- `reset` - 重置对话历史
- `save` - 手动保存对话
- `status` - 查看系统状态
- `exit` / `quit` - 退出程序

---

## 🔧 常见问题快速修复

### ❌ "未设置 DASHSCOPE_API_KEY"

**解决方法：**
1. 确保已创建 `.env` 文件
2. 检查 API Key 是否正确填写
3. 重新启动程序

### ❌ "Docker 相关错误"

**解决方法：**
1. 确保 Docker Desktop 正在运行
2. 测试 Docker：`docker version`
3. 如果不需要代码执行，可以在 `config.yaml` 中禁用：
   ```yaml
   sandbox:
     enabled: false
   ```

### ❌ "ModuleNotFoundError"

**解决方法：**
```bash
# 重新安装依赖
pip install -r requirements.txt

# 或清除缓存后重装
pip cache purge
pip install -r requirements.txt
```

### ⚠️ 首次运行很慢

**原因：** 首次运行需要下载 Docker 镜像（约 100-200MB）

**解决方法：** 耐心等待，后续运行会很快

---

## 📊 成本参考

使用阿里云百炼的成本非常低：

| 模型 | 价格 | 1000 次对话约 |
|------|------|--------------|
| qwen-turbo | ¥2/百万tokens | ¥2-5 |
| qwen-plus | ¥4/百万tokens | ¥4-10 |
| qwen-max | ¥40/百万tokens | ¥40-100 |

**建议：**
- 日常使用：`qwen-turbo`（经济实惠）
- 复杂任务：`qwen-plus`（性能平衡）
- 关键场景：`qwen-max`（最强性能）

---

## 📁 目录结构说明

```
kortix-cli/
├── run.py              # 主程序入口
├── start.bat           # Windows 启动脚本
├── start.sh            # Linux/Mac 启动脚本
├── config.yaml         # 配置文件（可自定义）
├── requirements.txt    # Python 依赖
├── .env               # API Key（需自行创建）
├── .env.example       # .env 示例文件
├── README.md          # 完整文档
├── QUICKSTART.md      # 本文件
├── core/              # 核心代码
│   ├── agent.py       # Agent 逻辑
│   ├── llm.py         # LLM 接口
│   ├── sandbox.py     # Docker 沙箱
│   └── utils/         # 工具类
└── conversations/     # 对话历史（自动生成）
```

---

## 🎓 进阶使用

### 自定义模型

编辑 `config.yaml`：
```yaml
llm:
  model: qwen-max  # 更换为更强的模型
```

### 调整生成参数

```yaml
llm:
  temperature: 0.9  # 提高创造性（0-1）
  max_tokens: 4000  # 增加回复长度
```

### 禁用代码执行

```yaml
sandbox:
  enabled: false  # 禁用沙箱
```

### 保存重要对话

在对话中输入 `save` 命令，或对话结束后自动保存到 `conversations/` 目录。

---

## 📞 获取帮助

- 查看完整文档：`README.md`
- 运行测试：
  ```bash
  python core/llm.py      # 测试 LLM
  python core/sandbox.py  # 测试沙箱
  python core/agent.py    # 测试 Agent
  ```

---

**准备好了吗？开始你的 AI 之旅吧！** 🚀

```bash
python run.py
```
