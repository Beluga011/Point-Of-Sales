import sys
import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox, QDialog, QFrame, 
                             QDateEdit, QComboBox, QGraphicsDropShadowEffect,
                             QScrollArea, QGridLayout, QProgressBar, QSizePolicy)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal, QSize, QPointF
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QBrush, QLinearGradient

# --- STYLING CONSTANTS ---
PRIMARY = "#2563eb"
SECONDARY = "#64748b"
BG_COLOR = "#f8fafc"
CARD_BG = "#ffffff"
SUCCESS = "#16a34a"
DANGER = "#dc2626"
CHART_LINE = "#3b82f6"
CHART_FILL = "#dbeafe"
TEXT_COLOR = "#1e293b"

STYLESHEET = f"""
    QWidget {{ font-family: 'Segoe UI', sans-serif; color: #1e293b; }}
    QWidget#reports_window {{ background-color: {BG_COLOR}; }}
    QFrame[card="true"] {{
        background-color: {CARD_BG};
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }}
    QLabel[heading="true"] {{ font-size: 18px; font-weight: bold; color: #0f172a; }}
    QLabel[subheading="true"] {{ font-size: 12px; color: {SECONDARY}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
    QPushButton {{
        padding: 6px 12px; border-radius: 5px; font-weight: 600; border: none;
    }}
    QTableWidget {{ border: none; gridline-color: #f1f5f9; }}
    QHeaderView::section {{ background-color: #f8fafc; border: none; font-weight: bold; padding: 6px; }}
"""

# --- SIMPLE SALE CLASS (with corrected column mapping) ---
class SimpleSale:
    def __init__(self, sale_id, date, time, items_data, total, tax, discount, payment_method, cashier_id):
        self.sale_id = sale_id
        self.date = date
        self.time = time
        
        # Parse items_data from JSON string
        try:
            self.items = json.loads(items_data) if items_data else []
        except (json.JSONDecodeError, TypeError):
            self.items = []
        
        # Parse numeric fields with error handling
        try:
            self.total = float(total) if total else 0.0
        except (ValueError, TypeError):
            self.total = 0.0
            
        try:
            self.tax = float(tax) if tax else 0.0
        except (ValueError, TypeError):
            self.tax = 0.0
            
        try:
            self.discount = float(discount) if discount else 0.0
        except (ValueError, TypeError):
            self.discount = 0.0
            
        self.payment_method = payment_method
        self.cashier_id = cashier_id
        
        # Combine date and time for full timestamp
        self.full_date = f"{date} {time}" if date and time else date

    @classmethod
    def from_dict(cls, data):
        # Debug: print what we're receiving
        print(f"DEBUG: Raw data keys: {list(data.keys())}")
        
        # Try to map columns correctly based on the actual CSV structure
        # From your debug output, it seems the columns are mismatched
        return cls(
            sale_id=data.get('sale_id', ''),
            date=data.get('date', ''),
            time=data.get('time', ''),
            items_data=data.get('total', '[]'),  # items_data seems to be in the 'total' column
            total=data.get('tax', 0.0),          # total seems to be in the 'tax' column  
            tax=data.get('discount', 0.0),       # tax seems to be in the 'discount' column
            discount=data.get('payment_method', 0.0),  # discount seems to be in 'payment_method'
            payment_method=data.get('cashier_id', ''), # payment_method seems to be in 'cashier_id'
            cashier_id=data.get('items_data', '')      # cashier_id seems to be in 'items_data'
        )

