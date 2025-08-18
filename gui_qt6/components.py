#!/usr/bin/env python3
"""
现代化UI组件
替代原有的复杂Tkinter组件
"""

from PyQt6.QtWidgets import (
    QPushButton, QLabel, QFrame, QVBoxLayout,
    QHBoxLayout, QWidget, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from .font_manager import get_button_font, get_default_font, get_title_font
from language_manager import get_text


class ModernButton(QPushButton):
    """现代化按钮组件 - 替代CursorProButton"""
    
    def __init__(self, text: str, button_type: str = "primary", parent=None):
        super().__init__(text, parent)
        self.button_type = button_type
        self._setup_button()
    
    def _setup_button(self):
        """设置按钮样式"""
        self.setFont(get_button_font())
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 设置CSS类名用于样式表
        if self.button_type == "secondary":
            self.setProperty("class", "secondary")
        elif self.button_type == "warning":
            self.setProperty("class", "warning")
        elif self.button_type == "success":
            self.setProperty("class", "success")
        
        # 设置最小尺寸
        self.setMinimumHeight(45)
    
    def set_enabled_state(self, enabled: bool):
        """设置按钮启用状态"""
        self.setEnabled(enabled)
        if enabled:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ForbiddenCursor))


class TitleLabel(QLabel):
    """标题标签组件"""
    
    def __init__(self, text: str, size: int = 24, parent=None):
        super().__init__(text, parent)
        self.setFont(get_title_font(size))
        self.setProperty("class", "title")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class SubtitleLabel(QLabel):
    """副标题标签组件"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(get_default_font(16, bold=True))
        self.setProperty("class", "subtitle")


class SecondaryLabel(QLabel):
    """次要文本标签"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(get_default_font(10))
        self.setProperty("class", "secondary")


class LinkLabel(QLabel):
    """链接标签组件"""
    
    clicked = pyqtSignal()
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFont(get_default_font(10))
        self.setProperty("class", "link")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class WarningFrame(QFrame):
    """警告信息框组件"""
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self._setup_frame(text)
    
    def _setup_frame(self, text: str):
        """设置警告框"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        warning_label = QLabel(text)
        warning_label.setFont(get_default_font(9))
        warning_label.setProperty("class", "warning")
        warning_label.setWordWrap(True)
        
        layout.addWidget(warning_label)


class SectionFrame(QFrame):
    """区域框架组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 6px;
            }}
        """)


class ScrollableFrame(QScrollArea):
    """可滚动框架组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 创建内容widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setWidget(self.content_widget)
    
    def add_widget(self, widget):
        """添加widget到滚动区域"""
        self.content_layout.addWidget(widget)
    
    def add_stretch(self):
        """添加弹性空间"""
        self.content_layout.addStretch()


class StatusLabel(QLabel):
    """状态显示标签"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(get_default_font(10))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()  # 默认隐藏
    
    def show_status(self, message: str, status_type: str = "info"):
        """显示状态信息"""
        self.setText(message)
        
        # 根据状态类型设置颜色
        colors = {
            "success": "#059669",
            "error": "#dc2626", 
            "warning": "#d97706",
            "info": "#0ea5e9"
        }
        
        color = colors.get(status_type, colors["info"])
        self.setStyleSheet(f"color: {color};")
        self.show()
    
    def hide_status(self):
        """隐藏状态信息"""
        self.hide()


class LanguageSelector(QWidget):
    """语言选择器组件"""
    
    language_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 语言标签
        self.label = SecondaryLabel(get_text("app.language"))
        layout.addWidget(self.label)
        
        # 语言下拉框 - 将在主窗口中实现
        # 这里只是占位符
        layout.addStretch()


# 导出所有组件
__all__ = [
    'ModernButton',
    'TitleLabel',
    'SubtitleLabel',
    'SecondaryLabel',
    'LinkLabel',
    'WarningFrame',
    'SectionFrame',
    'ScrollableFrame',
    'StatusLabel',
    'LanguageSelector'
]
