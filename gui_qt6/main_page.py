#!/usr/bin/env python3
"""
PyQt6主功能页面
替代原有的Tkinter主页面
"""

import webbrowser
import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QTextEdit, QMessageBox, QSpacerItem, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor

from .components import (
    TitleLabel, SubtitleLabel, SecondaryLabel, LinkLabel,
    ModernButton, StatusLabel, SectionFrame
)
from .workers import CloseIDEWorker, CleanDatabaseWorker, ModifyIDsWorker, RunAllWorker
from .patch_worker import PatchWorker, RestoreWorker, ScanWorker
from .font_manager import get_default_font, get_monospace_font
from augment_tools_core.common_utils import (
    IDEType, get_ide_display_name, get_ide_process_names
)
from augment_tools_core.patch_manager import PatchMode
from language_manager import get_language_manager, get_text
from .about_dialog import AboutDialog


class MainPage(QWidget):
    """PyQt6主功能页面"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.language_manager = get_language_manager(config_manager)
        
        # 当前工作线程
        self.current_worker = None
        
        # 进程检查缓存
        self._process_cache = {}
        self._cache_timer = QTimer()
        self._cache_timer.timeout.connect(self._clear_process_cache)
        self._cache_timer.start(2000)  # 每2秒清理缓存
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 10, 30, 10)  # 减少上下边距
        main_layout.setSpacing(8)  # 减少间距使布局更紧凑
        
        # 顶部栏
        self._create_top_bar(main_layout)
        
        # 标题区域
        self._create_title_section(main_layout)
        
        # IDE选择区域
        self._create_ide_section(main_layout)
        
        # 按钮区域
        self._create_buttons_section(main_layout)
        
        # 日志区域
        self._create_log_section(main_layout)
        
        # 状态显示
        self._create_status_section(main_layout)
        
        # 底部信息
        self._create_bottom_section(main_layout)
        
        # 添加弹性空间
        main_layout.addStretch()
    
    def _create_top_bar(self, parent_layout):
        """创建顶部栏"""
        top_layout = QHBoxLayout()
        
        # 语言选择
        lang_label = SecondaryLabel(get_text("app.language"))
        top_layout.addWidget(lang_label)
        
        self.language_combo = QComboBox()
        self.language_combo.setFont(get_default_font(9))
        self.language_combo.setMaximumWidth(120)
        
        # 填充语言选项
        available_langs = self.language_manager.get_available_languages()
        lang_values = list(available_langs.values())
        self.language_combo.addItems(lang_values)
        
        # 设置当前语言
        current_lang = self.language_manager.get_language()
        current_display = available_langs.get(current_lang, lang_values[0])
        current_index = lang_values.index(current_display) if current_display in lang_values else 0
        self.language_combo.setCurrentIndex(current_index)
        
        top_layout.addWidget(self.language_combo)
        top_layout.addStretch()
        
        # 关于按钮
        self.about_btn = ModernButton(get_text("app.about"), "secondary")
        # 根据语言调整按钮宽度
        if self.config_manager.get_language() == "en_US":
            self.about_btn.setMaximumWidth(100)  # 英文版本增加宽度
        else:
            self.about_btn.setMaximumWidth(80)   # 中文版本保持原宽度
        top_layout.addWidget(self.about_btn)
        
        parent_layout.addLayout(top_layout)
    
    def _create_title_section(self, parent_layout):
        """创建标题区域"""
        self.title_label = TitleLabel(get_text("app.title"), 18)
        parent_layout.addWidget(self.title_label)
        
        self.welcome_label = SecondaryLabel(get_text("app.welcome"))
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(self.welcome_label)
    
    def _create_ide_section(self, parent_layout):
        """创建IDE选择区域"""
        # IDE选择标签
        self.ide_label = SubtitleLabel(get_text("app.select_ide"))
        parent_layout.addWidget(self.ide_label)

        # IDE选择框架 - 使用水平布局
        ide_frame = SectionFrame()
        ide_layout = QHBoxLayout(ide_frame)
        ide_layout.setSpacing(25)  # 增加间距从15到25
        ide_layout.setContentsMargins(15, 8, 15, 8)  # 减少内边距

        # IDE下拉框 - 适当调整宽度
        self.ide_combo = QComboBox()
        self.ide_combo.setFont(get_default_font(10))
        self.ide_combo.addItems(["VS Code", "Cursor", "Windsurf", "JetBrains"])
        self.ide_combo.setMaximumWidth(160)  # 稍微增加宽度
        self.ide_combo.setMinimumWidth(140)

        # 设置上次选择的IDE
        last_ide = self.config_manager.get_last_selected_ide()
        if last_ide in ["VS Code", "Cursor", "Windsurf", "JetBrains"]:
            self.ide_combo.setCurrentText(last_ide)

        ide_layout.addWidget(self.ide_combo)

        # 添加一些弹性空间
        ide_layout.addSpacing(20)

        # 补丁模式选择 - 放在同一行
        self.patch_mode_label = SecondaryLabel(get_text("app.patch_mode"))
        ide_layout.addWidget(self.patch_mode_label)

        self.patch_mode_combo = QComboBox()
        self.patch_mode_combo.setFont(get_default_font(9))
        self._update_patch_mode_combo()  # 使用多语言文本
        self.patch_mode_combo.setMaximumWidth(150)  # 增加宽度以适应英文
        ide_layout.addWidget(self.patch_mode_combo)

        ide_layout.addStretch()  # 添加弹性空间
        parent_layout.addWidget(ide_frame)

    def _update_patch_mode_combo(self):
        """更新补丁模式下拉框的多语言文本"""
        current_index = self.patch_mode_combo.currentIndex() if hasattr(self, 'patch_mode_combo') else 0

        # 清空并重新添加多语言文本
        self.patch_mode_combo.clear()
        self.patch_mode_combo.addItems([
            get_text("patch_modes.random"),
            get_text("patch_modes.block"),
            get_text("patch_modes.empty"),
            get_text("patch_modes.stealth"),
            get_text("patch_modes.debug")
        ])

        # 恢复之前的选择
        if current_index < self.patch_mode_combo.count():
            self.patch_mode_combo.setCurrentIndex(current_index)

    def _create_buttons_section(self, parent_layout):
        """创建按钮区域"""
        # 主要操作按钮
        self.run_all_btn = ModernButton(get_text("buttons.run_all"), "primary")
        self.run_all_btn.setMaximumHeight(40)  # 减少高度使布局更紧凑
        parent_layout.addWidget(self.run_all_btn)

        # 基础工具按钮组 - 使用水平布局
        basic_tools_frame = SectionFrame()
        basic_tools_layout = QHBoxLayout(basic_tools_frame)
        basic_tools_layout.setSpacing(15)  # 增加间距从10到15
        basic_tools_layout.setContentsMargins(10, 4, 10, 4)  # 进一步减少内边距

        # 关闭IDE按钮
        self.close_ide_btn = ModernButton(get_text("buttons.close_ide"), "warning")
        self.close_ide_btn.setMaximumHeight(35)  # 减少高度使布局更紧凑
        self.close_ide_btn.setMinimumWidth(180)  # 大幅增加最小宽度以适应英文
        basic_tools_layout.addWidget(self.close_ide_btn)

        # 清理数据库按钮
        self.clean_db_btn = ModernButton(get_text("buttons.clean_db"), "secondary")
        self.clean_db_btn.setMaximumHeight(35)
        self.clean_db_btn.setMinimumWidth(180)  # 大幅增加最小宽度以适应英文
        basic_tools_layout.addWidget(self.clean_db_btn)

        # 修改遥测ID按钮
        self.modify_ids_btn = ModernButton(get_text("buttons.modify_ids"), "secondary")
        self.modify_ids_btn.setMaximumHeight(35)
        self.modify_ids_btn.setMinimumWidth(180)  # 大幅增加最小宽度以适应英文
        basic_tools_layout.addWidget(self.modify_ids_btn)

        parent_layout.addWidget(basic_tools_frame)

        # 代码补丁区域
        self._create_patch_section(parent_layout)

    def _create_patch_section(self, parent_layout):
        """创建代码补丁区域"""
        # 补丁区域标题
        self.patch_title_label = SubtitleLabel(get_text("app.code_patch"))
        parent_layout.addWidget(self.patch_title_label)

        # 补丁框架
        patch_frame = SectionFrame()
        patch_layout = QVBoxLayout(patch_frame)
        patch_layout.setSpacing(8)  # 减少间距

        # 补丁按钮组 - 优化布局
        patch_btn_layout = QHBoxLayout()
        patch_btn_layout.setSpacing(12)  # 增加间距
        patch_btn_layout.setContentsMargins(5, 0, 5, 0)  # 添加左右边距

        # 应用补丁按钮
        self.apply_patch_btn = ModernButton(get_text("buttons.apply_patch"), "success")
        self.apply_patch_btn.setMaximumHeight(35)  # 减少高度使布局更紧凑
        self.apply_patch_btn.setMinimumWidth(150)  # 大幅增加最小宽度以适应英文
        patch_btn_layout.addWidget(self.apply_patch_btn)

        # 恢复原始文件按钮
        self.restore_patch_btn = ModernButton(get_text("buttons.restore_files"), "warning")
        self.restore_patch_btn.setMaximumHeight(35)
        self.restore_patch_btn.setMinimumWidth(150)  # 大幅增加最小宽度以适应英文
        patch_btn_layout.addWidget(self.restore_patch_btn)

        # 扫描状态按钮
        self.scan_patch_btn = ModernButton(get_text("buttons.scan_status"), "secondary")
        self.scan_patch_btn.setMaximumHeight(35)
        self.scan_patch_btn.setMinimumWidth(150)  # 大幅增加最小宽度以适应英文
        patch_btn_layout.addWidget(self.scan_patch_btn)

        patch_layout.addLayout(patch_btn_layout)

        # 补丁状态显示
        self.patch_status_label = SecondaryLabel(get_text("status.not_scanned"))
        self.patch_status_label.setStyleSheet("color: #6b7280; font-style: italic; font-size: 10px;")
        patch_layout.addWidget(self.patch_status_label)

        parent_layout.addWidget(patch_frame)

    def _create_log_section(self, parent_layout):
        """创建日志区域"""
        self.log_label = SubtitleLabel(get_text("app.operation_log"))
        parent_layout.addWidget(self.log_label)

        # 创建日志容器
        log_container = QFrame()
        log_container.setMaximumHeight(130)  # 为更高的按钮进一步增加容器高度
        log_container.setMinimumHeight(110)  # 增加最小高度
        log_container.setStyleSheet("QFrame { border: 1px solid #e2e8f0; border-radius: 6px; }")

        # 日志文本框
        self.log_text = QTextEdit(log_container)
        self.log_text.setFont(get_monospace_font(9))
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("QTextEdit { border: none; background: transparent; }")

        # 清空日志按钮 - 放在右下角
        self.clear_log_btn = ModernButton(get_text("buttons.clear_log"), "secondary")
        self.clear_log_btn.setParent(log_container)
        # 根据语言调整按钮宽度
        if self.config_manager.get_language() == "en_US":
            btn_width = 160  # 英文版本大幅增加宽度
        else:
            btn_width = 140  # 中文版本也大幅增加宽度

        self.clear_log_btn.setFixedSize(btn_width, 36)  # 进一步增加按钮高度确保文字完全显示

        # 重写容器的resizeEvent来定位按钮
        def resize_log_container(event):
            # 调整日志文本框大小，为按钮留出更多空间
            self.log_text.setGeometry(5, 5, event.size().width() - btn_width - 25, event.size().height() - 15)
            # 将按钮定位到右下角，确保有足够的垂直空间
            btn_x = event.size().width() - btn_width - 10
            btn_y = event.size().height() - 44  # 为更高的按钮增加Y位置偏移，确保按钮完全可见
            self.clear_log_btn.move(btn_x, btn_y)
            self.clear_log_btn.raise_()  # 确保按钮在最上层

        log_container.resizeEvent = resize_log_container
        parent_layout.addWidget(log_container)
    
    def _create_status_section(self, parent_layout):
        """创建状态显示区域"""
        self.status_label = StatusLabel()
        parent_layout.addWidget(self.status_label)
    
    def _create_bottom_section(self, parent_layout):
        """创建底部信息区域"""
        # 版本信息
        self.version_label = SecondaryLabel(get_text("app.version"))
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(self.version_label)
        
        # 版权信息
        self.copyright_label = SecondaryLabel(get_text("copyright.notice"))
        self.copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        parent_layout.addWidget(self.copyright_label)
        
        # GitHub链接
        github_layout = QHBoxLayout()
        github_layout.addStretch()
        
        open_source_label = SecondaryLabel(get_text("copyright.open_source"))
        github_layout.addWidget(open_source_label)
        
        self.github_link = LinkLabel("GitHub")
        github_layout.addWidget(self.github_link)
        
        github_layout.addStretch()
        parent_layout.addLayout(github_layout)
        
        # 防诈骗警告
        self.fraud_label = SecondaryLabel(get_text("copyright.report_fraud"))
        self.fraud_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fraud_label.setStyleSheet("color: #dc2626; font-weight: bold;")
        parent_layout.addWidget(self.fraud_label)
    
    def _connect_signals(self):
        """连接信号"""
        # 语言切换
        self.language_combo.currentTextChanged.connect(self._on_language_change)
        
        # IDE选择
        self.ide_combo.currentTextChanged.connect(self._on_ide_change)
        
        # 按钮点击
        self.about_btn.clicked.connect(self._show_about)
        self.run_all_btn.clicked.connect(self._run_all_clicked)
        self.close_ide_btn.clicked.connect(self._close_ide_clicked)
        self.clean_db_btn.clicked.connect(self._clean_database_clicked)
        self.modify_ids_btn.clicked.connect(self._modify_ids_clicked)
        self.clear_log_btn.clicked.connect(self._clear_log)

        # 补丁按钮
        self.apply_patch_btn.clicked.connect(self._apply_patch_clicked)
        self.restore_patch_btn.clicked.connect(self._restore_patch_clicked)
        self.scan_patch_btn.clicked.connect(self._scan_patch_clicked)

        # GitHub链接
        self.github_link.clicked.connect(self._open_github)

    def _clear_process_cache(self):
        """清理进程缓存"""
        self._process_cache.clear()

    def _on_language_change(self, selected_display: str):
        """处理语言变更"""
        available_langs = self.language_manager.get_available_languages()

        for code, display in available_langs.items():
            if display == selected_display:
                self.language_manager.set_language(code)
                self._update_ui_texts()
                break

    def _on_ide_change(self, selected_ide: str):
        """处理IDE选择变更"""
        self.config_manager.set_last_selected_ide(selected_ide)

    def _update_ui_texts(self):
        """更新所有UI文本"""
        # 更新按钮文本
        self.run_all_btn.setText(get_text("buttons.run_all"))
        self.close_ide_btn.setText(get_text("buttons.close_ide"))
        self.clean_db_btn.setText(get_text("buttons.clean_db"))
        self.modify_ids_btn.setText(get_text("buttons.modify_ids"))
        self.apply_patch_btn.setText(get_text("buttons.apply_patch"))
        self.restore_patch_btn.setText(get_text("buttons.restore_files"))
        self.scan_patch_btn.setText(get_text("buttons.scan_status"))
        self.clear_log_btn.setText(get_text("buttons.clear_log"))
        self.about_btn.setText(get_text("app.about"))

        # 更新补丁模式下拉框
        self._update_patch_mode_combo()

        # 更新状态标签
        self.patch_status_label.setText(get_text("status.not_scanned"))

        # 根据语言调整按钮宽度
        if self.config_manager.get_language() == "en_US":
            self.about_btn.setMaximumWidth(100)
            # 清理日志按钮现在在日志框内，需要重新设置大小
            btn_width = 160
            self.clear_log_btn.setFixedSize(btn_width, 36)  # 进一步增加按钮高度
        else:
            self.about_btn.setMaximumWidth(80)
            # 清理日志按钮现在在日志框内，需要重新设置大小
            btn_width = 140
            self.clear_log_btn.setFixedSize(btn_width, 36)  # 进一步增加按钮高度

        # 更新标签文本
        self.title_label.setText(get_text("app.title"))
        self.welcome_label.setText(get_text("app.welcome"))
        self.ide_label.setText(get_text("app.select_ide"))
        self.patch_mode_label.setText(get_text("app.patch_mode"))  # 更新补丁模式标签
        self.patch_title_label.setText(get_text("app.code_patch"))  # 更新代码补丁标题
        self.log_label.setText(get_text("app.operation_log"))  # 更新操作日志标签
        self.version_label.setText(get_text("app.version"))
        self.copyright_label.setText(get_text("copyright.notice"))
        self.fraud_label.setText(get_text("copyright.report_fraud"))

    def _show_about(self):
        """显示关于对话框"""
        AboutDialog(self, self.config_manager, show_dont_show_again=True).show()

    def _open_github(self):
        """打开GitHub链接"""
        try:
            webbrowser.open(get_text("copyright.github"))
        except Exception as e:
            print(f"Error opening GitHub link: {e}")

    def _clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def _add_log(self, message: str):
        """添加日志信息"""
        self.log_text.append(message)
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def get_selected_ide_type(self) -> IDEType:
        """获取选中的IDE类型"""
        ide_name = self.ide_combo.currentText()
        if ide_name == "VS Code":
            return IDEType.VSCODE
        elif ide_name == "Cursor":
            return IDEType.CURSOR
        elif ide_name == "Windsurf":
            return IDEType.WINDSURF
        elif ide_name == "JetBrains":
            return IDEType.JETBRAINS
        else:
            return IDEType.VSCODE  # 默认

    def _is_ide_running(self, ide_type: IDEType) -> bool:
        """检查IDE是否正在运行"""
        cache_key = f"ide_running_{ide_type.value}"

        # 检查缓存
        if cache_key in self._process_cache:
            return self._process_cache[cache_key]

        try:
            process_names = get_ide_process_names(ide_type)
            is_running = False

            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in process_names:
                    is_running = True
                    break

            # 缓存结果
            self._process_cache[cache_key] = is_running
            return is_running

        except Exception:
            self._process_cache[cache_key] = False
            return False

    def _set_buttons_enabled(self, enabled: bool):
        """设置所有按钮的启用状态"""
        self.run_all_btn.set_enabled_state(enabled)
        self.close_ide_btn.set_enabled_state(enabled)
        self.clean_db_btn.set_enabled_state(enabled)
        self.modify_ids_btn.set_enabled_state(enabled)

    def _show_warning_dialog(self, title: str, message: str) -> bool:
        """显示警告对话框"""
        reply = QMessageBox.question(
            self, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _show_info_dialog(self, title: str, message: str):
        """显示信息对话框"""
        QMessageBox.information(self, title, message)

    def _run_all_clicked(self):
        """处理一键修改按钮点击"""
        ide_type = self.get_selected_ide_type()
        ide_name = get_ide_display_name(ide_type)

        # 显示确认对话框
        if not self._show_warning_dialog(
            get_text("dialogs.titles.run_all_confirm"),
            get_text("dialogs.messages.run_all_warning", ide_name=ide_name)
        ):
            return

        # 禁用按钮
        self._set_buttons_enabled(False)

        # 创建并启动工作线程
        self.current_worker = RunAllWorker(ide_type, "augment")
        self._connect_worker_signals(self.current_worker)
        self.current_worker.start()

    def _close_ide_clicked(self):
        """处理关闭IDE按钮点击"""
        ide_type = self.get_selected_ide_type()
        ide_name = get_ide_display_name(ide_type)

        # 显示确认对话框
        if not self._show_warning_dialog(
            get_text("dialogs.titles.close_confirm", ide_name=ide_name),
            get_text("dialogs.messages.close_warning", ide_name=ide_name)
        ):
            return

        # 禁用按钮
        self._set_buttons_enabled(False)

        # 创建并启动工作线程
        self.current_worker = CloseIDEWorker(ide_type)
        self._connect_worker_signals(self.current_worker)
        self.current_worker.start()

    def _clean_database_clicked(self):
        """处理清理数据库按钮点击"""
        ide_type = self.get_selected_ide_type()
        ide_name = get_ide_display_name(ide_type)

        # JetBrains 产品不需要数据库清理，引导用户使用修改遥测ID功能
        if ide_type == IDEType.JETBRAINS:
            self._show_info_dialog(
                get_text("dialogs.titles.jetbrains_notice"),
                get_text("dialogs.messages.jetbrains_db_notice", ide_name=ide_name)
            )
            return

        # 检查IDE是否正在运行
        if self._is_ide_running(ide_type):
            self._show_info_dialog(
                get_text("dialogs.titles.ide_running", ide_name=ide_name),
                get_text("dialogs.messages.ide_running_warning", ide_name=ide_name)
            )
            return

        # 禁用按钮
        self._set_buttons_enabled(False)

        # 创建并启动工作线程
        self.current_worker = CleanDatabaseWorker(ide_type, "augment")
        self._connect_worker_signals(self.current_worker)
        self.current_worker.start()

    def _modify_ids_clicked(self):
        """处理修改遥测ID按钮点击"""
        ide_type = self.get_selected_ide_type()
        ide_name = get_ide_display_name(ide_type)

        # 检查IDE是否正在运行
        if self._is_ide_running(ide_type):
            self._show_info_dialog(
                get_text("dialogs.titles.ide_running", ide_name=ide_name),
                get_text("dialogs.messages.ide_running_warning", ide_name=ide_name)
            )
            return

        # 禁用按钮
        self._set_buttons_enabled(False)

        # 创建并启动工作线程
        self.current_worker = ModifyIDsWorker(ide_type)
        self._connect_worker_signals(self.current_worker)
        self.current_worker.start()

    def _connect_worker_signals(self, worker):
        """连接工作线程信号"""
        worker.progress_updated.connect(self._add_log)
        worker.status_changed.connect(self.status_label.show_status)
        worker.task_completed.connect(self._on_task_completed)

    def _on_task_completed(self, success: bool):
        """处理任务完成"""
        # 重新启用按钮
        self._set_buttons_enabled(True)

        # 清理工作线程
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None

        # 显示完成状态
        if success:
            self.status_label.show_status(get_text("status.success"), "success")
        else:
            self.status_label.show_status(get_text("status.error"), "error")

        # 3秒后隐藏状态
        QTimer.singleShot(3000, self.status_label.hide_status)

    # === 补丁相关方法 ===

    def _get_selected_ide_type(self) -> IDEType:
        """获取选中的IDE类型"""
        ide_text = self.ide_combo.currentText()
        ide_mapping = {
            "VS Code": IDEType.VSCODE,
            "Cursor": IDEType.CURSOR,
            "Windsurf": IDEType.WINDSURF,
            "JetBrains": IDEType.JETBRAINS
        }
        return ide_mapping.get(ide_text, IDEType.VSCODE)

    def _get_selected_patch_mode(self) -> PatchMode:
        """获取选中的补丁模式"""
        mode_index = self.patch_mode_combo.currentIndex()
        # 对应新的下拉框选项：随机假数据、完全阻止、空数据、隐身模式、调试模式
        modes = [PatchMode.RANDOM, PatchMode.BLOCK, PatchMode.EMPTY, PatchMode.STEALTH, PatchMode.DEBUG]
        return modes[mode_index] if mode_index < len(modes) else PatchMode.RANDOM

    def _apply_patch_clicked(self):
        """应用补丁按钮点击"""
        if self.current_worker:
            return

        ide_type = self._get_selected_ide_type()
        patch_mode = self._get_selected_patch_mode()

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认补丁操作",
            f"即将对 {get_ide_display_name(ide_type)} 应用代码补丁\n"
            f"补丁模式: {patch_mode.value}\n\n"
            f"此操作将修改扩展文件，建议先关闭IDE。\n"
            f"系统会自动创建备份文件。\n\n"
            f"是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 禁用按钮
        self._set_buttons_enabled(False)

        # 清空日志
        self.log_text.clear()
        self.log_text.append("开始应用代码补丁...")

        # 创建并启动补丁Worker
        self.current_worker = PatchWorker(ide_type, patch_mode)
        self.current_worker.progress_updated.connect(self._add_log)
        self.current_worker.patch_completed.connect(self._on_patch_completed)
        self.current_worker.file_found.connect(self._on_patch_file_found)
        self.current_worker.start()

    def _restore_patch_clicked(self):
        """恢复补丁按钮点击"""
        if self.current_worker:
            return

        ide_type = self._get_selected_ide_type()

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认恢复操作",
            f"即将恢复 {get_ide_display_name(ide_type)} 的原始文件\n\n"
            f"此操作将从备份文件恢复原始扩展文件。\n"
            f"建议先关闭IDE。\n\n"
            f"是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 禁用按钮
        self._set_buttons_enabled(False)

        # 清空日志
        self.log_text.clear()
        self.log_text.append("开始恢复原始文件...")

        # 创建并启动恢复Worker
        self.current_worker = RestoreWorker(ide_type)
        self.current_worker.progress_updated.connect(self._add_log)
        self.current_worker.restore_completed.connect(self._on_restore_completed)
        self.current_worker.start()

    def _scan_patch_clicked(self):
        """扫描补丁状态按钮点击"""
        if self.current_worker:
            return

        ide_type = self._get_selected_ide_type()

        # 禁用按钮
        self._set_buttons_enabled(False)

        # 清空日志
        self.log_text.clear()
        self.log_text.append("开始扫描补丁状态...")

        # 创建并启动扫描Worker
        self.current_worker = ScanWorker([ide_type])
        self.current_worker.progress_updated.connect(self._add_log)
        self.current_worker.scan_completed.connect(self._on_scan_completed)
        self.current_worker.file_found.connect(self._on_scan_file_found)
        self.current_worker.start()

    def _on_patch_completed(self, success: bool, message: str):
        """补丁完成回调"""
        self._on_task_completed(success)
        if success:
            self.patch_status_label.setText("状态: 补丁已应用")
            self.patch_status_label.setStyleSheet("color: #059669; font-weight: bold;")
        else:
            self.patch_status_label.setText("状态: 补丁失败")
            self.patch_status_label.setStyleSheet("color: #dc2626; font-weight: bold;")

    def _on_restore_completed(self, success: bool, message: str):
        """恢复完成回调"""
        self._on_task_completed(success)
        if success:
            self.patch_status_label.setText("状态: 已恢复原始文件")
            self.patch_status_label.setStyleSheet("color: #0891b2; font-weight: bold;")
        else:
            self.patch_status_label.setText("状态: 恢复失败")
            self.patch_status_label.setStyleSheet("color: #dc2626; font-weight: bold;")

    def _on_scan_completed(self, results: dict):
        """扫描完成回调"""
        self._on_task_completed(True)

        # 更新状态显示
        ide_type = self._get_selected_ide_type()
        ide_results = results.get(ide_type.value, [])

        if not ide_results:
            self.patch_status_label.setText(get_text("status.not_scanned"))
            self.patch_status_label.setStyleSheet("color: #6b7280; font-style: italic;")
        else:
            patched_status = get_text("patch.status.patched")
            patched_count = sum(1 for r in ide_results if r['status'] == patched_status)
            total_count = len(ide_results)

            if patched_count == 0:
                self.patch_status_label.setText(f"{get_text('status.not_scanned')}: {get_text('patch.status.not_patched')} ({total_count} 个文件)")
                self.patch_status_label.setStyleSheet("color: #dc2626; font-weight: bold;")
            elif patched_count == total_count:
                self.patch_status_label.setText(f"{get_text('status.ready')}: {get_text('patch.status.patched')} ({patched_count}/{total_count})")
                self.patch_status_label.setStyleSheet("color: #059669; font-weight: bold;")
            else:
                self.patch_status_label.setText(f"{get_text('status.warning')}: 部分补丁 ({patched_count}/{total_count})")
                self.patch_status_label.setStyleSheet("color: #d97706; font-weight: bold;")

    def _on_patch_file_found(self, file_path: str, status: str):
        """补丁文件发现回调"""
        self._add_log(f"📄 文件: {file_path} - {status}")

    def _on_scan_file_found(self, ide_type: str, file_path: str, status: str):
        """扫描文件发现回调"""
        self._add_log(f"📄 {ide_type}: {file_path} - {status}")
