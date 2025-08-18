"""
清理策略模块 - 整合不同的清理方式
定义和实现不同的清理策略，整合数据库清理和文件删除功能
"""
import asyncio
from enum import Enum
from typing import Dict, Any, Optional
from .common_utils import IDEType, get_ide_display_name, print_info, print_success, print_warning, print_error
from .database_manager import clean_ide_database
from .file_cleaner import FileCleaner
from .process_manager import ProcessManager

class CleanupMode(Enum):
    """清理模式枚举"""
    DATABASE_ONLY = "database_only"      # 仅数据库内容清理
    FILE_ONLY = "file_only"              # 仅物理文件删除
    HYBRID = "hybrid"                     # 混合模式（推荐）
    AGGRESSIVE = "aggressive"             # 激进模式（强制终止进程+物理删除）

class CleanupOptions:
    """清理选项配置"""
    def __init__(self, 
                 mode: CleanupMode = CleanupMode.HYBRID,
                 keyword: str = "augment",
                 force_delete: bool = False,
                 kill_processes: bool = False,
                 skip_process_check: bool = False):
        self.mode = mode
        self.keyword = keyword
        self.force_delete = force_delete
        self.kill_processes = kill_processes
        self.skip_process_check = skip_process_check

class CleanupResult:
    """清理结果"""
    def __init__(self):
        self.database_cleaned = False
        self.database_entries_removed = 0
        self.files_deleted = 0
        self.global_storage_files = 0
        self.workspace_storage_files = 0
        self.processes_killed = 0
        self.errors = []
        self.warnings = []
    
    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """添加警告信息"""
        self.warnings.append(warning)
    
    def get_summary(self) -> str:
        """获取清理结果摘要"""
        summary = []
        
        if self.database_cleaned:
            summary.append(f"数据库清理: 移除 {self.database_entries_removed} 个条目")
        
        if self.files_deleted > 0:
            summary.append(f"文件删除: {self.files_deleted} 个文件")
            summary.append(f"  - globalStorage: {self.global_storage_files} 个")
            summary.append(f"  - workspaceStorage: {self.workspace_storage_files} 个")
        
        if self.processes_killed > 0:
            summary.append(f"进程终止: {self.processes_killed} 个进程")
        
        if self.errors:
            summary.append(f"错误: {len(self.errors)} 个")
        
        if self.warnings:
            summary.append(f"警告: {len(self.warnings)} 个")
        
        return "\n".join(summary) if summary else "无操作执行"

