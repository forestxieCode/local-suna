-- ============================================================================
-- Kortix 数据库初始化脚本
-- ============================================================================
-- 本脚本在PostgreSQL首次启动时自动执行，创建必要的扩展和基础结构

-- 启用必要的PostgreSQL扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID生成
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- 文本搜索
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN索引支持
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- 性能统计

-- 创建应用角色（如果需要更细粒度的权限控制）
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kortix_app') THEN
    CREATE ROLE kortix_app;
  END IF;
END
$$;

-- 授予基本权限
GRANT ALL PRIVILEGES ON DATABASE kortix TO kortix;

-- 设置默认schema
SET search_path TO public;

-- 创建时间戳触发器函数（自动更新updated_at字段）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 输出初始化完成信息
DO $$
BEGIN
  RAISE NOTICE '✅ Kortix数据库初始化完成';
  RAISE NOTICE '📊 已启用扩展: uuid-ossp, pg_trgm, btree_gin, pg_stat_statements';
  RAISE NOTICE '🔧 已创建触发器函数: update_updated_at_column()';
END
$$;
