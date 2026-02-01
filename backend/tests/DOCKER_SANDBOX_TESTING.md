# Docker沙箱测试和验证指南

## 前提条件检查

在运行测试之前，请确保：

### 1. Docker已安装

```bash
# 检查Docker版本
docker --version
# 应该显示: Docker version 20.x 或更高

# 检查Docker是否运行
docker ps
# 应该正常显示容器列表（可以为空）
```

**Windows用户**：
- 安装Docker Desktop: https://www.docker.com/products/docker-desktop
- 确保Docker Desktop正在运行（系统托盘中有Docker图标）

**Linux用户**：
```bash
# 启动Docker服务
sudo systemctl start docker

# 添加当前用户到docker组（避免sudo）
sudo usermod -aG docker $USER
# 需要重新登录才能生效
```

### 2. 构建沙箱镜像

```bash
# 从项目根目录运行
cd D:\project\local-suna

# 构建Docker镜像（需要5-10分钟）
docker build -t kortix-sandbox:latest -f backend\core\sandbox\Dockerfile .

# 验证镜像已创建
docker images | grep kortix-sandbox
```

**镜像大小**：约1.5GB（包含Python、Node.js、Playwright）

### 3. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
# 沙箱配置
SANDBOX_PROVIDER=docker
DOCKER_HOST=unix:///var/run/docker.sock  # Windows: npipe:////./pipe/docker_engine
SANDBOX_IMAGE=kortix-sandbox:latest
SANDBOX_MEMORY_LIMIT=512m
SANDBOX_CPU_LIMIT=1.0
```

**Windows用户注意**：
```bash
# Windows上的Docker Host配置
DOCKER_HOST=npipe:////./pipe/docker_engine
```

---

## 运行测试

### 方式1：自动化测试脚本

```bash
# 进入backend目录
cd backend

# 运行完整测试套件
python tests\test_docker_sandbox.py
```

**测试内容**：
1. ✅ 适配器初始化
2. ✅ 沙箱生命周期管理（创建、启动、停止、删除）
3. ✅ 命令执行（Python、Node.js、Shell）
4. ✅ 文件操作（读、写、列表、删除）
5. ✅ 资源监控（CPU、内存使用）
6. ✅ 兼容层验证

**预期输出**：
```
============================================================
Docker沙箱集成测试
============================================================

🧪 测试: 适配器初始化
  ✓ 适配器初始化成功: Docker

🧪 测试: 沙箱生命周期
  ℹ 创建沙箱...
  ✓ 沙箱创建成功: abc123def456
  ✓ 沙箱状态正常: STARTED
  ...

============================================================
测试总结
============================================================

  适配器初始化: ✓ 通过
  沙箱生命周期: ✓ 通过
  命令执行: ✓ 通过
  文件操作: ✓ 通过
  资源监控: ✓ 通过
  兼容层: ✓ 通过

总计: 6/6 测试通过

🎉 所有测试通过！
```

### 方式2：手动交互测试

使用Python REPL进行手动测试：

```python
# 进入backend目录并启动Python
cd backend
python

# 在Python中执行：
import asyncio
import os

# 设置环境
os.environ["SANDBOX_PROVIDER"] = "docker"

# 导入模块
from core.sandbox.factory import get_sandbox_adapter

# 创建测试函数
async def test():
    # 获取适配器
    adapter = await get_sandbox_adapter()
    print(f"适配器: {adapter.get_provider_name()}")
    
    # 创建沙箱
    print("创建沙箱...")
    info = await adapter.create_sandbox()
    sandbox_id = info.sandbox_id
    print(f"沙箱ID: {sandbox_id}")
    
    # 执行命令
    print("执行命令...")
    result = await adapter.execute_command(
        sandbox_id,
        "python3 -c 'print(\"Hello, Docker!\")'",
        timeout=30
    )
    print(f"输出: {result.stdout}")
    
    # 文件操作
    print("写入文件...")
    await adapter.write_file(
        sandbox_id,
        "/workspace/test.txt",
        b"Hello, World!"
    )
    
    print("读取文件...")
    content = await adapter.read_file(sandbox_id, "/workspace/test.txt")
    print(f"内容: {content.decode()}")
    
    # 清理
    print("删除沙箱...")
    await adapter.delete_sandbox(sandbox_id)
    print("测试完成！")

# 运行测试
asyncio.run(test())
```

### 方式3：兼容层测试

测试现有接口是否正常工作：

```python
import asyncio
import os

os.environ["SANDBOX_PROVIDER"] = "docker"

from core.sandbox.sandbox import create_sandbox, delete_sandbox

