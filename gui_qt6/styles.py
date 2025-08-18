#!/usr/bin/env python3
"""
CursorPro风格样式表
现代化的UI样式定义
"""

# CursorPro颜色系统
COLORS = {
    'primary': '#4f46e5',      # 主色调
    'primary_hover': '#4338ca', # 主色调悬停
    'secondary': '#6b7280',     # 次要颜色
    'secondary_hover': '#4b5563', # 次要颜色悬停
    'warning': '#dc2626',       # 警告色
    'warning_hover': '#b91c1c', # 警告色悬停
    'success': '#059669',       # 成功色
    'background': '#f5f5f5',    # 背景色
    'surface': '#ffffff',       # 表面色
    'text_primary': '#1f2937',  # 主要文字
    'text_secondary': '#6b7280', # 次要文字
    'text_disabled': '#9ca3af', # 禁用文字
    'border': '#e5e7eb',        # 边框色
    'warning_bg': '#fef3c7',    # 警告背景
    'warning_text': '#92400e'   # 警告文字
}


def get_main_window_style() -> str:
    """主窗口样式"""
    return f"""
    QMainWindow {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
    }}
    
    QWidget {{
        background-color: {COLORS['background']};
        color: {COLORS['text_primary']};
    }}
    """


def get_button_style() -> str:
    """按钮样式"""
    return f"""
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: bold;
        min-height: 20px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS['primary_hover']};
        padding-top: 13px;
        padding-bottom: 11px;
    }}
    
    QPushButton:disabled {{
        background-color: {COLORS['text_disabled']};
        color: {COLORS['text_secondary']};
    }}
    
    QPushButton.secondary {{
        background-color: {COLORS['secondary']};
    }}
    
    QPushButton.secondary:hover {{
        background-color: {COLORS['secondary_hover']};
    }}
    
    QPushButton.warning {{
        background-color: {COLORS['warning']};
    }}

    QPushButton.warning:hover {{
        background-color: {COLORS['warning_hover']};
    }}

    QPushButton.success {{
        background-color: {COLORS['success']};
    }}

    QPushButton.success:hover {{
        background-color: #047857;
    }}
    """


def get_combobox_style() -> str:
    """下拉框样式"""
    return f"""
    QComboBox {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 120px;
        color: {COLORS['text_primary']};
    }}
    
    QComboBox:hover {{
        border-color: {COLORS['primary']};
    }}
    
    QComboBox:focus {{
        border-color: {COLORS['primary']};
        outline: none;
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {COLORS['text_secondary']};
        margin-right: 5px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        selection-background-color: {COLORS['primary']};
        selection-color: white;
        padding: 4px;
    }}
    """


def get_label_style() -> str:
    """标签样式"""
    return f"""
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
    }}
    
    QLabel.title {{
        font-size: 24px;
        font-weight: bold;
        color: {COLORS['primary']};
    }}
    
    QLabel.subtitle {{
        font-size: 16px;
        font-weight: bold;
        color: {COLORS['text_primary']};
    }}
    
    QLabel.secondary {{
        color: {COLORS['text_secondary']};
    }}
    
    QLabel.link {{
        color: {COLORS['primary']};
        text-decoration: underline;
    }}
    
    QLabel.link:hover {{
        color: {COLORS['primary_hover']};
    }}
    
    QLabel.warning {{
        color: {COLORS['warning_text']};
        background-color: {COLORS['warning_bg']};
        padding: 12px;
        border-radius: 6px;
    }}
    """


def get_textedit_style() -> str:
    """文本编辑器样式"""
    return f"""
    QTextEdit {{
        background-color: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px;
        color: {COLORS['text_primary']};
    }}
    
    QTextEdit:focus {{
        border-color: {COLORS['primary']};
        outline: none;
    }}
    """


def get_scrollarea_style() -> str:
    """滚动区域样式"""
    return f"""
    QScrollArea {{
        background-color: {COLORS['background']};
        border: none;
    }}
    
    QScrollBar:vertical {{
        background-color: {COLORS['background']};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {COLORS['text_disabled']};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['text_secondary']};
    }}
    
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    """


def get_complete_style() -> str:
    """获取完整的应用样式"""
    return (
        get_main_window_style() +
        get_button_style() +
        get_combobox_style() +
        get_label_style() +
        get_textedit_style() +
        get_scrollarea_style()
    )
