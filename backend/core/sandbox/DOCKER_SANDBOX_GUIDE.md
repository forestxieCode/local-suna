# Docker沙箱使用指南

## 构建沙箱镜像

从项目根目录运行：

```bash
# 构建镜像
docker build -t kortix-sandbox:latest -f backend/core/sandbox/Dockerfile .

# 或者构建轻量级版本（不包含浏览器）
docker build -t kortix-sandbox:lite -f backend/core/sandbox/Dockerfile.lite .
```

## 环境变量配置

在 `.env` 文件中配置：

```bash
# 沙箱提供商选择
SANDBOX_PROVIDER=docker  # docker | e2b | daytona

# Docker 配置
DOCKER_HOST=unix:///var/run/docker.sock  # Windows: npipe:////./pipe/docker_engine
SANDBOX_IMAGE=kortix-sandbox:latest
SANDBOX_NETWORK=bridge

# 资源限制
SANDBOX_MEMORY_LIMIT=512m  # 每个容器的内存限制
SANDBOX_CPU_LIMIT=1.0      # CPU 限制 (1.0 = 1 核心)
SANDBOX_TIMEOUT=300        # 执行超时（秒）

# GPU 支持（可选，需要 nvidia-docker）
SANDBOX_ENABLE_GPU=false
```

## 使用示例

### Python 代码

```python
from core.sandbox.factory import get_sandbox_adapter

# 获取沙箱适配器
adapter = await get_sandbox_adapter()

# 创建沙箱
sandbox = await adapter.create_sandbox()
print(f"Created sandbox: {sandbox.sandbox_id}")

# 执行 Python 代码
result = await adapter.execute_command(
    sandbox.sandbox_id,
    "python3 -c 'print(\"Hello from sandbox!\")'",
)
print(result.stdout)  # Hello from sandbox!

# 写入文件
await adapter.write_file(
    sandbox.sandbox_id,
    "/workspace/script.py",
    b"print('Hello, World!')"
)

# 执行文件
result = await adapter.execute_command(
    sandbox.sandbox_id,
    "python3 /workspace/script.py"
)

# 读取文件
content = await adapter.read_file(
    sandbox.sandbox_id,
    "/workspace/script.py"
)

# 列出文件
files = await adapter.list_files(
    sandbox.sandbox_id,
    "/workspace"
)

# 清理
await adapter.delete_sandbox(sandbox.sandbox_id)
```

### Node.js 代码

```python
# 执行 Node.js 代码
result = await adapter.execute_command(
    sandbox.sandbox_id,
    "node -e 'console.log(\"Hello from Node.js\")'"
)

# 使用 npm 包
await adapter.execute_command(
    sandbox.sandbox_id,
    "npm install lodash",
    working_dir="/workspace"
)

result = await adapter.execute_command(
    sandbox.sandbox_id,
    "node -e 'const _ = require(\"lodash\"); console.log(_.chunk([1,2,3,4], 2))'",
    working_dir="/workspace"
)
```

## 镜像说明

### 完整镜像 (kortix-sandbox:latest)

包含：
- Python 3.11 + 常用数据科学包
- Node.js 20 + pnpm/yarn
- Playwright (Chromium 浏览器)
- 构建工具

大小：~1.5GB

### 轻量级镜像 (kortix-sandbox:lite)

包含：
- Python 3.11 (仅核心包)
- Node.js 20
- 基本工具

大小：~500MB

不包含：
- 浏览器
- 重型数据科学包
- 额外的开发工具

## 性能优化

### 预热镜像

在启动应用前构建镜像：

```bash
docker build -t kortix-sandbox:latest -f backend/core/sandbox/Dockerfile .
```

### 沙箱池

使用沙箱池预创建容器：

```python
# 配置池大小
SANDBOX_POOL_MIN_SIZE=5
SANDBOX_POOL_MAX_SIZE=20
```

### 资源限制

根据服务器配置调整：

```bash
# 轻量级部署
SANDBOX_MEMORY_LIMIT=256m
SANDBOX_CPU_LIMIT=0.5

# 标准部署
SANDBOX_MEMORY_LIMIT=512m
SANDBOX_CPU_LIMIT=1.0

# 高性能部署
SANDBOX_MEMORY_LIMIT=1g
SANDBOX_CPU_LIMIT=2.0
```

## 故障排查

### 容器创建失败

**错误**: `Docker image 'kortix-sandbox:latest' not found`

**解决**:
```bash
docker build -t kortix-sandbox:latest -f backend/core/sandbox/Dockerfile .
```

### 无法连接 Docker

**错误**: `Failed to connect to Docker`

**解决**:
- 确认 Docker Desktop 正在运行
- Windows: 检查 Docker Engine 是否启动
- Linux: 检查 Docker daemon 状态

```bash
# Linux
sudo systemctl status docker
sudo systemctl start docker

# 检查 Docker 权限
sudo usermod -aG docker $USER
```

### 执行超时

**错误**: `Command timeout after 300 seconds`

**解决**:
```bash
# 增加超时时间
SANDBOX_TIMEOUT=600  # 10 分钟
```

### 内存不足

**错误**: Container killed (OOM)

**解决**:
```bash
# 增加内存限制
SANDBOX_MEMORY_LIMIT=1g

# 或减少并发沙箱数量
SANDBOX_POOL_MAX_SIZE=10
```

## 安全考虑

### 网络隔离

使用专用网络：

```bash
# 创建隔离网络
docker network create kortix-sandbox-net

# 配置
SANDBOX_NETWORK=kortix-sandbox-net
```

### 文件系统隔离

沙箱无法访问主机文件系统，除非显式挂载。

### 资源限制

所有容器都有 CPU 和内存限制，防止资源耗尽。

### 用户权限

容器内代码以非 root 用户 `sandbox` 运行。

## 与现有系统集成

Docker沙箱完全兼容现有的沙箱接口，可以无缝替换Daytona：

```python
# 之前 (Daytona)
from core.sandbox.sandbox import get_or_start_sandbox

# 现在 (Docker)
from core.sandbox.factory import get_sandbox_adapter

adapter = await get_sandbox_adapter()
sandbox = await adapter.create_sandbox()
```

所有工具（shell, file reader等）都会自动使用新的适配器。
