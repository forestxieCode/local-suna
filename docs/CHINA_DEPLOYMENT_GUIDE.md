# Kortix 中国化部署完全指南

本指南涵盖了在中国环境下部署Kortix的所有方案，无需VPN即可完整使用所有功能。

---

## 🎯 部署方案对比

| 方案 | 适用场景 | 成本 | 复杂度 | 性能 |
|------|---------|------|--------|------|
| **阿里云全家桶** | 生产环境 | 中等 | 中等 | 高 |
| **腾讯云全家桶** | 生产环境 | 中等 | 中等 | 高 |
| **本地部署** | 开发/测试 | 免费 | 低 | 中 |
| **混合部署** | 灵活场景 | 低-中 | 中 | 中-高 |

---

## 📋 方案一：阿里云全家桶（推荐生产）

### 所需服务

1. **数据库**: 阿里云RDS PostgreSQL / PolarDB
2. **存储**: 阿里云OSS
3. **LLM**: 阿里云百炼（DashScope）
4. **短信**: 阿里云短信服务
5. **邮件**: 阿里云邮件推送
6. **计算**: 阿里云ECS（运行后端和Docker沙箱）

### 部署步骤

#### 1. 准备阿里云账号

```bash
# 注册阿里云账号
# https://www.aliyun.com/

# 完成实名认证（企业或个人）
```

#### 2. 开通所需服务

**RDS PostgreSQL**:
```bash
# 1. 进入RDS控制台
# 2. 创建PostgreSQL实例（推荐配置）
#    - 版本: PostgreSQL 14+
#    - 规格: 2核4GB起步
#    - 存储: 20GB起步
# 3. 创建数据库账号和数据库
#    - 数据库名: kortix
#    - 账号: kortix_admin
# 4. 配置白名单（添加ECS内网IP）
```

**OSS对象存储**:
```bash
# 1. 进入OSS控制台
# 2. 创建Bucket
#    - 名称: kortix-files
#    - 地域: 与ECS相同（如华东1）
#    - 读写权限: 私有
#    - 存储类型: 标准存储
# 3. 创建子账号AccessKey（推荐）
```

**百炼（DashScope）**:
```bash
# 1. 访问 https://dashscope.console.aliyun.com/
# 2. 开通服务
# 3. 创建API Key
# 4. 充值（按使用付费）
```

**短信服务**:
```bash
# 1. 进入短信服务控制台
# 2. 申请签名和模板
# 3. 获取AccessKey
```

**ECS云服务器**:
```bash
# 1. 创建ECS实例
#    - 规格: 2核4GB起步（推荐4核8GB）
#    - 系统: Ubuntu 22.04 / CentOS 8
#    - 带宽: 5Mbps起步
# 2. 配置安全组
#    - 开放端口: 80, 443, 8000, 3000
```

#### 3. 配置环境变量

复制并编辑配置文件：

```bash
# 复制模板
cp .env.aliyun.example .env

# 编辑配置
nano .env
```

填入实际的配置信息：

