import csv
import uuid
import os
import shutil
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
                             QComboBox, QDoubleSpinBox, QSpinBox, QCheckBox, QFrame,
                             QScrollArea, QSplitter, QFormLayout, QMenu, QAbstractItemView, 
                             QFileDialog, QSizePolicy, QStyle, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QSize, QTimer, QRegExp
from PyQt5.QtGui import QFont, QIcon, QColor, QRegExpValidator

from csv_handler import CSVHandler
from models import Product

# --- CONFIGURATION (Matches Inventory Window) ---
PRIMARY_COLOR = "#2563eb"  # Blue
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
    QWidget#products_window {{
        background-color: {BG_COLOR};
    }}

    /* Card Styling */
    QFrame[card="true"] {{
        background-color: white;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }}

    /* Labels */
    QLabel {{ font-size: 14px; }}

    /* Buttons */
    QPushButton {{
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        border: none;
    }}
    QPushButton:hover {{ opacity: 0.9; }}

    /* Inputs */
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        padding: 8px 12px;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        background-color: white;
        selection-background-color: {PRIMARY_COLOR};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {PRIMARY_COLOR};
    }}

    /* Table Styling (Matches InventoryWindow) */
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

# --- Helper: Numeric Sorting ---
class NumericTableWidgetItem(QTableWidgetItem):
    """Sorts based on UserRole data (numbers) instead of display text."""
    def __lt__(self, other):
        try:
            return float(self.data(Qt.UserRole) or 0) < float(other.data(Qt.UserRole) or 0)
        except:
            return super().__lt__(other)

