import click
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Assuming other modules are in the same package (augment_tools_core)
from .common_utils import (
    get_os_specific_vscode_paths,
    print_info,
    print_success,
    print_error,
    print_warning,
    IDEType,
    get_ide_display_name,
    validate_cleanup_options,
    get_cleanup_mode_display_name
)
from .database_manager import clean_ide_database, clean_vscode_database
from .telemetry_manager import modify_ide_telemetry_ids, modify_vscode_telemetry_ids

# Import language management
try:
    from language_manager import get_language_manager, get_text
    from config_manager import get_config_manager
    LANGUAGE_SUPPORT = True
except ImportError:
    LANGUAGE_SUPPORT = False
    def get_text(key, **kwargs):
        return key

def parse_ide_type(ide_name: str) -> IDEType:
    """Parse IDE name string to IDEType enum"""
    ide_name_lower = ide_name.lower()
    if ide_name_lower in ['vscode', 'vs-code', 'code']:
        return IDEType.VSCODE
    elif ide_name_lower in ['cursor']:
        return IDEType.CURSOR
    elif ide_name_lower in ['windsurf']:
        return IDEType.WINDSURF
    elif ide_name_lower in ['jetbrains', 'pycharm', 'intellij', 'idea', 'webstorm', 'phpstorm']:
        return IDEType.JETBRAINS
    else:
        raise click.BadParameter(get_text("cli.unsupported_ide", ide=ide_name))

@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--language', default=None, help='Set language (zh_CN, en_US)')
def main_cli(language):
    """
    AugmentCode-Free: Multi-IDE Maintenance Tools.
    Provides utilities for cleaning IDE databases and modifying telemetry IDs.
    Supports VS Code, Cursor, and Windsurf.
    """
    if LANGUAGE_SUPPORT and language:
        config_manager = get_config_manager()
        language_manager = get_language_manager(config_manager)
        language_manager.set_language(language)

@main_cli.command("clean-db")
@click.option('--ide', default='vscode', show_default=True,
              help=get_text("cli.ide_option_help"))
@click.option('--keyword', default='augment', show_default=True,
              help=get_text("cli.keyword_option_help"))
def clean_db_command(ide: str, keyword: str):
    """Cleans the specified IDE's state database by removing entries matching the keyword."""
    try:
        ide_type = parse_ide_type(ide)
        ide_name = get_ide_display_name(ide_type)

        print_info(get_text("cli.executing", operation=f"{ide_name} Database Cleaning (keyword: '{keyword}')"))

        if clean_ide_database(ide_type, keyword):
            print_info(get_text("cli.finished"))
        else:
            print_error(get_text("cli.errors"))

    except click.BadParameter as e:
        print_error(str(e))
        return

@main_cli.command("modify-ids")
@click.option('--ide', default='vscode', show_default=True,
              help=get_text("cli.ide_option_help"))
def modify_ids_command(ide: str):
    """Modifies the specified IDE's telemetry IDs (machineId, devDeviceId) in storage.json."""
    try:
        ide_type = parse_ide_type(ide)
        ide_name = get_ide_display_name(ide_type)

        print_info(get_text("cli.executing", operation=f"{ide_name} Telemetry ID Modification"))

        if modify_ide_telemetry_ids(ide_type):
            print_info(get_text("cli.finished"))
        else:
            print_error(get_text("cli.errors"))

    except click.BadParameter as e:
        print_error(str(e))
        return

@main_cli.command("run-all")
@click.option('--ide', default='vscode', show_default=True,
              help=get_text("cli.ide_option_help"))
@click.option('--keyword', default='augment', show_default=True,
              help=get_text("cli.keyword_clean_help"))
@click.pass_context
def run_all_command(ctx, ide: str, keyword: str):
    """Runs all available tools for the specified IDE: clean-db and then modify-ids."""
    try:
        ide_type = parse_ide_type(ide)
        ide_name = get_ide_display_name(ide_type)

        print_info(get_text("cli.executing", operation=f"Run All Tools for {ide_name}"))

        print_info(get_text("cli.step", step="1", operation=f"{ide_name} Database Cleaning"))
        try:
            ctx.invoke(clean_db_command, ide=ide, keyword=keyword)
        except Exception as e:
            print_error(get_text("cli.error_occurred", step="database cleaning", error=str(e)))
            print_warning(get_text("cli.proceeding"))

        print_info(get_text("cli.step", step="2", operation=f"{ide_name} Telemetry ID Modification"))
        try:
            ctx.invoke(modify_ids_command, ide=ide)
        except Exception as e:
            print_error(get_text("cli.error_occurred", step="telemetry ID modification", error=str(e)))

        print_success(get_text("cli.all_finished", ide_name=ide_name))

    except click.BadParameter as e:
        print_error(str(e))
        return

# Legacy commands for backward compatibility
@main_cli.command("clean-vscode-db", hidden=True)
@click.option('--keyword', default='augment', show_default=True, help='Keyword to search for and remove from the database (case-insensitive).')
def clean_vscode_db_command(keyword: str):
    """[DEPRECATED] Use 'clean-db --ide vscode' instead."""
    print_warning("This command is deprecated. Use 'clean-db --ide vscode' instead.")
    ctx = click.get_current_context()
    ctx.invoke(clean_db_command, ide='vscode', keyword=keyword)

