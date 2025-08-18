#!/usr/bin/env python3
"""
补丁操作Worker - 异步执行补丁相关任务
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import List, Optional, Dict

from augment_tools_core.common_utils import IDEType, print_info, print_success, print_error, print_warning
from augment_tools_core.patch_manager import PatchManager, PatchMode, PatchResult
from augment_tools_core.extension_finder import ExtensionFinder
from language_manager import get_text


class PatchWorker(QThread):
    """补丁操作Worker"""
    
    # 信号定义
    progress_updated = pyqtSignal(str)  # 进度更新
    patch_completed = pyqtSignal(bool, str)  # 补丁完成 (成功, 消息)
    file_found = pyqtSignal(str, str)  # 找到文件 (文件路径, 状态)
    
    def __init__(self, ide_type: IDEType, patch_mode: PatchMode, portable_root: Optional[str] = None):
        super().__init__()
        self.ide_type = ide_type
        self.patch_mode = patch_mode
        self.portable_root = portable_root
        self.patch_manager = PatchManager()
        self.extension_finder = ExtensionFinder()
        
    def run(self):
        """执行补丁操作"""
        try:
            self.progress_updated.emit(get_text("patch.searching"))

            # 查找扩展文件
            extension_files = self.extension_finder.find_extension_files(
                self.ide_type, self.portable_root
            )

            if not extension_files:
                self.patch_completed.emit(False, get_text("patch.not_found", ide_type=self.ide_type.value))
                return

            self.progress_updated.emit(get_text("patch.found_files", count=len(extension_files)))

            # 对每个文件应用补丁
            success_count = 0
            total_files = len(extension_files)

            for i, file_path in enumerate(extension_files, 1):
                self.progress_updated.emit(get_text("patch.processing",
                                                  current=i, total=total_files, file=file_path))

                # 检查文件状态
                status = self.patch_manager.get_patch_status(file_path)
                self.file_found.emit(file_path, status)

                if status == get_text("patch.status.patched"):
                    self.progress_updated.emit(get_text("patch.already_patched", file=file_path))
                    continue

                # 应用补丁
                result = self.patch_manager.apply_patch(file_path, self.patch_mode)

                if result.success:
                    success_count += 1
                    self.progress_updated.emit(get_text("patch.patch_success", file=file_path))
                else:
                    self.progress_updated.emit(get_text("patch.patch_failed", message=result.message))

            # 完成总结
            if success_count > 0:
                message = get_text("patch.completed", success=success_count, total=total_files)
                self.progress_updated.emit(f"🎉 {message}")
                self.patch_completed.emit(True, message)
            else:
                message = get_text("patch.no_success")
                self.progress_updated.emit(f"⚠️ {message}")
                self.patch_completed.emit(False, message)

        except Exception as e:
            error_msg = get_text("patch.error", error=str(e))
            self.progress_updated.emit(f"❌ {error_msg}")
            self.patch_completed.emit(False, error_msg)


class RestoreWorker(QThread):
    """恢复操作Worker"""
    
    # 信号定义
    progress_updated = pyqtSignal(str)  # 进度更新
    restore_completed = pyqtSignal(bool, str)  # 恢复完成 (成功, 消息)
    
    def __init__(self, ide_type: IDEType, portable_root: Optional[str] = None):
        super().__init__()
        self.ide_type = ide_type
        self.portable_root = portable_root
        self.patch_manager = PatchManager()
        self.extension_finder = ExtensionFinder()
        
    def run(self):
        """执行恢复操作"""
        try:
            self.progress_updated.emit(get_text("patch.searching"))

            # 查找扩展文件
            extension_files = self.extension_finder.find_extension_files(
                self.ide_type, self.portable_root
            )

            if not extension_files:
                self.restore_completed.emit(False, get_text("patch.not_found", ide_type=self.ide_type.value))
                return

            self.progress_updated.emit(get_text("patch.found_files", count=len(extension_files)))

            # 对每个文件尝试恢复
            success_count = 0
            total_files = len(extension_files)

            for i, file_path in enumerate(extension_files, 1):
                self.progress_updated.emit(get_text("patch.restoring",
                                                  current=i, total=total_files, file=file_path))

                result = self.patch_manager.restore_from_backup(file_path)

                if result.success:
                    success_count += 1
                    self.progress_updated.emit(get_text("patch.restore_success", file=file_path))
                else:
                    self.progress_updated.emit(get_text("patch.restore_skipped", message=result.message))

            # 完成总结
            if success_count > 0:
                message = get_text("patch.restore_completed", success=success_count, total=total_files)
                self.progress_updated.emit(f"🎉 {message}")
                self.restore_completed.emit(True, message)
            else:
                message = get_text("patch.restore_no_success")
                self.progress_updated.emit(f"⚠️ {message}")
                self.restore_completed.emit(False, message)

        except Exception as e:
            error_msg = get_text("patch.restore_error", error=str(e))
            self.progress_updated.emit(f"❌ {error_msg}")
            self.restore_completed.emit(False, error_msg)


class ScanWorker(QThread):
    """扫描Worker - 查找和检查扩展文件状态"""
    
    # 信号定义
    progress_updated = pyqtSignal(str)  # 进度更新
    scan_completed = pyqtSignal(dict)  # 扫描完成 (结果字典)
    file_found = pyqtSignal(str, str, str)  # 找到文件 (IDE类型, 文件路径, 状态)
    
    def __init__(self, ide_types: List[IDEType], portable_roots: Optional[Dict[IDEType, str]] = None):
        super().__init__()
        self.ide_types = ide_types
        self.portable_roots = portable_roots or {}
        self.patch_manager = PatchManager()
        self.extension_finder = ExtensionFinder()
        
    def run(self):
        """执行扫描操作"""
        try:
            self.progress_updated.emit(get_text("patch.scanning"))

            results = {}

            for ide_type in self.ide_types:
                self.progress_updated.emit(get_text("patch.scanning_ide", ide_type=ide_type.value))

                portable_root = self.portable_roots.get(ide_type)
                extension_files = self.extension_finder.find_extension_files(ide_type, portable_root)

                ide_results = []
                for file_path in extension_files:
                    status = self.patch_manager.get_patch_status(file_path)
                    ide_results.append({
                        'path': file_path,
                        'status': status
                    })
                    self.file_found.emit(ide_type.value, file_path, status)

                results[ide_type.value] = ide_results
                self.progress_updated.emit(get_text("patch.scan_completed",
                                                  ide_type=ide_type.value, count=len(extension_files)))

            self.progress_updated.emit(get_text("patch.scan_finished"))
            self.scan_completed.emit(results)

        except Exception as e:
            error_msg = get_text("patch.scan_error", error=str(e))
            self.progress_updated.emit(f"❌ {error_msg}")
            self.scan_completed.emit({})


class BatchPatchWorker(QThread):
    """批量补丁Worker - 对多个IDE同时应用补丁"""
    
    # 信号定义
    progress_updated = pyqtSignal(str)  # 进度更新
    batch_completed = pyqtSignal(bool, str, dict)  # 批量完成 (成功, 消息, 详细结果)
    ide_completed = pyqtSignal(str, bool, str)  # 单个IDE完成 (IDE类型, 成功, 消息)
    
    def __init__(self, ide_configs: Dict[IDEType, Dict]):
        """
        ide_configs: {
            IDEType.VSCODE: {
                'patch_mode': PatchMode.RANDOM,
                'portable_root': None
            },
            ...
        }
        """
        super().__init__()
        self.ide_configs = ide_configs
        self.patch_manager = PatchManager()
        self.extension_finder = ExtensionFinder()
        
    def run(self):
        """执行批量补丁操作"""
        try:
            self.progress_updated.emit(get_text("patch.batch_starting"))

            total_ides = len(self.ide_configs)
            results = {}
            overall_success = True

            for i, (ide_type, config) in enumerate(self.ide_configs.items(), 1):
                self.progress_updated.emit(get_text("patch.batch_processing",
                                                  ide_type=ide_type.value, current=i, total=total_ides))

                patch_mode = config.get('patch_mode', PatchMode.RANDOM)
                portable_root = config.get('portable_root')

                # 查找扩展文件
                extension_files = self.extension_finder.find_extension_files(ide_type, portable_root)

                if not extension_files:
                    message = get_text("patch.batch_no_files")
                    results[ide_type.value] = {'success': False, 'message': message, 'files': []}
                    self.ide_completed.emit(ide_type.value, False, message)
                    overall_success = False
                    continue

                # 应用补丁
                success_count = 0
                file_results = []

                for file_path in extension_files:
                    result = self.patch_manager.apply_patch(file_path, patch_mode)
                    file_results.append({
                        'path': file_path,
                        'success': result.success,
                        'message': result.message
                    })
                    if result.success:
                        success_count += 1

                # 记录结果
                ide_success = success_count > 0
                message = get_text("patch.batch_success", success=success_count, total=len(extension_files))
                results[ide_type.value] = {
                    'success': ide_success,
                    'message': message,
                    'files': file_results
                }

                self.ide_completed.emit(ide_type.value, ide_success, message)
                if not ide_success:
                    overall_success = False

            # 完成总结
            if overall_success:
                final_message = get_text("patch.batch_completed", count=total_ides)
            else:
                final_message = get_text("patch.batch_partial")

            self.progress_updated.emit(f"🎉 {final_message}")
            self.batch_completed.emit(overall_success, final_message, results)

        except Exception as e:
            error_msg = get_text("patch.batch_error", error=str(e))
            self.progress_updated.emit(f"❌ {error_msg}")
            self.batch_completed.emit(False, error_msg, {})