async def test_compat():
    # 使用兼容接口创建沙箱
    sandbox = await create_sandbox(
        password="test123",
        project_id="test"
    )
    print(f"沙箱创建: {sandbox.id}")
    
    # 使用Daytona-like接口执行命令
    result = await sandbox.process.execute(
        "echo 'Testing compatibility layer'"
    )
    print(f"命令输出: {result.stdout}")
    
    # 使用files接口
    await sandbox.files.write("/workspace/compat.txt", b"Test")
    content = await sandbox.files.read("/workspace/compat.txt")
    print(f"文件内容: {content}")
    
    # 清理
    await delete_sandbox(sandbox.id)
    print("兼容层测试成功！")

asyncio.run(test_compat())
```

---

## 性能测试

### 冷启动时间测试

```bash
# 测试沙箱创建时间
python -c "
import asyncio
import time
import os
os.environ['SANDBOX_PROVIDER'] = 'docker'

from core.sandbox.factory import get_sandbox_adapter

async def bench():
    adapter = await get_sandbox_adapter()
    
    start = time.time()
    info = await adapter.create_sandbox()
    elapsed = time.time() - start
    
    print(f'沙箱创建时间: {elapsed:.2f}秒')
    
    await adapter.delete_sandbox(info.sandbox_id)

asyncio.run(bench())
"
```

**预期结果**：
- Docker（首次）: 2-5秒
- Docker（镜像缓存后）: 0.5-1秒
- Daytona: 3-5秒

### 并发测试

```python
import asyncio
import os
os.environ["SANDBOX_PROVIDER"] = "docker"

from core.sandbox.factory import get_sandbox_adapter

async def create_and_test(index):
    adapter = await get_sandbox_adapter()
    info = await adapter.create_sandbox()
    
    result = await adapter.execute_command(
        info.sandbox_id,
        f"echo 'Sandbox {index}'",
    )
    
    await adapter.delete_sandbox(info.sandbox_id)
    return result.stdout.strip()

async def concurrent_test(count=5):
    tasks = [create_and_test(i) for i in range(count)]
    results = await asyncio.gather(*tasks)
    
    print(f"成功创建并测试 {len(results)} 个沙箱")
    for i, result in enumerate(results):
        print(f"  沙箱 {i}: {result}")

asyncio.run(concurrent_test(5))
```

---

## 故障排查

### 问题1：Docker连接失败

**错误**：
```
Failed to connect to Docker: ...
```

**解决方案**：
```bash
# 1. 检查Docker是否运行
docker ps

# 2. Windows: 确保Docker Desktop正在运行

# 3. Linux: 启动Docker服务
sudo systemctl start docker

# 4. 检查DOCKER_HOST配置
echo $DOCKER_HOST

# Windows应该是:
npipe:////./pipe/docker_engine

# Linux/Mac应该是:
unix:///var/run/docker.sock
```

### 问题2：镜像未找到

**错误**：
```
Docker image 'kortix-sandbox:latest' not found
```

**解决方案**：
```bash
# 重新构建镜像
docker build -t kortix-sandbox:latest -f backend\core\sandbox\Dockerfile .

# 验证镜像存在
docker images | grep kortix-sandbox
```

### 问题3：权限错误（Linux）

**错误**：
```
Permission denied while trying to connect to Docker daemon
```

**解决方案**：
```bash
# 添加用户到docker组
sudo usermod -aG docker $USER

# 重新登录或运行
newgrp docker

# 或者临时使用sudo
sudo python tests/test_docker_sandbox.py
```

### 问题4：容器启动慢

**现象**：测试超时或很慢

**解决方案**：
```bash
# 1. 检查系统资源
docker stats

# 2. 增加容器资源限制
# 在.env中修改:
SANDBOX_MEMORY_LIMIT=1g
SANDBOX_CPU_LIMIT=2.0

# 3. 清理旧容器
docker container prune -f

# 4. 清理未使用的镜像
docker image prune -a -f
```

### 问题5：命令执行超时

**错误**：
```
Command timeout after 300 seconds
```

**解决方案**：
```bash
# 增加超时时间（在.env中）
SANDBOX_TIMEOUT=600  # 10分钟

# 或在代码中指定
result = await adapter.execute_command(
    sandbox_id,
    command,
    timeout=600
)
```

---

## 验收标准

测试通过的标准：

- [x] 所有6个自动化测试通过
- [x] 沙箱创建时间 < 5秒
- [x] 命令执行正常（Python、Node.js、Shell）
- [x] 文件操作正常（读、写、列表、删除）
- [x] 兼容层正常工作（现有工具无需修改）
- [x] 资源监控有数据
- [x] 并发创建5个沙箱无错误

---

## 下一步

测试通过后：

1. **更新文档**：
   - 添加Docker沙箱到部署文档
   - 更新README快速开始指南

2. **通知用户**：
   - 发布更新说明
   - 提供Daytona到Docker迁移指南

3. **监控生产**：
   - 在staging环境测试
   - 收集性能数据
   - 收集用户反馈

4. **优化**：
   - 镜像大小优化
   - 启动时间优化
   - 沙箱池预热

5. **移除Daytona**（未来）：
   - 确认所有用户迁移
   - 移除Daytona依赖
   - 清理遗留代码
