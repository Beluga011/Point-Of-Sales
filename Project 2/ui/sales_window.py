from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFrame, QMessageBox, QDialog, QDialogButtonBox,
                             QComboBox, QSpinBox, QSplitter, QSizePolicy, QScrollArea, 
                             QFormLayout, QGridLayout, QShortcut, QGraphicsOpacityEffect,
                             QListWidget, QInputDialog, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QThread, QPropertyAnimation, QPoint, QEasingCurve, QSize
from PyQt5.QtGui import QFont, QColor, QKeySequence, QIcon
from datetime import datetime
import json
import uuid
import os

# Assumed imports from your project structure
from csv_handler import CSVHandler
from models import Product, Sale, SaleItem

# --- Helper Classes ---

class ToastNotification(QLabel):
    """Non-blocking overlay notification"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: #1e293b; 
                color: white; 
                padding: 10px 20px; 
                border-radius: 20px;
                font-family: 'Segoe UI';
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #334155;
            }
        """)
        self.hide()
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

class DataWorker(QThread):
    """Background thread for loading data"""
    data_loaded = pyqtSignal(list, dict)
    
    def run(self):
        try:
            products_data = CSVHandler.read_csv('products.csv')
            products = [Product.from_dict(p) for p in products_data if p.get('active', 'true').lower() == 'true']
            promo_data = CSVHandler.read_promo_codes()
            promos = {}
            for promo in promo_data:
                if promo.get('active', 'True').lower() == 'true':
                    promos[promo['code']] = float(promo['discount_percent'])
            self.data_loaded.emit(products, promos)
        except Exception as e:
            print(f"Background load error: {e}")
            self.data_loaded.emit([], {})

# --- Main Window ---

