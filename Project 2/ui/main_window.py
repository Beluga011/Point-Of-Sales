# main_window.py (updated)
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QFrame, QSplitter,
                             QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from models import User

from ui.sales_window import SalesWindow
from ui.products_window import ProductsWindow
from ui.inventory_window import InventoryWindow
from ui.reports_window import ReportsWindow
from ui.users_window import UsersWindow
from ui.login_window import LoginWindow

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.show_login()
    
    def show_login(self):
        """Show the login window"""
        self.login_window = LoginWindow(self.on_login_success)
        self.login_window.show()
    
    def on_login_success(self, user):
        """Handle successful login"""
        self.current_user = user
        if hasattr(self, 'login_window'):
            self.login_window.close()
        self.init_ui()
        self.showMaximized()
    
    def init_ui(self):
        """Initialize the main UI after login"""
        self.setWindowTitle(f'Point of Sale System - {self.current_user.username} ({self.current_user.role})')
        self.setMinimumSize(1200, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.setHandleWidth(2)
        main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #cbd5e1;
            }
            QSplitter::handle:hover {
                background-color: #94a3b8;
            }
        """)
        
        # Sidebar
        sidebar = self.create_sidebar()
        sidebar.setMaximumWidth(280)
        sidebar.setMinimumWidth(250)
        main_splitter.addWidget(sidebar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)  # Added margins for content
        content_layout.setSpacing(0)
        
        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.content_stack)
        
        main_splitter.addWidget(content_widget)
        
        # Set stretch factors (sidebar 0, content 1)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(main_splitter)
        
        # Initialize windows
        self.init_windows()
        
        # Show sales window by default
        self.show_sales()
    
    def create_sidebar(self):
        """Create the sidebar"""
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QFrame()
        header.setFixedHeight(120)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #4f46e5);
                border-bottom: 1px solid #334155;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(20, 20, 20, 20)
        
        # App title
        title = QLabel('POS System')
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setStyleSheet("color: white; margin-bottom: 5px;")
        title.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(title)
        
        # User info
        user_info = QLabel(f"{self.current_user.username} • {self.current_user.role}")
        user_info.setFont(QFont('Segoe UI', 11))
        user_info.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        user_info.setAlignment(Qt.AlignLeft)
        header_layout.addWidget(user_info)
        
        layout.addWidget(header)
        
        # Navigation
        nav_frame = QFrame()
        nav_layout = QVBoxLayout(nav_frame)
        nav_layout.setSpacing(8)
        nav_layout.setContentsMargins(15, 20, 15, 20)
        
        # Navigation buttons
        nav_buttons = [
            ('📊 Sales', 'point-of-sale', self.show_sales),
            ('📦 Products', 'package', self.show_products),
            ('📋 Inventory', 'warehouse', self.show_inventory),
            ('📈 Reports', 'chart-bar', self.show_reports),
        ]
        
        if self.current_user.role in ['Admin', 'Manager']:
            nav_buttons.append(('👥 Users', 'system-users', self.show_users))
        
        for text, icon, callback in nav_buttons:
            btn = QPushButton(text)
            btn.setIcon(QIcon.fromTheme(icon))
            btn.setFixedHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #cbd5e1;
                    border: none;
                    text-align: left;
                    padding-left: 15px;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #475569;
                }
            """)
            btn.clicked.connect(callback)
            nav_layout.addWidget(btn)
        
        nav_layout.addStretch()
        layout.addWidget(nav_frame, 1)
        
        # Footer
        footer = QFrame()
        footer.setFixedHeight(80)
        footer.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-top: 1px solid #334155;
            }
        """)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(15, 10, 15, 10)
        
        # Logout button
        logout_btn = QPushButton('🚪 Logout')
        logout_btn.setIcon(QIcon.fromTheme("system-log-out"))
        logout_btn.clicked.connect(self.logout)
        logout_btn.setFixedHeight(45)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:pressed {
                background-color: #991b1b;
            }
        """)
        footer_layout.addWidget(logout_btn)
        
        layout.addWidget(footer)
        
        return sidebar
    
    def init_windows(self):
        """Initialize all the application windows"""
        # Initialize windows with proper size policies
        self.sales_window = SalesWindow(self.current_user)
        self.products_window = ProductsWindow()
        self.inventory_window = InventoryWindow()
        self.reports_window = ReportsWindow()
        self.users_window = UsersWindow()
        
        # Set size policies for all windows to expand
        for window in [self.sales_window, self.products_window, self.inventory_window, 
                      self.reports_window, self.users_window]:
            window.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.content_stack.addWidget(self.sales_window)
        self.content_stack.addWidget(self.products_window)
        self.content_stack.addWidget(self.inventory_window)
        self.content_stack.addWidget(self.reports_window)
        self.content_stack.addWidget(self.users_window)
    
    def show_sales(self):
        """Show sales window and ensure it's properly loaded"""
        self.content_stack.setCurrentWidget(self.sales_window)
        # Ensure sales window refreshes and displays correctly
        if hasattr(self.sales_window, 'load_products'):
            self.sales_window.load_products()
        if hasattr(self.sales_window, 'refresh_display'):
            self.sales_window.refresh_display()
    
    def show_products(self):
        """Show products window"""
        self.content_stack.setCurrentWidget(self.products_window)
        if hasattr(self.products_window, 'load_products'):
            self.products_window.load_products()
    
    def show_inventory(self):
        """Show inventory window"""
        self.content_stack.setCurrentWidget(self.inventory_window)
        if hasattr(self.inventory_window, 'load_inventory'):
            self.inventory_window.load_inventory()
    
    def show_reports(self):
        """Show reports window"""
        self.content_stack.setCurrentWidget(self.reports_window)
        if hasattr(self.reports_window, 'load_reports'):
            self.reports_window.load_reports()
    
    def show_users(self):
        """Show users window (admin only)"""
        if self.current_user.role in ['Admin', 'Manager']:
            self.content_stack.setCurrentWidget(self.users_window)
            if hasattr(self.users_window, 'load_users'):
                self.users_window.load_users()
        else:
            self.show_sales()  # Fallback to sales if unauthorized
    
    def logout(self):
        """Logout and return to login screen"""
        self.close()
        self.current_user = None
        self.show_login()