# login_window.py (updated)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMessageBox, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from csv_handler import CSVHandler
from models import User

class LoginWindow(QWidget):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        self.setWindowTitle('POS System - Login')
        self.setMinimumSize(400, 400)
        self.setMaximumSize(400, 500)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 40, 30, 30)
        main_layout.setSpacing(0)
        
        # Header section
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(15)
        
        # App icon/logo
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setText("🏪")
        icon_label.setStyleSheet("font-size: 48px; margin-bottom: 10px;")
        header_layout.addWidget(icon_label)
        
        # Title
        title = QLabel('Point of Sale System')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 24, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        header_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel('Please sign in to continue')
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont('Arial', 12))
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 30px;")
        header_layout.addWidget(subtitle)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(30)
        
        # Login form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(20)
        
        # Username field
        username_layout = QVBoxLayout()
        username_layout.setSpacing(8)
        
        username_label = QLabel('Username:')
        username_label.setFont(QFont('Arial', 11, QFont.Bold))
        username_label.setStyleSheet("color: #2c3e50;")
        username_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Enter your username')
        self.username_input.setText('admin')
        self.username_input.setMinimumHeight(45)
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        username_layout.addWidget(self.username_input)
        form_layout.addLayout(username_layout)
        
        # Password field
        password_layout = QVBoxLayout()
        password_layout.setSpacing(8)
        
        password_label = QLabel('Password:')
        password_label.setFont(QFont('Arial', 11, QFont.Bold))
        password_label.setStyleSheet("color: #2c3e50;")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Enter your password')
        self.password_input.setText('admin123')
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px 15px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8f9fa;
            }
        """)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)
        
        main_layout.addLayout(form_layout)
        main_layout.addSpacing(30)
        
        # Login button
        login_btn = QPushButton('Sign In')
        login_btn.setMinimumHeight(50)
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:focus {
                outline: none;
            }
        """)
        login_btn.clicked.connect(self.attempt_login)
        main_layout.addWidget(login_btn)
        
        # Add stretch to push everything up and prevent cutoff
        main_layout.addStretch(1)
    
    def load_users(self):
        """Create default users if none exist"""
        users = CSVHandler.read_csv('users.csv')
        if not users:
            # Create default admin user
            admin_user = User(
                user_id='1',
                username='admin',
                password='admin123', 
                role='Admin',
                active=True
            )
            CSVHandler.append_csv('users.csv', admin_user.to_dict())
            
            # Create default cashier user
            cashier_user = User(
                user_id='2',
                username='cashier', 
                password='cashier123',
                role='Cashier',
                active=True
            )
            CSVHandler.append_csv('users.csv', cashier_user.to_dict())
    
    def attempt_login(self):
        """Handle login attempt"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, 'Login Error', 
                               'Please enter both username and password.')
            return
        
        users = CSVHandler.read_csv('users.csv')
        for user_data in users:
            try:
                user = User.from_dict(user_data)
                if (user.username == username and 
                    user.password == password and 
                    user.active):
                    self.on_login_success(user)
                    return
            except Exception as e:
                print(f"Error parsing user: {e}")
                continue
        
        QMessageBox.warning(self, 'Login Error', 
                           'Invalid username or password.')
        self.password_input.clear()
        self.password_input.setFocus()