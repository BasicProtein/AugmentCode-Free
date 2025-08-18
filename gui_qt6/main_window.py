#!/usr/bin/env python3
"""
PyQt6主窗口
替代原有的Tkinter主窗口
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from .welcome_page import WelcomePage
from .main_page import MainPage
from .styles import get_complete_style
from .font_manager import get_font_manager
from config_manager import get_config_manager
from language_manager import get_language_manager, get_text
from .about_dialog import AboutDialog


class MainWindow(QMainWindow):
    """PyQt6主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化管理器
        self.config_manager = get_config_manager()
        self.language_manager = get_language_manager(self.config_manager)
        self.font_manager = get_font_manager()
        
        # 页面堆栈
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # 页面实例
        self.welcome_page = None
        self.main_page = None
        
        # 设置窗口
        self._setup_window()
        
        # 应用样式
        self._apply_styles()
        
        # 显示初始页面
        self._show_initial_page()
    
    def _setup_window(self):
        """设置窗口属性"""
        # 窗口标题
        self.setWindowTitle(get_text("app.title"))
        
        # 窗口大小和位置
        geometry = self.config_manager.get_window_geometry()
        if 'x' in geometry:
            # 解析几何字符串 "500x750+100+100"
            parts = geometry.replace('+', 'x').split('x')
            if len(parts) >= 2:
                width, height = int(parts[0]), int(parts[1])
                # 确保最小尺寸：宽度680px，高度780px
                width = max(width, 680)  # 确保最小宽度
                height = max(height, 780)
                self.resize(width, height)
        else:
            self.resize(680, 780)  # 大幅增加宽度以容纳更宽的按钮
        
        # 禁用窗口大小调整
        self.setFixedSize(self.size())
        
        # 居中显示
        self._center_window()
        
        # 设置窗口图标（如果有的话）
        try:
            # 这里可以设置应用图标
            # self.setWindowIcon(QIcon("icon.png"))
            pass
        except:
            pass
    
    def _center_window(self):
        """将窗口居中显示"""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
    
    def _apply_styles(self):
        """应用样式表"""
        self.setStyleSheet(get_complete_style())
    
    def _show_initial_page(self):
        """显示初始页面"""
        if self.config_manager.is_first_run():
            self._show_welcome_page()
        else:
            self._show_main_page()
            # 如果设置了启动时显示关于对话框
            if self.config_manager.should_show_about_on_startup():
                # 延迟显示，确保主窗口已完全加载
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(500, self._show_startup_about)
    
    def _show_startup_about(self):
        """启动时显示关于对话框"""
        AboutDialog(self, self.config_manager, show_dont_show_again=True).show()
    
    def _show_welcome_page(self):
        """显示欢迎页面"""
        if not self.welcome_page:
            self.welcome_page = WelcomePage(self.config_manager)
            self.welcome_page.continue_clicked.connect(self._on_welcome_continue)
            self.stacked_widget.addWidget(self.welcome_page)
        
        self.stacked_widget.setCurrentWidget(self.welcome_page)
    
    def _show_main_page(self):
        """显示主功能页面"""
        if not self.main_page:
            self.main_page = MainPage(self.config_manager)
            self.stacked_widget.addWidget(self.main_page)
        
        self.stacked_widget.setCurrentWidget(self.main_page)
    
    def _on_welcome_continue(self):
        """处理欢迎页面继续事件"""
        self._show_main_page()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果有正在运行的工作线程，先取消
        if hasattr(self, 'main_page') and self.main_page and self.main_page.current_worker:
            self.main_page.current_worker.cancel()
            self.main_page.current_worker.wait(1000)  # 等待最多1秒
        
        # 保存窗口几何信息
        geometry = f"{self.width()}x{self.height()}"
        self.config_manager.set_window_geometry(geometry)
        
        event.accept()


class AugmentCodeApp:
    """AugmentCode-Free PyQt6应用程序"""
    
    def __init__(self):
        self.app = None
        self.main_window = None
    
    def run(self):
        """运行应用程序"""
        try:
            # 创建QApplication
            self.app = QApplication(sys.argv)
            
            # 设置应用程序属性
            self.app.setApplicationName("AugmentCode-Free")
            self.app.setApplicationVersion("1.0.6")
            self.app.setOrganizationName("AugmentCode-Free Team")
            
            # 启用高DPI支持 (PyQt6兼容性修复)
            try:
                self.app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            except AttributeError:
                # PyQt6中此属性可能不存在，忽略
                pass

            try:
                self.app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
            except AttributeError:
                # PyQt6中此属性可能不存在，忽略
                pass
            
            # 创建主窗口
            self.main_window = MainWindow()
            self.main_window.show()
            
            # 运行事件循环
            return self.app.exec()
            
        except Exception as e:
            print(f"❌ 启动PyQt6应用时发生错误: {e}")
            return 1
    
    def quit(self):
        """退出应用程序"""
        if self.app:
            self.app.quit()


def main():
    """主函数 - 启动PyQt6应用"""
    app = AugmentCodeApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