# --- SIMPLE CSV HANDLER ---
class SimpleCSVHandler:
    @staticmethod
    def read_csv(filename):
        try:
            with open(filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                data = list(reader)
                
                # Debug: print first record to understand structure
                if data:
                    first_record = data[0]
                    print(f"DEBUG: First record structure:")
                    for key, value in first_record.items():
                        print(f"  {key}: {value[:100]}{'...' if len(str(value)) > 100 else ''}")
                
                return data
        except FileNotFoundError:
            print(f"DEBUG: File {filename} not found")
            return []
        except Exception as e:
            print(f"DEBUG: Error reading CSV: {e}")
            return []

# --- WORKER THREAD (Prevents UI Freezing) ---
class ReportLoaderThread(QThread):
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            raw_data = SimpleCSVHandler.read_csv('sales.csv')
            print(f"DEBUG: Loaded {len(raw_data)} raw records from CSV")
            
            sales = []
            for record in raw_data:
                try:
                    sale = SimpleSale.from_dict(record)
                    sales.append(sale)
                    print(f"DEBUG: Processed sale {sale.sale_id}: total={sale.total}, items={len(sale.items)}")
                except Exception as e:
                    print(f"DEBUG: Error processing record: {e}")
                    continue
            
            # Sort by date descending
            sales.sort(key=lambda x: self.parse_date(x.full_date or x.date), reverse=True)
            print(f"DEBUG: Processed {len(sales)} sales records")
            
            self.data_loaded.emit(sales)
        except FileNotFoundError:
            print("DEBUG: sales.csv file not found")
            self.data_loaded.emit([])
        except Exception as e:
            print(f"DEBUG: Error in ReportLoaderThread: {e}")
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
    
    def parse_date(self, date_str):
        """Parse date string that could be either with or without time"""
        try:
            # Try format with time first
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Try format without time
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                # If both fail, return current date as fallback
                print(f"DEBUG: Could not parse date: {date_str}")
                return datetime.now()

# --- CUSTOM WIDGET: KPI CARD ---
class KPICard(QFrame):
    def __init__(self, title, icon_char="₱"):
        super().__init__()
        self.setProperty("card", "true")
        self.setFixedSize(200, 100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {SECONDARY}; font-size: 13px; font-weight: 600;")
        
        self.value_lbl = QLabel("...")
        self.value_lbl.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.value_lbl.setStyleSheet(f"color: {PRIMARY};")
        
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)

    def set_value(self, text):
        self.value_lbl.setText(text)

# --- CUSTOM WIDGET: TREND CHART ---
class TrendChart(QWidget):
    def __init__(self):
        super().__init__()
        self.data_points = [] # List of (date_str, amount)
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_data(self, data):
        # Data should be a dict {date: total}
        self.data_points = sorted(data.items()) # Sort by date
        print(f"DEBUG: TrendChart received {len(self.data_points)} data points")
        self.update() # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        padding = 30
        
        # Background
        painter.fillRect(self.rect(), QColor(CARD_BG))
        
        if not self.data_points:
            painter.setPen(QColor(SECONDARY))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data Available for Range")
            return

        # Scales
        dates = [d[0] for d in self.data_points]
        values = [d[1] for d in self.data_points]
        max_val = max(values) if values else 100
        
        # Avoid division by zero
        if max_val == 0:
            max_val = 1
        
        # Draw Grid & Y-Axis
        painter.setPen(QPen(QColor("#f1f5f9"), 1, Qt.SolidLine))
        steps = 4
        for i in range(steps + 1):
            y = h - padding - (i * (h - 2 * padding) / steps)
            painter.drawLine(padding, int(y), w - padding, int(y))
            
            # Label
            val_label = f"{int(max_val * (i/steps))}"
            painter.setPen(QColor(SECONDARY))
            painter.drawText(0, int(y) - 5, padding - 5, 10, Qt.AlignRight, val_label)
            painter.setPen(QPen(QColor("#f1f5f9"), 1, Qt.SolidLine)) # Reset pen

        # Draw Line
        if len(self.data_points) > 1:
            path_points = []
            x_step = (w - 2 * padding) / (len(self.data_points) - 1)
            
            for i, val in enumerate(values):
                x = padding + (i * x_step)
                # Invert Y (0 is top)
                y = h - padding - ((val / max_val) * (h - 2 * padding))
                path_points.append(QPointF(x, y))
            
            # Draw Thick Line
            pen = QPen(QColor(CHART_LINE))
            pen.setWidth(3)
            painter.setPen(pen)
            for i in range(len(path_points) - 1):
                painter.drawLine(path_points[i], path_points[i+1])
                
            # Draw Dots
            painter.setBrush(QBrush(QColor(PRIMARY)))
            painter.setPen(Qt.NoPen)
            for p in path_points:
                painter.drawEllipse(p, 4, 4)

# --- CUSTOM WIDGET: CATEGORY BAR CHART ---
class CategoryChart(QWidget):
    def __init__(self):
        super().__init__()
        self.categories = [] # List of (name, total)
        self.setMinimumHeight(200)

    def set_data(self, data_dict):
        # Sort by value desc and take top 5
        self.categories = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"DEBUG: CategoryChart received {len(self.categories)} categories")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        
        if not self.categories:
            painter.setPen(QColor(SECONDARY))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Category Data")
            return

        max_val = self.categories[0][1] if self.categories else 1
        
        # Fix: Avoid division by zero
        if max_val == 0:
            max_val = 1
        
        bar_height = 25
        spacing = 15
        start_y = 10
        
        label_width = 100
        chart_width = w - label_width - 50
        
        for i, (cat, val) in enumerate(self.categories):
            y = start_y + i * (bar_height + spacing)
            
            # Draw Label
            painter.setPen(QColor(TEXT_COLOR))
            painter.drawText(0, y, label_width, bar_height, Qt.AlignRight | Qt.AlignVCenter, cat)
            
            # Draw Bar Background
            painter.setBrush(QBrush(QColor("#f1f5f9")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(label_width + 10, y, chart_width, bar_height, 4, 4)
            
            # Draw Fill Bar - Fix: prevent division by zero
            bar_w = (val / max_val) * chart_width if max_val > 0 else 0
            painter.setBrush(QBrush(QColor(SUCCESS))) # Green bars
            painter.drawRoundedRect(label_width + 10, y, int(bar_w), bar_height, 4, 4)
            
            # Draw Value
            painter.setPen(QColor(SECONDARY))
            value_text = f"₱{val/1000:.1f}k" if val >= 1000 else f"₱{val:.0f}"
            painter.drawText(int(label_width + 10 + bar_w + 5), y, 50, bar_height, Qt.AlignLeft | Qt.AlignVCenter, value_text)

# --- MAIN WINDOW ---
class ReportsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("reports_window")
        self.setStyleSheet(STYLESHEET)
        self.all_sales = []
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # 1. Header & Toolbar
        header = QHBoxLayout()
        
        title_block = QVBoxLayout()
        title = QLabel("Sales Analytics")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        subtitle = QLabel("Overview of financial performance")
        subtitle.setStyleSheet(f"color: {SECONDARY}; font-size: 14px;")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        
        header.addLayout(title_block)
        header.addStretch()
        
        # Filters
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Last 7 Days", "Last 30 Days", "This Month", "All Time"])
        self.period_combo.setFixedWidth(150)
        self.period_combo.currentIndexChanged.connect(self.process_data)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setStyleSheet(f"background-color: {PRIMARY}; color: white;")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        header.addWidget(self.period_combo)
        header.addWidget(self.refresh_btn)
        main_layout.addLayout(header)

        # 2. Scroll Area for Dashboard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        
        # --- A. KPI Cards ---
        kpi_layout = QHBoxLayout()
        self.card_rev = KPICard("Total Revenue")
        self.card_orders = KPICard("Total Orders")
        self.card_avg = KPICard("Avg. Order Value")
        
        kpi_layout.addWidget(self.card_rev)
        kpi_layout.addWidget(self.card_orders)
        kpi_layout.addWidget(self.card_avg)
        content_layout.addLayout(kpi_layout)
        
        # --- B. Charts Row ---
        charts_layout = QHBoxLayout()
        
        # Trend Card
        trend_card = QFrame()
        trend_card.setProperty("card", "true")
        t_layout = QVBoxLayout(trend_card)
        
        trend_label = QLabel("Revenue Trend")
        trend_label.setProperty("heading", "true")
        t_layout.addWidget(trend_label)
        
        self.trend_chart = TrendChart()
        t_layout.addWidget(self.trend_chart)
        
        # Category Card
        cat_card = QFrame()
        cat_card.setProperty("card", "true")
        c_layout = QVBoxLayout(cat_card)
        
        cat_label = QLabel("Top Categories")
        cat_label.setProperty("heading", "true")
        c_layout.addWidget(cat_label)
        
        self.cat_chart = CategoryChart()
        c_layout.addWidget(self.cat_chart)
        
        charts_layout.addWidget(trend_card, 2) # 2/3 width
        charts_layout.addWidget(cat_card, 1)   # 1/3 width
        content_layout.addLayout(charts_layout)
        
        # --- C. Recent Transactions Table ---
        table_card = QFrame()
        table_card.setProperty("card", "true")
        table_layout = QVBoxLayout(table_card)
        
        tbl_header = QHBoxLayout()
        
        table_label = QLabel("Recent Transactions")
        table_label.setProperty("heading", "true")
        tbl_header.addWidget(table_label)
        
        export_btn = QPushButton("Export CSV")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet(f"color: {PRIMARY}; background: transparent; border: 1px solid {PRIMARY};")
        export_btn.clicked.connect(self.export_csv)
        tbl_header.addStretch()
        tbl_header.addWidget(export_btn)
        
        table_layout.addLayout(tbl_header)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "ID", "Items", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFixedHeight(300)
        
        table_layout.addWidget(self.table)
        content_layout.addWidget(table_card)
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Loading Bar (Hidden by default)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {PRIMARY}; }}")
        self.progress.hide()
        main_layout.addWidget(self.progress)

    # --- LOGIC ---

    def refresh_data(self):
        self.progress.show()
        self.progress.setRange(0, 0) # Infinite spinner
        self.refresh_btn.setEnabled(False)
        
        self.loader = ReportLoaderThread()
        self.loader.data_loaded.connect(self.on_data_loaded)
        self.loader.error_occurred.connect(self.on_error)
        self.loader.start()

    def on_data_loaded(self, sales):
        self.all_sales = sales
        print(f"DEBUG: Received {len(sales)} sales in on_data_loaded")
        self.progress.hide()
        self.refresh_btn.setEnabled(True)
        self.process_data()

    def on_error(self, msg):
        self.progress.hide()
        self.refresh_btn.setEnabled(True)
        print(f"Report Error: {msg}")

    def parse_date(self, date_str):
        """Parse date string that could be either with or without time"""
        try:
            # Try format with time first
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Try format without time
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                # If both fail, return current date as fallback
                print(f"DEBUG: Could not parse date: {date_str}")
                return datetime.now()

    def process_data(self):
        print("DEBUG: process_data called")
        
        # 1. Filter by Date
        filter_mode = self.period_combo.currentText()
        filtered = []
        today = datetime.now().date()
        
        cutoff = None
        if filter_mode == "Last 7 Days":
            cutoff = today - timedelta(days=7)
        elif filter_mode == "Last 30 Days":
            cutoff = today - timedelta(days=30)
        elif filter_mode == "This Month":
            cutoff = today.replace(day=1)
        
        print(f"DEBUG: Filter mode: {filter_mode}, Cutoff: {cutoff}")
        
        for s in self.all_sales:
            try:
                # Use full_date if available, otherwise use date
                date_to_parse = s.full_date if hasattr(s, 'full_date') and s.full_date else s.date
                s_date = self.parse_date(date_to_parse).date()
                if cutoff is None or s_date >= cutoff:
                    filtered.append(s)
            except Exception as e:
                print(f"Error parsing date {s.date}: {e}")
                pass

        print(f"DEBUG: After filtering: {len(filtered)} sales")

        # 2. Calculate KPIs
        total_rev = sum(s.total for s in filtered)
        count = len(filtered)
        avg = total_rev / count if count > 0 else 0
        
        print(f"DEBUG: KPIs - Revenue: {total_rev}, Orders: {count}, Avg: {avg}")
        
        self.card_rev.set_value(f"₱{total_rev:,.2f}")
        self.card_orders.set_value(str(count))
        self.card_avg.set_value(f"₱{avg:,.2f}")

        # 3. Prepare Chart Data
        # Trend (Daily Sum)
        trend_data = defaultdict(float)
        # Categories - group by product name since there's no category field
        cat_data = defaultdict(float)

        for s in filtered:
            # Trend - extract just the date part
            try:
                day_str = s.date.split(" ")[0] if " " in s.date else s.date  # YYYY-MM-DD
                trend_data[day_str] += s.total
            except Exception as e:
                print(f"DEBUG: Error processing trend data for sale {s.sale_id}: {e}")
            
            # Categories - use product names since there's no category field
            try:
                if hasattr(s, 'items') and s.items:
                    for item in s.items:
                        # Use product name as category
                        product_name = item.get('name', 'Unknown Product')
                        # Calculate item total: price * quantity
                        quantity = item.get('quantity', 1)
                        price = item.get('price', 0)
                        item_total = price * quantity
                        cat_data[product_name] += item_total
                else:
                    # If no items, use a default category
                    cat_data['Uncategorized'] += s.total
            except Exception as e:
                print(f"DEBUG: Error processing category data for sale {s.sale_id}: {e}")
                cat_data['Uncategorized'] += s.total

        print(f"DEBUG: Trend data points: {len(trend_data)}")
        print(f"DEBUG: Category data points: {len(cat_data)}")
        if cat_data:
            print(f"DEBUG: Sample category data: {list(cat_data.items())[:3]}")

        self.trend_chart.set_data(trend_data)
        self.cat_chart.set_data(cat_data)

        # 4. Populate Table (Top 50 recent)
        self.table.setRowCount(0)
        display_limit = min(len(filtered), 50)
        self.table.setRowCount(display_limit)
        
        for r in range(display_limit):
            s = filtered[r]
            
            # Date
            self.table.setItem(r, 0, QTableWidgetItem(s.date))
            # ID
            self.table.setItem(r, 1, QTableWidgetItem(str(s.sale_id)))
            # Items (Count)
            item_count = len(s.items) if hasattr(s, 'items') and s.items else 0
            self.table.setItem(r, 2, QTableWidgetItem(f"{item_count} items"))
            # Total
            total_item = QTableWidgetItem(f"₱{s.total:,.2f}")
            total_item.setForeground(QColor(SUCCESS))
            total_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.table.setItem(r, 3, total_item)

        print("DEBUG: Table populated")

    def export_csv(self):
        if not self.all_sales:
            QMessageBox.warning(self, "No Data", "No sales data to export.")
            return

        try:
            filename = f"sales_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Sale ID", "Total Amount", "Items Count"])
                for s in self.all_sales:
                    item_count = len(s.items) if hasattr(s, 'items') and s.items else 0
                    writer.writerow([s.date, s.sale_id, s.total, item_count])
            
            QMessageBox.information(self, "Export Successful", f"Report saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))