#!/usr/bin/env python3
"""
Kortix CLI - 轻量级 AI Agent 命令行工具

使用方法:
    python run.py                 # 启动交互式对话
    python run.py --config path   # 使用自定义配置文件
    python run.py --help          # 显示帮助信息
"""

import sys
import os
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich import print as rprint
from rich.prompt import Prompt

from core.agent import Agent
from core.utils import init_config, setup_logging, get_config

console = Console()


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🤖 Kortix AI Agent CLI                       ║
║                                                           ║
║         轻量级 AI 助手 - 对话 + 代码执行                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    console.print(banner, style="bold blue")


def print_help():
    """打印帮助信息"""
    help_text = """
**可用命令:**

- `help` - 显示此帮助信息
- `reset` - 重置对话历史
- `save` - 保存当前对话历史
- `exit` 或 `quit` - 退出程序

**使用提示:**

1. 直接输入问题与 AI 对话
2. 可以要求 AI 编写和执行代码
3. 代码会在安全的 Docker 容器中执行

**示例:**

```
You: 帮我写一个计算质数的 Python 函数
You: 请分析这段数据: [1, 2, 3, 4, 5]
You: 生成一个随机密码
```
"""
    console.print(Markdown(help_text))


def print_status():
    """打印系统状态"""
    config = get_config()
    
    status_text = f"""
**系统状态:**

✅ LLM: {config.llm_provider} ({config.llm_model})
✅ 沙箱: {"已启用 (Docker)" if config.sandbox_enabled else "已禁用"}
✅ 对话历史: {"保存到文件" if config.history_save_to_file else "仅内存"}
"""
    console.print(Markdown(status_text))


@click.command()
@click.option('--config', default='config.yaml', help='配置文件路径')
@click.option('--debug', is_flag=True, help='启用调试模式')
def main(config: str, debug: bool):
    """Kortix AI Agent CLI - 命令行 AI 助手"""
    
    # 初始化配置
    try:
        init_config(config)
        cfg = get_config()
        
        # 设置日志级别
        log_level = "DEBUG" if debug else cfg.log_level
        log_file = cfg.get('logging.file_path') if cfg.get('logging.save_to_file') else None
        setup_logging(level=log_level, log_file=log_file)
    
    except FileNotFoundError as e:
        console.print(f"[red]错误: {e}[/red]")
        console.print("\n[yellow]提示: 请确保 config.yaml 存在，或使用 --config 指定配置文件[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]初始化失败: {e}[/red]")
        sys.exit(1)
    
    # 打印欢迎信息
    print_banner()
    print_status()
    
    # 初始化 Agent
    try:
        agent = Agent()
        console.print("[green]✅ Agent 初始化成功[/green]")
        
        if cfg.sandbox_enabled:
            console.print("[green]✅ Docker 沙箱已就绪[/green]")
        
        console.print("\n[dim]输入 'help' 查看帮助，'exit' 退出[/dim]\n")
    
    except ValueError as e:
        console.print(f"[red]错误: {e}[/red]")
        console.print("\n[yellow]请检查配置文件中的 API Key 设置[/yellow]")
        console.print("[yellow]或设置环境变量: DASHSCOPE_API_KEY=your-api-key[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Agent 初始化失败: {e}[/red]")
        import traceback
        if debug:
            traceback.print_exc()
        sys.exit(1)
    
    # 主循环
    try:
        while True:
            # 获取用户输入
            try:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
            except (KeyboardInterrupt, EOFError):
                console.print("\n\n[yellow]👋 再见！[/yellow]")
                break
            
            if not user_input:
                continue
            
            # 处理命令
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("\n[yellow]👋 再见！[/yellow]")
                break
            
            elif user_input.lower() == 'help':
                print_help()
                continue
            
            elif user_input.lower() == 'reset':
                agent.reset()
                console.print("[green]✅ 对话历史已重置[/green]")
                continue
            
            elif user_input.lower() == 'save':
                agent.save_history()
                console.print("[green]✅ 对话历史已保存[/green]")
                continue
            
            elif user_input.lower() == 'status':
                print_status()
                continue
            
            # 与 Agent 对话
            try:
                console.print("\n[bold green]Agent[/bold green]: ", end='')
                
                # 流式输出
                response = ""
                for chunk in agent.chat(user_input, stream=True):
                    console.print(chunk, end='', style="")
                    response += chunk
                
                console.print()  # 换行
            
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠️ 对话已中断[/yellow]")
                continue
            
            except Exception as e:
                console.print(f"\n[red]❌ 错误: {e}[/red]")
                if debug:
                    import traceback
                    traceback.print_exc()
    
    finally:
        # 保存对话历史
        try:
            agent.save_history()
        except Exception:
            pass
        
        # 清理资源
        try:
            agent.cleanup()
        except Exception:
            pass
        
        console.print("\n[dim]感谢使用 Kortix AI Agent![/dim]")


if __name__ == "__main__":
    main()
