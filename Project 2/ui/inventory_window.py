import uuid
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QSpinBox, 
                             QDoubleSpinBox, QLineEdit, QAbstractItemView, 
                             QFormLayout, QFrame, QComboBox, QCheckBox,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QCursor

from csv_handler import CSVHandler
from models import Product

# --- CONFIGURATION & STYLES ---
PRIMARY_COLOR = "#2563eb"  # Blue
HOVER_COLOR = "#1d4ed8"    # Darker Blue
DANGER_COLOR = "#dc2626"   # Red
SUCCESS_COLOR = "#16a34a"  # Green
TEXT_COLOR = "#1e293b"     # Slate 800
BG_COLOR = "#f8fafc"       # Slate 50

STYLESHEET = f"""
    QWidget {{ 
        font-family: 'Segoe UI', sans-serif; 
        color: {TEXT_COLOR};
    }}
    
    /* Main Window Background */
    QWidget#inventory_window {{
        background-color: {BG_COLOR};
    }}

    /* Card Styling */
    QFrame#content_card {{
        background-color: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }}

    /* Labels */
    QLabel {{ font-size: 14px; }}
    QLabel#header_title {{ font-size: 24px; font-weight: bold; color: #0f172a; }}

    /* Buttons */
    QPushButton {{
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        border: none;
    }}
    QPushButton:hover {{ opacity: 0.9; }}
    
    QPushButton#btn_primary {{ background-color: {PRIMARY_COLOR}; color: white; }}
    QPushButton#btn_primary:hover {{ background-color: {HOVER_COLOR}; }}
    
    QPushButton#btn_success {{ background-color: {SUCCESS_COLOR}; color: white; }}
    
    QPushButton#btn_secondary {{ 
        background-color: white; 
        border: 1px solid #cbd5e1; 
        color: {TEXT_COLOR}; 
    }}
    QPushButton#btn_secondary:hover {{ background-color: #f1f5f9; }}

    /* Inputs */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        padding: 8px 12px;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        background-color: white;
        selection-background-color: {PRIMARY_COLOR};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
        border: 1px solid {PRIMARY_COLOR};
    }}

    /* Table Styling */
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

class NumericTableWidgetItem(QTableWidgetItem):
    """Sorts numbers correctly instead of alphabetically."""
    def __lt__(self, other):
        try: return (self.data(Qt.UserRole) or 0) < (other.data(Qt.UserRole) or 0)
        except: return super().__lt__(other)

class ProductFormDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.product = product
        self.is_edit = product is not None
        self.setWindowTitle("Product Details")
        self.setMinimumSize(450, 580)
        self.setStyleSheet(STYLESHEET)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        title = QLabel("Edit Product" if self.is_edit else "New Product")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)

        # Form Container
        form = QFormLayout()
        form.setVerticalSpacing(15)
        form.setHorizontalSpacing(20)
        
        # --- Form Fields ---
        self.name_in = QLineEdit()
        self.name_in.setPlaceholderText("e.g. Potato Chips")
        if self.is_edit: self.name_in.setText(self.product.name)

        self.cat_in = QComboBox()
        self.cat_in.addItems(["Beverages", "Snacks", "Canned Goods", "Toiletries", "Household", "Other"])
        self.cat_in.setEditable(True)
        if self.is_edit: self.cat_in.setCurrentText(self.product.category)
        
        self.price_in = QDoubleSpinBox()
        self.price_in.setRange(0, 100000)
        self.price_in.setPrefix("₱ ")
        if self.is_edit: self.price_in.setValue(self.product.price)
        
        self.stock_in = QSpinBox()
        self.stock_in.setRange(0, 10000)
        if self.is_edit: self.stock_in.setValue(self.product.stock)
        
        self.barcode_in = QLineEdit()
        self.barcode_in.setPlaceholderText("Scan barcode...")
        if self.is_edit: self.barcode_in.setText(getattr(self.product, 'barcode', ''))

        self.active_chk = QCheckBox("Active for Sales")
        self.active_chk.setChecked(True if not self.is_edit else self.product.active)

        self.discount_chk = QCheckBox("Eligible for Discount")
        self.discount_chk.setChecked(True if not self.is_edit else getattr(self.product, 'discount_eligibility', True))

        self.id_in = QLineEdit()
        self.id_in.setPlaceholderText("Auto-generated")
        if self.is_edit: self.id_in.setText(self.product.product_id)
        self.id_in.setEnabled(False)
        self.id_in.setStyleSheet("background-color: #f1f5f9; color: #94a3b8;")

        # Adding Rows with styled labels
        def add_row(label, widget):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: 600; color: #475569;")
            form.addRow(lbl, widget)

        add_row("Name*", self.name_in)
        add_row("Category", self.cat_in)
        add_row("Price", self.price_in)
        add_row("Stock", self.stock_in)
        add_row("Barcode", self.barcode_in)
        form.addRow("", self.active_chk)
        form.addRow("", self.discount_chk)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #e2e8f0;")
        form.addRow(line)
        add_row("System ID", self.id_in)

        layout.addLayout(form)
        
        # Action Buttons
        btns = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.setObjectName("btn_secondary")
        cancel.setCursor(Qt.PointingHandCursor)
        cancel.clicked.connect(self.reject)
        
        save = QPushButton("Save Details")
        save.setObjectName("btn_primary")
        save.setCursor(Qt.PointingHandCursor)
        save.clicked.connect(self.validate_and_save)
        
        btns.addStretch()
        btns.addWidget(cancel)
        btns.addWidget(save)
        layout.addLayout(btns)

    def validate_and_save(self):
        if not self.name_in.text().strip():
            QMessageBox.warning(self, "Required Field", "Please enter a Product Name.")
            self.name_in.setFocus()
            return
        self.accept()

    def get_product(self):
        pid = self.id_in.text() or str(uuid.uuid4().int)[:8]
        return Product(
            product_id=pid,
            name=self.name_in.text().strip(),
            category=self.cat_in.currentText(),
            price=self.price_in.value(),
            stock=self.stock_in.value(),
            active=str(self.active_chk.isChecked()),
            barcode=self.barcode_in.text().strip(),
            discount_eligibility=str(self.discount_chk.isChecked())
        )

class InventoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.products = []
        self.setObjectName("inventory_window")
        self.setStyleSheet(STYLESHEET)
        self.init_ui()
        self.load_inventory()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # --- Top Header ---
        header = QHBoxLayout()
        
        title_block = QVBoxLayout()
        lbl_title = QLabel('Inventory')
        lbl_title.setObjectName("header_title")
        lbl_subtitle = QLabel("Manage your products and stock levels")
        lbl_subtitle.setStyleSheet("color: #64748b; font-size: 14px;")
        title_block.addWidget(lbl_title)
        title_block.addWidget(lbl_subtitle)
        
        header.addLayout(title_block)
        header.addStretch()

        ref = QPushButton("Refresh Data")
        ref.setObjectName("btn_secondary")
        ref.setCursor(Qt.PointingHandCursor)
        ref.clicked.connect(self.load_inventory)
        header.addWidget(ref)
        
        layout.addLayout(header)

        # --- Main Content Card ---
        self.card = QFrame()
        self.card.setObjectName("content_card")
        
        # Add Drop Shadow to Card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # --- Toolbar (Search + Add) ---
        tb = QHBoxLayout()
        
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search products...")
        self.search.setFixedWidth(300)
        self.search.textChanged.connect(self.filter_products)
        
        add = QPushButton("+ Add Product")
        add.setObjectName("btn_success") # Green button
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self.add_product)
        
        tb.addWidget(self.search)
        tb.addStretch()
        tb.addWidget(add)
        card_layout.addLayout(tb)

        # --- Table Setup ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['ID', 'Barcode', 'Name', 'Category', 'Price', 'Stock', 'Actions'])
        
        # Column Sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Barcode
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Price
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Stock
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # Name (Fills space)
        
        # FIX: Increased width for Actions column
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 200) # Increased from 160 to 200

        # Table Styling
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50) # Taller rows
        self.table.setShowGrid(False)
        self.table.setFrameShape(QFrame.NoFrame)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setSortingEnabled(True)
        
        card_layout.addWidget(self.table)
        layout.addWidget(self.card)

    def load_inventory(self):
        try:
            data = CSVHandler.read_csv('products.csv')
            self.products = [Product.from_dict(p) for p in data]
            self.filter_products()
        except Exception as e:
            # Handle empty file or first run gracefully
            print(f"Loading error (might be empty file): {e}")
            self.products = []
            self.filter_products()

    def filter_products(self):
        q = self.search.text().lower()
        if not q:
            filtered = self.products
        else:
            filtered = [p for p in self.products if 
                        q in p.name.lower() or 
                        q in p.product_id.lower() or 
                        q in getattr(p, 'barcode', '').lower()]
        self.populate(filtered)

    def populate(self, prods):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(prods))
        
        for r, p in enumerate(prods):
            # Helper for text items
            def item(text, align=Qt.AlignLeft | Qt.AlignVCenter, color="#1e293b"):
                it = QTableWidgetItem(str(text))
                it.setForeground(QColor(color))
                it.setTextAlignment(align)
                return it

            # ID (Centered, Gray)
            self.table.setItem(r, 0, item(p.product_id, Qt.AlignCenter, "#94a3b8"))
            
            # Barcode
            self.table.setItem(r, 1, item(getattr(p, 'barcode', '')))
            
            # Name
            self.table.setItem(r, 2, item(p.name))
            
            # Category
            self.table.setItem(r, 3, item(p.category, Qt.AlignLeft | Qt.AlignVCenter, "#475569")) 
            
            # Price (Right Align)
            pi = NumericTableWidgetItem(f"₱{p.price:,.2f}")
            pi.setData(Qt.UserRole, p.price)
            pi.setForeground(QColor(PRIMARY_COLOR))
            pi.setFont(QFont("Segoe UI", 9, QFont.Bold))
            pi.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 4, pi)
            
            # Stock (Center Align)
            si = NumericTableWidgetItem(str(p.stock))
            si.setData(Qt.UserRole, p.stock)
            si.setTextAlignment(Qt.AlignCenter)
            if p.stock < 10:
                si.setForeground(QColor(DANGER_COLOR))
                si.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(r, 5, si)
            
            # --- Action Buttons ---
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(8) # Reduced spacing
            l.setAlignment(Qt.AlignCenter)
            
            # Common Button Style (FIX: Reduced padding to 4px 8px)
            btn_style = "background: transparent; font-weight: bold; border: none; padding: 4px 8px;"

            btn_edit = QPushButton("Edit")
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setStyleSheet(f"color: {PRIMARY_COLOR}; {btn_style}")
            btn_edit.clicked.connect(lambda _, x=p: self.edit_product(x))
            
            btn_del = QPushButton("Delete")
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet(f"color: {DANGER_COLOR}; {btn_style}")
            btn_del.clicked.connect(lambda _, x=p: self.delete_product(x))
            
            l.addWidget(btn_edit)
            l.addWidget(QLabel("|", styleSheet="color: #e2e8f0;"))
            l.addWidget(btn_del)
            self.table.setCellWidget(r, 6, w)

        self.table.setSortingEnabled(True)

    def add_product(self):
        d = ProductFormDialog(self)
        if d.exec_() == QDialog.Accepted:
            try:
                CSVHandler.append_csv('products.csv', d.get_product().to_dict())
                self.load_inventory()
                self.show_toast("Success", "Product added.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def edit_product(self, p):
        d = ProductFormDialog(self, p)
        if d.exec_() == QDialog.Accepted:
            try:
                CSVHandler.update_csv('products.csv', 'product_id', p.product_id, d.get_product().to_dict())
                self.load_inventory()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def delete_product(self, p):
        confirm = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to remove '{p.name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            try:
                CSVHandler.delete_row('products.csv', 'product_id', p.product_id)
                self.load_inventory()
            except AttributeError:
                QMessageBox.critical(self, "Error", "CSVHandler is missing 'delete_row' method.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def show_toast(self, title, msg):
        QMessageBox.information(self, title, msg)
        