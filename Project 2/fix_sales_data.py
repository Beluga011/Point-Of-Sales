import csv
from datetime import datetime

def fix_sales_data():
    """Fix any corrupted sales data by removing incomplete records"""
    try:
        with open('sales.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)
        
        # Filter out rows missing essential fields
        valid_rows = []
        for row in rows:
            # Check if essential fields exist and are not empty
            if (row.get('sale_id') and row.get('date') and row.get('time') and 
                row.get('total') and row.get('payment_method')):
                valid_rows.append(row)
            else:
                print(f"Removing invalid row: {row}")
        
        # Write back only valid rows
        if valid_rows:
            with open('sales.csv', 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=valid_rows[0].keys())
                writer.writeheader()
                writer.writerows(valid_rows)
            print(f"Fixed sales data: {len(valid_rows)} valid records")
        else:
            print("No valid sales records found")
            
    except Exception as e:
        print(f"Error fixing sales data: {e}")

if __name__ == '__main__':
    fix_sales_data()