from csv_handler import CSVHandler
from datetime import datetime, timedelta
import random

def create_sample_sales():
    """Create sample sales data for testing"""
    
    # Sample products
    products = [
        {'id': '1', 'name': 'Product A', 'price': 100.0, 'tax_rate': 12.0},
        {'id': '2', 'name': 'Product B', 'price': 200.0, 'tax_rate': 12.0},
        {'id': '3', 'name': 'Product C', 'price': 150.0, 'tax_rate': 12.0},
    ]
    
    # Create sample sales for the last 7 days
    sales_data = []
    for i in range(20):
        sale_date = (datetime.now() - timedelta(days=random.randint(0, 6))).strftime('%Y-%m-%d')
        sale_time = f"{random.randint(8, 20):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
        
        # Create 1-3 random items per sale
        items = []
        for _ in range(random.randint(1, 3)):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            items.append({
                'product_id': product['id'],
                'name': product['name'],
                'quantity': quantity,
                'price': product['price'],
                'tax_rate': product['tax_rate']
            })
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['price'] for item in items)
        tax = subtotal * 0.12  # 12% tax
        discount = subtotal * random.uniform(0, 0.2)  # 0-20% discount
        total = subtotal + tax - discount
        
        sale_data = {
            'sale_id': str(i + 1),
            'date': sale_date,
            'time': sale_time,
            'total': f"{total:.2f}",
            'tax': f"{tax:.2f}",
            'discount': f"{discount:.2f}",
            'payment_method': random.choice(['cash', 'card', 'mixed']),
            'cashier_id': '1',
            'items': str(items).replace("'", '"')  # Convert to JSON string
        }
        
        sales_data.append(sale_data)
    
    # Write to CSV
    CSVHandler.write_csv('sales.csv', sales_data)
    print(f"Created {len(sales_data)} sample sales records")

if __name__ == '__main__':
    create_sample_sales()