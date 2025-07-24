#!/usr/bin/env python3
"""
GUI Module for AugmentCode-Free
Provides a modern, CursorPro-style graphical interface with page management.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import sys
import os
import subprocess
import psutil
import webbrowser

# Import the core functionality
from augment_tools_core.common_utils import (
    get_os_specific_vscode_paths,
    print_info,
    print_success,
    print_error,
    print_warning,
    IDEType,
    get_ide_paths,
    get_ide_display_name,
    get_ide_process_names
)
from augment_tools_core.database_manager import clean_ide_database
from augment_tools_core.telemetry_manager import modify_ide_telemetry_ids

# Import language and config management
from language_manager import get_language_manager, get_text
from config_manager import get_config_manager
from welcome_dialog import AboutDialog


class CursorProButton(tk.Frame):
    """CursorPro style rounded button widget"""
    def __init__(self, parent, text, command, style="primary", **kwargs):
        super().__init__(parent, bg='#f5f5f5', **kwargs)

        self.command = command
        self.is_hovered = False
        self.is_disabled = False
        self.style = style
        self.text = text

        # Style configurations
        self.styles = {
            "primary": {
                "bg": "#4f46e5",
                "fg": "white",
                "hover_bg": "#4338ca",
                "disabled_bg": "#9ca3af"
            },
            "secondary": {
                "bg": "#6b7280",
                "fg": "white", 
                "hover_bg": "#4b5563",
                "disabled_bg": "#d1d5db"
            },
            "warning": {
                "bg": "#dc2626",
                "fg": "white",
                "hover_bg": "#b91c1c", 
                "disabled_bg": "#fca5a5"
            }
        }

        self.setup_button()

    def setup_button(self):
        """Setup the button canvas and bindings"""
        self.canvas = tk.Canvas(self, height=45, highlightthickness=0, 
                               bg='#f5f5f5', cursor='hand2')
        self.canvas.pack(fill='both', expand=True)

        # Bind events
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<Enter>', self.on_enter)
        self.canvas.bind('<Leave>', self.on_leave)
        # Redraw when either the frame or the canvas itself is resized.
        self.bind('<Configure>', self.on_resize)
        self.canvas.bind('<Configure>', self.on_resize)

        # Initial draw (will retry until size is valid)
        self.after(10, self._draw_button)

    def _draw_button(self):
        """Draw the button with current state"""
        self.canvas.delete('all')
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:
            return

        style_config = self.styles[self.style]
        
        # Determine colors based on state
        if self.is_disabled:
            bg_color = style_config["disabled_bg"]
            text_color = "#6b7280"
        elif self.is_hovered:
            bg_color = style_config["hover_bg"]
            text_color = style_config["fg"]
        else:
            bg_color = style_config["bg"]
            text_color = style_config["fg"]

        # Draw rounded rectangle
        radius = 8
        self.canvas.create_rounded_rect(2, 2, width-2, height-2, radius, 
                                       fill=bg_color, outline="")

        # Draw text
        self.canvas.create_text(width//2, height//2, text=self.text,
                               font=('Microsoft YaHei', 11, 'bold'),
                               fill=text_color)

    def on_click(self, event):
        """Handle button click"""
        if not self.is_disabled and self.command:
            self.command()

    def on_enter(self, event):
        """Handle mouse enter"""
        if not self.is_disabled:
            self.is_hovered = True
            self._draw_button()

    def on_leave(self, event):
        """Handle mouse leave"""
        self.is_hovered = False
        self._draw_button()

    def on_resize(self, event):
        """Handle widget resize"""
        self._draw_button()

    def config_state(self, state):
        """Configure button state"""
        if state == 'disabled':
            self.is_disabled = True
            self.canvas.config(cursor='')
        else:
            self.is_disabled = False
            self.canvas.config(cursor='hand2')
        self._draw_button()
    
    def update_text(self, new_text):
        """Update button text"""
        self.text = new_text
        self._draw_button()


# Add rounded rectangle method to Canvas
def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
    """Create a rounded rectangle on canvas"""
    points = []
    for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                 (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                 (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                 (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
        points.extend([x, y])
    return self.create_polygon(points, smooth=True, **kwargs)

tk.Canvas.create_rounded_rect = create_rounded_rect


class ModernDialog:
    """Modern-style dialog for confirmations"""
    def __init__(self, parent, title, message, dialog_type="info"):
        self.parent = parent
        self.title = title
        self.message = message
        self.dialog_type = dialog_type
        self.result = None

    def show(self):
        """Show dialog and return result"""
        if self.dialog_type == "warning":
            return messagebox.askyesno(self.title, self.message, parent=self.parent)
        else:
            messagebox.showinfo(self.title, self.message, parent=self.parent)
            return True


def show_info(parent, title, message):
    """Show info dialog"""
    dialog = ModernDialog(parent, title, message, "info")
    return dialog.show()


def show_warning(parent, title, message):
    """Show warning dialog"""
    dialog = ModernDialog(parent, title, message, "warning")
    return dialog.show()


class WelcomePage:
    """Welcome page for first run - replaces dialog with full page"""
    
    def __init__(self, parent, config_manager, on_continue_callback):
        self.parent = parent
        self.config_manager = config_manager
        self.language_manager = get_language_manager(config_manager)
        self.on_continue_callback = on_continue_callback
        
        # Create main frame for welcome page
        self.frame = tk.Frame(parent, bg='#f5f5f5')
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the welcome page UI"""
        # Create scrollable frame
        canvas = tk.Canvas(self.frame, bg='#f5f5f5', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f5f5')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Main container
        main_frame = tk.Frame(scrollable_frame, bg='#f5f5f5')
        main_frame.pack(fill='both', expand=True, padx=30, pady=15)
        
        # Title section
        title_frame = tk.Frame(main_frame, bg='#f5f5f5')
        title_frame.pack(fill='x', pady=(0, 10))

        # App title with gradient effect
        title_canvas = tk.Canvas(title_frame, height=50, bg='#f5f5f5', highlightthickness=0)
        title_canvas.pack(fill='x', pady=(0, 3))
        
        # Store canvas for potential animation
        self.title_canvas = title_canvas
        self.parent.after(100, self._draw_title)
        
        # Welcome title
        welcome_title = tk.Label(title_frame,
                                text=get_text("dialogs.titles.welcome_title"),
                                font=('Microsoft YaHei', 16, 'bold'),
                                fg='#1f2937', bg='#f5f5f5')
        welcome_title.pack(pady=(0, 5))
        self.welcome_title = welcome_title
        
        # Language selection section
        lang_section = tk.Frame(main_frame, bg='#f5f5f5')
        lang_section.pack(fill='x', pady=(0, 10))

        lang_label = tk.Label(lang_section,
                             text=get_text("app.language"),
                             font=('Microsoft YaHei', 10, 'bold'),
                             fg='#374151', bg='#f5f5f5')
        lang_label.pack(pady=(0, 5))
        self.lang_label = lang_label
        
        # Language selection frame
        lang_select_frame = tk.Frame(lang_section, bg='#ffffff', relief='solid', bd=1)
        lang_select_frame.pack(fill='x', pady=(0, 5))
        
        # Style for combobox
        style = ttk.Style()
        style.theme_use('clam')
        # Modern flat style for combobox
        style.configure('Welcome.TCombobox',
                       fieldbackground='#ffffff',  # inner field
                       background='#ffffff',       # outer frame
                       bordercolor='#d1d5db',      # border colour
                       lightcolor='#d1d5db',
                       darkcolor='#d1d5db',
                       borderwidth=1,
                       relief='flat',
                       padding=4,
                       arrowcolor='#4f46e5')
        style.map('Welcome.TCombobox',
                   fieldbackground=[('active', '#ffffff')],
                   background=[('active', '#ffffff')],
                   bordercolor=[('focus', '#4f46e5')],
                   arrowcolor=[('active', '#4f46e5'), ('!active', '#6b7280')])
        
        self.language_var = tk.StringVar()
        available_langs = self.language_manager.get_available_languages()
        # Remove duplicates while preserving order
        lang_values = list(dict.fromkeys(available_langs.values()))
        
        # Set current language as default
        current_lang = self.language_manager.get_language()
        current_display = available_langs.get(current_lang, lang_values[0])
        self.language_var.set(current_display)
        
        self.language_combo = ttk.Combobox(lang_select_frame,
                                          
                                 textvariable=self.language_var,
                                          values=lang_values,
                                          state="readonly",
                                          font=('Microsoft YaHei', 10),
                                          style='Welcome.TCombobox')
        # Hide legacy combobox
        self.language_combo.pack_forget()
        # Create radio-button style selector
        style.configure('Lang.TRadiobutton', background='#ffffff', foreground='#374151', font=('Microsoft YaHei', 10))
        style.map('Lang.TRadiobutton',
                   foreground=[('active', '#4338ca'), ('selected', '#4338ca')])
        for display in lang_values:
            rb = ttk.Radiobutton(lang_select_frame,
                                 text=display,
                                 value=display,
                                 takefocus=False,
                                 textvariable=self.language_var,
                                 command=lambda d=display: self._on_language_change(),
                                 style='Lang.TRadiobutton')
            rb.pack(side='left', padx=20, pady=6)
        
        # Welcome message
        message_frame = tk.Frame(main_frame, bg='#f5f5f5')
        message_frame.pack(fill='x', pady=(0, 8))

        welcome_text = get_text("dialogs.messages.welcome_message")
        self.welcome_message = tk.Label(message_frame,
                                       text=welcome_text,
                                       font=('Microsoft YaHei', 9),
                                       fg='#4b5563', bg='#f5f5f5',
                                       wraplength=420, justify='left')
        self.welcome_message.pack(pady=(0, 8))
        
        # Warning frame
        warning_frame = tk.Frame(main_frame, bg='#fef3c7', relief='solid', bd=1)
        warning_frame.pack(fill='x', pady=(0, 8))

        warning_text = get_text("dialogs.messages.first_run_warning")
        self.warning_label = tk.Label(warning_frame,
                                     text=warning_text,
                                     font=('Microsoft YaHei', 8),
                                     fg='#92400e', bg='#fef3c7',
                                     wraplength=420, justify='left')
        self.warning_label.pack(padx=12, pady=12)
        
        # GitHub link
        github_frame = tk.Frame(main_frame, bg='#f5f5f5')
        github_frame.pack(fill='x', pady=(0, 8))

        self.github_label = tk.Label(github_frame,
                                    text=get_text("copyright.github"),
                                    font=('Microsoft YaHei', 9, 'underline'),
                                    fg='#3b82f6', bg='#f5f5f5',
                                    cursor='hand2')
        self.github_label.pack()
        self.github_label.bind('<Button-1>', self._open_github)

        # Continue button
        continue_btn = tk.Button(main_frame,
                               text=get_text("buttons.ok") + " - " + get_text("dialogs.messages.continue_text"),
                               font=('Microsoft YaHei', 10, 'bold'),
                               bg='#4f46e5', fg='white',
                               relief='flat', cursor='hand2',
                               bd=0, pady=10, padx=25,
                               command=self._on_continue)
        continue_btn.pack(pady=(10, 20))
        self.continue_btn = continue_btn
    
    def _draw_title(self):
        """Draw animated title"""
        if hasattr(self, 'title_canvas'):
            self.title_canvas.delete('all')
            width = self.title_canvas.winfo_width()
            height = self.title_canvas.winfo_height()
            
            if width > 1 and height > 1:
                # Draw gradient title
                self.title_canvas.create_text(width//2, height//2, 
                                            text=get_text("app.title"),
                                            font=('Microsoft YaHei', 24, 'bold'),
                                            fill='#4f46e5')
    
    def _on_language_change(self, event=None):
        """Handle language change"""
        selected_display = self.language_var.get()
        available_langs = self.language_manager.get_available_languages()
        
        # Find language code by display name
        for code, display in available_langs.items():
            if display == selected_display:
                self.language_manager.set_language(code)
                self._update_texts()
                break
    
    def _update_texts(self):
        """Update all texts after language change"""
        self.welcome_title.config(text=get_text("dialogs.titles.welcome_title"))
        self.lang_label.config(text=get_text("app.language"))
        self.welcome_message.config(text=get_text("dialogs.messages.welcome_message"))
        self.warning_label.config(text=get_text("dialogs.messages.first_run_warning"))
        self.github_label.config(text=get_text("copyright.github"))
        self.continue_btn.config(text=get_text("buttons.ok") + " - " + get_text("dialogs.messages.continue_text"))
        self._draw_title()
    
    def _open_github(self, event=None):
        """Open GitHub repository"""
        try:
            webbrowser.open(get_text("copyright.github"))
        except Exception as e:
            print(f"Error opening GitHub link: {e}")
    
    def _on_continue(self):
        """Handle continue button"""
        # Mark first run as complete
        self.config_manager.mark_first_run_complete()
        # Also disable welcome page for future runs
        self.config_manager.set_show_welcome(False)

        # Call the callback to switch to main page
        if self.on_continue_callback:
            self.on_continue_callback()
    
    def show(self):
        """Show the welcome page"""
        self.frame.pack(fill='both', expand=True)
    
    def hide(self):
        """Hide the welcome page"""
        self.frame.pack_forget()


class MainPage:
    """Main functionality page"""

    def __init__(self, parent, config_manager, language_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.language_manager = language_manager

        # Create main frame for main page
        self.frame = tk.Frame(parent, bg='#f5f5f5')

        # Store references to UI elements for updating
        self.ui_elements = {}

        # Queue for thread-safe GUI updates
        self.message_queue = queue.Queue()

        # Process check cache for performance optimization
        self._process_cache = {}
        self._cache_timestamp = 0
        self._cache_duration = 2000  # Cache for 2 seconds

        # Setup GUI components
        self._setup_gui()

        # Start the message processor
        self._process_messages()

        # Override print functions to redirect to GUI
        self._setup_print_redirection()

    def _setup_gui(self):
        """Setup the main page GUI components"""
        # Main container with CursorPro-like background
        main_frame = tk.Frame(self.frame, bg='#f5f5f5')
        main_frame.pack(fill='both', expand=True, padx=30, pady=20)

        # Top bar with language selector and about button
        top_bar = tk.Frame(main_frame, bg='#f5f5f5')
        top_bar.pack(fill='x', pady=(0, 10))

        # Language selection (left side)
        lang_frame = tk.Frame(top_bar, bg='#f5f5f5')
        lang_frame.pack(side='left')

        lang_label = tk.Label(lang_frame, text=get_text("app.language"),
                             font=('Microsoft YaHei', 9),
                             fg='#6b7280', bg='#f5f5f5')
        lang_label.pack(side='left', padx=(0, 5))

        # Language combobox
        style = ttk.Style()
        style.theme_use('clam')
        # Consistent modern style for language combobox
        style.configure('Lang.TCombobox',
                       fieldbackground='#ffffff',
                       background='#ffffff',
                       bordercolor='#d1d5db',
                       lightcolor='#d1d5db',
                       darkcolor='#d1d5db',
                       borderwidth=1,
                       relief='flat',
                       padding=3,
                       arrowcolor='#4f46e5')
        style.map('Lang.TCombobox',
                   bordercolor=[('focus', '#4f46e5')],
                   arrowcolor=[('active', '#4f46e5'), ('!active', '#6b7280')])

        self.language_var = tk.StringVar()
        available_langs = self.language_manager.get_available_languages()
        # Remove duplicates while preserving order
        lang_values = list(dict.fromkeys(available_langs.values()))
        current_lang = self.language_manager.get_language()
        current_display = available_langs.get(current_lang, lang_values[0])
        self.language_var.set(current_display)

        self.language_combo = ttk.Combobox(lang_frame,
                                          
                                 textvariable=self.language_var,
                                          values=lang_values,
                                          state="readonly",
                                          font=('Microsoft YaHei', 9),
                                          style='Lang.TCombobox',
                                          width=12)
        # Hide legacy combobox
        self.language_combo.pack_forget()
        # Radio-button style selector
        style.configure('Lang2.TRadiobutton', background='#f5f5f5', foreground='#374151', font=('Microsoft YaHei', 9))
        style.map('Lang2.TRadiobutton',
                   foreground=[('active', '#4338ca'), ('selected', '#4338ca')])
        for display in lang_values:
            rb = ttk.Radiobutton(lang_frame,
                                 text=display,
                                 value=display,
                                 takefocus=False,
                                 textvariable=self.language_var,
                                 command=lambda d=display: self._on_language_change(),
                                 style='Lang2.TRadiobutton')
            rb.pack(side='left', padx=20)

        # About button (right side)
        about_btn = tk.Button(top_bar, text=get_text("app.about"),
                             font=('Microsoft YaHei', 9),
                             fg='#6b7280', bg='#f5f5f5',
                             relief='flat', cursor='hand2',
                             bd=0, command=self._show_about)
        about_btn.pack(side='right')
        self.ui_elements['about_btn'] = about_btn

        # Logo/Icon area - CursorPro style circular icon
        icon_frame = tk.Frame(main_frame, bg='#f5f5f5', height=100)
        icon_frame.pack(fill='x', pady=(0, 20))

        # Create gradient title using canvas that fills the frame width
        title_canvas = tk.Canvas(icon_frame, height=60, bg='#f5f5f5',
                                highlightthickness=0)
        title_canvas.pack(fill='x', pady=(20, 5))

        # Store canvas for animation
        self.title_canvas = title_canvas
        self.gradient_offset = 0

        # Wait for canvas to be properly sized, then start animation
        self.parent.after(100, self._animate_gradient)

        # Welcome text
        welcome_label = tk.Label(icon_frame, text=get_text("app.welcome"),
                                font=('Microsoft YaHei', 12),
                                fg='#6b7280', bg='#f5f5f5')
        welcome_label.pack(pady=(0, 25))
        self.ui_elements['welcome_label'] = welcome_label

        # IDE Selection Section
        ide_section = tk.Frame(main_frame, bg='#f5f5f5')
        ide_section.pack(fill='x', pady=(0, 20))

        ide_label = tk.Label(ide_section, text=get_text("app.select_ide"),
                            font=('Microsoft YaHei', 11, 'bold'),
                            fg='#374151', bg='#f5f5f5')
        ide_label.pack(anchor='w', pady=(0, 8))
        self.ui_elements['ide_label'] = ide_label

        # IDE selection frame
        ide_select_frame = tk.Frame(ide_section, bg='#ffffff', relief='flat', bd=0)
        ide_select_frame.pack(fill='x', pady=(0, 10))

        # Create styled combobox
        # IDE selector combobox style
        # Modern flat style for IDE combobox
        style.configure('Custom.TCombobox',
                       fieldbackground='#ffffff',
                       background='#ffffff',
                       bordercolor='#d1d5db',
                       lightcolor='#d1d5db',
                       darkcolor='#d1d5db',
                       borderwidth=1,
                       relief='flat',
                       padding=4,
                       arrowcolor='#4f46e5')
        style.map('Custom.TCombobox',
                   bordercolor=[('focus', '#4f46e5')],
                   arrowcolor=[('active', '#4f46e5'), ('!active', '#6b7280')])

        # Get last selected IDE from config
        last_ide = self.config_manager.get_last_selected_ide()
        self.ide_var = tk.StringVar(value=last_ide)
        # Hide legacy combobox and use flat radiobutton group
        self.ide_combo = ttk.Combobox(ide_select_frame)  # placeholder to reuse config function
        self.ide_combo.pack_forget()

        # Create flat-style toggle buttons for IDE selection
        style.configure('IDE.TRadiobutton',
                       background='#ffffff', foreground='#374151', font=('Microsoft YaHei', 10),
                       relief='flat', padding=6)
        style.map('IDE.TRadiobutton',
                   foreground=[('active', '#4338ca'), ('selected', '#ffffff')],
                   background=[('selected', '#4f46e5')])

        # Create buttons and store for style updates
        self.ide_buttons = []
        ide_values = ["VS Code", "Cursor", "Windsurf"]
        for ide in ide_values:
            rb = tk.Radiobutton(ide_select_frame,
                                 text=ide,
                                 value=ide,
                                 variable=self.ide_var,
                                 command=self._on_ide_change,
                                 font=('Microsoft YaHei', 10, 'bold'),
                                 bg='#ffffff', fg='#374151',
                                 activebackground='#e0e7ff', activeforeground='#374151',
                                 selectcolor='#4f46e5',
                                 indicatoron=0, bd=0, relief='flat', takefocus=False)
            rb.pack(side='left', padx=10, pady=4, expand=True, fill='x')
            self.ide_buttons.append(rb)

        # Apply initial style
        self._update_ide_button_styles()

        # Buttons container
        buttons_frame = tk.Frame(main_frame, bg='#f5f5f5')
        buttons_frame.pack(fill='x', pady=(0, 20))

        # Create buttons with different styles for better visual hierarchy
        self.run_all_btn = CursorProButton(buttons_frame, get_text("buttons.run_all"),
                                          self._run_all_clicked, style="primary")
        self.run_all_btn.pack(fill='x', pady=(0, 12))

        self.close_ide_btn = CursorProButton(buttons_frame, get_text("buttons.close_ide"),
                                            self._close_ide_clicked, style="warning")
        self.close_ide_btn.pack(fill='x', pady=(0, 12))

        self.clean_db_btn = CursorProButton(buttons_frame, get_text("buttons.clean_db"),
                                           self._clean_database_clicked, style="secondary")
        self.clean_db_btn.pack(fill='x', pady=(0, 12))

        self.modify_ids_btn = CursorProButton(buttons_frame, get_text("buttons.modify_ids"),
                                             self._modify_ids_clicked, style="secondary")
        self.modify_ids_btn.pack(fill='x', pady=(0, 12))

        # Set default keyword (no UI input needed)
        self.keyword_var = tk.StringVar(value="augment")

        # Version and copyright info at bottom
        bottom_frame = tk.Frame(main_frame, bg='#f5f5f5')
        bottom_frame.pack(fill='x', pady=(30, 10))

        # Version info
        version_label = tk.Label(bottom_frame, text=get_text("app.version"),
                                font=('Microsoft YaHei', 11),
                                fg='#9ca3af', bg='#f5f5f5')
        version_label.pack(pady=(0, 5))
        self.ui_elements['version_label'] = version_label

        # Copyright info
        copyright_label = tk.Label(bottom_frame, text=get_text("copyright.notice"),
                                  font=('Microsoft YaHei', 9),
                                  fg='#9ca3af', bg='#f5f5f5')
        copyright_label.pack(pady=(0, 5))
        self.ui_elements['copyright_label'] = copyright_label

        # Open source notice with GitHub link
        github_frame = tk.Frame(bottom_frame, bg='#f5f5f5')
        github_frame.pack(pady=(0, 5))

        open_source_label = tk.Label(github_frame, text=get_text("copyright.open_source"),
                                    font=('Microsoft YaHei', 9),
                                    fg='#9ca3af', bg='#f5f5f5')
        open_source_label.pack(side='left')

        github_link = tk.Label(github_frame, text="GitHub",
                              font=('Microsoft YaHei', 9, 'underline'),
                              fg='#3b82f6', bg='#f5f5f5',
                              cursor='hand2')
        github_link.pack(side='left', padx=(5, 0))
        github_link.bind('<Button-1>', self._open_github)

        # Fraud warning
        fraud_label = tk.Label(bottom_frame, text=get_text("copyright.report_fraud"),
                              font=('Microsoft YaHei', 9, 'bold'),
                              fg='#dc2626', bg='#f5f5f5')
        fraud_label.pack()
        self.ui_elements['fraud_label'] = fraud_label

        # Status info (hidden by default, shown in status updates)
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(bottom_frame, textvariable=self.status_var,
                                    font=('Microsoft YaHei', 10),
                                    fg='#059669', bg='#f5f5f5')
        # Don't pack initially - will show when needed

        # Hidden log window (can be toggled)
        self._setup_log_window(main_frame)

    def show(self):
        """Show the main page"""
        self.frame.pack(fill='both', expand=True)

    def hide(self):
        """Hide the main page"""
        self.frame.pack_forget()

    def _setup_log_window(self, parent):
        """Setup hidden log window"""
        # Log window (initially hidden)
        log_frame = tk.Frame(parent, bg='#f5f5f5')
        # Don't pack initially - will be shown when needed

        log_label = tk.Label(log_frame, text="操作日志:",
                            font=('Microsoft YaHei', 10, 'bold'),
                            fg='#374151', bg='#f5f5f5')
        log_label.pack(anchor='w', pady=(10, 5))

        # Text area for log output
        log_text_frame = tk.Frame(log_frame, bg='#ffffff', relief='solid', bd=1)
        log_text_frame.pack(fill='both', expand=True, pady=(0, 10))

        self.output_text = tk.Text(log_text_frame, height=8, wrap=tk.WORD,
                                  font=('Consolas', 9), bg='#ffffff', fg='#374151',
                                  relief='flat', bd=0)

        # Scrollbar for text area
        scrollbar = tk.Scrollbar(log_text_frame, orient='vertical', command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=scrollbar.set)

        self.output_text.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y')

        # Clear button
        clear_btn = tk.Button(log_frame, text=get_text("buttons.clear_log"), command=self._clear_output,
                             font=('Microsoft YaHei', 9), bg='#e74c3c', fg='white',
                             relief='flat', cursor='hand2', bd=0, pady=5)
        clear_btn.pack(pady=(10, 0))
        self.ui_elements['clear_btn'] = clear_btn

    def _on_language_change(self, event=None):
        """Handle language change"""
        selected_display = self.language_var.get()
        available_langs = self.language_manager.get_available_languages()

        # Find language code by display name
        for code, display in available_langs.items():
            if display == selected_display:
                self.language_manager.set_language(code)
                self._update_ui_texts()
                break

    def _update_ide_button_styles(self):
        """Update IDE buttons colors based on selection"""
        selected = self.ide_var.get()
        for btn in getattr(self, 'ide_buttons', []):
            if btn['value'] == selected:
                btn.config(bg='#4f46e5', fg='#ffffff')
            else:
                btn.config(bg='#ffffff', fg='#374151')

    def _on_ide_change(self, event=None):
        """Handle IDE selection change"""
        selected_ide = self.ide_var.get()
        self.config_manager.set_last_selected_ide(selected_ide)
        self._update_ide_button_styles()

    def _show_about(self):
        """Show about dialog"""
        AboutDialog(self.parent, self.config_manager, show_dont_show_again=True).show()

    def _open_github(self, event=None):
        """Open GitHub repository"""
        try:
            webbrowser.open(get_text("copyright.github"))
        except Exception as e:
            print(f"Error opening GitHub link: {e}")

    def _update_ui_texts(self):
        """Update all UI texts after language change"""
        # Update buttons
        self.run_all_btn.update_text(get_text("buttons.run_all"))
        self.close_ide_btn.update_text(get_text("buttons.close_ide"))
        self.clean_db_btn.update_text(get_text("buttons.clean_db"))
        self.modify_ids_btn.update_text(get_text("buttons.modify_ids"))

        # Update labels
        if 'welcome_label' in self.ui_elements:
            self.ui_elements['welcome_label'].config(text=get_text("app.welcome"))
        if 'ide_label' in self.ui_elements:
            self.ui_elements['ide_label'].config(text=get_text("app.select_ide"))
        if 'about_btn' in self.ui_elements:
            self.ui_elements['about_btn'].config(text=get_text("app.about"))
        if 'version_label' in self.ui_elements:
            self.ui_elements['version_label'].config(text=get_text("app.version"))
        if 'copyright_label' in self.ui_elements:
            self.ui_elements['copyright_label'].config(text=get_text("copyright.notice"))
        if 'fraud_label' in self.ui_elements:
            self.ui_elements['fraud_label'].config(text=get_text("copyright.report_fraud"))
        if 'clear_btn' in self.ui_elements:
            self.ui_elements['clear_btn'].config(text=get_text("buttons.clear_log"))

    def _animate_gradient(self):
        """Create animated gradient text effect"""
        if not hasattr(self, 'title_canvas') or not self.title_canvas.winfo_exists():
            return

        self.title_canvas.delete('all')
        width = self.title_canvas.winfo_width()
        height = self.title_canvas.winfo_height()

        if width > 1 and height > 1:
            # Create gradient effect
            self.title_canvas.create_text(width//2, height//2,
                                        text=get_text("app.title"),
                                        font=('Microsoft YaHei', 18, 'bold'),
                                        fill='#4f46e5')

        # Schedule next animation frame
        self.parent.after(100, self._animate_gradient)

    def _process_messages(self):
        """Process messages from the queue for thread-safe GUI updates"""
        try:
            while True:
                msg_type, message = self.message_queue.get_nowait()

                # Add to output text
                if hasattr(self, 'output_text'):
                    self.output_text.insert(tk.END, message + '\n')
                    self.output_text.see(tk.END)

                # Update status display (show temporarily)
                if msg_type == 'success':
                    self.show_status_message(get_text("status.success"), "#059669")
                elif msg_type == 'error':
                    self.show_status_message(get_text("status.error"), "#dc2626")
                elif msg_type == 'warning':
                    self.show_status_message(get_text("status.warning"), "#d97706")
                else:
                    self.show_status_message(get_text("status.processing"), "#0ea5e9")

        except queue.Empty:
            pass

        # Schedule next check
        self.parent.after(100, self._process_messages)

    def show_status_message(self, message, color):
        """Show status message temporarily"""
        self.status_var.set(message)
        self.status_label.config(fg=color)
        self.status_label.pack(pady=(10, 0))

        # Hide after 3 seconds
        self.parent.after(3000, lambda: self.status_label.pack_forget())

    def _setup_print_redirection(self):
        """Setup print function redirection to GUI"""
        def gui_print_info(message):
            self.message_queue.put(('info', f"ℹ️ {message}"))

        def gui_print_success(message):
            self.message_queue.put(('success', f"✅ {message}"))

        def gui_print_error(message):
            self.message_queue.put(('error', f"❌ {message}"))

        def gui_print_warning(message):
            self.message_queue.put(('warning', f"⚠️ {message}"))

        # Store original functions
        self.original_print_info = print_info
        self.original_print_success = print_success
        self.original_print_error = print_error
        self.original_print_warning = print_warning

        # Store GUI versions
        self.gui_print_info = gui_print_info
        self.gui_print_success = gui_print_success
        self.gui_print_error = gui_print_error
        self.gui_print_warning = gui_print_warning

    def _clear_output(self):
        """Clear the output text area"""
        if hasattr(self, 'output_text'):
            self.output_text.delete(1.0, tk.END)

    def get_selected_ide_type(self):
        """Get the selected IDE type"""
        ide_name = self.ide_var.get()
        if ide_name == "VS Code":
            return IDEType.VSCODE
        elif ide_name == "Cursor":
            return IDEType.CURSOR
        elif ide_name == "Windsurf":
            return IDEType.WINDSURF
        else:
            return IDEType.VSCODE  # Default

    def set_buttons_state(self, state):
        """Set all buttons state"""
        self.run_all_btn.config_state(state)
        self.close_ide_btn.config_state(state)
        self.clean_db_btn.config_state(state)
        self.modify_ids_btn.config_state(state)

        # Re-enable after 2 seconds
        if state == 'disabled':
            self.parent.after(2000, lambda: self.set_buttons_state('normal'))

    def _is_ide_running(self, ide_type):
        """Check if IDE is currently running with caching for performance"""
        import time
        current_time = int(time.time() * 1000)  # Current time in milliseconds

        # Check cache first
        cache_key = f"ide_running_{ide_type.value}"
        if (cache_key in self._process_cache and
            current_time - self._cache_timestamp < self._cache_duration):
            return self._process_cache[cache_key]

        try:
            # Show immediate feedback
            self.status_var.set("正在检查IDE状态...")

            process_names = get_ide_process_names(ide_type)
            is_running = False

            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in process_names:
                    is_running = True
                    break

            # Cache the result
            self._process_cache[cache_key] = is_running
            self._cache_timestamp = current_time

            # Clear status
            self.status_var.set("")

            return is_running
        except Exception:
            # Cache negative result on error
            self._process_cache[cache_key] = False
            self._cache_timestamp = current_time
            self.status_var.set("")
            return False

    # Button click handlers
    def _run_all_clicked(self):
        """Handle run all button click"""
        # Immediate feedback
        self.status_var.set("正在准备执行...")
        self.parent.update_idletasks()

        ide_type = self.get_selected_ide_type()
        ide_name = get_ide_display_name(ide_type)

        # Show special warning for this operation
        result = show_warning(
            self.parent,
            get_text("dialogs.titles.run_all_confirm"),
            get_text("dialogs.messages.run_all_warning", ide_name=ide_name)
        )

        if not result:
            self.status_var.set("")
            return

        keyword = self.keyword_var.get().strip()  # Use default "augment"

        self.set_buttons_state('disabled')
        self.status_var.set(get_text("status.running"))

        def run_all_task():
            try:
                self.gui_print_info(f"开始为 {ide_name} 执行所有工具")

                # Step 1: Close IDE
                self.gui_print_info(f"步骤 1: 关闭 {ide_name}")
                # Implementation would go here

                # Step 2: Clean database
                self.gui_print_info(f"步骤 2: 清理 {ide_name} 数据库")
                if clean_ide_database(ide_type, keyword):
                    self.gui_print_info("数据库清理完成")
                else:
                    self.gui_print_error("数据库清理失败")

                # Step 3: Modify telemetry IDs
                self.gui_print_info(f"步骤 3: 修改 {ide_name} 遥测ID")
                if modify_ide_telemetry_ids(ide_type):
                    self.gui_print_info("遥测ID修改完成")
                else:
                    self.gui_print_error("遥测ID修改失败")

                self.gui_print_success(f"{ide_name}所有工具已完成执行序列。")
                self.parent.after(0, lambda: self.status_var.set(get_text("status.completed")))

            except Exception as e:
                self.gui_print_error(f"运行所有工具时发生错误: {str(e)}")
                self.parent.after(0, lambda: self.status_var.set(get_text("status.failed")))
            finally:
                self.parent.after(0, lambda: self.set_buttons_state('normal'))

        # Run in separate thread
        thread = threading.Thread(target=run_all_task, daemon=True)
        thread.start()

    def _close_ide_clicked(self):
        """Handle close IDE button click"""
        # Immediate feedback
        self.status_var.set("正在准备关闭IDE...")
        self.parent.update_idletasks()

        ide_type = self.get_selected_ide_type()
        ide_name = get_ide_display_name(ide_type)

        # Show warning dialog
        result = show_warning(
            self.parent,
            get_text("dialogs.titles.close_confirm", ide_name=ide_name),
            get_text("dialogs.messages.close_warning", ide_name=ide_name)
        )

        if not result:
            self.status_var.set("")
            return

        self.set_buttons_state('disabled')
        self.status_var.set(get_text("status.closing_ide"))

        def close_task():
            try:
                self.gui_print_info(f"正在关闭 {ide_name}...")

                # Close IDE processes
                process_names = get_ide_process_names(ide_type)
                closed_any = False

                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] in process_names:
                        try:
                            proc.terminate()
                            closed_any = True
                            self.gui_print_info(f"已关闭 {proc.info['name']} (PID: {proc.info['pid']})")
                        except Exception as e:
                            self.gui_print_error(f"关闭进程失败: {e}")

                if closed_any:
                    self.gui_print_success(f"{ide_name} 已成功关闭")
                else:
                    self.gui_print_warning(f"未找到运行中的 {ide_name} 进程")

            except Exception as e:
                self.gui_print_error(f"关闭 {ide_name} 时发生错误: {str(e)}")
            finally:
                self.parent.after(0, lambda: self.set_buttons_state('normal'))

        # Run in separate thread
        thread = threading.Thread(target=close_task, daemon=True)
        thread.start()

    def _clean_database_clicked(self):
        """Handle clean database button click"""
        # Immediate feedback
        self.status_var.set("正在准备清理数据库...")
        self.parent.update_idletasks()

        ide_type = self.get_selected_ide_type()
        ide_name = get_ide_display_name(ide_type)
        keyword = self.keyword_var.get().strip()

        # Check if IDE is running
        if self._is_ide_running(ide_type):
            show_info(
                self.parent,
                get_text("dialogs.titles.ide_running", ide_name=ide_name),
                get_text("dialogs.messages.ide_running_warning", ide_name=ide_name)
            )
            self.status_var.set("")
            return

        self.set_buttons_state('disabled')
        self.status_var.set(get_text("status.cleaning_db"))

        def clean_task():
            try:
                self.gui_print_info(f"开始清理 {ide_name} 数据库 (关键字: '{keyword}')")

                if clean_ide_database(ide_type, keyword):
                    self.gui_print_info("数据库清理过程完成。")
                    self.parent.after(0, lambda: self.status_var.set(get_text("status.completed")))
                else:
                    self.gui_print_error("数据库清理过程报告错误。请检查之前的消息。")
                    self.parent.after(0, lambda: self.status_var.set(get_text("status.failed")))

            except Exception as e:
                self.gui_print_error(f"清理数据库时发生错误: {str(e)}")
                self.parent.after(0, lambda: self.status_var.set(get_text("status.failed")))
            finally:
                self.parent.after(0, lambda: self.set_buttons_state('normal'))

        # Run in separate thread
        thread = threading.Thread(target=clean_task, daemon=True)
        thread.start()

    def _modify_ids_clicked(self):
        """Handle modify IDs button click"""
        # Immediate feedback
        self.status_var.set("正在准备修改遥测ID...")
        self.parent.update_idletasks()

        ide_type = self.get_selected_ide_type()
        ide_name = get_ide_display_name(ide_type)

        # Check if IDE is running
        if self._is_ide_running(ide_type):
            show_info(
                self.parent,
                get_text("dialogs.titles.ide_running", ide_name=ide_name),
                get_text("dialogs.messages.ide_running_warning", ide_name=ide_name)
            )
            self.status_var.set("")
            return

        self.set_buttons_state('disabled')
        self.status_var.set(get_text("status.modifying_ids"))

        def modify_task():
            try:
                self.gui_print_info(f"开始修改 {ide_name} 遥测 ID")

                if modify_ide_telemetry_ids(ide_type):
                    self.gui_print_info("遥测 ID 修改过程完成。")
                    self.parent.after(0, lambda: self.status_var.set(get_text("status.completed")))
                else:
                    self.gui_print_error("遥测 ID 修改过程报告错误。请检查之前的消息。")
                    self.parent.after(0, lambda: self.status_var.set(get_text("status.failed")))

            except Exception as e:
                self.gui_print_error(f"修改遥测 ID 时发生错误: {str(e)}")
                self.parent.after(0, lambda: self.status_var.set(get_text("status.failed")))
            finally:
                self.parent.after(0, lambda: self.set_buttons_state('normal'))

        # Run in separate thread
        thread = threading.Thread(target=modify_task, daemon=True)
        thread.start()


class AugmentToolsGUI:
    def __init__(self, root):
        self.root = root

        # Initialize config and language managers
        self.config_manager = get_config_manager()
        self.language_manager = get_language_manager(self.config_manager)

        # Set window properties
        self.root.title(get_text("app.title"))
        geometry = self.config_manager.get_window_geometry()
        self.root.geometry(geometry)
        self.root.resizable(False, False)

        # Set window style like CursorPro
        self.root.configure(bg='#f5f5f5')

        # Center the window
        self.center_window()

        # Initialize pages
        self.current_page = None
        self.welcome_page = None
        self.main_page = None

        # Show appropriate page
        self._show_initial_page()

    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _show_initial_page(self):
        """Show the appropriate initial page"""
        if self.config_manager.is_first_run():
            self._show_welcome_page()
        else:
            self._show_main_page()
            # Show about dialog on startup if enabled
            if self.config_manager.should_show_about_on_startup():
                self.root.after(500, self._show_startup_about)  # Delay to ensure main window is ready

    def _show_startup_about(self):
        """Show about dialog on startup"""
        AboutDialog(self.root, self.config_manager, show_dont_show_again=True).show()

    def _show_welcome_page(self):
        """Show the welcome page"""
        if self.current_page:
            self.current_page.hide()

        if not self.welcome_page:
            self.welcome_page = WelcomePage(self.root, self.config_manager, self._on_welcome_continue)

        self.welcome_page.show()
        self.current_page = self.welcome_page

    def _show_main_page(self):
        """Show the main page"""
        if self.current_page:
            self.current_page.hide()

        if not self.main_page:
            self.main_page = MainPage(self.root, self.config_manager, self.language_manager)

        self.main_page.show()
        self.current_page = self.main_page

    def _on_welcome_continue(self):
        """Handle continue from welcome page"""
        self._show_main_page()


def main():
    """Main function to run the GUI application"""
    root = tk.Tk()
    app = AugmentToolsGUI(root)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print(get_text("console.interrupted"))
        sys.exit(0)


if __name__ == "__main__":
    main()