@main_cli.command("modify-vscode-ids", hidden=True)
def modify_vscode_ids_command():
    """[DEPRECATED] Use 'modify-ids --ide vscode' instead."""
    print_warning("This command is deprecated. Use 'modify-ids --ide vscode' instead.")
    ctx = click.get_current_context()
    ctx.invoke(modify_ids_command, ide='vscode')

# === 新增命令：增强清理功能 ===

@main_cli.command("clean-enhanced")
@click.option('--ide', required=True, help='IDE type (vscode, cursor, windsurf, jetbrains)')
@click.option('--mode', default='hybrid',
              type=click.Choice(['database_only', 'file_only', 'hybrid', 'aggressive']),
              help='Cleanup mode (default: hybrid)')
@click.option('--keyword', default='augment', help='Keyword to search for (default: augment)')
@click.option('--force', is_flag=True, help='Force delete locked files')
@click.option('--kill-processes', is_flag=True, help='Automatically kill IDE processes')
@click.option('--skip-process-check', is_flag=True, help='Skip process check')
def clean_enhanced_command(ide, mode, keyword, force, kill_processes, skip_process_check):
    """Enhanced cleanup with multiple strategies."""
    import asyncio
    from .database_manager import clean_ide_comprehensive
    from .common_utils import validate_cleanup_options, get_cleanup_mode_display_name

    try:
        ide_type = parse_ide_type(ide)
        ide_name = get_ide_display_name(ide_type)

        # 验证选项
        valid, error_msg = validate_cleanup_options(mode, ide_type)
        if not valid:
            print_error(error_msg)
            return

        print_info(f"开始增强清理 {ide_name}")
        print_info(f"清理模式: {get_cleanup_mode_display_name(mode)}")
        print_info(f"搜索关键字: {keyword}")

        if force:
            print_info("强制删除模式已启用")
        if kill_processes:
            print_info("自动终止进程模式已启用")
        if skip_process_check:
            print_info("跳过进程检查")

        # 执行清理
        async def run_cleanup():
            result = await clean_ide_comprehensive(
                ide_type=ide_type,
                mode=mode,
                keyword=keyword,
                force_delete=force,
                kill_processes=kill_processes or not skip_process_check
            )
            return result

        result = asyncio.run(run_cleanup())

        # 显示结果
        if result["success"]:
            print_success("清理完成!")
            print_info("清理结果:")
            print_info(result["summary"])
        else:
            print_error("清理过程中发生错误")
            for error in result.get("errors", []):
                print_error(f"  - {error}")

    except Exception as e:
        print_error(f"清理失败: {e}")

@main_cli.command("check-processes")
@click.option('--ide', required=True, help='IDE type (vscode, cursor, windsurf, jetbrains)')
def check_processes_command(ide):
    """Check running IDE processes."""
    from .process_manager import ProcessManager

    try:
        ide_type = parse_ide_type(ide)
        ide_name = get_ide_display_name(ide_type)

        pm = ProcessManager()
        processes = pm.get_ide_processes(ide_type)

        if processes:
            print_info(f"找到 {len(processes)} 个 {ide_name} 进程:")
            for proc in processes:
                print_info(f"  {proc}")
        else:
            print_info(f"未找到 {ide_name} 进程")

    except Exception as e:
        print_error(f"检查进程失败: {e}")

@main_cli.command("kill-processes")
@click.option('--ide', required=True, help='IDE type (vscode, cursor, windsurf, jetbrains)')
@click.option('--force', is_flag=True, help='Force kill processes')
def kill_processes_command(ide, force):
    """Kill IDE processes."""
    import asyncio
    from .process_manager import ProcessManager

    try:
        ide_type = parse_ide_type(ide)
        ide_name = get_ide_display_name(ide_type)

        pm = ProcessManager()

        # 检查进程
        processes = pm.get_ide_processes(ide_type)
        if not processes:
            print_info(f"未找到 {ide_name} 进程")
            return

        print_warning(f"即将终止 {len(processes)} 个 {ide_name} 进程")
        for proc in processes:
            print_warning(f"  {proc}")

        if not force:
            if not click.confirm("确定要终止这些进程吗？"):
                print_info("操作已取消")
                return

        # 终止进程
        async def kill_processes():
            return await pm.kill_ide_processes(ide_type, force=True)

        success = asyncio.run(kill_processes())

        if success:
            print_success("所有进程已成功终止")
        else:
            print_warning("部分进程可能无法终止")

    except Exception as e:
        print_error(f"终止进程失败: {e}")

@main_cli.command("file-cleanup")
@click.option('--ide', required=True, help='IDE type (vscode, cursor, windsurf, jetbrains)')
@click.option('--force', is_flag=True, help='Force delete locked files')
def file_cleanup_command(ide, force):
    """Clean IDE files only (no database modification)."""
    from .file_cleaner import FileCleaner

    try:
        ide_type = parse_ide_type(ide)
        ide_name = get_ide_display_name(ide_type)

        print_info(f"开始清理 {ide_name} 文件")

        fc = FileCleaner()
        results = fc.clean_ide_files(ide_type, force)

        total_deleted = results.get("globalStorage", 0) + results.get("workspaceStorage", 0)

        if total_deleted > 0:
            print_success(f"文件清理完成，共删除 {total_deleted} 个文件")
            print_info(f"  - globalStorage: {results.get('globalStorage', 0)} 个文件")
            print_info(f"  - workspaceStorage: {results.get('workspaceStorage', 0)} 个文件")
        else:
            print_info("没有找到需要删除的文件")

    except Exception as e:
        print_error(f"文件清理失败: {e}")

if __name__ == '__main__':
    main_cli()
