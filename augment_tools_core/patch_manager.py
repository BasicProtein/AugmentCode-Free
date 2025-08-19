#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码补丁管理器
移植并增强aug_cleaner的核心功能，支持多IDE的扩展文件补丁
"""

import re
import os
import stat
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Handle imports properly for both direct execution and module usage
try:
    from .common_utils import print_info, print_success, print_error, print_warning, IDEType
except ImportError:
    # Fallback for direct execution
    try:
        from augment_tools_core.common_utils import print_info, print_success, print_error, print_warning, IDEType
    except ImportError:
        # Minimal fallback implementations for direct testing
        def print_info(msg): print(f"[INFO] {msg}")
        def print_success(msg): print(f"[SUCCESS] {msg}")
        def print_error(msg): print(f"[ERROR] {msg}")
        def print_warning(msg): print(f"[WARNING] {msg}")
        
        # Mock IDEType for testing
        class IDEType(Enum):
            VSCODE = "vscode"
            CURSOR = "cursor"
            WINDSURF = "windsurf"
            JETBRAINS = "jetbrains"

# 导入语言管理器，但要处理可能的导入错误（优先相对导入，再尝试绝对导入）
try:
    from .language_manager import get_text
    LANGUAGE_SUPPORT = True
except Exception:
    try:
        from language_manager import get_text
        LANGUAGE_SUPPORT = True
    except Exception:
        # 如果都失败，保持 LANGUAGE_SUPPORT = False，并提供一个支持关键字格式化的回退实现
        LANGUAGE_SUPPORT = False
        def get_text(key_path: str, **kwargs):
            if kwargs:
                try:
                    return key_path.format(**kwargs)
                except Exception:
                    return key_path
            return key_path

# Local English fallback texts used when language support is unavailable
FALLBACK_TEXTS = {
    "patch.status.file_not_found": "file not found",
    "patch.status.patched": "patched",
    "patch.status.not_patched": "not patched",
    "patch.status.status_unknown": "status unknown",
}


class PatchMode(Enum):
    """补丁模式枚举"""
    BLOCK = "block"
    RANDOM = "random" 
    EMPTY = "empty"
    STEALTH = "stealth"
    DEBUG = "debug"


class PatchResult:
    """补丁操作结果"""
    def __init__(self, success: bool = False, message: str = "", file_path: str = "", backup_path: str = ""):
        self.success = success
        self.message = message
        self.file_path = file_path
        self.backup_path = backup_path


class PatchManager:
    """代码补丁管理器"""
    
    def __init__(self):
        # 补丁代码模板
        self.patches = {
            PatchMode.BLOCK: 'if (typeof s === "string" && (s.startsWith("report-") || s.startsWith("record-"))) { return { success: true }; }',
            
            PatchMode.RANDOM: 'if (typeof s === "string" && (s.startsWith("report-") || s.startsWith("record-"))) { i = { timestamp: Date.now(), version: Math.random().toString(36).substring(2, 8) }; }',
            
            PatchMode.EMPTY: 'if (typeof s === "string" && (s.startsWith("report-") || s.startsWith("record-"))) { i = {}; }',
            
            PatchMode.STEALTH: 'if (typeof s === "string" && (s.startsWith("report-") || s.startsWith("record-"))) { i = { timestamp: Date.now(), session: Math.random().toString(36).substring(2, 10), events: [] }; }',
            
            PatchMode.DEBUG: 'if (typeof s === "string" && (s.startsWith("report-") || s.startsWith("record-"))) { i = { timestamp: Date.now(), version: Math.random().toString(36).substring(2, 8) }; } if (typeof s === "string" && s === "subscription-info") { return { success: true, subscription: { Enterprise: {}, ActiveSubscription: { end_date: "2026-12-31", usage_balance_depleted: false } } }; } this.maxUploadSizeBytes = 999999999; this.maxTrackableFileCount = 999999; this.completionTimeoutMs = 999999; this.diffBudget = 999999; this.messageBudget = 999999; this.enableDebugFeatures = true;'
        }
        
        # 补丁签名，用于检测是否已补丁
        self.patch_signatures = [
            'startsWith("report-")',
            'startsWith("record-")', 
            'randSessionId',
            'this._userAgent = ""'
        ]
    
    def get_patch_description(self, mode: PatchMode) -> str:
        """获取补丁模式描述"""
        descriptions = {
            PatchMode.BLOCK: "完全遥测阻止 - 不发送任何数据",
            PatchMode.RANDOM: "随机假数据 - 服务器收到无意义数据", 
            PatchMode.EMPTY: "空数据模式 - 发送最小载荷",
            PatchMode.STEALTH: "隐身模式 - 发送逼真但假的遥测数据",
            PatchMode.DEBUG: "调试模式 - 假订阅 + 无限制 + 增强功能"
        }
        return descriptions.get(mode, "未知模式")
    
    def _ensure_write_permissions(self, file_path: str) -> bool:
        """确保文件有写权限"""
        try:
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                # 只保留权限位，去掉文件类型等其他位
                current_perms = stat.S_IMODE(file_path_obj.stat().st_mode)

                # 平台检测：Windows 使用 stat.S_IWRITE，POSIX 使用 stat.S_IWUSR
                if os.name == 'nt' or platform.system().lower().startswith('win'):
                    write_flag = getattr(stat, 'S_IWRITE', None)
                else:
                    write_flag = getattr(stat, 'S_IWUSR', None)

                # 如果无法获取适用的写标志，直接返回 True（无法修改权限）
                if write_flag is None:
                    return True

                # 检查是否已有写权限
                if not (current_perms & write_flag):
                    new_perms = current_perms | write_flag
                    try:
                        # 只修改权限位
                        file_path_obj.chmod(new_perms)
                        print_info(f"已为文件添加写权限: {file_path}")
                    except Exception:
                        # 有的平台可能需要使用 os.chmod
                        try:
                            os.chmod(str(file_path_obj), new_perms)
                            print_info(f"已为文件添加写权限: {file_path}")
                        except Exception as e:
                            print_warning(f"修改文件权限失败: {e}")
                            return False
            return True
        except Exception as e:
            print_warning(f"修改文件权限失败: {e}")
            return False
    
    def _generate_session_randomizer(self) -> str:
        """生成会话随机化代码"""
        return ' const chars = "0123456789abcdef"; let randSessionId = ""; for (let i = 0; i < 36; i++) { randSessionId += i === 8 || i === 13 || i === 18 || i === 23 ? "-" : i === 14 ? "4" : i === 19 ? chars[8 + Math.floor(4 * Math.random())] : chars[Math.floor(16 * Math.random())]; } this.sessionId = randSessionId; this._userAgent = "";'
    
    def _create_backup(self, file_path: str) -> Tuple[bool, str]:
        """创建文件备份"""
        try:
            file_path_obj = Path(file_path)
            # 正确生成备份文件名
            backup_path = file_path_obj.with_name(f'{file_path_obj.stem}_ori{file_path_obj.suffix}')
            
            if backup_path.exists():
                print_warning(f"备份文件已存在: {backup_path}")
                return True, str(backup_path)
            
            shutil.copy2(file_path, backup_path)
            print_success(f"备份创建成功: {backup_path}")
            return True, str(backup_path)
            
        except Exception as e:
            print_error(f"创建备份失败: {e}")
            return False, ""
    
    def _is_already_patched(self, content: str) -> bool:
        """检查文件是否已被补丁"""
        return any(sig in content for sig in self.patch_signatures)
    
    def _find_callapi_function(self, content: str) -> Optional[re.Match]:
        """查找async callApi函数"""
        pattern = r'(async\s+callApi\s*\([^)]*\)\s*\{)'
        return re.search(pattern, content)
    
    def apply_patch(self, file_path: str, patch_mode: PatchMode) -> PatchResult:
        """应用补丁到指定文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return PatchResult(False, f"文件不存在: {file_path}")
            
            print_info(f"开始补丁文件: {file_path}")
            print_info(f"补丁模式: {patch_mode.value} - {self.get_patch_description(patch_mode)}")
            
            # 读取文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                return PatchResult(False, f"读取文件失败: {e}")
            
            # 检查是否已被补丁
            if self._is_already_patched(content):
                return PatchResult(False, "文件已被补丁，跳过操作")
            
            # 查找callApi函数
            match = self._find_callapi_function(content)
            if not match:
                return PatchResult(False, "未找到async callApi函数")
            
            # 确保文件有写权限
            if not self._ensure_write_permissions(file_path):
                return PatchResult(False, "无法获取文件写权限")
            
            # 创建备份
            backup_success, backup_path = self._create_backup(file_path)
            if not backup_success:
                return PatchResult(False, "创建备份失败")
            
            # 生成完整补丁代码
            patch_code = self.patches[patch_mode] + self._generate_session_randomizer()
            
            # 应用补丁
            func_start = match.end()
            patched_content = content[:func_start] + patch_code + content[func_start:]
            
            # 写入补丁后的内容
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(patched_content)
                
                print_success(f"补丁应用成功: {file_path}")
                print_info(f"效果: {self.get_patch_description(patch_mode)}")
                print_info("隐私保护已启用!")
                
                return PatchResult(True, "补丁应用成功", file_path, backup_path)
                
            except Exception as e:
                # 尝试从备份恢复
                try:
                    # 确保恢复目标（file_path）具有写权限，以便可以将备份文件复制回去
                    self._ensure_write_permissions(file_path)
                    shutil.copy2(backup_path, file_path)
                    print_warning("已从备份恢复原始文件")
                except:
                    print_error("恢复原始文件失败!")
                
                return PatchResult(False, f"写入补丁文件失败: {e}")
                
        except Exception as e:
            return PatchResult(False, f"补丁操作失败: {e}")
    
    def restore_from_backup(self, file_path: str) -> PatchResult:
        """从备份恢复原始文件"""
        try:
            file_path_obj = Path(file_path)
            backup_path = file_path_obj.with_name(f'{file_path_obj.stem}_ori{file_path_obj.suffix}')
            
            if not backup_path.exists():
                return PatchResult(False, f"备份文件不存在: {backup_path}")
            
            # 确保恢复目标（file_path）具有写权限，以便可以将备份文件复制回去
            if not self._ensure_write_permissions(file_path):
                return PatchResult(False, "无法获取文件写权限")
            
            shutil.copy2(backup_path, file_path)
            print_success(f"已从备份恢复: {file_path}")
            
            return PatchResult(True, "恢复成功", file_path, str(backup_path))
            
        except Exception as e:
            return PatchResult(False, f"恢复失败: {e}")
    
    def get_patch_status(self, file_path: str) -> str:
        """获取文件的补丁状态"""
        try:
            if not os.path.exists(file_path):
                return get_text("patch.status.file_not_found") if LANGUAGE_SUPPORT else FALLBACK_TEXTS.get("patch.status.file_not_found", "file not found")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if self._is_already_patched(content):
                return get_text("patch.status.patched") if LANGUAGE_SUPPORT else FALLBACK_TEXTS.get("patch.status.patched", "patched")
            else:
                return get_text("patch.status.not_patched") if LANGUAGE_SUPPORT else FALLBACK_TEXTS.get("patch.status.not_patched", "not patched")

        except Exception:
            return get_text("patch.status.status_unknown") if LANGUAGE_SUPPORT else FALLBACK_TEXTS.get("patch.status.status_unknown", "status unknown")