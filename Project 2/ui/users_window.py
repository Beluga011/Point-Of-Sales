import hashlib
import uuid
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
                             QLineEdit, QComboBox, QCheckBox, QFrame, QGraphicsOpacityEffect,
                             QFormLayout, QAbstractItemView, QSizePolicy, QStyle)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QCursor

from csv_handler import CSVHandler
from models import User

# --- STYLING CONSTANTS (Matches Inventory) ---
PRIMARY_COLOR = "#2563eb"
DANGER_COLOR = "#dc2626"
TEXT_COLOR = "#1e293b"
BG_COLOR = "#f8fafc"

STYLESHEET = f"""
    QWidget {{ font-family: 'Segoe UI', sans-serif; color: {TEXT_COLOR}; }}
    QWidget#users_window {{ background-color: {BG_COLOR}; }}
    
    QFrame[card="true"] {{
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
    }}
    
    /* Input Styling */
    QLineEdit, QComboBox {{
        padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px;
    }}
    QLineEdit:focus {{ border: 1px solid {PRIMARY_COLOR}; }}
    
    /* Table Styling (Exact Match) */
    QTableWidget {{
        border: none;
        background-color: white;
        gridline-color: #f1f5f9;
        font-size: 13px;
    }}
    QTableWidget::item {{
        padding-left: 10px;
        border-bottom: 1px solid #f1f5f9;
    }}
    QHeaderView::section {{
        background-color: #f8fafc;
        padding: 12px 10px;
        border: none;
        border-bottom: 2px solid #e2e8f0;
        font-weight: bold;
        color: #64748b;
        text-transform: uppercase;
        font-size: 12px;
    }}
"""

# --- Helper: Toast Notification ---
class ToastNotification(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #1e293b; color: white; padding: 10px 20px; 
                border-radius: 20px; font-weight: bold; font-size: 14px;
            }
        """)
        self.hide()
        self.raise_()
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
    
    def show_message(self, message):
        self.setText(message)
        self.adjustSize()
        self.move((self.parent().width() - self.width()) // 2, self.parent().height() - 100)
        self.show()
        self.raise_()
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()
        QTimer.singleShot(2000, self.fade_out)
        
    def fade_out(self):
        self.animation.setDuration(500)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.finished.connect(self.hide)
        self.animation.start()

# --- Helper: User Dialog ---
class UserFormDialog(QDialog):
    def __init__(self, parent=None, user=None, existing_usernames=[]):
        super().__init__(parent)
        self.user = user
        self.existing_usernames = existing_usernames
        self.is_edit = user is not None
        self.setWindowTitle("Edit User" if self.is_edit else "New User")
        self.setMinimumSize(400, 380)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { font-weight: bold; color: #475569; font-size: 13px; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; }
            QLineEdit:focus { border: 1px solid #2563eb; }
        """)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title = QLabel("User Details")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #1e293b; margin-bottom: 5px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. admin_user")
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(['Admin', 'Manager', 'Cashier'])
        
        self.active_check = QCheckBox("Account is Active")
        self.active_check.setChecked(True)
        
        form.addRow("Username:", self.username_input)
        form.addRow("Password:", self.password_input)
        form.addRow("Role:", self.role_combo)
        form.addRow("", self.active_check)
        
        layout.addLayout(form)
        
        if self.is_edit:
            self.username_input.setText(self.user.username)
            self.role_combo.setCurrentText(self.user.role)
            self.active_check.setChecked(str(self.user.active).lower() == 'true')
            self.password_input.setPlaceholderText("(Leave blank to keep current)")
        else:
            self.password_input.setPlaceholderText("Enter secure password")

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("background: white; border: 1px solid #cbd5e1; padding: 6px 14px; border-radius: 4px; color: #475569;")
        
        save_btn = QPushButton("Save User")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_user)
        save_btn.setStyleSheet(f"background: {PRIMARY_COLOR}; color: white; border: none; padding: 6px 14px; border-radius: 4px; font-weight: bold;")
        
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(save_btn)
        layout.addLayout(btn_box)
        
    def save_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username:
            QMessageBox.warning(self, 'Required', 'Username is required')
            return
            
        current_username = self.user.username if self.is_edit else ""
        if username.lower() != current_username.lower() and username.lower() in [u.lower() for u in self.existing_usernames]:
            QMessageBox.warning(self, 'Duplicate', f'The username "{username}" is already taken.')
            return

        final_password = self.user.password if self.is_edit else ""
        if password:
            final_password = hashlib.sha256(password.encode()).hexdigest()
        elif not self.is_edit:
            QMessageBox.warning(self, 'Required', 'Password is required for new users')
            return

        user_id = self.user.user_id if self.is_edit else str(uuid.uuid4().int)[:8]
        
        self.user_data = {
            'user_id': user_id,
            'username': username,
            'password': final_password,
            'role': self.role_combo.currentText(),
            'active': str(self.active_check.isChecked())
        }
        self.accept()

