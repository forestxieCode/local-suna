# Docker沙箱快速开始指南

欢迎使用Kortix Docker沙箱！本指南将帮助您在5分钟内设置并验证Docker沙箱系统。

---

## 🚀 5分钟快速开始

### 第1步：安装Docker（2分钟）

#### Windows/Mac
1. 下载Docker Desktop: https://www.docker.com/products/docker-desktop
2. 安装并启动Docker Desktop
3. 验证安装：
   ```bash
   docker --version
   docker ps
   ```

#### Linux
```bash
# 安装Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 启动Docker
sudo systemctl start docker

# 添加当前用户到docker组
sudo usermod -aG docker $USER
# 重新登录以生效
```

---

### 第2步：构建沙箱镜像（3分钟）

```bash
# 进入项目目录
cd D:\project\local-suna

# 构建Docker镜像（首次需要5-10分钟）
docker build -t kortix-sandbox:latest -f backend\core\sandbox\Dockerfile .

# 验证镜像已创建
docker images | grep kortix-sandbox
# 应该看到: kortix-sandbox   latest   ...   1.5GB
```

**Windows用户**：使用反斜杠
```powershell
docker build -t kortix-sandbox:latest -f backend\core\sandbox\Dockerfile .
```

---

### 第3步：配置环境变量（30秒）

在项目根目录的 `.env` 文件中添加（如果没有`.env`文件，创建一个）：

```bash
# 沙箱配置
SANDBOX_PROVIDER=docker

# Windows
DOCKER_HOST=npipe:////./pipe/docker_engine

# Linux/Mac
# DOCKER_HOST=unix:///var/run/docker.sock

# 沙箱资源限制
SANDBOX_IMAGE=kortix-sandbox:latest
SANDBOX_MEMORY_LIMIT=512m
SANDBOX_CPU_LIMIT=1.0
SANDBOX_TIMEOUT=300
```

---

### 第4步：运行测试（1分钟）

```bash
# 进入backend目录
cd backend

# 运行集成测试
python tests\test_docker_sandbox.py
```

**预期输出**：
```
============================================================
Docker沙箱集成测试
============================================================
  ✓ 环境配置正确: SANDBOX_PROVIDER=docker

🧪 测试: 适配器初始化
  ✓ 适配器初始化成功: Docker

🧪 测试: 沙箱生命周期
  ✓ 沙箱创建成功: abc123def456
  ✓ 沙箱状态正常: STARTED
  ✓ 沙箱已停止
  ✓ 沙箱已重启
  ✓ 沙箱已删除

🧪 测试: 命令执行
  ✓ Python命令执行成功: Hello from Python
  ✓ Node.js命令执行成功: Hello from Node.js
  ✓ Shell命令执行成功

🧪 测试: 文件操作
  ✓ 文件写入成功
  ✓ 文件读取成功: 42 字节
  ✓ 找到测试文件，目录共有 1 个文件
  ✓ 文件删除成功
  ✓ 文件已成功删除

🧪 测试: 资源监控
  ✓ 沙箱健康状态良好
  ✓ 资源监控数据获取成功:
  ℹ   CPU: 0.52%
  ℹ   内存: 1.2%
  ℹ   内存使用: 6.14 MB

🧪 测试: 兼容层
  ✓ 沙箱创建成功: xyz789abc123
  ✓ process.execute 工作正常
  ✓ files操作工作正常
  ✓ 兼容层测试完成

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

如果看到这个输出，**恭喜！** Docker沙箱已成功集成 🎉

---

## 📊 验证现有功能

确保现有工具都能正常工作：

### 方式1：交互式测试

```bash
cd backend
python
```

在Python中：

```python
import asyncio
import os

# 设置使用Docker沙箱
os.environ["SANDBOX_PROVIDER"] = "docker"

# 导入现有接口（无需修改！）
from core.sandbox.sandbox import create_sandbox, delete_sandbox

