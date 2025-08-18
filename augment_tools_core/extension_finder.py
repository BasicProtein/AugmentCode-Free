#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩展文件查找器
自动查找不同IDE的AugmentCode扩展文件，支持多版本和便携版
"""

import os
import glob
from pathlib import Path
from typing import List, Dict, Optional
import platform

from .common_utils import IDEType, print_info, print_warning, print_error, print_success


class ExtensionFinder:
    """扩展文件查找器"""
    
    def __init__(self):
        self.system = platform.system().lower()
        
        # 扩展文件路径模式
        self.extension_patterns = {
            IDEType.VSCODE: {
                "windows": [
                    os.path.expanduser("~/.vscode/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/AppData/Roaming/Code/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.vscode/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/AppData/Roaming/Code/User/extensions/augment.*/out/extension.js"),
                ],
                "linux": [
                    os.path.expanduser("~/.vscode/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.config/Code/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.vscode/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/.config/Code/User/extensions/augment.*/out/extension.js"),
                ],
                "darwin": [
                    os.path.expanduser("~/.vscode/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/Library/Application Support/Code/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.vscode/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/Library/Application Support/Code/User/extensions/augment.*/out/extension.js"),
                ]
            },
            IDEType.CURSOR: {
                "windows": [
                    # cursor 可能使用 vscode-augment 扩展名称
                    os.path.expanduser("~/.cursor/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/AppData/Roaming/Cursor/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    # 原有的 cursor-augment 模式
                    os.path.expanduser("~/.cursor/extensions/augment.cursor-augment-*/out/extension.js"),
                    os.path.expanduser("~/AppData/Roaming/Cursor/User/extensions/augment.cursor-augment-*/out/extension.js"),
                    # 通用 augment 模式
                    os.path.expanduser("~/.cursor/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/AppData/Roaming/Cursor/User/extensions/augment.*/out/extension.js"),
                    # 额外的可能路径
                    os.path.expanduser("~/AppData/Local/Programs/cursor/resources/app/extensions/augment.*/out/extension.js"),
                ],
                "linux": [
                    os.path.expanduser("~/.cursor/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.config/Cursor/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.cursor/extensions/augment.cursor-augment-*/out/extension.js"),
                    os.path.expanduser("~/.config/Cursor/User/extensions/augment.cursor-augment-*/out/extension.js"),
                    os.path.expanduser("~/.cursor/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/.config/Cursor/User/extensions/augment.*/out/extension.js"),
                ],
                "darwin": [
                    os.path.expanduser("~/.cursor/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/Library/Application Support/Cursor/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.cursor/extensions/augment.cursor-augment-*/out/extension.js"),
                    os.path.expanduser("~/Library/Application Support/Cursor/User/extensions/augment.cursor-augment-*/out/extension.js"),
                    os.path.expanduser("~/.cursor/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/Library/Application Support/Cursor/User/extensions/augment.*/out/extension.js"),
                ]
            },
            IDEType.WINDSURF: {
                "windows": [
                    # windsurf 可能使用 vscode-augment 扩展名称
                    os.path.expanduser("~/.windsurf/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/AppData/Roaming/Windsurf/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    # 原有的 windsurf-augment 模式
                    os.path.expanduser("~/.windsurf/extensions/augment.windsurf-augment-*/out/extension.js"),
                    os.path.expanduser("~/AppData/Roaming/Windsurf/User/extensions/augment.windsurf-augment-*/out/extension.js"),
                    # 通用 augment 模式
                    os.path.expanduser("~/.windsurf/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/AppData/Roaming/Windsurf/User/extensions/augment.*/out/extension.js"),
                    # 额外的可能路径
                    os.path.expanduser("~/AppData/Local/Programs/windsurf/resources/app/extensions/augment.*/out/extension.js"),
                ],
                "linux": [
                    os.path.expanduser("~/.windsurf/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.config/Windsurf/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.windsurf/extensions/augment.windsurf-augment-*/out/extension.js"),
                    os.path.expanduser("~/.config/Windsurf/User/extensions/augment.windsurf-augment-*/out/extension.js"),
                    os.path.expanduser("~/.windsurf/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/.config/Windsurf/User/extensions/augment.*/out/extension.js"),
                ],
                "darwin": [
                    os.path.expanduser("~/.windsurf/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/Library/Application Support/Windsurf/User/extensions/augment.vscode-augment-*/out/extension.js"),
                    os.path.expanduser("~/.windsurf/extensions/augment.windsurf-augment-*/out/extension.js"),
                    os.path.expanduser("~/Library/Application Support/Windsurf/User/extensions/augment.windsurf-augment-*/out/extension.js"),
                    os.path.expanduser("~/.windsurf/extensions/augment.*/out/extension.js"),
                    os.path.expanduser("~/Library/Application Support/Windsurf/User/extensions/augment.*/out/extension.js"),
                ]
            }
        }
        
        # 通用扩展名模式（用于模糊匹配）
        self.generic_patterns = [
            "*augment*extension.js",
            "*augment*/out/extension.js", 
            "*augment*/dist/extension.js",
            "*augment*/build/extension.js"
        ]
    
    def find_extension_files(self, ide_type: IDEType, portable_root: Optional[str] = None) -> List[str]:
        """查找指定IDE的扩展文件 - 增强搜索策略"""
        found_files = []

        print_info(f"开始查找 {ide_type.value} 扩展文件...")

        # 如果指定了便携版根目录
        if portable_root:
            print_info("正在搜索便携版扩展...")
            portable_files = self._find_portable_extensions(ide_type, portable_root)
            found_files.extend(portable_files)

        # 查找标准安装位置
        print_info("正在搜索标准安装位置...")
        standard_files = self._find_standard_extensions(ide_type)
        found_files.extend(standard_files)

        # 去重并验证文件
        unique_files = list(set(found_files))
        print_info(f"去重后找到 {len(unique_files)} 个文件，开始验证...")

        valid_files = []
        for file in unique_files:
            if os.path.exists(file):
                if self._is_valid_extension_file(file):
                    valid_files.append(file)
                    print_success(f"✅ 验证通过: {file}")
                else:
                    print_warning(f"⚠️ 验证失败: {file} (不是有效的扩展文件)")
            else:
                print_warning(f"⚠️ 文件不存在: {file}")

        # 如果标准搜索没有找到有效文件，启用关键词搜索
        if not valid_files:
            print_warning(f"标准搜索未找到有效的 {ide_type.value} 扩展文件，启用关键词搜索...")
            keyword_files = self.search_by_keyword("augment")

            # 过滤出与当前IDE相关的文件
            ide_keyword_files = []
            for file in keyword_files:
                file_lower = file.lower()
                if (ide_type == IDEType.CURSOR and ("cursor" in file_lower or "vscode" in file_lower)) or \
                   (ide_type == IDEType.VSCODE and "vscode" in file_lower) or \
                   (ide_type == IDEType.WINDSURF and "windsurf" in file_lower):
                    ide_keyword_files.append(file)

            valid_files.extend(ide_keyword_files)
            valid_files = list(set(valid_files))  # 再次去重

        if valid_files:
            print_success(f"✅ 找到 {len(valid_files)} 个 {ide_type.value} 扩展文件:")
            for file in valid_files:
                print_info(f"  - {file}")
        else:
            print_warning(f"❌ 未找到 {ide_type.value} 的扩展文件")
            print_info("建议检查:")
            print_info("  1. 是否已安装 Augment 扩展")
            print_info("  2. 扩展是否在预期的安装位置")
            print_info("  3. 是否使用了便携版安装")

        return valid_files
    
    def _find_standard_extensions(self, ide_type: IDEType) -> List[str]:
        """查找标准安装位置的扩展文件 - 增强调试信息"""
        found_files = []

        if ide_type not in self.extension_patterns:
            print_warning(f"不支持的IDE类型: {ide_type}")
            return found_files

        patterns = self.extension_patterns[ide_type].get(self.system, [])
        print_info(f"正在搜索 {ide_type.value} 扩展文件，系统: {self.system}")
        print_info(f"搜索模式数量: {len(patterns)}")

        for i, pattern in enumerate(patterns, 1):
            try:
                print_info(f"  [{i}/{len(patterns)}] 搜索: {pattern}")
                matches = glob.glob(pattern)
                if matches:
                    print_success(f"    ✅ 找到 {len(matches)} 个匹配文件")
                    for match in matches:
                        print_info(f"      - {match}")
                    found_files.extend(matches)
                else:
                    print_info(f"    ❌ 未找到匹配文件")
            except Exception as e:
                print_warning(f"    ⚠️ 搜索模式失败 {pattern}: {e}")

        if not found_files:
            print_warning(f"所有搜索模式都未找到 {ide_type.value} 扩展文件")
            print_info("建议检查以下位置是否存在扩展文件:")
            for pattern in patterns:
                # 移除通配符，显示基础目录
                base_dir = pattern.replace("/*", "").replace("*", "")
                if os.path.exists(os.path.dirname(base_dir)):
                    print_info(f"  - {os.path.dirname(base_dir)} (目录存在)")
                else:
                    print_info(f"  - {os.path.dirname(base_dir)} (目录不存在)")

        return found_files
    
    def _find_portable_extensions(self, ide_type: IDEType, portable_root: str) -> List[str]:
        """查找便携版扩展文件"""
        found_files = []
        
        try:
            portable_path = Path(portable_root)
            if not portable_path.exists():
                print_warning(f"便携版路径不存在: {portable_root}")
                return found_files
            
            # 在便携版目录中搜索扩展文件
            search_patterns = [
                "extensions/augment*/out/extension.js",
                "data/extensions/augment*/out/extension.js",
                "user-data/extensions/augment*/out/extension.js",
                "resources/app/extensions/augment*/out/extension.js"
            ]
            
            for pattern in search_patterns:
                search_path = portable_path / pattern
                matches = glob.glob(str(search_path))
                found_files.extend(matches)
            
            # 递归搜索（限制深度）
            for root, dirs, files in os.walk(portable_root):
                # 限制搜索深度
                level = root.replace(portable_root, '').count(os.sep)
                if level >= 4:
                    dirs[:] = []  # 不再深入
                    continue
                
                for file in files:
                    if file == "extension.js" and "augment" in root.lower():
                        full_path = os.path.join(root, file)
                        found_files.append(full_path)
        
        except Exception as e:
            print_error(f"搜索便携版扩展失败: {e}")
        
        return found_files
    
    def _is_valid_extension_file(self, file_path: str) -> bool:
        """验证是否为有效的扩展文件 - 支持压缩文件"""
        try:
            # 首先检查文件路径是否包含 augment 关键词
            if "augment" in file_path.lower():
                print_info(f"    文件路径包含 'augment'，认为是有效扩展文件")
                return True

            # 读取文件内容进行更深入的检查
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(5000)  # 读取更多内容以便在压缩代码中查找

            # 检查是否包含关键标识（包括压缩后可能的形式）
            indicators = [
                "callapi",  # 可能被压缩为小写
                "callApi",  # 原始形式
                "augment",
                "extension",
                "vscode",
                "activate",
                # 添加一些压缩后可能保留的模式
                "async",
                "function",
                "exports"
            ]

            found_indicators = []
            content_lower = content.lower()
            for indicator in indicators:
                if indicator.lower() in content_lower:
                    found_indicators.append(indicator)

            if found_indicators:
                print_info(f"    文件验证通过，找到标识: {found_indicators}")
                return True
            else:
                # 对于 extension.js 文件，如果在 augment 相关目录中，也认为是有效的
                if file_path.endswith("extension.js") and "augment" in file_path.lower():
                    print_info(f"    文件是 extension.js 且在 augment 目录中，认为有效")
                    return True

                print_warning(f"    文件验证失败，未找到任何标识。文件开头内容: {content[:200]}...")
                return False

        except Exception as e:
            print_warning(f"    文件验证异常: {e}")
            return False
    
    def find_all_extensions(self, portable_roots: Optional[Dict[IDEType, str]] = None) -> Dict[IDEType, List[str]]:
        """查找所有支持的IDE的扩展文件"""
        results = {}
        
        for ide_type in [IDEType.VSCODE, IDEType.CURSOR, IDEType.WINDSURF]:
            portable_root = None
            if portable_roots and ide_type in portable_roots:
                portable_root = portable_roots[ide_type]
            
            files = self.find_extension_files(ide_type, portable_root)
            if files:
                results[ide_type] = files
        
        return results
    
    def get_latest_extension(self, ide_type: IDEType, portable_root: Optional[str] = None) -> Optional[str]:
        """获取最新版本的扩展文件"""
        files = self.find_extension_files(ide_type, portable_root)
        
        if not files:
            return None
        
        # 按修改时间排序，返回最新的
        try:
            latest_file = max(files, key=lambda f: os.path.getmtime(f))
            return latest_file
        except Exception:
            # 如果获取修改时间失败，返回第一个
            return files[0]
    
    def search_by_keyword(self, keyword: str = "augment", search_paths: Optional[List[str]] = None) -> List[str]:
        """通过关键词搜索扩展文件 - 增强搜索能力"""
        found_files = []

        if not search_paths:
            # 扩展默认搜索路径，参考参考项目的路径结构
            search_paths = [
                os.path.expanduser("~/.vscode"),
                os.path.expanduser("~/.cursor"),
                os.path.expanduser("~/.windsurf"),
                os.path.expanduser("~/AppData/Roaming") if self.system == "windows" else "",
                os.path.expanduser("~/AppData/Local/Programs") if self.system == "windows" else "",
                os.path.expanduser("~/.config") if self.system == "linux" else "",
                os.path.expanduser("~/Library/Application Support") if self.system == "darwin" else "",
                # 添加更多可能的安装位置
                "C:/Users/" + os.environ.get("USERNAME", "") + "/AppData/Roaming" if self.system == "windows" else "",
                "C:/Users/" + os.environ.get("USERNAME", "") + "/AppData/Local/Programs" if self.system == "windows" else "",
            ]
            search_paths = [p for p in search_paths if p and os.path.exists(p)]

        print_info(f"开始关键词搜索: '{keyword}'")
        print_info(f"搜索路径数量: {len(search_paths)}")

        for i, search_path in enumerate(search_paths, 1):
            try:
                print_info(f"  [{i}/{len(search_paths)}] 搜索路径: {search_path}")
                path_found_count = 0

                for root, dirs, files in os.walk(search_path):
                    # 限制搜索深度
                    level = root.replace(search_path, '').count(os.sep)
                    if level >= 6:  # 增加搜索深度
                        dirs[:] = []
                        continue

                    # 检查目录名是否包含关键词
                    if keyword.lower() in root.lower():
                        for file in files:
                            if file == "extension.js":
                                full_path = os.path.join(root, file)
                                if self._is_valid_extension_file(full_path):
                                    found_files.append(full_path)
                                    path_found_count += 1
                                    print_success(f"    ✅ 找到: {full_path}")

                if path_found_count == 0:
                    print_info(f"    ❌ 在此路径未找到匹配文件")
                else:
                    print_success(f"    ✅ 在此路径找到 {path_found_count} 个文件")

            except Exception as e:
                print_warning(f"    ⚠️ 搜索路径失败 {search_path}: {e}")

        unique_files = list(set(found_files))  # 去重
        print_info(f"关键词搜索完成，共找到 {len(unique_files)} 个唯一文件")
        return unique_files
