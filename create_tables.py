from scrape_and_save import DB_USER
from sqlalchemy import create_engine , text

# NEW (WSL MySQL):
WINDOWS_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "mande123"
DATABASE_URL = f"mysql+pymysql://root:{DB_PASSWORD}@{WINDOWS_HOST}:3306/price_tracker"

engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})

# Create the date dimension table
create_date_dimension = """
CREATE TABLE IF NOT EXISTS date_dimension (
    date_id INT PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    day_of_week VARCHAR(10),
    is_weekend BOOLEAN DEFAULT FALSE,
    quarter INT,
    INDEX idx_date_year (year),
    INDEX idx_date_month (month)
)
"""

# Create the products table
create_products_table = """
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    store_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_product_store (store_name)
)
"""

# Create the price_history table with date_id
create_price_history_table = """
CREATE TABLE IF NOT EXISTS price_history (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    date_id INT NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (date_id) REFERENCES date_dimension(date_id) ON DELETE CASCADE,
    INDEX idx_price_product_date (product_id, date_id),
    INDEX idx_price_date (date_id)
)
"""

with engine.begin() as connection:
    connection.execute(text(create_date_dimension))
    connection.execute(text(create_products_table))
    connection.execute(text(create_price_history_table))

print("✅ All tables created successfully!")
print("📊 Database schema is ready for professional time-series analysis!")