```bash
# =============================================================================
# 云服务商选择
# =============================================================================
CLOUD_PROVIDER=aliyun

# =============================================================================
# 阿里云主账号配置
# =============================================================================
ALIYUN_ACCESS_KEY_ID=LTAI5t...（你的AccessKey ID）
ALIYUN_ACCESS_KEY_SECRET=xxx...（你的AccessKey Secret）
ALIYUN_REGION=cn-hangzhou  # 根据你的地域调整

# =============================================================================
# 数据库配置 - RDS PostgreSQL
# =============================================================================
DATABASE_PROVIDER=aliyun
ALIYUN_RDS_HOST=rm-xxxxx.pg.rds.aliyuncs.com  # RDS内网地址
ALIYUN_RDS_PORT=5432
ALIYUN_RDS_DATABASE=kortix
ALIYUN_RDS_USERNAME=kortix_admin
ALIYUN_RDS_PASSWORD=你的数据库密码

# =============================================================================
# 对象存储 - OSS
# =============================================================================
STORAGE_PROVIDER=aliyun
ALIYUN_OSS_BUCKET=kortix-files
ALIYUN_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
ALIYUN_OSS_INTERNAL_ENDPOINT=oss-cn-hangzhou-internal.aliyuncs.com  # ECS内网访问

# =============================================================================
# LLM服务 - 百炼
# =============================================================================
DASHSCOPE_API_KEY=sk-xxx...（你的DashScope API Key）
MAIN_LLM=dashscope
MAIN_LLM_MODEL=qwen-max
REASONING_LLM=dashscope
REASONING_LLM_MODEL=qwen-turbo

# =============================================================================
# 沙箱配置 - Docker
# =============================================================================
SANDBOX_PROVIDER=docker
DOCKER_HOST=unix:///var/run/docker.sock
SANDBOX_IMAGE=kortix-sandbox:latest

# =============================================================================
# 短信服务
# =============================================================================
ALIYUN_SMS_SIGN_NAME=你的短信签名
ALIYUN_SMS_TEMPLATE_CODE=SMS_123456789  # 你的模板CODE

# =============================================================================
# 邮件服务
# =============================================================================
ALIYUN_EMAIL_FROM=noreply@yourdomain.com
ALIYUN_EMAIL_FROM_NAME=Kortix
```

#### 4. ECS服务器部署

**安装依赖**:

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 安装pnpm
npm install -g pnpm

# 安装Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# 安装Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

**部署应用**:

```bash
# 克隆代码
git clone https://github.com/your-repo/kortix.git
cd kortix

# 复制配置
cp .env.aliyun.example .env
# 编辑.env填入实际配置

# 安装依赖
pnpm install
cd backend && poetry install && cd ..

# 构建Docker沙箱镜像
docker build -t kortix-sandbox:latest -f backend/core/sandbox/Dockerfile .

# 运行数据库迁移
cd backend && poetry run alembic upgrade head && cd ..

# 构建前端
cd apps/frontend && pnpm build && cd ../..

# 启动服务（使用PM2）
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # 设置开机自启
```

#### 5. 配置Nginx反向代理

```nginx
# /etc/nginx/sites-available/kortix
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/kortix /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. 配置SSL证书（推荐）

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 📋 方案二：腾讯云全家桶

与阿里云类似，使用 `.env.tencent.example` 配置：

**所需服务**:
- 数据库: 腾讯云TDSQL-C PostgreSQL版
- 存储: 腾讯云COS
- LLM: 腾讯混元（或使用Ollama本地）
- 短信: 腾讯云短信
- 邮件: 腾讯云邮件推送
- 计算: 腾讯云CVM

配置方式参考阿里云，使用对应的腾讯云服务即可。

---

## 📋 方案三：本地部署（开发/测试）

### 所需工具

- Docker Desktop
- PostgreSQL 14+
- MinIO（S3兼容存储）
- Ollama（本地LLM）
- Mailpit（本地邮件测试）

### 快速开始

```bash
# 1. 使用Docker Compose启动所有服务
docker-compose -f docker-compose.local.yaml up -d

# 服务包括：
# - PostgreSQL (端口5432)
# - MinIO (端口9000, 控制台9001)
# - Redis (端口6379)
# - Mailpit (端口1025, Web界面8025)

# 2. 安装Ollama
# Windows/Mac: https://ollama.ai/download
# Linux:
curl -fsSL https://ollama.ai/sh | sh

# 3. 拉取LLM模型
ollama pull qwen2.5:7b

# 4. 复制本地配置
cp .env.local.example .env

# 5. 安装依赖
pnpm install
cd backend && poetry install && cd ..

# 6. 构建沙箱镜像
docker build -t kortix-sandbox:latest -f backend/core/sandbox/Dockerfile .

# 7. 运行数据库迁移
cd backend && poetry run alembic upgrade head && cd ..