# --- Main Window ---
class UsersWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.users = []
        self.setObjectName("users_window")
        self.setStyleSheet(STYLESHEET)
        self.init_ui()
        self.toast = ToastNotification(self)
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        
        title_block = QVBoxLayout()
        title = QLabel('User Management')
        title.setFont(QFont('Segoe UI', 24, QFont.Bold))
        title.setStyleSheet("color: #0f172a;")
        subtitle = QLabel("Manage system access and permissions")
        subtitle.setStyleSheet("color: #64748b; font-size: 14px;")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        
        header.addLayout(title_block)
        header.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.clicked.connect(self.load_users)
        refresh_btn.setStyleSheet("background: white; border: 1px solid #cbd5e1; padding: 8px 16px; border-radius: 4px; color: #475569;")
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Card
        card = QFrame()
        card.setProperty("card", "true")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.filter_users)
        
        add_btn = QPushButton(" + Add User")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.add_user)
        add_btn.setStyleSheet("background-color: #16a34a; color: white; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        
        toolbar.addWidget(self.search_input)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        card_layout.addLayout(toolbar)
        
        # Table Setup (Matches Inventory Style)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Name', 'Role', 'Status', 'User ID', 'Actions'])
        
        # Column Resizing Logic
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)           # Name Stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Role fits content
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Status fits content
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # ID fits content
        header.setSectionResizeMode(4, QHeaderView.Fixed)             # Actions Fixed
        self.table.setColumnWidth(4, 180)

        # Table Appearance
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50) # Taller rows
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.setAlternatingRowColors(False) # Clean white like inventory
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        
        card_layout.addWidget(self.table)
        layout.addWidget(card)

    def load_users(self):
        try:
            data = CSVHandler.read_csv('users.csv')
            self.users = [User.from_dict(u) for u in data]
            self.filter_users()
            self.toast.show_message("Users Loaded")
        except Exception as e:
            self.users = []
            self.table.setRowCount(0)

    def filter_users(self):
        query = self.search_input.text().lower()
        filtered = [u for u in self.users if query in u.username.lower() or query in u.role.lower()]
        self.populate_table(filtered)

    def populate_table(self, user_list):
        self.table.setRowCount(len(user_list))
        
        for row, user in enumerate(user_list):
            # Helper for text items
            def item(text, align=Qt.AlignLeft | Qt.AlignVCenter, color=TEXT_COLOR, bold=False):
                it = QTableWidgetItem(str(text))
                it.setForeground(QColor(color))
                it.setTextAlignment(align)
                if bold: it.setFont(QFont("Segoe UI", 9, QFont.Bold))
                return it

            # 1. Name (Dark, Bold)
            self.table.setItem(row, 0, item(user.username, bold=True))
            
            # 2. Role (Badge Style)
            role_colors = {
                "Admin": ("#e0e7ff", "#4338ca"),   # Indigo
                "Manager": ("#fef3c7", "#b45309"), # Amber
                "Cashier": ("#ccfbf1", "#0f766e")  # Teal
            }
            bg, fg = role_colors.get(user.role, ("#f1f5f9", "#475569"))
            
            role_lbl = QLabel(user.role)
            role_lbl.setAlignment(Qt.AlignCenter)
            role_lbl.setStyleSheet(f"background-color: {bg}; color: {fg}; border-radius: 10px; padding: 2px 8px; font-weight: bold; font-family: 'Segoe UI'; font-size: 11px;")
            role_lbl.setFixedSize(80, 24)
            
            w_role = QWidget()
            l_role = QHBoxLayout(w_role)
            l_role.setContentsMargins(10, 0, 0, 0) # Left margin to align
            l_role.addWidget(role_lbl)
            l_role.setAlignment(Qt.AlignLeft)
            self.table.setCellWidget(row, 1, w_role)
            
            # 3. Status (Text)
            is_active = str(user.active).lower() == 'true'
            status_text = "Active" if is_active else "Inactive"
            status_color = "#16a34a" if is_active else "#dc2626"
            self.table.setItem(row, 2, item(status_text, color=status_color, bold=True))
            
            # 4. User ID (Gray, Centered)
            self.table.setItem(row, 3, item(user.user_id, Qt.AlignCenter, "#94a3b8"))
            
            # 5. Actions (Text Links: Edit | Delete)
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(8)
            l.setAlignment(Qt.AlignCenter)
            
            btn_style = "background: transparent; border: none; font-weight: bold; padding: 0px;"

            btn_edit = QPushButton("Edit")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet(f"color: {PRIMARY_COLOR}; {btn_style}")
            btn_edit.clicked.connect(lambda _, u=user: self.edit_user(u))
            
            btn_del = QPushButton("Delete")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet(f"color: {DANGER_COLOR}; {btn_style}")
            btn_del.clicked.connect(lambda _, u=user: self.delete_user(u))
            
            l.addWidget(btn_edit)
            l.addWidget(QLabel("|", styleSheet="color: #cbd5e1;"))
            l.addWidget(btn_del)
            
            self.table.setCellWidget(row, 4, w)

    def add_user(self):
        usernames = [u.username for u in self.users]
        dialog = UserFormDialog(self, existing_usernames=usernames)
        if dialog.exec_() == QDialog.Accepted:
            try:
                CSVHandler.append_csv('users.csv', dialog.user_data)
                self.load_users()
                self.toast.show_message(f"User Added")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def edit_user(self, user):
        usernames = [u.username for u in self.users]
        dialog = UserFormDialog(self, user, existing_usernames=usernames)
        if dialog.exec_() == QDialog.Accepted:
            try:
                CSVHandler.update_csv('users.csv', 'user_id', user.user_id, dialog.user_data)
                self.load_users()
                self.toast.show_message(f"User Updated")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_user(self, user):
        # Prevent deleting last admin
        admins = [u for u in self.users if u.role == "Admin" and str(u.active).lower() == 'true']
        if user.role == "Admin" and len(admins) <= 1:
            QMessageBox.critical(self, "Action Denied", "You cannot delete the only active Administrator.")
            return

        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete user '{user.username}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                CSVHandler.delete_row('users.csv', 'user_id', user.user_id)
                self.load_users()
                self.toast.show_message("User Deleted")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))