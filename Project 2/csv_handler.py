import csv
import os

class CSVHandler:
    @staticmethod
    def create_csv(filename, headers):
        """Creates a new CSV file with the specified headers."""
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
        except Exception as e:
            print(f"Error creating {filename}: {e}")

    @staticmethod
    def read_csv(filename):
        if not os.path.exists(filename):
            return []
        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as file:
                return list(csv.DictReader(file))
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return []

    @staticmethod
    def write_csv(filename, data):
        if not data:
            return
        try:
            headers = list(data[0].keys())
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            print(f"Error writing {filename}: {e}")

    @staticmethod
    def append_csv(filename, row_dict):
        file_exists = os.path.exists(filename)
        try:
            with open(filename, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=row_dict.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row_dict)
        except Exception as e:
            print(f"Error appending {filename}: {e}")

    @staticmethod
    def update_csv(filename, key_field, key_value, updated_row):
        data = CSVHandler.read_csv(filename)
        updated_data = []
        found = False
        for row in data:
            if row.get(key_field) == str(key_value):
                row.update(updated_row)
                updated_data.append(row)
                found = True
            else:
                updated_data.append(row)
        
        if found:
            CSVHandler.write_csv(filename, updated_data)

    @staticmethod
    def read_promo_codes():
        if not os.path.exists('promos.csv'):
            with open('promos.csv', 'w', newline='', encoding='utf-8') as f:
                f.write("code,discount_percent,active\nWELCOME,10,True")
        return CSVHandler.read_csv('promos.csv')
    
    # Add this inside your CSVHandler class in csv_handler.py

@staticmethod
def delete_row(file_path, id_column, id_value):
    """Removes a row where the id_column matches the id_value."""
    rows = CSVHandler.read_csv(file_path)
    # Filter out the row that matches the ID
    updated_rows = [row for row in rows if row.get(id_column) != str(id_value)]
    
    # Write the data back to CSV
    if updated_rows:
        CSVHandler.write_csv(file_path, updated_rows)
    else:
        # If list is empty (all deleted), write just headers if possible, 
        # or handle based on your specific write_csv implementation.
        # This assumes write_csv handles a list of dicts.
        CSVHandler.write_csv(file_path, updated_rows)