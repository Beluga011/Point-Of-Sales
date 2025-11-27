import json

class Product:
    def __init__(self, product_id, name, category, price, stock, active=True, cost=0.0, barcode="", discount_eligibility=True):
        self.product_id = str(product_id)
        self.name = str(name)
        self.category = str(category)
        
        try: self.price = float(price)
        except: self.price = 0.0
            
        try: self.stock = int(float(stock))
        except: self.stock = 0
            
        try: self.cost = float(cost)
        except: self.cost = 0.0
        
        # Handle Active status safely
        if isinstance(active, str):
            self.active = active.lower() == 'true'
        else:
            self.active = bool(active)

        # Handle Barcode
        self.barcode = str(barcode) if barcode else ""

        # Handle Discount Eligibility safely
        if isinstance(discount_eligibility, str):
            self.discount_eligibility = discount_eligibility.lower() == 'true'
        else:
            self.discount_eligibility = bool(discount_eligibility)

    @classmethod
    def from_dict(cls, data):
        return cls(
            product_id=data.get('product_id', ''),
            name=data.get('name', 'Unknown'),
            category=data.get('category', 'Uncategorized'),
            price=data.get('price', 0),
            stock=data.get('stock', 0),
            active=data.get('active', 'true'),
            cost=data.get('cost', 0.0),
            barcode=data.get('barcode', ''),
            discount_eligibility=data.get('discount_eligibility', 'true') # Defaults to True if missing
        )

    def to_dict(self):
        return {
            'product_id': self.product_id,
            'name': self.name,
            'category': self.category,
            'price': str(self.price),
            'stock': str(self.stock),
            'active': str(self.active),
            'cost': str(self.cost),
            'barcode': self.barcode,
            'discount_eligibility': str(self.discount_eligibility)
        }

# --- SaleItem, Sale, User classes (Standard) ---
class SaleItem:
    def __init__(self, product_id, name, quantity, price, tax_rate=0.0):
        self.product_id = str(product_id)
        self.name = str(name)
        try: self.quantity = int(float(quantity))
        except: self.quantity = 0
        try: self.price = float(price)
        except: self.price = 0.0
    
    @property
    def subtotal(self): return self.price * self.quantity
    
    @property
    def tax_amount(self): return (self.subtotal / 1.12) * 0.12

    def to_dict(self):
        return {'product_id': self.product_id, 'name': self.name, 'quantity': self.quantity, 'price': self.price}

class Sale:
    def __init__(self, sale_id, date, time, items, total, tax, discount, payment_method, cashier_id):
        self.sale_id = str(sale_id)
        self.date = str(date)
        self.time = str(time)
        self.items = items
        try: self.total = float(total)
        except: self.total = 0.0
        try: self.tax = float(tax)
        except: self.tax = 0.0
        try: self.discount = float(discount)
        except: self.discount = 0.0
        self.payment_method = str(payment_method)
        self.cashier_id = str(cashier_id)

    @classmethod
    def from_dict(cls, data):
        items = []
        try:
            raw = json.loads(data.get('items_data', '[]'))
            for i in raw: items.append(SaleItem(i.get('product_id',''), i.get('name',''), i.get('quantity',0), i.get('price',0)))
        except: pass
        return cls(data.get('sale_id',''), data.get('date',''), data.get('time',''), items, 
                   data.get('total',0), data.get('tax',0), data.get('discount',0), 
                   data.get('payment_method',''), data.get('cashier_id',''))

    def to_dict(self):
        return {
            'sale_id': self.sale_id, 'date': self.date, 'time': self.time,
            'items_data': json.dumps([i.to_dict() for i in self.items]),
            'total': str(self.total), 'tax': str(self.tax), 'discount': str(self.discount),
            'payment_method': self.payment_method, 'cashier_id': self.cashier_id
        }

class User:
    def __init__(self, user_id, username, password, role, active=True):
        self.user_id = str(user_id)
        self.username = str(username)
        self.password = str(password)
        self.role = str(role)
        self.active = str(active).lower() == 'true'

    @classmethod
    def from_dict(cls, data):
        return cls(data.get('user_id',''), data.get('username',''), data.get('password',''), data.get('role','Cashier'), data.get('active','true'))