class SalesWindow(QWidget):
    data_updated = pyqtSignal()
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.cart = []
        self.held_transactions = {} 
        self.products = []
        self.current_page = 0
        self.products_per_page = 10 
        self.promo_codes = {}
        self.tax_rate = 0.12 
        
        self.apply_modern_styles()
        self.setup_ui()
        self.setup_shortcuts()
        self.toast = ToastNotification(self)
        self.loader = DataWorker()
        self.loader.data_loaded.connect(self.on_data_loaded)
        self.refresh_products()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.check_for_updates)
        self.refresh_timer.start(10000) 
        self.data_updated.connect(self.update_real_time_info)

    def apply_modern_styles(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                background-color: #f8fafc; 
                color: #1e293b;
            }
            QFrame[card="true"] {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QLineEdit, QSpinBox {
                padding: 8px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                background-color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus, QSpinBox:focus { border: 1px solid #2563eb; }
            QTableWidget {
                border: none;
                gridline-color: #e2e8f0;
                background-color: white;
                selection-background-color: #eff6ff;
                selection-color: #1e293b;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #475569;
                font-size: 12px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                border-radius: 4px;
            }
            QPushButton { outline: none; }
        """)

    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_F1), self, lambda: self.search_input.setFocus())
        QShortcut(QKeySequence(Qt.Key_F5), self, self.refresh_products)
        QShortcut(QKeySequence(Qt.Key_F12), self, lambda: self.checkout('cash'))
        QShortcut(QKeySequence(Qt.Key_Delete), self, self.remove_selected_item)

    def setup_ui(self):
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(1)
        main_splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")
        
        left_widget = self.create_products_section()
        main_splitter.addWidget(left_widget)
        
        right_widget = self.create_cart_section()
        main_splitter.addWidget(right_widget)
        
        main_splitter.setStretchFactor(0, 65)
        main_splitter.setStretchFactor(1, 35)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(main_splitter)

    # --- Product Section ---

    def create_products_section(self):
        widget = QFrame()
        widget.setProperty("card", "true")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QHBoxLayout()
        title = QLabel('Product Catalog')
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setStyleSheet("color: #1e293b;")
        header.addWidget(title)
        
        self.stats_label = QLabel('Ready')
        self.stats_label.setStyleSheet("color: #64748b; font-weight: 500;")
        header.addStretch()
        header.addWidget(self.stats_label)
        layout.addLayout(header)
        
        # Search Bar
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        
        search_icon = QPushButton()
        search_icon.setIcon(QIcon.fromTheme("edit-find"))
        search_icon.setFixedSize(30, 36)
        search_icon.setStyleSheet("""
            QPushButton { 
                background-color: #f1f5f9; 
                border: 1px solid #cbd5e1; 
                border-right: none;
                border-top-left-radius: 4px; 
                border-bottom-left-radius: 4px;
                color: #64748b; 
                border-left: 1px solid #cbd5e1;
            }
        """)
        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Scan barcode or search (F1)...')
        self.search_input.textChanged.connect(self.filter_products_local) 
        self.search_input.returnPressed.connect(self.add_top_result)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit { 
                padding: 5px; 
                border: 1px solid #cbd5e1; 
                border-radius: 0px;
                border-left: none; 
                border-right: none; 
            }
            QLineEdit:focus { border: 1px solid #2563eb; border-left: none; border-right: none; }
        """)
        search_layout.addWidget(self.search_input)
        
        self.clear_search_btn = QPushButton("✕")
        self.clear_search_btn.setFixedSize(30, 36)
        self.clear_search_btn.setToolTip("Clear Search")
        self.clear_search_btn.clicked.connect(lambda: self.search_input.clear())
        self.clear_search_btn.setCursor(Qt.PointingHandCursor)
        self.clear_search_btn.setStyleSheet("""
            QPushButton { 
                background-color: #f1f5f9; 
                border: 1px solid #cbd5e1; 
                border-left: none;
                border-top-right-radius: 4px; 
                border-bottom-right-radius: 4px;
                color: #94a3b8;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #fee2e2; 
                color: #dc2626; 
                border-color: #cbd5e1;
            }
        """)
        search_layout.addWidget(self.clear_search_btn)
        layout.addWidget(search_container)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels(['Name', 'Category', 'Price', 'Stock', 'Action'])
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setFocusPolicy(Qt.NoFocus)
        self.products_table.setShowGrid(False)
        self.products_table.setAlternatingRowColors(True)
        layout.addWidget(self.products_table)
        
        layout.addWidget(self.create_pagination_controls())
        return widget

    def create_pagination_controls(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        
        btn_style = """
            QPushButton { 
                background-color: #f1f5f9; 
                color: #334155; 
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #e2e8f0; }
            QPushButton:disabled { color: #94a3b8; background-color: #f8fafc; }
        """
        
        self.prev_btn = QPushButton('Previous')
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setStyleSheet(btn_style)
        
        self.next_btn = QPushButton('Next')
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setStyleSheet(btn_style)
        
        self.page_info = QLabel('Page 1')
        self.page_info.setStyleSheet("color: #64748b; font-weight: bold;")
        self.page_info.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.page_info, 1)
        layout.addWidget(self.next_btn)
        return widget

    # --- Cart Section ---

    def create_cart_section(self):
        widget = QFrame()
        widget.setProperty("card", "true")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f8fafc; border-bottom: 1px solid #e2e8f0; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        cart_title = QLabel('Current Order')
        cart_title.setFont(QFont('Segoe UI', 14, QFont.Bold))
        cart_title.setStyleSheet("color: #1e293b;")
        
        self.recall_btn = QPushButton('Recall Hold')
        self.recall_btn.setFlat(True)
        self.recall_btn.setCursor(Qt.PointingHandCursor)
        self.recall_btn.setStyleSheet("color: #2563eb; font-weight: bold; text-align: right; border: none;")
        self.recall_btn.clicked.connect(self.recall_transaction_dialog)
        
        header_layout.addWidget(cart_title)
        header_layout.addStretch()
        header_layout.addWidget(self.recall_btn)
        layout.addWidget(header_frame)
        
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(['Item', 'Qty', 'Total', ''])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setShowGrid(False)
        self.cart_table.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self.cart_table, 1)
        
        summary_widget = QWidget()
        summary_widget.setStyleSheet("background-color: #ffffff; border-top: 1px solid #e2e8f0;")
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(20, 15, 20, 20)
        summary_layout.setSpacing(10)
        
        promo_layout = QHBoxLayout()
        self.discount_input = QSpinBox()
        self.discount_input.setRange(0, 100)
        self.discount_input.setSuffix('% Off')
        self.discount_input.setFixedWidth(100)
        self.discount_input.valueChanged.connect(self.update_totals)
        
        self.promo_input = QLineEdit()
        self.promo_input.setPlaceholderText('Promo Code')
        self.promo_input.textChanged.connect(self.apply_promo_code)
        
        promo_layout.addWidget(self.discount_input)
        promo_layout.addWidget(self.promo_input)
        summary_layout.addLayout(promo_layout)
        
        self.subtotal_label = QLabel('Subtotal: ₱0.00')
        self.subtotal_label.setAlignment(Qt.AlignRight)
        
        self.total_label = QLabel('₱0.00')
        self.total_label.setAlignment(Qt.AlignRight)
        self.total_label.setFont(QFont('Segoe UI', 24, QFont.Bold))
        self.total_label.setStyleSheet("color: #16a34a;")
        
        summary_layout.addWidget(self.subtotal_label)
        summary_layout.addWidget(self.total_label)
        
        layout.addWidget(summary_widget)
        layout.addWidget(self.create_checkout_buttons())
        return widget

    def create_checkout_buttons(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: #f8fafc; padding: 10px;")
        layout = QGridLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 0, 10, 10)
        
        def btn_style(bg_color, border_color, text_color="white"):
            return f"""
                QPushButton {{
                    background-color: {bg_color};
                    border-bottom: 3px solid {border_color};
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                    color: {text_color};
                    border-left: none;
                    border-right: none;
                    border-top: none;
                }}
                QPushButton:hover {{
                    opacity: 0.9;
                    background-color: {bg_color};
                }}
                QPushButton:pressed {{
                    border-bottom: none;
                    margin-top: 3px;
                }}
            """
        
        self.cash_btn = QPushButton('💵 CASH')
        self.cash_btn.setMinimumHeight(55)
        self.cash_btn.setStyleSheet(btn_style("#16a34a", "#15803d"))
        self.cash_btn.clicked.connect(lambda: self.checkout('cash'))
        
        self.card_btn = QPushButton('💳 CARD')
        self.card_btn.setMinimumHeight(55)
        self.card_btn.setStyleSheet(btn_style("#2563eb", "#1d4ed8"))
        self.card_btn.clicked.connect(lambda: self.checkout('card'))
        
        self.gcash_btn = QPushButton('📱 GCASH')
        self.gcash_btn.setMinimumHeight(55)
        self.gcash_btn.setStyleSheet(btn_style("#0f766e", "#0d9488"))
        self.gcash_btn.clicked.connect(lambda: self.checkout('gcash'))
        
        self.maya_btn = QPushButton('MAYA')
        self.maya_btn.setMinimumHeight(55)
        self.maya_btn.setStyleSheet(btn_style("#000000", "#22c55e"))
        self.maya_btn.clicked.connect(lambda: self.checkout('maya'))
        
        self.hold_btn = QPushButton('⏸ HOLD')
        self.hold_btn.setFixedHeight(40)
        self.hold_btn.setStyleSheet(btn_style("#d97706", "#b45309")) 
        self.hold_btn.clicked.connect(self.hold_transaction)
        
        self.clear_btn = QPushButton('🗑 CLEAR')
        self.clear_btn.setFixedHeight(40)
        self.clear_btn.setStyleSheet(btn_style("#dc2626", "#b91c1c"))
        self.clear_btn.clicked.connect(self.clear_cart)

        layout.addWidget(self.cash_btn, 0, 0, 1, 2)
        layout.addWidget(self.card_btn, 1, 0)
        layout.addWidget(self.gcash_btn, 1, 1)
        layout.addWidget(self.maya_btn, 2, 0, 1, 2)
        layout.addWidget(self.hold_btn, 3, 0)
        layout.addWidget(self.clear_btn, 3, 1)
        
        return widget

    # --- Data Handling ---

    def refresh_products(self):
        self.loader.start()
        
    def check_for_updates(self):
        self.refresh_products()

    def on_data_loaded(self, products, promos):
        self.products = products
        self.promo_codes = promos
        self.update_products_table()
        self.update_stats()

    def update_stats(self):
        low_stock = sum(1 for p in self.products if p.stock < 10)
        self.stats_label.setText(f"{len(self.products)} Products | {low_stock} Low Stock")

    def filter_products_local(self):
        query = self.search_input.text().lower().strip()
        self.current_page = 0
        self.update_products_table(filter_query=query)

    def add_top_result(self):
        query = self.search_input.text().lower().strip()
        if not query: return
        exact_match = next((p for p in self.products if p.barcode.lower() == query or p.product_id.lower() == query), None)
        if exact_match:
            self.add_product_to_cart(exact_match)
            self.search_input.clear()
            self.toast.show_message(f"Added {exact_match.name}")

    def update_products_table(self, filter_query=None):
        if filter_query:
            filtered_list = [p for p in self.products if filter_query in p.name.lower() or filter_query in p.barcode.lower()]
        else:
            filtered_list = self.products

        total_pages = max(1, (len(filtered_list) + self.products_per_page - 1) // self.products_per_page)
        self.current_page = min(self.current_page, total_pages - 1)
        
        start_idx = self.current_page * self.products_per_page
        end_idx = start_idx + self.products_per_page
        page_products = filtered_list[start_idx:end_idx]
        
        self.page_info.setText(f"Page {self.current_page + 1}/{total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

        self.products_table.setRowCount(len(page_products))
        
        for row, product in enumerate(page_products):
            name_item = QTableWidgetItem(product.name)
            name_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.products_table.setItem(row, 0, name_item)
            
            cat_item = QTableWidgetItem(product.category)
            cat_item.setTextAlignment(Qt.AlignCenter)
            cat_item.setFlags(Qt.ItemIsEnabled)
            self.products_table.setItem(row, 1, cat_item)
            
            price_item = QTableWidgetItem(f"₱{product.price:.2f}")
            price_item.setFont(QFont('Segoe UI', 10, QFont.Bold))
            price_item.setForeground(QColor("#16a34a"))
            self.products_table.setItem(row, 2, price_item)
            
            stock_widget = QLabel(str(product.stock))
            stock_widget.setAlignment(Qt.AlignCenter)
            if product.stock == 0:
                stock_widget.setStyleSheet("background-color: #fee2e2; color: #dc2626; border-radius: 4px; padding: 2px;")
                stock_widget.setText("OUT")
            elif product.stock < 10:
                stock_widget.setStyleSheet("background-color: #fef3c7; color: #d97706; border-radius: 4px; padding: 2px;")
            self.products_table.setCellWidget(row, 3, stock_widget)
            
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 2, 0, 2)
            add_btn = QPushButton("Add")
            add_btn.setCursor(Qt.PointingHandCursor)
            add_btn.setStyleSheet("""
                QPushButton { background-color: #2563eb; color: white; border-radius: 4px; padding: 4px; font-size: 11px; font-weight: bold;}
                QPushButton:hover { background-color: #1d4ed8; }
            """)
            add_btn.clicked.connect(lambda checked, p=product: self.add_product_to_cart(p))
            if product.stock <= 0: add_btn.setEnabled(False)
            
            btn_layout.addWidget(add_btn)
            self.products_table.setCellWidget(row, 4, btn_widget)
            self.products_table.setRowHeight(row, 50) 

    def update_cart_table(self):
        self.cart_table.setRowCount(len(self.cart))
        for row, item in enumerate(self.cart):
            name_item = QTableWidgetItem(item.name)
            name_item.setFont(QFont('Segoe UI', 11))
            self.cart_table.setItem(row, 0, name_item)
            
            spin = QSpinBox()
            spin.setRange(1, 999)
            spin.setValue(item.quantity)
            spin.setFixedWidth(60)
            spin.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 4px;")
            spin.valueChanged.connect(lambda val, r=row: self.update_quantity(r, val))
            self.cart_table.setCellWidget(row, 1, spin)
            
            total = item.price * item.quantity
            total_item = QTableWidgetItem(f"₱{total:.2f}")
            total_item.setFont(QFont('Segoe UI', 11, QFont.Bold))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.cart_table.setItem(row, 2, total_item)
            
            rem_btn = QPushButton("×")
            rem_btn.setFixedSize(24, 24)
            rem_btn.setCursor(Qt.PointingHandCursor)
            rem_btn.setStyleSheet("background-color: transparent; color: #ef4444; font-size: 18px; font-weight: bold; border: none;")
            rem_btn.clicked.connect(lambda checked, r=row: self.remove_from_cart(r))
            self.cart_table.setCellWidget(row, 3, rem_btn)
            self.cart_table.setRowHeight(row, 45)
        self.update_totals()

    # --- Cart Logic ---

    def add_product_to_cart(self, product):
        if product.stock <= 0:
            self.toast.show_message("Out of Stock!")
            return
        for item in self.cart:
            if item.product_id == product.product_id:
                if item.quantity + 1 > product.stock:
                    self.toast.show_message("Max Stock Reached")
                    return
                item.quantity += 1
                self.update_cart_table()
                self.toast.show_message(f"Updated {product.name} (+1)")
                return
        new_item = SaleItem(
            product_id=product.product_id,
            name=product.name,
            quantity=1,
            price=product.price,
            tax_rate=self.tax_rate
        )
        self.cart.append(new_item)
        self.update_cart_table()
        self.toast.show_message(f"Added {product.name}")

    def update_quantity(self, row, qty):
        if 0 <= row < len(self.cart):
            item = self.cart[row]
            item.quantity = qty
            self.cart_table.item(row, 2).setText(f"₱{item.price * item.quantity:.2f}")
            self.update_totals()

    def remove_from_cart(self, row):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self.update_cart_table()

    def remove_selected_item(self):
        row = self.cart_table.currentRow()
        if row >= 0:
            self.remove_from_cart(row)

    def update_totals(self):
        subtotal = sum(item.price * item.quantity for item in self.cart)
        discount_percent = self.discount_input.value()
        discount_amt = subtotal * (discount_percent / 100)
        total = subtotal - discount_amt
        self.subtotal_label.setText(f"Subtotal: ₱{subtotal:.2f}")
        self.total_label.setText(f"₱{total:.2f}")

    def apply_promo_code(self):
        code = self.promo_input.text().strip()
        if code in self.promo_codes:
            self.discount_input.setValue(int(self.promo_codes[code]))
            self.toast.show_message(f"Promo '{code}' Applied!")

    # --- Transaction Management ---

    def hold_transaction(self):
        if not self.cart: return
        hold_id = datetime.now().strftime("%H:%M:%S")
        self.held_transactions[hold_id] = self.cart.copy()
        self.cart.clear()
        self.update_cart_table()
        self.discount_input.setValue(0)
        self.toast.show_message(f"Transaction Held ({hold_id})")

    def recall_transaction_dialog(self):
        if not self.held_transactions:
            self.toast.show_message("No held transactions")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Recall Transaction")
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        for hold_id, items in self.held_transactions.items():
            total = sum(i.price * i.quantity for i in items)
            list_widget.addItem(f"Time: {hold_id} - {len(items)} Items - ₱{total:.2f}")
        layout.addWidget(list_widget)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        if dialog.exec_() == QDialog.Accepted:
            selected = list_widget.currentRow()
            if selected >= 0:
                hold_id = list(self.held_transactions.keys())[selected]
                if self.cart:
                    resp = QMessageBox.question(self, "Overwrite?", "Current cart is not empty. Overwrite?")
                    if resp == QMessageBox.No: return
                self.cart = self.held_transactions.pop(hold_id)
                self.update_cart_table()
                self.toast.show_message("Transaction Recalled")

    def clear_cart(self):
        if not self.cart: return
        if QMessageBox.question(self, "Confirm", "Clear entire cart?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.cart.clear()
            self.update_cart_table()
            self.discount_input.setValue(0)

    def checkout(self, payment_method):
        if not self.cart:
            self.toast.show_message("Cart is empty!")
            return
        for item in self.cart:
            product = next((p for p in self.products if p.product_id == item.product_id), None)
            if not product:
                QMessageBox.warning(self, 'Product Not Found', f'{item.name} is no longer available')
                return
            if product.stock < item.quantity:
                QMessageBox.warning(self, 'Insufficient Stock', f'Not enough stock for {item.name}')
                return
        
        # Parse total carefully
        total_str = self.total_label.text().replace('₱', '').replace(',', '')
        total_amount = float(total_str)
        
        if payment_method == 'cash':
            amount, ok = QInputDialog.getDouble(self, "Cash Payment", f"Total: ₱{total_amount:.2f}\nEnter Cash:", 0, 0, 100000, 2)
            if not ok: return
            if amount < total_amount:
                QMessageBox.warning(self, "Error", "Insufficient Cash")
                return
            change = amount - total_amount
            QMessageBox.information(self, "Success", f"Change: ₱{change:.2f}")
        elif payment_method in ['gcash', 'maya']:
            QMessageBox.information(self, f"{payment_method.upper()} Payment", f"Waiting for {payment_method.upper()} confirmation...\n(Simulated Success)")

        sale_obj = self.record_sale(payment_method, total_amount)
        self.show_receipt(sale_obj, payment_method)
        self.cart.clear()
        self.update_cart_table()
        self.discount_input.setValue(0)
        self.toast.show_message("Transaction Complete!")
        self.data_updated.emit() 

    def record_sale(self, payment_method, total):
        sale_id = self.generate_sale_id()
        now = datetime.now()
        subtotal = sum(item.price * item.quantity for item in self.cart)
        discount_val = subtotal - total
        sale = Sale(
            sale_id=sale_id,
            date=now.strftime('%Y-%m-%d'),
            time=now.strftime('%H:%M:%S'),
            items=self.cart.copy(),
            total=total,
            tax=sum(item.tax_amount for item in self.cart),
            discount=discount_val,
            payment_method=payment_method,
            cashier_id=self.current_user.user_id
        )
        try:
            CSVHandler.append_csv('sales.csv', sale.to_dict())
            products_list = CSVHandler.read_csv('products.csv')
            for item in self.cart:
                for p_data in products_list:
                    if p_data['product_id'] == item.product_id:
                        curr = int(p_data.get('stock', 0))
                        new_stock = max(0, curr - item.quantity)
                        CSVHandler.update_csv('products.csv', 'product_id', item.product_id, {'stock': str(new_stock)})
                        break
            return sale
        except Exception as e:
            print(f"Error saving sale: {e}")
            return sale

    def generate_sale_id(self):
        try:
            sales = CSVHandler.read_csv('sales.csv')
            return str(len(sales) + 1)
        except:
            return "1"

    def show_receipt(self, sale, payment_method):
        receipt = ReceiptDialog(sale, payment_method, self.current_user, self)
        receipt.exec_()
    
    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_products_table(self.search_input.text().lower())

    def next_page(self):
        self.current_page += 1
        self.update_products_table(self.search_input.text().lower())
        
    def update_real_time_info(self):
        self.refresh_products()

# --- Receipt Dialog (Redesigned) ---

class ReceiptDialog(QDialog):
    def __init__(self, sale, payment_method, current_user, parent=None):
        super().__init__(parent)
        self.sale = sale
        self.payment_method = payment_method
        self.current_user = current_user
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('Receipt')
        self.setFixedSize(380, 650)
        self.setStyleSheet("background-color: #f3f3f3;") # Light grey surroundings
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Paper visual container
        paper_widget = QWidget()
        paper_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 0px; 
            }
        """)
        paper_layout = QVBoxLayout(paper_widget)
        paper_layout.setContentsMargins(5, 5, 5, 5)
        
        # Receipt Text
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        # Font: Monospace essential for alignment
        font = QFont("Courier New", 9)
        font.setStyleHint(QFont.Monospace)
        self.preview.setFont(font)
        self.preview.setFrameStyle(QFrame.NoFrame)
        self.preview.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.preview.setText(self.generate_receipt_text())
        
        paper_layout.addWidget(self.preview)
        layout.addWidget(paper_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        print_btn = QPushButton('Print / Save')
        print_btn.clicked.connect(self.print_receipt)
        print_btn.setStyleSheet("background-color: #10b981; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background-color: #ef4444; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        
        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        
    def generate_receipt_text(self):
        width = 40 # Approx width for 58mm/80mm thermal printers
        
        def center_line(text):
            return text.center(width) + "\n"
        
        def line_sep():
            return ("-" * width) + "\n"
            
        def double_sep():
            return ("=" * width) + "\n"
            
        def format_lr(label, value):
            """Format Left-Right aligned text"""
            val_str = f"{value:.2f}"
            padding = width - len(label) - len(val_str)
            if padding < 1: padding = 1
            return f"{label}{' ' * padding}{val_str}\n"

        # --- Header ---
        txt =  center_line("BBC INC.")
        txt += center_line("123 Sitio Mayapyap")
        txt += center_line("Rosario, Batangas")
        txt += center_line("VAT REG TIN: 000-123-456-000")
        txt += line_sep()
        
        # --- Transaction Info ---
        txt += f"OR #: {self.sale.sale_id}\n"
        txt += f"Date: {self.sale.date} {self.sale.time}\n"
        txt += f"Cashier: {self.current_user.username}\n"
        txt += line_sep()
        
        # --- Items ---
        # Format: 
        # Item Name
        #   Qty @ Price          Total
        for item in self.sale.items:
            # Truncate name if too long for one line, or let it wrap
            txt += f"{item.name[:width]}\n" 
            
            qty_price = f"   {item.quantity} @ {item.price:.2f}"
            total_val = item.quantity * item.price
            total_str = f"{total_val:.2f}"
            
            pad = width - len(qty_price) - len(total_str)
            if pad < 1: pad = 1
            txt += f"{qty_price}{' ' * pad}{total_str}\n"
            
        txt += line_sep()
        
        # --- Totals & VAT ---
        # Standard PH Retail: Prices are VAT Inclusive
        total_due = self.sale.total
        vatable_sales = total_due / 1.12
        vat_amount = total_due - vatable_sales
        
        txt += format_lr("Total Sales", total_due)
        txt += format_lr("Less: VAT", 0.00) # Usually shown 0 if prices are inclusive
        txt += format_lr("AMOUNT DUE", total_due)
        txt += double_sep()
        
        # --- Payment ---
        txt += f"Payment: {self.payment_method.upper()}\n"
        # Note: 'Cash Tendered' & 'Change' ideally passed here. 
        # Using placeholder or just total for now.
        txt += line_sep()
        
        # --- VAT Breakdown Table ---
        txt += "VAT ANALYSIS\n"
        txt += format_lr("Vatable Sales", vatable_sales)
        txt += format_lr("VAT Amount", vat_amount)
        txt += format_lr("VAT Exempt", 0.00)
        txt += format_lr("Zero Rated", 0.00)
        txt += line_sep()
        
        # --- Footer Fields ---
        txt += "Sold to: ___________________________\n"
        txt += "Address: ___________________________\n"
        txt += "TIN: _______________________________\n"
        txt += "Bus. Style: ________________________\n"
        txt += line_sep()
        
        # --- Disclaimer ---
        txt += center_line("THIS DOCUMENT IS NOT VALID FOR")
        txt += center_line("CLAIM OF INPUT TAX")
        txt += center_line("THIS SERVES AS YOUR OFFICIAL RECEIPT")
        txt += double_sep()
        txt += center_line("Thank you! Please come again.")
        
        return txt

    def print_receipt(self):
        filename = f"receipt_{self.sale.sale_id}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.generate_receipt_text())
            QMessageBox.information(self, 'Printed', f'Receipt saved to {filename}')
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))