class CleanupStrategy:
    """清理策略执行器"""
    
    def __init__(self):
        self.file_cleaner = FileCleaner()
        self.process_manager = ProcessManager()
    
    async def execute_cleanup(self, ide_type: IDEType, options: CleanupOptions) -> CleanupResult:
        """
        执行清理操作
        
        Args:
            ide_type: IDE类型
            options: 清理选项
            
        Returns:
            CleanupResult: 清理结果
        """
        result = CleanupResult()
        ide_name = get_ide_display_name(ide_type)
        
        print_info(f"开始清理 {ide_name} (模式: {options.mode.value})")
        
        try:
            # 步骤1：检查和处理进程
            if not options.skip_process_check:
                await self._handle_processes(ide_type, options, result)
            
            # 步骤2：根据模式执行清理
            if options.mode == CleanupMode.DATABASE_ONLY:
                await self._database_cleanup(ide_type, options, result)
            elif options.mode == CleanupMode.FILE_ONLY:
                await self._file_cleanup(ide_type, options, result)
            elif options.mode == CleanupMode.HYBRID:
                await self._hybrid_cleanup(ide_type, options, result)
            elif options.mode == CleanupMode.AGGRESSIVE:
                await self._aggressive_cleanup(ide_type, options, result)
            
            print_success(f"{ide_name} 清理完成")
            print_info("清理结果:")
            print_info(result.get_summary())
            
        except Exception as e:
            error_msg = f"清理过程中发生错误: {e}"
            print_error(error_msg)
            result.add_error(error_msg)
        
        return result
    
    async def _handle_processes(self, ide_type: IDEType, options: CleanupOptions, result: CleanupResult):
        """处理IDE进程"""
        print_info("检查IDE进程...")
        
        if self.process_manager.check_ide_processes(ide_type):
            processes = self.process_manager.get_ide_processes(ide_type)
            print_warning(f"检测到 {len(processes)} 个IDE进程仍在运行!")
            
            for proc in processes:
                print_warning(f"  {proc}")
            
            if options.kill_processes or options.mode == CleanupMode.AGGRESSIVE:
                print_info("自动终止IDE进程...")
                success = await self.process_manager.kill_ide_processes(ide_type, force=True)
                if success:
                    result.processes_killed = len(processes)
                    print_success("所有IDE进程已终止")
                else:
                    warning_msg = "部分进程无法终止"
                    print_warning(warning_msg)
                    result.add_warning(warning_msg)
            else:
                warning_msg = "建议先关闭IDE或使用自动终止选项"
                print_warning(warning_msg)
                result.add_warning(warning_msg)
        else:
            print_info("未检测到IDE进程")
    
    async def _database_cleanup(self, ide_type: IDEType, options: CleanupOptions, result: CleanupResult):
        """数据库清理模式"""
        print_info("执行数据库内容清理...")
        
        try:
            success = clean_ide_database(ide_type, options.keyword)
            if success:
                result.database_cleaned = True
                # 注意：这里无法获取具体删除的条目数，需要修改database_manager.py来返回这个信息
                result.database_entries_removed = 1  # 占位符
                print_success("数据库清理完成")
            else:
                error_msg = "数据库清理失败"
                print_error(error_msg)
                result.add_error(error_msg)
        except Exception as e:
            error_msg = f"数据库清理异常: {e}"
            print_error(error_msg)
            result.add_error(error_msg)
    
    async def _file_cleanup(self, ide_type: IDEType, options: CleanupOptions, result: CleanupResult):
        """文件删除模式"""
        print_info("执行物理文件删除...")
        
        try:
            file_results = self.file_cleaner.clean_ide_files(ide_type, options.force_delete)
            result.global_storage_files = file_results.get("globalStorage", 0)
            result.workspace_storage_files = file_results.get("workspaceStorage", 0)
            result.files_deleted = result.global_storage_files + result.workspace_storage_files
            
            if result.files_deleted > 0:
                print_success(f"文件删除完成，共删除 {result.files_deleted} 个文件")
            else:
                print_info("没有找到需要删除的文件")
        except Exception as e:
            error_msg = f"文件删除异常: {e}"
            print_error(error_msg)
            result.add_error(error_msg)
    
    async def _hybrid_cleanup(self, ide_type: IDEType, options: CleanupOptions, result: CleanupResult):
        """混合清理模式（推荐）"""
        print_info("执行混合清理模式...")
        
        # 先执行数据库清理
        await self._database_cleanup(ide_type, options, result)
        
        # 再执行文件清理
        await self._file_cleanup(ide_type, options, result)
        
        print_success("混合清理模式完成")
    
    async def _aggressive_cleanup(self, ide_type: IDEType, options: CleanupOptions, result: CleanupResult):
        """激进清理模式"""
        print_info("执行激进清理模式...")
        
        # 强制设置选项
        aggressive_options = CleanupOptions(
            mode=options.mode,
            keyword=options.keyword,
            force_delete=True,
            kill_processes=True,
            skip_process_check=False
        )
        
        # 强制终止进程
        if self.process_manager.check_ide_processes(ide_type):
            processes = self.process_manager.get_ide_processes(ide_type)
            print_info(f"激进模式：强制终止 {len(processes)} 个进程")
            success = await self.process_manager.kill_ide_processes(ide_type, force=True)
            if success:
                result.processes_killed = len(processes)
        
        # 执行混合清理（强制模式）
        await self._database_cleanup(ide_type, aggressive_options, result)
        await self._file_cleanup(ide_type, aggressive_options, result)
        
        print_success("激进清理模式完成")

# 便捷函数
async def quick_cleanup(ide_type: IDEType, mode: CleanupMode = CleanupMode.HYBRID, **kwargs) -> CleanupResult:
    """
    快速清理函数
    
    Args:
        ide_type: IDE类型
        mode: 清理模式
        **kwargs: 其他选项
        
    Returns:
        CleanupResult: 清理结果
    """
    options = CleanupOptions(mode=mode, **kwargs)
    strategy = CleanupStrategy()
    return await strategy.execute_cleanup(ide_type, options)

def get_cleanup_mode_description(mode: CleanupMode) -> str:
    """获取清理模式描述"""
    descriptions = {
        CleanupMode.DATABASE_ONLY: "仅清理数据库内容，保留文件结构",
        CleanupMode.FILE_ONLY: "仅删除物理文件，不修改数据库内容", 
        CleanupMode.HYBRID: "推荐模式：先清理数据库内容，再删除相关文件",
        CleanupMode.AGGRESSIVE: "激进模式：强制终止进程并删除所有相关文件"
    }
    return descriptions.get(mode, "未知模式")