async def test():
    # 创建沙箱（使用现有API）
    sandbox = await create_sandbox(
        password="test123",
        project_id="test-project"
    )
    print(f"✓ 沙箱创建: {sandbox.id[:12]}")
    
    # 执行Python代码
    result = await sandbox.process.execute(
        "python3 -c 'import sys; print(f\"Python {sys.version}\")'",
    )
    print(f"✓ {result.stdout.strip()}")
    
    # 执行Node.js代码
    result = await sandbox.process.execute(
        "node -e 'console.log(`Node.js ${process.version}`)'",
    )
    print(f"✓ {result.stdout.strip()}")
    
    # 文件操作
    await sandbox.files.write("/workspace/demo.txt", b"Hello, Kortix!")
    content = await sandbox.files.read("/workspace/demo.txt")
    print(f"✓ 文件内容: {content.decode()}")
    
    # 列出文件
    files = await sandbox.files.list("/workspace")
    print(f"✓ 工作目录有 {len(files)} 个文件")
    
    # 清理
    await delete_sandbox(sandbox.id)
    print("✓ 测试完成，所有功能正常！")

# 运行测试
asyncio.run(test())
```

**预期输出**：
```
✓ 沙箱创建: abc123def456
✓ Python 3.11.x
✓ Node.js v20.x.x
✓ 文件内容: Hello, Kortix!
✓ 工作目录有 1 个文件
✓ 测试完成，所有功能正常！
```

---

## 🔧 常见问题

### Q: 测试失败了，怎么办？

**A**: 首先确认：
1. Docker是否正在运行：`docker ps`
2. 镜像是否已构建：`docker images | grep kortix`
3. 环境变量是否正确：查看 `.env` 文件

然后查看详细的故障排查指南：`backend/tests/DOCKER_SANDBOX_TESTING.md`

### Q: 镜像太大（1.5GB），能优化吗？

**A**: 可以，有几个选项：

1. **精简版镜像**（未来功能）- 移除Playwright浏览器
2. **多阶段构建** - 减少层数
3. **Alpine基础镜像** - 更小的基础镜像

当前1.5GB包含完整功能，适合生产使用。

### Q: 如何从Daytona迁移？

**A**: 非常简单，只需修改 `.env`：

```bash
# 之前
SANDBOX_PROVIDER=daytona
DAYTONA_API_KEY=your-key

# 之后
SANDBOX_PROVIDER=docker
# 删除或注释掉DAYTONA_*配置

# 就这么简单！无需修改代码
```

### Q: Docker沙箱相比Daytona有什么优势？

**A**: 
- ✅ **免费** - Daytona收费，Docker完全免费
- ✅ **中国友好** - 无需VPN，完全本地
- ✅ **快速** - 冷启动 < 1秒
- ✅ **可定制** - 可以修改Dockerfile添加需要的工具
- ✅ **离线可用** - 不依赖外部服务

### Q: 生产环境建议？

**A**: 

1. **资源限制**：
   ```bash
   # 根据服务器配置调整
   SANDBOX_MEMORY_LIMIT=1g
   SANDBOX_CPU_LIMIT=2.0
   ```

2. **网络隔离**：
   ```bash
   # 创建专用网络
   docker network create kortix-sandbox-net
   SANDBOX_NETWORK=kortix-sandbox-net
   ```

3. **监控**：
   - 使用 `docker stats` 监控资源使用
   - 设置告警阈值

4. **清理**：
   ```bash
   # 定期清理停止的容器
   docker container prune -f
   ```

---

## 🎯 下一步

测试通过后，您可以：

### 1. 启动应用并使用

```bash
# 确保.env配置正确
SANDBOX_PROVIDER=docker

# 启动应用
pnpm dev

# 应该看到日志：
# 🐳 Using new sandbox adapter system (Docker-based)
```

### 2. 使用现有功能

所有Shell工具、文件工具等都会自动使用Docker沙箱，无需修改！

### 3. 性能优化

- 调整资源限制
- 启用沙箱池（预创建容器）
- 优化镜像大小

### 4. 部署到生产

参考文档：
- `backend/core/DOCKER_SANDBOX_INTEGRATION.md` - 集成说明
- `backend/core/sandbox/DOCKER_SANDBOX_GUIDE.md` - 详细指南

---

## 📚 更多资源

- **完整测试指南**: `backend/tests/DOCKER_SANDBOX_TESTING.md`
- **集成文档**: `backend/core/DOCKER_SANDBOX_INTEGRATION.md`
- **使用指南**: `backend/core/sandbox/DOCKER_SANDBOX_GUIDE.md`
- **适配器接口**: `backend/core/sandbox/adapter.py`

---

## 🆘 需要帮助？

如果遇到问题：

1. 查看 `backend/tests/DOCKER_SANDBOX_TESTING.md` 故障排查部分
2. 检查Docker日志：`docker logs <container_id>`
3. 运行详细测试：`python tests/test_docker_sandbox.py`

---

**祝您使用愉快！** 🎉
