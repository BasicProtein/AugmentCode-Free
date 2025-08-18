"""
进程管理模块 - 检测和管理IDE进程
基于clean.js的进程管理功能，适配Python环境
"""
import subprocess
import platform
import time
import logging
from typing import List, Dict, Optional, Union
from pathlib import Path
from .common_utils import IDEType, print_info, print_success, print_warning, print_error

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProcessInfo:
    """进程信息类"""
    def __init__(self, name: str, pid: str, memory: str = "N/A", command_line: str = ""):
        self.name = name
        self.pid = pid
        self.memory = memory
        self.command_line = command_line
    
    def __str__(self):
        return f"PID: {self.pid}, 名称: {self.name}, 内存: {self.memory}"

class ProcessManager:
    """进程管理器 - 检测和管理IDE进程"""
    
    # IDE进程名称映射
    IDE_PROCESS_NAMES = {
        IDEType.VSCODE: [
            'Code.exe', 'Code - Insiders.exe', 'Code - OSS.exe', 'VSCode.exe'
        ],
        IDEType.CURSOR: [
            'Cursor.exe', 'cursor.exe'
        ],
        IDEType.WINDSURF: [
            'Windsurf.exe', 'windsurf.exe'
        ],
        IDEType.JETBRAINS: [
            'idea64.exe', 'idea.exe', 'pycharm64.exe', 'pycharm.exe',
            'webstorm64.exe', 'webstorm.exe', 'phpstorm64.exe', 'phpstorm.exe',
            'clion64.exe', 'clion.exe', 'rider64.exe', 'rider.exe'
        ]
    }
    
    def __init__(self):
        self.system = platform.system()
    
    def check_ide_processes(self, ide_type: IDEType) -> bool:
        """
        检查指定IDE的进程是否在运行
        
        Args:
            ide_type: IDE类型
            
        Returns:
            bool: 是否有进程在运行
        """
        processes = self.get_ide_processes(ide_type)
        return len(processes) > 0
    
    def get_ide_processes(self, ide_type: IDEType) -> List[ProcessInfo]:
        """
        获取指定IDE的所有进程信息
        
        Args:
            ide_type: IDE类型
            
        Returns:
            List[ProcessInfo]: 进程信息列表
        """
        process_names = self.IDE_PROCESS_NAMES.get(ide_type, [])
        all_processes = []
        
        for process_name in process_names:
            processes = self._get_processes_by_name(process_name)
            all_processes.extend(processes)
        
        # 额外查找基于命令行的进程（适用于Electron应用）
        if ide_type in [IDEType.VSCODE, IDEType.CURSOR]:
            electron_processes = self._get_electron_processes(ide_type)
            all_processes.extend(electron_processes)
        
        # 去重（基于PID）
        unique_processes = {}
        for proc in all_processes:
            if proc.pid not in unique_processes:
                unique_processes[proc.pid] = proc
        
        return list(unique_processes.values())
    
    def _get_processes_by_name(self, process_name: str) -> List[ProcessInfo]:
        """根据进程名获取进程信息"""
        processes = []
        
        try:
            if self.system == "Windows":
                # 使用tasklist命令
                cmd = f'tasklist /FI "IMAGENAME eq {process_name}" /FO CSV'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk', errors='ignore')
                
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[1:]:  # 跳过标题行
                        if line.strip() and process_name.lower() in line.lower():
                            parts = [part.strip('"') for part in line.split('","')]
                            if len(parts) >= 5:
                                processes.append(ProcessInfo(
                                    name=parts[0],
                                    pid=parts[1],
                                    memory=parts[4]
                                ))
            else:
                # Linux/macOS使用ps命令
                search_pattern = process_name.replace('.exe', '')
                cmd = f'ps aux | grep -i "{search_pattern}" | grep -v grep'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            parts = line.split()
                            if len(parts) >= 11:
                                processes.append(ProcessInfo(
                                    name=search_pattern,
                                    pid=parts[1],
                                    memory=f"{parts[5]}KB"
                                ))
        
        except Exception as e:
            print_warning(f"获取进程 {process_name} 信息失败: {e}")
        
        return processes
    
    def _get_electron_processes(self, ide_type: IDEType) -> List[ProcessInfo]:
        """获取基于Electron的IDE进程"""
        processes = []
        
        if self.system != "Windows":
            return processes
        
        try:
            # 根据IDE类型确定搜索关键字
            search_keywords = {
                IDEType.VSCODE: ['Code', 'vscode'],
                IDEType.CURSOR: ['Cursor', 'cursor']
            }
            
            keywords = search_keywords.get(ide_type, [])
            
            for keyword in keywords:
                cmd = f'wmic process where "CommandLine like \'%{keyword}%\'" get ProcessId,Name,CommandLine /format:csv'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='gbk', errors='ignore')
                
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip() and keyword.lower() in line.lower() and '.exe' in line.lower():
                            parts = line.split(',')
                            if len(parts) >= 3:
                                name = parts[1].strip()
                                pid = parts[2].strip()
                                command_line = parts[3].strip() if len(parts) > 3 else ""

                                if name and pid and pid.isdigit():
                                    processes.append(ProcessInfo(
                                        name=name,
                                        pid=pid,
                                        command_line=command_line
                                    ))
        
        except Exception as e:
            print_warning(f"获取Electron进程失败: {e}")

        return processes

    async def kill_ide_processes(self, ide_type: IDEType, force: bool = False) -> bool:
        """
        终止指定IDE的所有进程

        Args:
            ide_type: IDE类型
            force: 是否强制终止

        Returns:
            bool: 是否成功终止所有进程
        """
        print_info(f"正在终止 {ide_type.value} 进程...")

        # 获取所有进程
        processes = self.get_ide_processes(ide_type)
        if not processes:
            print_info("未找到相关进程")
            return True

        print_info(f"找到 {len(processes)} 个进程:")
        for proc in processes:
            print_info(f"  {proc}")

        # 第一步：使用标准方法终止进程
        success = await self._kill_processes_standard(processes, ide_type)

        if success:
            print_success("所有进程已成功终止")
            return True

        if not force:
            print_warning("部分进程无法终止，可以尝试强制模式")
            return False

        # 第二步：强制终止残留进程
        print_info("启用强制模式...")
        return await self._kill_processes_force(ide_type)

    async def _kill_processes_standard(self, processes: List[ProcessInfo], ide_type: IDEType) -> bool:
        """使用标准方法终止进程"""
        try:
            if self.system == "Windows":
                # 按进程名批量终止
                process_names = set(proc.name for proc in processes)
                for process_name in process_names:
                    try:
                        cmd = f'taskkill /F /IM "{process_name}"'
                        subprocess.run(cmd, shell=True, check=False, capture_output=True)
                        print_info(f"已终止 {process_name} 进程")
                    except Exception as e:
                        print_warning(f"终止 {process_name} 失败: {e}")
            else:
                # Linux/macOS使用pkill
                for proc in processes:
                    try:
                        subprocess.run(['kill', '-TERM', proc.pid], check=False)
                        print_info(f"已终止进程 PID: {proc.pid}")
                    except Exception as e:
                        print_warning(f"终止进程 {proc.pid} 失败: {e}")

            # 等待进程终止
            await self._sleep(3)

            # 检查是否还有残留进程
            remaining = self.get_ide_processes(ide_type)
            return len(remaining) == 0

        except Exception as e:
            print_error(f"标准终止方法失败: {e}")
            return False

    async def _kill_processes_force(self, ide_type: IDEType) -> bool:
        """强制终止进程（多种策略）"""
        max_retries = 3

        for retry in range(max_retries):
            print_info(f"强制终止尝试 {retry + 1}/{max_retries}")

            remaining_processes = self.get_ide_processes(ide_type)
            if not remaining_processes:
                print_success("强制终止成功")
                return True

            print_info(f"仍有 {len(remaining_processes)} 个进程在运行")

            if self.system == "Windows":
                # Windows强制终止策略
                await self._windows_force_kill(remaining_processes)
            else:
                # Linux/macOS强制终止策略
                await self._unix_force_kill(remaining_processes)

            await self._sleep(2)

        # 最终检查
        final_check = self.get_ide_processes(ide_type)
        if final_check:
            print_warning(f"仍有 {len(final_check)} 个进程无法终止")
            for proc in final_check:
                print_warning(f"  顽固进程: {proc}")
            return False

        return True

    async def _windows_force_kill(self, processes: List[ProcessInfo]):
        """Windows强制终止策略"""
        # 策略1：逐个PID终止
        for proc in processes:
            try:
                cmd = f'taskkill /F /PID {proc.pid}'
                subprocess.run(cmd, shell=True, check=False, capture_output=True)
                print_info(f"强制终止进程 PID: {proc.pid}")
            except Exception as e:
                print_warning(f"无法终止进程 {proc.pid}: {e}")

        await self._sleep(1)

        # 策略2：使用wmic删除
        try:
            process_names = set(proc.name for proc in processes)
            for process_name in process_names:
                cmd = f'wmic process where "name=\'{process_name}\'" delete'
                subprocess.run(cmd, shell=True, check=False, capture_output=True)
                print_info(f"使用wmic删除进程: {process_name}")
        except Exception as e:
            print_warning(f"wmic删除失败: {e}")

    async def _unix_force_kill(self, processes: List[ProcessInfo]):
        """Unix系统强制终止策略"""
        for proc in processes:
            try:
                # 先尝试SIGTERM
                subprocess.run(['kill', '-TERM', proc.pid], check=False)
                await self._sleep(1)

                # 再尝试SIGKILL
                subprocess.run(['kill', '-KILL', proc.pid], check=False)
                print_info(f"强制终止进程 PID: {proc.pid}")
            except Exception as e:
                print_warning(f"无法终止进程 {proc.pid}: {e}")

    async def _sleep(self, seconds: float):
        """异步睡眠"""
        time.sleep(seconds)  # 简化版本，实际可以使用asyncio.sleep

    def find_processes_using_file(self, file_path: Path) -> List[ProcessInfo]:
        """
        查找占用指定文件的进程

        Args:
            file_path: 文件路径

        Returns:
            List[ProcessInfo]: 占用文件的进程列表
        """
        processes = []

        if self.system != "Windows":
            return processes  # 目前只支持Windows

        try:
            # 方法1：使用handle.exe（如果可用）
            try:
                cmd = f'handle.exe "{file_path}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')

                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if '.exe' in line and 'pid:' in line.lower():
                            import re
                            pid_match = re.search(r'pid:\s*(\d+)', line, re.IGNORECASE)
                            if pid_match:
                                pid = pid_match.group(1)
                                name_match = re.search(r'(\w+\.exe)', line, re.IGNORECASE)
                                name = name_match.group(1) if name_match else "Unknown"
                                processes.append(ProcessInfo(name=name, pid=pid))
            except Exception:
                pass  # handle.exe可能不可用

            # 方法2：使用PowerShell查找
            if not processes:
                ps_script = f'''
                $file = "{str(file_path).replace(chr(92), chr(92)+chr(92))}"
                Get-Process | Where-Object {{
                    try {{
                        $_.Modules | Where-Object {{ $_.FileName -eq $file }}
                    }} catch {{ }}
                }} | ForEach-Object {{
                    Write-Host "PID:$($_.Id),NAME:$($_.ProcessName)"
                }}
                '''

                cmd = f'powershell -Command "{ps_script}"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')

                if result.returncode == 0:
                    import re
                    matches = re.findall(r'PID:(\d+),NAME:(\w+)', result.stdout)
                    for pid, name in matches:
                        processes.append(ProcessInfo(name=f"{name}.exe", pid=pid))

        except Exception as e:
            print_warning(f"查找占用文件的进程失败: {e}")

        return processes
