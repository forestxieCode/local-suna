# 中国本土LLM提供商使用指南

本文档介绍如何在 Kortix 中使用中国本土的 LLM 提供商，无需 VPN 即可使用。

## 支持的提供商

### 1. 阿里云百炼 (DashScope) ⭐ 推荐

**优势**:
- 国内访问速度快
- 稳定性好，阿里云基础设施
- 模型能力强（Qwen系列）
- 价格合理
- 支持超长上下文（100万tokens）

**如何使用**:

1. 注册阿里云账号: https://www.aliyun.com/
2. 开通百炼服务: https://dashscope.console.aliyun.com/
3. 创建 API 密钥: https://dashscope.console.aliyun.com/apiKey
4. 在 `.env` 中配置:

```bash
DASHSCOPE_API_KEY=sk-your-api-key-here
MAIN_LLM=dashscope
MAIN_LLM_MODEL=qwen-max
```

**可用模型**:

| 模型 | 用途 | 上下文 | 价格（¥/百万tokens） |
|------|------|--------|---------------------|
| `qwen-max` | 最强能力，复杂任务 | 32K | 输入¥40，输出¥120 |
| `qwen-plus` | 平衡性能和成本 | 32K | 输入¥4，输出¥12 |
| `qwen-turbo` | 快速响应，简单任务 | 32K | 输入¥2，输出¥6 |
| `qwen-long` | 超长上下文 | 1M | 输入¥0.5，输出¥2 |
| `qwen2.5-coder-32k` | 代码专用 | 32K | 输入¥2，输出¥6 |

**推荐配置**:
```bash
# 主要任务使用 qwen-max 获得最佳效果
MAIN_LLM_MODEL=qwen-max

# 简单推理任务使用 qwen-turbo 节省成本
REASONING_LLM_MODEL=qwen-turbo
```

---

### 2. Ollama (本地部署) ⭐ 免费

**优势**:
- 完全免费
- 离线可用，不需要网络
- 数据隐私（完全本地）
- 支持中文模型（Qwen）
- 适合开发和测试

**如何使用**:

1. 下载 Ollama: https://ollama.ai/download
2. 安装并启动（会自动运行）
3. 拉取模型:
```bash
# 推荐：Alibaba Qwen 2.5（对中文支持好）
ollama pull qwen2.5:7b

# 或其他模型
ollama pull llama3.1:8b
ollama pull deepseek-coder:6.7b
```

4. 在 `.env` 中配置:
```bash
OLLAMA_BASE_URL=http://localhost:11434
MAIN_LLM=ollama
MAIN_LLM_MODEL=qwen2.5:7b
```

**可用模型**:

| 模型 | 大小 | 用途 | 内存需求 |
|------|------|------|---------|
| `qwen2.5:7b` | 7B | 通用，中文优秀 | 8GB+ RAM |
| `qwen2.5:14b` | 14B | 更强能力 | 16GB+ RAM |
| `llama3.1:8b` | 8B | Meta 最新模型 | 8GB+ RAM |
| `deepseek-coder:6.7b` | 6.7B | 代码专用 | 8GB+ RAM |
| `mistral:7b` | 7B | 通用 | 8GB+ RAM |
| `phi3:mini` | 3.8B | 轻量级 | 4GB+ RAM |

**硬件建议**:
- CPU: 现代多核处理器（推荐8核+）
- RAM: 8GB起步，16GB更好
- GPU: 可选，有NVIDIA GPU会更快

---

### 3. 智谱 AI (ZhipuAI)

**优势**:
- 清华大学技术
- GLM 模型系列
- 有免费额度
- 支持视觉模型

**如何使用**:

1. 注册账号: https://open.bigmodel.cn/
2. 创建 API 密钥
3. 在 `.env` 中配置:
```bash
ZHIPU_API_KEY=your-api-key-here
MAIN_LLM=zhipu
MAIN_LLM_MODEL=glm-4-flash
```

**可用模型**:

| 模型 | 用途 | 上下文 | 价格（¥/百万tokens） |
|------|------|--------|---------------------|
| `glm-4` | 旗舰模型 | 128K | 输入¥100，输出¥100 |
| `glm-4-flash` | 快速经济 | 128K | 输入¥1，输出¥1 |
| `glm-4v` | 视觉理解 | 8K | 输入¥50，输出¥50 |

---

## 多提供商策略

可以同时配置多个提供商，根据任务类型选择：

```bash
# .env 配置示例

# 主要任务：使用阿里云百炼（付费，质量高）
MAIN_LLM=dashscope
MAIN_LLM_MODEL=qwen-max
DASHSCOPE_API_KEY=sk-your-key

# 简单推理：使用本地 Ollama（免费）
REASONING_LLM=ollama
REASONING_LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434

# 备用：智谱 AI
ZHIPU_API_KEY=your-zhipu-key
```

## 成本优化建议

### 1. 混合使用策略
- **复杂任务**: `qwen-max` (DashScope)
- **简单对话**: `qwen-turbo` (DashScope)
- **开发测试**: `qwen2.5:7b` (Ollama 本地)

### 2. 估算成本

以每天处理 100 万 tokens 为例：

| 策略 | 提供商 | 月成本 |
|------|--------|--------|
| 全用 qwen-max | DashScope | ¥4,800 |
| 混合 (70% turbo + 30% max) | DashScope | ¥1,200 |
| 全用本地 | Ollama | ¥0 |

### 3. 节省技巧
- 开发环境使用 Ollama 免费本地模型
- 生产环境根据任务复杂度选择模型
- 使用 `qwen-long` 处理超长文档（更便宜）
- 启用响应缓存减少重复调用

## 性能对比

基于实际测试（处理中文任务）：

| 指标 | DashScope (qwen-max) | Ollama (qwen2.5:7b) | ZhipuAI (glm-4) |
|------|---------------------|---------------------|-----------------|
| 响应速度 | ⚡⚡⚡ 快 | ⚡⚡ 中等 | ⚡⚡⚡ 快 |
| 中文理解 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 代码生成 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 成本 | 💰💰💰 中 | 💰 免费 | 💰💰 低 |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## 故障排查

### Ollama 连接问题
```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 重启 Ollama
ollama serve
```

### DashScope API 错误
- 检查 API 密钥是否正确
- 确认账户有余额
- 检查模型名称是否正确

### 网络问题
- DashScope 和 ZhipuAI 都在国内，不需要 VPN
- Ollama 完全离线，无网络要求

## 推荐配置

### 个人开发者（预算有限）
```bash
MAIN_LLM=ollama
MAIN_LLM_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
```

### 小团队（平衡成本和质量）
```bash
MAIN_LLM=dashscope
MAIN_LLM_MODEL=qwen-plus  # 性价比高
REASONING_LLM=dashscope
REASONING_LLM_MODEL=qwen-turbo  # 简单任务用便宜的
DASHSCOPE_API_KEY=sk-your-key
```

### 企业用户（追求最佳质量）
```bash
MAIN_LLM=dashscope
MAIN_LLM_MODEL=qwen-max  # 最强模型
REASONING_LLM=dashscope
REASONING_LLM_MODEL=qwen-plus
DASHSCOPE_API_KEY=sk-your-key
```

## 更多资源

- [阿里云百炼文档](https://help.aliyun.com/zh/dashscope/)
- [Ollama 官方文档](https://ollama.ai/)
- [智谱 AI 文档](https://open.bigmodel.cn/dev/api)
- [Qwen 模型介绍](https://github.com/QwenLM/Qwen)