# --- Main Window ---
class ProductsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.products = []
        self.setObjectName("products_window")
        self.setStyleSheet(STYLESHEET)
        
        # Performance: Search Timer (Debouncing)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300) 
        self.search_timer.timeout.connect(self.execute_filter)

        self.init_ui()
        self.load_products()
    
    def init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30) # Spacious margins
        layout.setSpacing(20)

        # 1. Controls Section
        controls_widget = self.create_controls_section()
        
        # 2. Table Section
        table_widget = self.create_table_section()
        
        # Add Drop Shadow to Table Card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        table_widget.setGraphicsEffect(shadow)

        layout.addWidget(controls_widget)
        layout.addWidget(table_widget)
    
    def create_controls_section(self):
        widget = QWidget()
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        # Header Row
        header_row = QHBoxLayout()
        header = QLabel('Product Management')
        header.setFont(QFont('Segoe UI', 24, QFont.Bold)) # Larger, bolder title
        header.setStyleSheet("color: #0f172a;")
        
        self.stats_label = QLabel("Loading...")
        self.stats_label.setStyleSheet("color: #64748b; font-size: 14px;")
        
        header_row.addWidget(header)
        header_row.addStretch()
        header_row.addWidget(self.stats_label)
        layout.addLayout(header_row)
        
        # --- Toolbar Row ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search Name, ID, Barcode...')
        self.search_input.setFixedWidth(280)
        self.search_input.textChanged.connect(self.on_search_text_changed)
        
        # Filters
        self.cat_filter = QComboBox()
        self.cat_filter.addItem("All Categories")
        self.cat_filter.setFixedWidth(160)
        self.cat_filter.currentTextChanged.connect(self.execute_filter)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Active", "Inactive", "Low Stock"])
        self.status_filter.setFixedWidth(140)
        self.status_filter.currentTextChanged.connect(self.execute_filter)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.cat_filter)
        toolbar.addWidget(self.status_filter)
        toolbar.addStretch()
        
        # Buttons
        icon_add = self.style().standardIcon(QStyle.SP_FileIcon)
        icon_del = self.style().standardIcon(QStyle.SP_TrashIcon)
        icon_save = self.style().standardIcon(QStyle.SP_DialogSaveButton)

        # Helper to style buttons
        def style_btn(btn, color):
            btn.setStyleSheet(f"background-color: {color}; color: white;")
            btn.setCursor(Qt.PointingHandCursor)

        add_btn = QPushButton(' Add Product')
        add_btn.setIcon(icon_add)
        add_btn.clicked.connect(self.add_product)
        style_btn(add_btn, SUCCESS_COLOR)
        
        self.delete_btn = QPushButton(' Delete')
        self.delete_btn.setIcon(icon_del)
        self.delete_btn.clicked.connect(self.delete_product)
        style_btn(self.delete_btn, DANGER_COLOR)
        
        export_btn = QPushButton(' Export')
        export_btn.setIcon(icon_save)
        export_btn.clicked.connect(self.export_data)
        style_btn(export_btn, "#0f766e") # Teal
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(self.delete_btn)
        toolbar.addWidget(export_btn)
        
        layout.addLayout(toolbar)
        return widget
    
    def create_table_section(self):
        widget = QFrame()
        widget.setProperty("card", "true") # Triggers CSS
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(10)
        self.products_table.setHorizontalHeaderLabels([
            'ID', 'Name', 'Category', 'Price', 'Cost', 'Margin', 'Stock', 
            'Barcode', 'Discount', 'Status'
        ])
        
        # --- Column Sizing (Matches InventoryWindow logic) ---
        header = self.products_table.horizontalHeader()
        
        # Resize To Content (Tight fit)
        for col in [0, 5, 6, 8, 9]:
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        
        # Name stretches to fill space
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        
        # Interactive (User can resize)
        header.setSectionResizeMode(2, QHeaderView.Interactive) # Category
        header.setSectionResizeMode(3, QHeaderView.Interactive) # Price
        header.setSectionResizeMode(4, QHeaderView.Interactive) # Cost
        header.setSectionResizeMode(7, QHeaderView.Interactive) # Barcode
        
        # Default Widths
        self.products_table.setColumnWidth(2, 120)
        self.products_table.setColumnWidth(3, 100)
        self.products_table.setColumnWidth(4, 100)
        self.products_table.setColumnWidth(7, 120)
        
        # --- Table Properties ---
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.verticalHeader().setDefaultSectionSize(50) # Taller rows
        self.products_table.setShowGrid(False) # No Grid
        self.products_table.setFrameShape(QFrame.NoFrame)
        self.products_table.setAlternatingRowColors(False) # White background only
        self.products_table.setFocusPolicy(Qt.NoFocus) # No ugly dotted lines
        
        # Interactions
        self.products_table.setSortingEnabled(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.products_table.doubleClicked.connect(self.edit_selected_product)
        
        # Context Menu
        self.products_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.products_table.customContextMenuRequested.connect(self.open_context_menu)
        
        layout.addWidget(self.products_table)
        return widget
    
    # --- Data Logic ---

    def load_products(self):
        try:
            raw_data = CSVHandler.read_csv('products.csv')
            self.products = [Product.from_dict(p) for p in raw_data]
            
            # Populate Category Filter
            current_cat = self.cat_filter.currentText()
            categories = sorted(list(set(p.category for p in self.products if p.category)))
            self.cat_filter.blockSignals(True)
            self.cat_filter.clear()
            self.cat_filter.addItem("All Categories")
            self.cat_filter.addItems(categories)
            index = self.cat_filter.findText(current_cat)
            if index >= 0:
                self.cat_filter.setCurrentIndex(index)
            self.cat_filter.blockSignals(False)
            
            self.execute_filter()
        except Exception as e:
            print(f"Load info: {e}")
            self.products = []
            self.execute_filter()

    def save_all_products(self):
        temp_file = 'products_temp.csv'
        final_file = 'products.csv'
        
        try:
            data_to_save = []
            for p in self.products:
                data_to_save.append({
                    'product_id': p.product_id,
                    'name': p.name,
                    'category': p.category,
                    'price': str(p.price),
                    'cost': str(getattr(p, 'cost', 0.0)),
                    'stock': str(p.stock),
                    'barcode': getattr(p, 'barcode', ''),
                    'discount_eligibility': str(getattr(p, 'discount_eligibility', True)),
                    'active': str(p.active)
                })
            
            CSVHandler.write_csv(temp_file, data_to_save)
            
            if os.path.exists(final_file):
                os.remove(final_file)
            os.rename(temp_file, final_file)
            
            self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save data safely.\nError: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def on_search_text_changed(self):
        self.search_timer.start()

    def execute_filter(self):
        search_txt = self.search_input.text().lower()
        cat_filter = self.cat_filter.currentText()
        status_filter = self.status_filter.currentText()
        
        filtered = []
        for p in self.products:
            match_search = (search_txt in p.name.lower() or 
                            search_txt in str(p.product_id).lower() or 
                            search_txt in getattr(p, 'barcode', '').lower())
            
            match_cat = (cat_filter == "All Categories" or p.category == cat_filter)
            
            match_status = True
            if status_filter == "Active":
                match_status = p.active
            elif status_filter == "Inactive":
                match_status = not p.active
            elif status_filter == "Low Stock":
                match_status = p.stock < 10
            
            if match_search and match_cat and match_status:
                filtered.append(p)
        
        self.update_table(filtered)
        self.stats_label.setText(f"Showing {len(filtered)} of {len(self.products)} products")

    def update_table(self, products):
        self.products_table.setSortingEnabled(False)
        self.products_table.setRowCount(len(products))
        
        for row, p in enumerate(products):
            # Helper to create formatted items
            def item(text, align=Qt.AlignLeft | Qt.AlignVCenter, color="#1e293b", font_weight=QFont.Normal):
                it = QTableWidgetItem(str(text))
                it.setForeground(QColor(color))
                it.setTextAlignment(align)
                if font_weight != QFont.Normal:
                    it.setFont(QFont("Segoe UI", 9, font_weight))
                return it
            
            # Helper for Numeric items
            def num_item(text, value, color="#1e293b", align=Qt.AlignRight | Qt.AlignVCenter, bold=False):
                it = NumericTableWidgetItem(str(text))
                it.setData(Qt.UserRole, value)
                it.setForeground(QColor(color))
                it.setTextAlignment(align)
                if bold:
                    it.setFont(QFont("Segoe UI", 9, QFont.Bold))
                return it

            # 0. ID (Gray, Center)
            self.products_table.setItem(row, 0, item(p.product_id, Qt.AlignCenter, "#94a3b8"))
            
            # 1. Name (Dark, Left)
            self.products_table.setItem(row, 1, item(p.name))
            
            # 2. Category (Slate, Left)
            self.products_table.setItem(row, 2, item(p.category, color="#475569"))
            
            # 3. Price (Blue, Bold, Right)
            self.products_table.setItem(row, 3, num_item(f"₱{p.price:.2f}", p.price, PRIMARY_COLOR, bold=True))
            
            # 4. Cost (Slate, Right)
            cost = getattr(p, 'cost', 0.0)
            self.products_table.setItem(row, 4, num_item(f"₱{cost:.2f}", cost, "#64748b"))
            
            # 5. Margin (Color Coded, Center)
            margin = 0
            if p.price > 0: margin = ((p.price - cost) / p.price) * 100
            
            m_color = SUCCESS_COLOR if margin >= 20 else ("#ca8a04" if margin >= 0 else DANGER_COLOR)
            self.products_table.setItem(row, 5, num_item(f"{margin:.1f}%", margin, m_color, Qt.AlignCenter, True))
            
            # 6. Stock (Color Coded, Center)
            s_color = DANGER_COLOR if p.stock < 10 else TEXT_COLOR
            self.products_table.setItem(row, 6, num_item(str(p.stock), p.stock, s_color, Qt.AlignCenter, p.stock < 10))
            
            # 7. Barcode (Left)
            self.products_table.setItem(row, 7, item(getattr(p, 'barcode', '')))
            
            # 8. Discount (Center)
            disc = getattr(p, 'discount_eligibility', True)
            self.products_table.setItem(row, 8, item("Yes" if disc else "-", Qt.AlignCenter, SUCCESS_COLOR if disc else "#cbd5e1"))
            
            # 9. Status (Center)
            active = p.active
            self.products_table.setItem(row, 9, item("Active" if active else "Inactive", Qt.AlignCenter, SUCCESS_COLOR if active else "#94a3b8", QFont.Bold))

        self.products_table.setSortingEnabled(True)

    # --- Actions ---

    def add_product(self):
        dialog = ProductDialog(self, all_products=self.products)
        if dialog.exec_() == QDialog.Accepted:
            new_prod = dialog.get_product_object()
            self.products.append(new_prod)
            self.save_all_products()

    def edit_selected_product(self):
        rows = self.products_table.selectionModel().selectedRows()
        if not rows:
            return
        
        row_idx = rows[0].row()
        prod_id = self.products_table.item(row_idx, 0).text()
        
        product = next((p for p in self.products if str(p.product_id) == prod_id), None)
        if product:
            dialog = ProductDialog(self, product=product, all_products=self.products)
            if dialog.exec_() == QDialog.Accepted:
                updated_prod = dialog.get_product_object()
                idx = self.products.index(product)
                self.products[idx] = updated_prod
                self.save_all_products()

    def delete_product(self):
        rows = self.products_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Warning", "Please select a product to delete.")
            return
            
        row_idx = rows[0].row()
        prod_name = self.products_table.item(row_idx, 1).text()
        prod_id = self.products_table.item(row_idx, 0).text()
        
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{prod_name}'?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.products = [p for p in self.products if str(p.product_id) != prod_id]
            self.save_all_products()

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "inventory_export.csv", "CSV Files (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    headers = ['ID', 'Name', 'Category', 'Price', 'Cost', 'Margin %', 'Stock', 'Barcode', 'Status']
                    writer.writerow(headers)
                    for p in self.products:
                        cost = getattr(p, 'cost', 0.0)
                        margin = 0
                        if p.price > 0: 
                            margin = ((p.price - cost) / p.price) * 100
                        writer.writerow([
                            p.product_id, p.name, p.category, 
                            f"{p.price:.2f}", f"{cost:.2f}", f"{margin:.1f}%",
                            p.stock, getattr(p, 'barcode', ''), "Active" if p.active else "Inactive"
                        ])
                QMessageBox.information(self, "Success", "Export successful!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def open_context_menu(self, position):
        menu = QMenu()
        
        icon_edit = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        icon_del = self.style().standardIcon(QStyle.SP_TrashIcon)

        edit_action = menu.addAction(icon_edit, "Edit Product")
        delete_action = menu.addAction(icon_del, "Delete Product")
        action = menu.exec_(self.products_table.viewport().mapToGlobal(position))
        
        if action == edit_action:
            self.edit_selected_product()
        elif action == delete_action:
            self.delete_product()


# --- Add/Edit Dialog ---
class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None, all_products=[]):
        super().__init__(parent)
        self.product = product
        self.all_products = all_products
        self.is_edit = product is not None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('Edit Product' if self.is_edit else 'Add New Product')
        self.setMinimumSize(500, 600)
        self.setStyleSheet("background-color: #f8fafc;")
        
        layout = QVBoxLayout(self)
        
        # Header
        header_lbl = QLabel('Product Details')
        header_lbl.setFont(QFont('Segoe UI', 16, QFont.Bold))
        header_lbl.setStyleSheet("color: #1e293b; padding-bottom: 10px;")
        layout.addWidget(header_lbl)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: white; border-radius: 8px;")
        form_layout = QFormLayout(form_widget)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # Styles
        input_style = "QLineEdit, QSpinBox, QDoubleSpinBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; background: #fff; } QLineEdit:focus { border: 2px solid #3b82f6; }"
        
        # Fields
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(input_style)
        form_layout.addRow('Product Name:', self.name_input)
        
        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        cats = sorted(list(set(p.category for p in self.all_products if p.category)))
        self.category_input.addItems(cats)
        self.category_input.setStyleSheet(input_style)
        form_layout.addRow('Category:', self.category_input)
        
        # --- Pricing Section ---
        price_group = QFrame()
        price_group.setStyleSheet("background-color: #f1f5f9; border-radius: 6px; padding: 10px;")
        price_layout = QFormLayout(price_group)
        
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMaximum(1000000)
        self.cost_input.setPrefix('₱ ')
        self.cost_input.setStyleSheet(input_style)
        self.cost_input.valueChanged.connect(self.calculate_margin)
        price_layout.addRow('Cost (Supplier):', self.cost_input)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(1000000)
        self.price_input.setPrefix('₱ ')
        self.price_input.setStyleSheet(input_style)
        self.price_input.valueChanged.connect(self.calculate_margin)
        price_layout.addRow('Selling Price:', self.price_input)
        
        self.margin_label = QLabel("Profit Margin: 0.0%")
        self.margin_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        price_layout.addRow('', self.margin_label)
        
        form_layout.addRow(price_group)
        
        # --- Inventory Section ---
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(1000000)
        self.stock_input.setStyleSheet(input_style)
        form_layout.addRow('Initial Stock:', self.stock_input)
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan or type (Numbers only)")
        self.barcode_input.setStyleSheet(input_style)
        # VALIDATION: Only allow numbers
        self.barcode_input.setValidator(QRegExpValidator(QRegExp("[0-9]+")))
        form_layout.addRow('Barcode:', self.barcode_input)
        
        # Checkboxes
        self.discount_check = QCheckBox(' Eligible for Discount')
        self.discount_check.setStyleSheet("font-size: 14px;")
        form_layout.addRow('', self.discount_check)
        
        self.active_check = QCheckBox(' Product is Active')
        self.active_check.setChecked(True)
        self.active_check.setStyleSheet("font-size: 14px;")
        form_layout.addRow('', self.active_check)
        
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.validate_and_save)
        buttons.rejected.connect(self.reject)
        
        # Button Styles
        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Save Product")
        ok_btn.setStyleSheet("QPushButton { background-color: #16a34a; color: white; border-radius: 5px; padding: 8px 20px; font-weight: bold; } QPushButton:hover { background-color: #15803d; }")
        
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setStyleSheet("QPushButton { background-color: #94a3b8; color: white; border-radius: 5px; padding: 8px 20px; font-weight: bold; } QPushButton:hover { background-color: #64748b; }")
        
        layout.addWidget(buttons)
        
        # Pre-fill Data
        if self.is_edit:
            self.name_input.setText(self.product.name)
            self.category_input.setCurrentText(self.product.category)
            self.price_input.setValue(self.product.price)
            self.cost_input.setValue(getattr(self.product, 'cost', 0.0))
            self.stock_input.setValue(self.product.stock)
            self.barcode_input.setText(getattr(self.product, 'barcode', ''))
            self.discount_check.setChecked(getattr(self.product, 'discount_eligibility', True))
            self.active_check.setChecked(self.product.active)
            self.calculate_margin()
        else:
            self.barcode_input.setText(str(uuid.uuid4().int)[:13])

    def calculate_margin(self):
        cost = self.cost_input.value()
        price = self.price_input.value()
        if price > 0:
            margin = ((price - cost) / price) * 100
            self.margin_label.setText(f"Profit Margin: {margin:.1f}%")
            if margin < 0:
                self.margin_label.setStyleSheet("color: #dc2626; font-weight: bold;")
            elif margin < 20:
                self.margin_label.setStyleSheet("color: #ca8a04; font-weight: bold;")
            else:
                self.margin_label.setStyleSheet("color: #16a34a; font-weight: bold;")
        else:
            self.margin_label.setText("Profit Margin: 0.0%")
            self.margin_label.setStyleSheet("color: #64748b;")

    def validate_and_save(self):
        # 1. Basic Validation
        if not self.name_input.text().strip():
            QMessageBox.warning(self, 'Error', 'Product name is required.')
            return

        # 2. Duplicate Barcode Check
        new_barcode = self.barcode_input.text().strip()
        current_id = self.product.product_id if self.is_edit else None
        
        if new_barcode:
            for p in self.all_products:
                if getattr(p, 'barcode', '') == new_barcode:
                    if self.is_edit and str(p.product_id) == str(current_id):
                        continue
                    QMessageBox.warning(self, 'Error', f'Barcode "{new_barcode}" is already used by product "{p.name}".')
                    return

        # 3. Price Warning
        if self.price_input.value() < self.cost_input.value():
            confirm = QMessageBox.question(self, "Negative Margin", 
                                         "Selling price is lower than cost. Continue?", 
                                         QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.No:
                return

        self.accept()

    def get_product_object(self):
        """Returns a Product object with the form data"""
        data = {
            'product_id': self.product.product_id if self.is_edit else str(uuid.uuid4().int)[:8],
            'name': self.name_input.text(),
            'category': self.category_input.currentText(),
            'price': self.price_input.value(),
            'cost': self.cost_input.value(),
            'stock': self.stock_input.value(),
            'barcode': self.barcode_input.text(),
            'discount_eligibility': str(self.discount_check.isChecked()),
            'active': str(self.active_check.isChecked())
        }
        return Product.from_dict(data)