# 8. 启动应用
pnpm dev
```

访问:
- 前端: http://localhost:3000
- 后端: http://localhost:8000
- MinIO控制台: http://localhost:9001 (minioadmin/minioadmin)
- Mailpit: http://localhost:8025

---

## 📋 方案四：混合部署

根据需求灵活组合：

**示例1: 阿里云数据库 + 本地LLM**

```bash
# .env
CLOUD_PROVIDER=aliyun

# 数据库用阿里云RDS
DATABASE_PROVIDER=aliyun
ALIYUN_RDS_HOST=xxx

# 存储用阿里云OSS
STORAGE_PROVIDER=aliyun
ALIYUN_OSS_BUCKET=xxx

# LLM用本地Ollama（免费）
MAIN_LLM=ollama
OLLAMA_BASE_URL=http://localhost:11434

# 沙箱用Docker
SANDBOX_PROVIDER=docker
```

**示例2: 本地开发 + 云端LLM**

```bash
# .env
CLOUD_PROVIDER=local

# 数据库和存储都用本地
DATABASE_PROVIDER=local
STORAGE_PROVIDER=local

# LLM用阿里云百炼（付费但质量高）
DASHSCOPE_API_KEY=sk-xxx
MAIN_LLM=dashscope
MAIN_LLM_MODEL=qwen-max
```

---

## 🔧 成本估算

### 阿里云全家桶（小型项目）

| 服务 | 配置 | 月费用 |
|------|------|--------|
| ECS | 2核4GB | ¥100-200 |
| RDS PostgreSQL | 2核4GB | ¥200-300 |
| OSS | 10GB存储+流量 | ¥10-30 |
| 百炼 | 100万tokens | ¥40-400 |
| 短信 | 1000条 | ¥30-50 |
| 带宽 | 5Mbps | ¥50-100 |
| **总计** | | **¥430-1080/月** |

### 本地部署

| 成本 | 费用 |
|------|------|
| 硬件 | 已有电脑 |
| 软件 | 全部免费 |
| LLM | Ollama免费 |
| **总计** | **¥0** |

---

## 📊 性能对比

### LLM响应速度

| 提供商 | 延迟 | 吞吐量 | 可用性 |
|--------|------|--------|--------|
| 阿里云百炼 | 1-2s | 高 | 99.9% |
| Ollama本地 | <100ms | 中 | 100% |

### 沙箱启动速度

| 提供商 | 冷启动 | 热启动 |
|--------|--------|--------|
| Docker | <1s | <100ms |
| Daytona | 3-5s | 1-2s |

---

## 🚨 常见问题

### Q: 必须使用阿里云吗？

**A**: 不是。你可以选择：
- 阿里云全家桶
- 腾讯云全家桶
- 完全本地部署
- 混合方案（推荐开发阶段）

### Q: LLM费用会很高吗？

**A**: 取决于使用量：
- 开发测试：使用Ollama本地模型（免费）
- 小规模生产：qwen-turbo（¥2/百万tokens）
- 大规模生产：根据预算选择合适模型

### Q: 能否使用国外的Supabase？

**A**: 可以，但：
- 需要稳定的国际网络
- 延迟较高
- 不推荐国内生产环境

### Q: Docker沙箱安全吗？

**A**: 是的：
- 容器隔离
- 资源限制
- 非root用户运行
- 网络隔离选项

---

## 📚 相关文档

- **快速开始**: `docs/DOCKER_SANDBOX_QUICKSTART.md`
- **LLM提供商**: `docs/CHINA_LLM_PROVIDERS.md`
- **数据库适配器**: `backend/core/database/README.md`
- **存储适配器**: `backend/core/storage/adapters/README.md`

---

## 🆘 需要帮助？

遇到问题请：

1. 查看对应服务的文档
2. 检查配置文件是否正确
3. 查看应用日志
4. 参考故障排查文档

---

**祝部署顺利！** 🚀
