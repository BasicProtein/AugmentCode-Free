#!/usr/bin/env python3
"""
工作线程类
优化性能，避免UI线程阻塞
"""

import psutil
from PyQt6.QtCore import QThread, pyqtSignal
from augment_tools_core.common_utils import (
    IDEType, get_ide_display_name, get_ide_process_names
)
from augment_tools_core.database_manager import clean_ide_database, clean_ide_database_enhanced
from augment_tools_core.telemetry_manager import modify_ide_telemetry_ids
from language_manager import get_text


class BaseWorker(QThread):
    """基础工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(str)  # 进度更新
    status_changed = pyqtSignal(str, str)  # 状态变化 (message, type)
    task_completed = pyqtSignal(bool)  # 任务完成 (success)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_cancelled = False
    
    def cancel(self):
        """取消任务"""
        self.is_cancelled = True
    
    def emit_progress(self, message: str):
        """发送进度信息"""
        if not self.is_cancelled:
            self.progress_updated.emit(message)
    
    def emit_status(self, message: str, status_type: str = "info"):
        """发送状态信息"""
        if not self.is_cancelled:
            self.status_changed.emit(message, status_type)


class CloseIDEWorker(BaseWorker):
    """关闭IDE工作线程"""
    
    def __init__(self, ide_type: IDEType, parent=None):
        super().__init__(parent)
        self.ide_type = ide_type
        self.ide_name = get_ide_display_name(ide_type)
    
    def run(self):
        """执行关闭IDE任务"""
        try:
            self.emit_progress(get_text("workers.close_ide.closing", ide_name=self.ide_name))
            self.emit_status(get_text("workers.close_ide.closing", ide_name=self.ide_name), "info")

            # 获取进程名称
            process_names = get_ide_process_names(self.ide_type)
            closed_any = False

            # 查找并关闭进程
            for proc in psutil.process_iter(['pid', 'name']):
                if self.is_cancelled:
                    return

                if proc.info['name'] in process_names:
                    try:
                        proc.terminate()
                        closed_any = True
                        self.emit_progress(get_text("workers.close_ide.closed_process",
                                                  process_name=proc.info['name'],
                                                  pid=proc.info['pid']))
                    except Exception as e:
                        self.emit_progress(get_text("workers.close_ide.close_failed", error=str(e)))
                        self.emit_status(get_text("workers.close_ide.close_failed", error=str(e)), "error")

            if closed_any:
                self.emit_progress(get_text("workers.close_ide.success", ide_name=self.ide_name))
                self.emit_status(get_text("workers.close_ide.success", ide_name=self.ide_name), "success")
                self.task_completed.emit(True)
            else:
                self.emit_progress(get_text("workers.close_ide.not_found", ide_name=self.ide_name))
                self.emit_status(get_text("workers.close_ide.not_found", ide_name=self.ide_name), "warning")
                self.task_completed.emit(True)

        except Exception as e:
            self.emit_progress(get_text("workers.close_ide.error", ide_name=self.ide_name, error=str(e)))
            self.emit_status(get_text("status.failed"), "error")
            self.task_completed.emit(False)


class CleanDatabaseWorker(BaseWorker):
    """清理数据库工作线程"""
    
    def __init__(self, ide_type: IDEType, keyword: str, parent=None):
        super().__init__(parent)
        self.ide_type = ide_type
        self.keyword = keyword
        self.ide_name = get_ide_display_name(ide_type)
    
    def run(self):
        """执行清理数据库任务（增强版）"""
        try:
            self.emit_progress(get_text("workers.clean_db.starting",
                                      ide_name=self.ide_name, keyword=self.keyword))
            self.emit_status(get_text("workers.clean_db.cleaning", ide_name=self.ide_name), "info")

            # 使用增强版数据库清理，获取详细结果
            result = clean_ide_database_enhanced(self.ide_type, self.keyword)

            if self.is_cancelled:
                return

            if result["success"]:
                # 显示详细的清理结果
                if result["entries_removed"] > 0:
                    self.emit_progress(get_text("workers.clean_db.entries_removed",
                                              count=result['entries_removed']))
                else:
                    self.emit_progress(get_text("workers.clean_db.no_entries"))

                if result["backup_created"]:
                    self.emit_progress(get_text("workers.clean_db.backup_created"))

                self.emit_progress(get_text("workers.clean_db.completed"))
                self.emit_status(get_text("status.success"), "success")
                self.task_completed.emit(True)
            else:
                error_msg = result.get("error_message", get_text("status.error"))
                self.emit_progress(get_text("workers.clean_db.failed", error=error_msg))
                self.emit_status(get_text("status.error"), "error")
                self.task_completed.emit(False)

        except Exception as e:
            self.emit_progress(get_text("workers.clean_db.error", error=str(e)))
            self.emit_status(get_text("status.failed"), "error")
            self.task_completed.emit(False)


class ModifyIDsWorker(BaseWorker):
    """修改遥测ID工作线程"""
    
    def __init__(self, ide_type: IDEType, parent=None):
        super().__init__(parent)
        self.ide_type = ide_type
        self.ide_name = get_ide_display_name(ide_type)
    
    def run(self):
        """执行修改遥测ID任务"""
        try:
            self.emit_progress(get_text("workers.modify_ids.starting", ide_name=self.ide_name))
            self.emit_status(get_text("workers.modify_ids.modifying", ide_name=self.ide_name), "info")

            # 执行遥测ID修改
            success = modify_ide_telemetry_ids(self.ide_type)

            if self.is_cancelled:
                return

            if success:
                self.emit_progress(get_text("workers.modify_ids.completed"))
                self.emit_status(get_text("status.success"), "success")
                self.task_completed.emit(True)
            else:
                self.emit_progress(get_text("workers.modify_ids.failed"))
                self.emit_status(get_text("status.error"), "error")
                self.task_completed.emit(False)

        except Exception as e:
            self.emit_progress(get_text("workers.modify_ids.error", error=str(e)))
            self.emit_status(get_text("status.failed"), "error")
            self.task_completed.emit(False)


class RunAllWorker(BaseWorker):
    """一键执行所有工具工作线程"""
    
    def __init__(self, ide_type: IDEType, keyword: str, parent=None):
        super().__init__(parent)
        self.ide_type = ide_type
        self.keyword = keyword
        self.ide_name = get_ide_display_name(ide_type)
    
    def run(self):
        """执行所有工具任务"""
        try:
            self.emit_progress(get_text("workers.run_all.starting", ide_name=self.ide_name))
            self.emit_status(get_text("workers.run_all.running"), "info")

            # 步骤1: 关闭IDE
            self.emit_progress(get_text("workers.run_all.step_close", ide_name=self.ide_name))
            self._close_ide()

            if self.is_cancelled:
                return

            # 步骤2: 清理数据库
            self.emit_progress(get_text("workers.run_all.step_clean", ide_name=self.ide_name))
            db_success = clean_ide_database(self.ide_type, self.keyword)

            if self.is_cancelled:
                return

            if db_success:
                self.emit_progress(get_text("workers.run_all.db_completed"))
            else:
                self.emit_progress(get_text("workers.run_all.db_failed"))

            # 步骤3: 修改遥测ID
            self.emit_progress(get_text("workers.run_all.step_modify", ide_name=self.ide_name))
            id_success = modify_ide_telemetry_ids(self.ide_type)

            if self.is_cancelled:
                return

            if id_success:
                self.emit_progress(get_text("workers.run_all.ids_completed"))
            else:
                self.emit_progress(get_text("workers.run_all.ids_failed"))

            # 完成
            overall_success = db_success and id_success
            if overall_success:
                self.emit_progress(get_text("workers.run_all.all_completed", ide_name=self.ide_name))
                self.emit_status(get_text("status.completed"), "success")
            else:
                self.emit_progress(get_text("workers.run_all.partial_failed", ide_name=self.ide_name))
                self.emit_status(get_text("status.failed"), "warning")

            self.task_completed.emit(overall_success)

        except Exception as e:
            self.emit_progress(get_text("workers.run_all.error", error=str(e)))
            self.emit_status(get_text("status.failed"), "error")
            self.task_completed.emit(False)
    
    def _close_ide(self):
        """关闭IDE的内部方法"""
        try:
            process_names = get_ide_process_names(self.ide_type)
            for proc in psutil.process_iter(['pid', 'name']):
                if self.is_cancelled:
                    return
                if proc.info['name'] in process_names:
                    try:
                        proc.terminate()
                        self.emit_progress(get_text("workers.close_ide.closed_process",
                                                  process_name=proc.info['name'],
                                                  pid=proc.info['pid']))
                    except Exception as e:
                        self.emit_progress(get_text("workers.close_ide.close_failed", error=str(e)))
        except Exception as e:
            self.emit_progress(get_text("workers.close_ide.error", ide_name=self.ide_name, error=str(e)))


# === 新增工作线程：增强清理功能 ===

class EnhancedCleanupWorker(BaseWorker):
    """增强清理工作线程（支持多种清理模式）"""

    def __init__(self, ide_type: IDEType, mode: str = "hybrid",
                 keyword: str = "augment", force_delete: bool = False,
                 kill_processes: bool = False, parent=None):
        super().__init__(parent)
        self.ide_type = ide_type
        self.mode = mode
        self.keyword = keyword
        self.force_delete = force_delete
        self.kill_processes = kill_processes
        self.ide_name = get_ide_display_name(ide_type)

    def run(self):
        """执行增强清理任务"""
        import asyncio
        try:
            self.emit_progress(f"开始增强清理 {self.ide_name} (模式: {self.mode})")
            self.emit_status(f"正在执行增强清理...", "info")

            # 导入清理功能
            from augment_tools_core.database_manager import clean_ide_comprehensive

            # 执行异步清理
            async def run_cleanup():
                return await clean_ide_comprehensive(
                    ide_type=self.ide_type,
                    mode=self.mode,
                    keyword=self.keyword,
                    force_delete=self.force_delete,
                    kill_processes=self.kill_processes
                )

            # 在新的事件循环中运行
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            result = loop.run_until_complete(run_cleanup())

            if self.is_cancelled:
                return

            if result["success"]:
                # 显示详细结果
                self.emit_progress("清理结果:")
                if result.get("database_cleaned"):
                    self.emit_progress(f"  数据库清理: 删除 {result.get('database_entries_removed', 0)} 个条目")
                if result.get("files_deleted", 0) > 0:
                    self.emit_progress(f"  文件删除: {result['files_deleted']} 个文件")
                    self.emit_progress(f"    - globalStorage: {result.get('global_storage_files', 0)} 个")
                    self.emit_progress(f"    - workspaceStorage: {result.get('workspace_storage_files', 0)} 个")
                if result.get("processes_killed", 0) > 0:
                    self.emit_progress(f"  进程终止: {result['processes_killed']} 个进程")

                self.emit_progress("增强清理完成。")
                self.emit_status("增强清理完成", "success")
                self.task_completed.emit(True)
            else:
                error_messages = result.get("errors", ["未知错误"])
                for error in error_messages:
                    self.emit_progress(f"错误: {error}")
                self.emit_status("增强清理失败", "error")
                self.task_completed.emit(False)

        except Exception as e:
            self.emit_progress(f"增强清理时发生错误: {str(e)}")
            self.emit_status(f"清理失败: {str(e)}", "error")
            self.task_completed.emit(False)

class ProcessManagerWorker(BaseWorker):
    """进程管理工作线程"""

    def __init__(self, ide_type: IDEType, action: str = "check", parent=None):
        super().__init__(parent)
        self.ide_type = ide_type
        self.action = action  # "check" 或 "kill"
        self.ide_name = get_ide_display_name(ide_type)

    def run(self):
        """执行进程管理任务"""
        try:
            from augment_tools_core.process_manager import ProcessManager

            pm = ProcessManager()

            if self.action == "check":
                self.emit_progress(f"检查 {self.ide_name} 进程...")
                processes = pm.get_ide_processes(self.ide_type)

                if processes:
                    self.emit_progress(f"找到 {len(processes)} 个 {self.ide_name} 进程:")
                    for proc in processes:
                        self.emit_progress(f"  {proc}")
                    self.emit_status(f"找到 {len(processes)} 个进程", "info")
                else:
                    self.emit_progress(f"未找到 {self.ide_name} 进程")
                    self.emit_status("未找到进程", "info")

                self.task_completed.emit(True)

            elif self.action == "kill":
                self.emit_progress(f"终止 {self.ide_name} 进程...")

                import asyncio

                async def kill_processes():
                    return await pm.kill_ide_processes(self.ide_type, force=True)

                # 在新的事件循环中运行
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                success = loop.run_until_complete(kill_processes())

                if success:
                    self.emit_progress("所有进程已成功终止")
                    self.emit_status("进程终止完成", "success")
                    self.task_completed.emit(True)
                else:
                    self.emit_progress("部分进程可能无法终止")
                    self.emit_status("进程终止部分失败", "warning")
                    self.task_completed.emit(False)

        except Exception as e:
            self.emit_progress(f"进程管理时发生错误: {str(e)}")
            self.emit_status(f"操作失败: {str(e)}", "error")
            self.task_completed.emit(False)


# 导出所有工作线程
__all__ = [
    'BaseWorker',
    'CloseIDEWorker', 
    'CleanDatabaseWorker',
    'ModifyIDsWorker',
    'RunAllWorker'
]
