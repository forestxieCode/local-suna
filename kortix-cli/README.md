# Kortix CLI v2.0 - 完整工具系统

**🤖 强大 · 智能 · 易用**

专为中国用户优化的 AI Agent CLI 工具 - 支持完整工具系统和 Function Calling

---

## ✨ v2.0 新特性

### 🛠️ 5大工具系统
- ✅ **文件管理** - 读写编辑搜索文件
- ✅ **Web 搜索** - 实时网络搜索（Tavily）
- ✅ **Shell 命令** - 执行系统命令
- ✅ **代码执行** - Docker 沙箱安全执行
- ✅ **计算器** - 数学计算和工具函数

### 🚀 核心能力
- ✅ **Function Calling** - AI 智能选择和调用工具
- ✅ **多轮对话** - 支持复杂任务的多步骤协作
- ✅ **流式输出** - 实时显示 AI 思考和执行过程

---

## 📦 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 API Key
```bash
cp .env.example .env
# 编辑 .env，填入你的 DASHSCOPE_API_KEY
```

### 3. 运行
```bash
python run.py
```

---

## 🎮 使用示例

### 示例 1: 文件操作
```
You: 创建一个文件 hello.txt，内容是 "Hello, Kortix!"

Agent: 🔧 [使用工具: write_file]
       ✅ 成功 - 已写入 16 字节

       文件已创建成功！
```

### 示例 2: Web 搜索
```
You: 搜索最新的 AI 新闻

Agent: 🔧 [使用工具: search]
       ✅ 成功
       
       1. **OpenAI发布GPT-5预览版**
          OpenAI今日发布了GPT-5的预览版...
          
       2. **Google推出新AI助手**
          Google宣布推出全新的AI助手...
```

### 示例 3: 代码执行
```
You: 生成10个随机数并计算平均值

Agent: 🔧 [使用工具: execute_python]
       ✅ 代码执行成功
       
       生成的随机数: [45, 23, 78, 12, ...]
       平均值: 52.30
```

### 示例 4: 多工具协作
```
You: 搜索Python教程，然后创建一个总结文档

Agent: 🔧 [使用工具: search]
       ✅ 找到5条结果
       
       🔧 [使用工具: write_file]
       ✅ 已创建文件 python_summary.md
       
       完成！已搜索并创建总结文档。
```

---

## 🛠️ 完整工具列表

| 工具 | 函数 | 说明 |
|------|------|------|
| **文件管理** | read_file | 读取文件内容 |
| | write_file | 写入文件 |
| | edit_file | 编辑文件（替换文本） |
| | list_files | 列出目录文件 |
| | search_in_files | 搜索文件内容 |
| | delete_file | 删除文件 |
| **Web 搜索** | search | 网络搜索 |
| | search_news | 新闻搜索 |
| **Shell** | execute | 执行Shell命令 |
| **计算器** | calculate | 数学计算 |
| | get_current_time | 获取当前时间 |
| **代码执行** | execute_python | 执行Python代码 |

---

## ⚙️ 配置说明

### 必需配置
- `DASHSCOPE_API_KEY` - 阿里云百炼 API Key（[获取](https://dashscope.console.aliyun.com/)）

### 可选配置
- `TAVILY_API_KEY` - Web搜索功能（[获取](https://tavily.com/)）

### config.yaml
```yaml
llm:
  model: qwen-plus  # 推荐 qwen-plus（更好的 function calling）
  
tools:
  file_manager:
    enabled: true
  web_search:
    enabled: true  # 没有 API Key 会自动禁用
  shell:
    enabled: true
  calculator:
    enabled: true
  code_executor:
    enabled: true
```

---

## 🧪 测试

### 测试所有工具
```bash
python test_tools.py
```

### 测试 Agent
```bash
python core/agent.py
```

---

## 📊 版本对比

| 特性 | v1.0 | v2.0 |
|-----|------|------|
| 工具数量 | 1 | 5 |
| Function Calling | ❌ | ✅ |
| 文件管理 | ❌ | ✅ |
| Web 搜索 | ❌ | ✅ |
| 多轮对话 | ❌ | ✅ |

---

## 💰 成本说明

### 阿里云百炼（必需）
- qwen-plus: ¥4/百万tokens（推荐）
- qwen-max: ¥40/百万tokens

### Tavily（可选）
- 免费额度: 1000次搜索/月
- 付费: $0.001/次搜索

**月成本**: ¥50-200（大部分用户）

---

## 📖 文档

- [QUICKSTART.md](QUICKSTART.md) - 5分钟快速开始
- [SUMMARY.md](SUMMARY.md) - 项目简化总结
- [使用说明.md](使用说明.md) - 详细使用指南

---

## 🎓 使用技巧

### 1. 工具自动组合
AI 会自动组合多个工具完成复杂任务：
```
You: 搜索Python教程，下载前3个链接到文件
Agent: [自动调用 search → write_file → ...]
```

### 2. 文件操作
所有文件在 `./workspace` 目录：
```
You: 列出所有文件
You: 读取 test.txt
You: 创建 script.py
```

### 3. 数学计算
支持复杂表达式：
```
You: 计算 sin(pi/2) + log(100)
You: sqrt(16) * pow(2, 3)
```

---

## 🔐 安全性

- ✅ 代码在 Docker 容器中隔离执行
- ✅ 文件操作限制在 workspace
- ✅ Shell 命令有超时限制
- ✅ 数学计算使用安全环境

---

## 📝 更新日志

### v2.0.0 (2026-02-01)
- ✅ 新增完整工具系统
- ✅ 支持 Function Calling
- ✅ 多轮对话支持
- ✅ 新增5大工具类别

### v1.0.0 (2026-02-01)
- ✅ 初始版本
- ✅ 基本对话功能

---

## 📄 许可证

Apache-2.0 License

---

**准备好体验完整的 AI Agent 了吗？** 🚀

```bash
python run.py
```
