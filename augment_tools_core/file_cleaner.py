"""
文件清理模块 - 安全删除和强制删除功能
基于clean.js的文件删除功能，适配Python环境
"""
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict
from .common_utils import IDEType, get_ide_paths, print_info, print_success, print_warning, print_error
from .process_manager import ProcessManager

class FileCleaner:
    """文件清理器 - 安全删除和强制删除文件"""
    
    # 目标文件名
    TARGET_FILES = ['state.vscdb', 'state.vscdb.backup']
    
    def __init__(self):
        self.process_manager = ProcessManager()
    
    def clean_ide_files(self, ide_type: IDEType, force_mode: bool = False) -> Dict[str, int]:
        """
        清理指定IDE的状态文件
        
        Args:
            ide_type: IDE类型
            force_mode: 是否启用强制模式
            
        Returns:
            Dict[str, int]: 清理结果统计
        """
        print_info(f"开始清理 {ide_type.value} 状态文件...")
        
        paths = get_ide_paths(ide_type)
        if not paths:
            print_error(f"无法获取 {ide_type.value} 路径")
            return {"globalStorage": 0, "workspaceStorage": 0}
        
        results = {
            "globalStorage": 0,
            "workspaceStorage": 0
        }
        
        # 清理globalStorage
        global_storage_path = None
        if "state_db" in paths:
            global_storage_path = paths["state_db"].parent
            results["globalStorage"] = self._clean_global_storage(global_storage_path, force_mode)

        # 清理workspaceStorage
        if global_storage_path:
            workspace_storage_path = global_storage_path.parent / "workspaceStorage"
            if workspace_storage_path.exists():
                results["workspaceStorage"] = self._clean_workspace_storage(workspace_storage_path, force_mode)
        
        return results
    
    def _clean_global_storage(self, global_storage_path: Path, force_mode: bool) -> int:
        """清理globalStorage目录"""
        print_info("清理 globalStorage...")
        
        if not global_storage_path.exists():
            print_error(f"globalStorage 目录不存在: {global_storage_path}")
            return 0
        
        deleted_count = 0
        for file_name in self.TARGET_FILES:
            file_path = global_storage_path / file_name
            if self.safe_delete_file(file_path, force_mode):
                deleted_count += 1
        
        print_success(f"globalStorage 清理完成，删除了 {deleted_count} 个文件")
        return deleted_count
    
    def _clean_workspace_storage(self, workspace_storage_path: Path, force_mode: bool) -> int:
        """清理workspaceStorage目录"""
        print_info("清理 workspaceStorage...")
        
        if not workspace_storage_path.exists():
            print_error(f"workspaceStorage 目录不存在: {workspace_storage_path}")
            return 0
        
        total_deleted = 0
        workspaces_processed = 0
        
        try:
            # 遍历所有工作区目录
            for workspace_dir in workspace_storage_path.iterdir():
                if workspace_dir.is_dir():
                    print_info(f"检查工作区: {workspace_dir.name}")
                    
                    deleted_in_workspace = 0
                    for file_name in self.TARGET_FILES:
                        file_path = workspace_dir / file_name
                        if self.safe_delete_file(file_path, force_mode):
                            deleted_in_workspace += 1
                            total_deleted += 1
                    
                    if deleted_in_workspace > 0:
                        workspaces_processed += 1
        
        except Exception as e:
            print_error(f"读取 workspaceStorage 目录失败: {e}")
            return 0
        
        print_success(f"workspaceStorage 清理完成:")
        print_info(f"  - 处理了 {workspaces_processed} 个工作区")
        print_info(f"  - 删除了 {total_deleted} 个文件")
        return total_deleted
    
    def safe_delete_file(self, file_path: Path, force_mode: bool = False) -> bool:
        """
        安全删除文件（带重试机制）
        
        Args:
            file_path: 文件路径
            force_mode: 是否启用强制模式
            
        Returns:
            bool: 是否成功删除
        """
        if not file_path.exists():
            return False
        
        print_info(f"尝试删除: {file_path}")
        
        # 第一步：尝试正常删除
        try:
            file_path.unlink()
            print_success(f"已删除: {file_path}")
            return True
        except (PermissionError, OSError) as e:
            if e.errno in [13, 32]:  # EACCES, EBUSY
                print_warning(f"删除失败: {file_path}")
                print_warning(f"错误: {e}")
                
                if force_mode:
                    print_info("启用强制模式，等待后重试...")
                    return self._force_delete_file(file_path)
                else:
                    print_info("可以尝试使用强制模式")
                    return False
            else:
                print_error(f"删除失败: {file_path} - {e}")
                return False
        except Exception as e:
            print_error(f"删除失败: {file_path} - {e}")
            return False
    
    def _force_delete_file(self, file_path: Path) -> bool:
        """强制删除文件（多种方法）"""
        # 等待一下，让可能的文件锁释放
        time.sleep(1)
        
        # 第二步：再次尝试正常删除
        try:
            file_path.unlink()
            print_success(f"延迟删除成功: {file_path}")
            return True
        except Exception:
            pass
        
        print_info("正常删除仍然失败，尝试查找并终止占用进程...")
        
        # 第三步：查找并终止占用文件的进程
        if os.name == 'nt':  # Windows
            occupying_processes = self.process_manager.find_processes_using_file(file_path)
            if occupying_processes:
                print_info(f"找到 {len(occupying_processes)} 个占用文件的进程")
                for proc in occupying_processes:
                    print_info(f"  {proc}")
                
                # 终止占用进程
                self._kill_occupying_processes(occupying_processes)
                time.sleep(2)
                
                # 再次尝试删除
                try:
                    file_path.unlink()
                    print_success(f"终止占用进程后删除成功: {file_path}")
                    return True
                except Exception:
                    pass
        
        # 第四步：使用系统命令强制删除
        if os.name == 'nt':  # Windows
            return self._windows_force_delete(file_path)
        else:
            return self._unix_force_delete(file_path)
    
    def _kill_occupying_processes(self, processes: List) -> None:
        """终止占用文件的进程"""
        for proc in processes:
            try:
                if os.name == 'nt':
                    subprocess.run(f'taskkill /F /PID {proc.pid}', shell=True, check=False, capture_output=True)
                else:
                    subprocess.run(['kill', '-KILL', proc.pid], check=False)
                print_info(f"已终止占用进程 PID: {proc.pid}")
            except Exception as e:
                print_warning(f"无法终止进程 {proc.pid}: {e}")
    
    def _windows_force_delete(self, file_path: Path) -> bool:
        """Windows强制删除方法"""
        methods = [
            {
                "name": "del命令",
                "command": f'del /F /Q "{file_path}"'
            },
            {
                "name": "PowerShell Remove-Item",
                "command": f'powershell -Command "Remove-Item -Path \'{file_path}\' -Force -ErrorAction SilentlyContinue"'
            },
            {
                "name": "attrib + del",
                "command": f'attrib -R -S -H "{file_path}" && del /F /Q "{file_path}"'
            }
        ]
        
        for method in methods:
            try:
                print_info(f"尝试使用 {method['name']} 删除文件...")
                subprocess.run(method["command"], shell=True, check=False, capture_output=True)
                
                # 检查文件是否真的被删除了
                if not file_path.exists():
                    print_success(f"使用 {method['name']} 强制删除成功: {file_path}")
                    return True
            except Exception as e:
                print_warning(f"{method['name']} 失败: {e}")
        
        # 最后的尝试：等待更长时间后再试
        print_info("等待5秒后最后一次尝试...")
        time.sleep(5)
        
        try:
            file_path.unlink()
            print_success(f"最终删除成功: {file_path}")
            return True
        except Exception as e:
            print_error(f"最终删除失败: {file_path}")
            print_error(f"最终错误: {e}")
            print_info("文件可能被系统进程锁定，建议重启后再试")
            return False
    
    def _unix_force_delete(self, file_path: Path) -> bool:
        """Unix系统强制删除方法"""
        try:
            # 尝试修改权限后删除
            os.chmod(file_path, 0o777)
            file_path.unlink()
            print_success(f"强制删除成功: {file_path}")
            return True
        except Exception as e:
            print_error(f"强制删除失败: {file_path} - {e}")
            return False
