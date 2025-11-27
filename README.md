# Point-Of-Sales 🏪

[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg)](http://unlicense.org/)
[![Stars](https://img.shields.io/github/stars/Beluga011/Point-Of-Sales.svg?style=social&label=Stars)](https://github.com/Beluga011/Point-Of-Sales)
[![Forks](https://img.shields.io/github/forks/Beluga011/Point-Of-Sales.svg?style=social&label=Forks)](https://github.com/Beluga011/Point-Of-Sales)

A comprehensive Point of Sales (POS) system built with Python and PyQt5, designed to streamline sales operations, manage inventory, and generate insightful reports. The system provides a user-friendly interface with role-based access control, ensuring secure and efficient management of your business.

## Table of Contents

1.  [Features](#features)
2.  [Tech Stack](#tech-stack)
3.  [Installation](#installation)
4.  [Usage](#usage)
5.  [Project Structure](#project-structure)
6.  [Contributing](#contributing)
7.  [License](#license)
8.  [Important Links](#important-links)
9.  [Footer](#footer)

## Features ✨

-   **User Authentication**: Secure login system with role-based access (Admin, Manager, Cashier).
-   **Inventory Management**: Add, edit, and delete products with details like name, category, price, and stock.
-   **Product Catalog**: Browse and search products with real-time stock status.
-   **Sales Transactions**: Process sales with cash, card, GCash, and Maya payment options.
-   **Cart Management**: Add, update, and remove items from the cart.
-   **Discount & Promo Codes**: Apply discounts and promo codes to sales.
-   **Reporting & Analytics**: Generate sales reports with revenue trends and top categories.
-   **Transaction Holding**: Hold and recall transactions for efficient order management.
-   **Receipt Generation**: Generate and print detailed receipts.
-   **User Management (Admin)**: Add, edit, and delete user accounts with role management.

## Tech Stack 💻

-   **Language**: Python
-   **GUI Framework**: PyQt5
-   **Data Storage**: CSV files (products.csv, users.csv, sales.csv, promos.csv)
-   **Other**: hashlib for password hashing

## Installation ⚙️

1.  **Prerequisites**:
    -   Python 3.x
    -   PyQt5 library

2.  **Clone the repository**:
    ```bash
    git clone https://github.com/Beluga011/Point-Of-Sales.git
    cd Point-Of-Sales
    ```

3.  **Install PyQt5**:
    ```bash
    pip install PyQt5
    ```

4.  **Run the application**:
    ```bash
    cd "Project 2"
    python main.py
    ```

## Usage 🚀

1.  **Login**: Launch the application and log in with your credentials. Default users are created upon first launch if none exist:
    -   **Admin**: username = `admin`, password = `admin123`
    -   **Cashier**: username = `cashier`, password = `cashier123`

2.  **Main Interface**: The main window provides access to different modules:
    -   **Sales**: Process new sales, manage the cart, and apply discounts.
    -   **Products**: Manage product details and inventory.
    -   **Inventory**: Overview of product stock levels.
    -   **Reports**: Generate sales reports and analytics.
    -   **Users (Admin only)**: Manage user accounts and roles.

3.  **Sales Transactions**:
    -   Search for products by name or barcode.
    -   Add products to the cart.
    -   Adjust quantities in the cart.
    -   Apply discounts or promo codes.
    -   Select payment method (Cash, Card, GCash, Maya).
    -   Complete the transaction and generate a receipt.

4.  **Inventory Management**:
    -   Add new products with details like name, category, price, and stock.
    -   Edit existing product details.
    -   Delete products from the inventory.

5.  **Reporting**:
    -   Generate sales reports for different time periods (Last 7 Days, Last 30 Days, This Month, All Time).
    -   View revenue trends and top product categories.

**Important Notes:**

-   The application uses CSV files for data storage. Ensure that these files are present in the correct directory.
-   The `ensure_data_files()` function in `main.py` creates these files with headers if they don't exist.
-   The `create_sample_sales.py` script can be used to generate sample sales data for testing purposes. Execute with `python Project 2/create_sample_sales.py`

## Project Structure 📂

```
Point-Of-Sales/
├── Project 2/
│   ├── main.py               # Main application entry point
│   ├── create_sample_sales.py # Script to generate sample sales data
│   ├── csv_handler.py        # CSV file handling class
│   ├── fix_sales_data.py     # Script to fix corrupted sales data
│   ├── models.py             # Data models (Product, Sale, User)
│   ├── products.csv          # Product data
│   ├── promos.csv            # Promo code data
│   ├── receipt_11.txt        # Sample receipt (Not used in the current implementation)
│   ├── sales.csv             # Sales transaction data
│   ├── ui/
│   │   ├── inventory_window.py # Inventory management UI
│   │   ├── login_window.py     # Login UI
│   │   ├── main_window.py      # Main window UI (Sidebar and content stacking)
│   │   ├── products_window.py  # Product management UI
│   │   ├── reports_window.py   # Reporting and analytics UI
│   │   ├── sales_window.py     # Sales transaction UI
│   │   ├── users_window.py     # User management UI
├── README.md
```

## Contributing 🤝

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with descriptive messages.
4.  Submit a pull request.

## License 📜

This project is licensed under the Unlicense - see the [LICENSE](http://unlicense.org/) file for details.

## Important Links 🔗

-   **Repository**: [https://github.com/Beluga011/Point-Of-Sales](https://github.com/Beluga011/Point-Of-Sales)

## Footer 📌

```html
<p align="center">
  <a href="https://github.com/Beluga011/Point-Of-Sales">Point-Of-Sales</a> • A project by <a href="https://github.com/Beluga011">Beluga011</a>
</p>
<p align="center">
  Fork, Like, Star, and report issues!
</p>
```


---
**<p align="center">Generated by [ReadmeCodeGen](https://www.readmecodegen.com/)</p>**
