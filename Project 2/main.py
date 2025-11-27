import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QStackedWidget, QLabel, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# Import your windows from the ui subfolder
from ui.inventory_window import InventoryWindow
from ui.products_window import ProductsWindow  # Add this import
from ui.sales_window import SalesWindow
from ui.reports_window import ReportsWindow
from ui.users_window import UsersWindow
from ui.login_window import LoginWindow
from csv_handler import CSVHandler
from models import User

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.setWindowTitle("POS System")
        self.setGeometry(100, 100, 1200, 800)
        
        # Show login first
        self.show_login()

    def show_login(self):
        """Show login window"""
        self.login_window = LoginWindow(self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user):
        """Handle successful login"""
        self.current_user = user
        self.login_window.close()
        self.init_ui()
        self.show()

    def init_ui(self):
        """Initialize main UI after login"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setStyleSheet("background-color: #1e293b; border: none;")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # App Title in Sidebar
        title_lbl = QLabel("POS SYSTEM")
        title_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 20px; padding: 20px;")
        title_lbl.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title_lbl)
        
        # Navigation Buttons
        self.nav_btns = []
        
        def create_nav_btn(text, index):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(50)
            btn.setFont(QFont("Segoe UI", 11))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #94a3b8;
                    border: none;
                    text-align: left;
                    padding-left: 30px;
                }
                QPushButton:hover {
                    background-color: #334155;
                    color: white;
                }
                QPushButton:checked {
                    background-color: #2563eb;
                    color: white;
                    border-left: 4px solid #60a5fa;
                }
            """)
            btn.clicked.connect(lambda: self.switch_page(index, btn))
            self.nav_btns.append(btn)
            sidebar_layout.addWidget(btn)
        
        create_nav_btn("Inventory", 0)
        create_nav_btn("Products", 1)  # Add Products button
        create_nav_btn("Sales", 2)
        create_nav_btn("Reports", 3)
        
        # Only show Users tab for admin users
        if self.current_user.role.lower() == 'admin':
            create_nav_btn("Users", 4)
        
        sidebar_layout.addStretch()
        
        # User Info
        user_lbl = QLabel(f"Logged in as:\n{self.current_user.username}\n({self.current_user.role})")
        user_lbl.setStyleSheet("color: #94a3b8; padding: 20px; font-size: 12px;")
        user_lbl.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(user_lbl)

        # Logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setFixedHeight(40)
        logout_btn.clicked.connect(self.logout)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: white;
                border: none;
                margin: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
        """)
        sidebar_layout.addWidget(logout_btn)

        main_layout.addWidget(sidebar)
        
        # --- Content Area ---
        content_area = QFrame()
        content_area.setStyleSheet("background-color: #f8fafc;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # Initialize Windows with current user where needed
        self.inventory_window = InventoryWindow()
        self.products_window = ProductsWindow()  # Initialize ProductsWindow
        self.sales_window = SalesWindow(self.current_user)
        self.reports_window = ReportsWindow()
        self.users_window = UsersWindow()
        
        self.stack.addWidget(self.inventory_window)
        self.stack.addWidget(self.products_window)  # Add ProductsWindow to stack
        self.stack.addWidget(self.sales_window)
        self.stack.addWidget(self.reports_window)
        
        # Only add Users window for admin users
        if self.current_user.role.lower() == 'admin':
            self.stack.addWidget(self.users_window)
        
        content_layout.addWidget(self.stack)
        main_layout.addWidget(content_area)
        
        # Select first page
        if self.nav_btns:
            self.nav_btns[0].click()

    def switch_page(self, index, active_btn):
        # Ensure index is valid (users tab might not be available)
        if index < self.stack.count():
            self.stack.setCurrentIndex(index)
            
            # Update button styles
            for btn in self.nav_btns:
                btn.setChecked(False)
            active_btn.setChecked(True)

    def logout(self):
        """Logout and return to login"""
        self.close()
        self.current_user = None
        self.show_login()

def ensure_data_files():
    """Create CSV files with headers if they don't exist"""
    files = {
        'products.csv': ['product_id', 'name', 'category', 'price', 'stock', 'active', 'cost', 'barcode', 'discount_eligibility'],
        'users.csv': ['user_id', 'username', 'password', 'role', 'active'],
        'sales.csv': ['sale_id', 'date', 'time', 'total', 'tax', 'discount', 'payment_method', 'cashier_id', 'items_data'],
        'promos.csv': ['code', 'discount_percent', 'active']
    }
    
    for filename, headers in files.items():
        if not os.path.exists(filename):
            CSVHandler.create_csv(filename, headers)

if __name__ == "__main__":
    ensure_data_files()
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())