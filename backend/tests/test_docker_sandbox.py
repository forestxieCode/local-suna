#!/usr/bin/env python3
"""
Docker沙箱集成测试脚本

测试Docker沙箱适配器的完整功能，确保与现有系统兼容。

用法:
    python test_docker_sandbox.py
    
环境要求:
    - Docker已安装并运行
    - 已构建kortix-sandbox镜像
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.sandbox.factory import get_sandbox_adapter
from core.sandbox.adapter import SandboxState
from core.utils.logger import logger


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_test(name: str):
    """打印测试名称"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}🧪 测试: {name}{Colors.END}")


def print_success(message: str):
    """打印成功消息"""
    print(f"  {Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """打印错误消息"""
    print(f"  {Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """打印信息"""
    print(f"  {Colors.YELLOW}ℹ {message}{Colors.END}")


async def test_adapter_initialization():
    """测试1: 适配器初始化"""
    print_test("适配器初始化")
    
    try:
        adapter = await get_sandbox_adapter()
        
        if not adapter.is_configured():
            print_error("适配器未正确配置")
            return False
        
        provider_name = adapter.get_provider_name()
        print_success(f"适配器初始化成功: {provider_name}")
        return True
        
    except Exception as e:
        print_error(f"适配器初始化失败: {e}")
        return False


async def test_sandbox_lifecycle():
    """测试2: 沙箱生命周期"""
    print_test("沙箱生命周期管理")
    
    sandbox_id = None
    try:
        adapter = await get_sandbox_adapter()
        
        # 创建沙箱
        print_info("创建沙箱...")
        info = await adapter.create_sandbox(
            metadata={'test': 'lifecycle', 'password': 'test123'}
        )
        sandbox_id = info.sandbox_id
        print_success(f"沙箱创建成功: {sandbox_id[:12]}")
        
        # 检查状态
        print_info("检查沙箱状态...")
        info = await adapter.get_sandbox(sandbox_id)
        if info.state == SandboxState.STARTED:
            print_success("沙箱状态正常: STARTED")
        else:
            print_error(f"沙箱状态异常: {info.state}")
            return False
        
        # 停止沙箱
        print_info("停止沙箱...")
        await adapter.stop_sandbox(sandbox_id)
        print_success("沙箱已停止")
        
        # 重启沙箱
        print_info("重启沙箱...")
        await adapter.start_sandbox(sandbox_id)
        print_success("沙箱已重启")
        
        # 清理
        print_info("删除沙箱...")
        await adapter.delete_sandbox(sandbox_id)
        print_success("沙箱已删除")
        
        return True
        
    except Exception as e:
        print_error(f"生命周期测试失败: {e}")
        
        # 清理失败的沙箱
        if sandbox_id:
            try:
                await adapter.delete_sandbox(sandbox_id)
            except:
                pass
        
        return False


async def test_command_execution():
    """测试3: 命令执行"""
    print_test("命令执行")
    
    sandbox_id = None
    try:
        adapter = await get_sandbox_adapter()
        
        # 创建沙箱
        print_info("创建测试沙箱...")
        info = await adapter.create_sandbox()
        sandbox_id = info.sandbox_id
        
        # 测试Python命令
        print_info("执行Python命令...")
        result = await adapter.execute_command(
            sandbox_id,
            "python3 -c 'print(\"Hello from Python\")'",
            timeout=30
        )
        
        if result.success and "Hello from Python" in result.stdout:
            print_success(f"Python命令执行成功: {result.stdout.strip()}")
        else:
            print_error(f"Python命令执行失败: {result.stderr}")
            return False
        
        # 测试Node.js命令
        print_info("执行Node.js命令...")
        result = await adapter.execute_command(
            sandbox_id,
            "node -e 'console.log(\"Hello from Node.js\")'",
            timeout=30
        )
        
        if result.success and "Hello from Node.js" in result.stdout:
            print_success(f"Node.js命令执行成功: {result.stdout.strip()}")
        else:
            print_error(f"Node.js命令执行失败: {result.stderr}")
            return False
        
        # 测试Shell命令
        print_info("执行Shell命令...")
        result = await adapter.execute_command(
            sandbox_id,
            "echo 'Hello from Bash' && pwd",
            timeout=30
        )
        
        if result.success:
            print_success(f"Shell命令执行成功")
            print_info(f"输出: {result.stdout.strip()}")
        else:
            print_error(f"Shell命令执行失败: {result.stderr}")
            return False
        
        # 清理
        await adapter.delete_sandbox(sandbox_id)
        return True
        
    except Exception as e:
        print_error(f"命令执行测试失败: {e}")
        if sandbox_id:
            try:
                await adapter.delete_sandbox(sandbox_id)
            except:
                pass
        return False


async def test_file_operations():
    """测试4: 文件操作"""
    print_test("文件系统操作")
    
    sandbox_id = None
    try:
        adapter = await get_sandbox_adapter()
        
        # 创建沙箱
        print_info("创建测试沙箱...")
        info = await adapter.create_sandbox()
        sandbox_id = info.sandbox_id
        
        # 写入文件
        print_info("写入测试文件...")
        test_content = b"Hello, Docker Sandbox!\nThis is a test file."
        await adapter.write_file(
            sandbox_id,
            "/workspace/test.txt",
            test_content
        )
        print_success("文件写入成功")
        
        # 读取文件
        print_info("读取测试文件...")
        content = await adapter.read_file(sandbox_id, "/workspace/test.txt")
        
        if content == test_content:
            print_success(f"文件读取成功: {len(content)} 字节")
        else:
            print_error(f"文件内容不匹配")
            return False
        
        # 列出文件
        print_info("列出工作目录...")
        files = await adapter.list_files(sandbox_id, "/workspace")
        
        test_file_found = any(f.path.endswith('test.txt') for f in files)
        if test_file_found:
            print_success(f"找到测试文件，目录共有 {len(files)} 个文件")
        else:
            print_error("测试文件未找到")
            return False
        
        # 删除文件
        print_info("删除测试文件...")
        await adapter.delete_file(sandbox_id, "/workspace/test.txt")
        print_success("文件删除成功")
        
        # 验证删除
        files = await adapter.list_files(sandbox_id, "/workspace")
        test_file_found = any(f.path.endswith('test.txt') for f in files)
        
        if not test_file_found:
            print_success("文件已成功删除")
        else:
            print_error("文件仍然存在")
            return False
        
        # 清理
        await adapter.delete_sandbox(sandbox_id)
        return True
        
    except Exception as e:
        print_error(f"文件操作测试失败: {e}")
        if sandbox_id:
            try:
                await adapter.delete_sandbox(sandbox_id)
            except:
                pass
        return False


async def test_resource_monitoring():
    """测试5: 资源监控"""
    print_test("资源监控")
    
    sandbox_id = None
    try:
        adapter = await get_sandbox_adapter()
        
        # 创建沙箱
        print_info("创建测试沙箱...")
        info = await adapter.create_sandbox()
        sandbox_id = info.sandbox_id
        
        # 健康检查
        print_info("执行健康检查...")
        is_healthy = await adapter.health_check(sandbox_id)
        
        if is_healthy:
            print_success("沙箱健康状态良好")
        else:
            print_error("沙箱健康检查失败")
            return False
        
        # 获取资源使用情况
        print_info("获取资源使用情况...")
        usage = await adapter.get_resource_usage(sandbox_id)
        
        if usage:
            print_success("资源监控数据获取成功:")
            if 'cpu_percent' in usage:
                print_info(f"  CPU: {usage['cpu_percent']}%")
            if 'memory_percent' in usage:
                print_info(f"  内存: {usage['memory_percent']}%")
            if 'memory_bytes' in usage:
                memory_mb = usage['memory_bytes'] / (1024 * 1024)
                print_info(f"  内存使用: {memory_mb:.2f} MB")
        else:
            print_error("无法获取资源使用数据")
            return False
        
        # 清理
        await adapter.delete_sandbox(sandbox_id)
        return True
        
    except Exception as e:
        print_error(f"资源监控测试失败: {e}")
        if sandbox_id:
            try:
                await adapter.delete_sandbox(sandbox_id)
            except:
                pass
        return False


async def test_compatibility_layer():
    """测试6: 兼容层"""
    print_test("兼容层（compat.py）")
    
    try:
        from core.sandbox.sandbox import get_or_start_sandbox, create_sandbox
        
        # 创建沙箱（使用兼容接口）
        print_info("使用兼容接口创建沙箱...")
        sandbox = await create_sandbox(
            password="test123",
            project_id="test-project"
        )
        
        print_success(f"沙箱创建成功: {sandbox.id[:12]}")
        
        # 测试process.execute
        print_info("测试process.execute...")
        result = await sandbox.process.execute("echo 'Test'")
        
        if result.success:
            print_success("process.execute 工作正常")
        else:
            print_error("process.execute 失败")
            return False
        
        # 测试files.write和files.read
        print_info("测试files操作...")
        await sandbox.files.write("/workspace/compat_test.txt", b"Compat test")
        content = await sandbox.files.read("/workspace/compat_test.txt")
        
        if content == b"Compat test":
            print_success("files操作工作正常")
        else:
            print_error("files操作失败")
            return False
        
        # 清理
        from core.sandbox.sandbox import delete_sandbox
        await delete_sandbox(sandbox.id)
        print_success("兼容层测试完成")
        
        return True
        
    except Exception as e:
        print_error(f"兼容层测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有测试"""
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}Docker沙箱集成测试{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    # 检查环境变量
    sandbox_provider = os.getenv("SANDBOX_PROVIDER", "").lower()
    if sandbox_provider != "docker":
        print_error("请设置 SANDBOX_PROVIDER=docker")
        print_info("在 .env 文件中添加: SANDBOX_PROVIDER=docker")
        return False
    
    print_success(f"环境配置正确: SANDBOX_PROVIDER={sandbox_provider}")
    
    tests = [
        ("适配器初始化", test_adapter_initialization),
        ("沙箱生命周期", test_sandbox_lifecycle),
        ("命令执行", test_command_execution),
        ("文件操作", test_file_operations),
        ("资源监控", test_resource_monitoring),
        ("兼容层", test_compatibility_layer),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"测试异常: {e}")
            results.append((test_name, False))
    
    # 打印总结
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}测试总结{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✓ 通过{Colors.END}" if result else f"{Colors.RED}✗ 失败{Colors.END}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{Colors.BOLD}总计: {passed}/{total} 测试通过{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过！{Colors.END}")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ 部分测试失败{Colors.END}")
        return False


if __name__ == "__main__":
    # 设置环境变量
    os.environ["SANDBOX_PROVIDER"] = "docker"
    
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}测试被用户中断{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}测试运行失败: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
