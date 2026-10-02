#  Price Tracker — Automated Data Pipeline

> A production-grade web scraping pipeline that collects product prices daily, stores them in MariaDB, and sends real-time notifications via Ntfy.

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![MariaDB](https://img.shields.io/badge/MariaDB-10.11-orange.svg)](https://mariadb.org)
[![Playwright](https://img.shields.io/badge/Playwright-1.40-green.svg)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

##  Overview

Price Tracker is an end-to-end automated data pipeline built to demonstrate **professional data engineering practices**. It scrapes e-commerce data, transforms it, stores it in a time-series database, and runs autonomously on a schedule.

**Built by a first-year Data Science student as part of a 3-month mastery roadmap.**

---

##  Features

| Feature | Description |
|---------|-------------|
|  **Automated Scraping** | Playwright browses JavaScript-heavy sites |
| 🗄️**Time-Series Storage** | Optimized schema with date dimension table |
|  **Retry Logic** | 3 attempts with backoff on failures |
|  **Instant Notifications** | Ntfy alerts on success/failure |
|  **Cron Scheduling** | Runs daily without manual intervention |
|  **Comprehensive Logging** | Every run recorded for debugging |
| 🛡️**Self-Healing Selectors** | Multiple fallbacks for resilience |

---

## 🏗️Architecture

```
┌──────────────────┐
│  Target Website  │
│  (books.toscrape)│
└────────┬─────────┘
         │ 1. Playwright
         ▼
┌──────────────────┐
│  Scraper Engine  │
│  (Python)        │
└────────┬─────────┘
         │ 2. Clean & Validate
         ▼
┌──────────────────┐
│  SQLAlchemy ORM  │
└────────┬─────────┘
         │ 3. Store
         ▼
┌──────────────────┐
│    MariaDB       │
│  price_tracker   │
│  ├── products    │
│  ├── price_history│
│  └── date_dimension│
└────────┬─────────┘
         │ 4. Notify
         ▼
┌──────────────────┐
│   Ntfy (Phone)   │
└──────────────────┘
```

---

## 🛠️Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Language** | Python 3.12 | Core logic |
| **Scraping** | Playwright | Headless browser automation |
| **Database** | MariaDB 10.11 | Relational storage |
| **ORM** | SQLAlchemy 2.0 | Database abstraction |
| **Driver** | PyMySQL | MySQL/MariaDB connector |
| **Scheduling** | Cron | Daily automation |
| **Notifications** | Ntfy | Push notifications |
| **Environment** | WSL2 + Ubuntu | Development environment |

---

##  Project Structure

```
price_tracker/
│
├──  README.md                 # This file
├──  requirements.txt          # Python dependencies
├──  .gitignore                # Git exclusions
├──  .env.example              # Environment template
│
├──  test_db.py                # Database connection test
├──  create_tables.py          # Schema creation script
├──  scrape_and_save.py        # Main pipeline (production)
├──  first_scraper.py          # Learning scraper (reference)
│
├──  scraper.log               # Application logs
├──  cron.log                  # Cron execution logs
│
└──  venv/                     # Virtual environment (not in Git)
```

---

## 🗄️Database Schema

### `products` — Unique Products

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | INT (PK) | Auto-increment identifier |
| `product_name` | VARCHAR(255) | Product title |
| `url` | VARCHAR(1000) | Unique product URL |
| `store_name` | VARCHAR(100) | Store identifier |
| `created_at` | TIMESTAMP | First seen |

### `price_history` — Price Over Time

| Column | Type | Description |
|--------|------|-------------|
| `price_id` | INT (PK) | Auto-increment identifier |
| `product_id` | INT (FK) | Links to `products` |
| `price` | DECIMAL(10,2) | Price at scrape time |
| `is_available` | BOOLEAN | In stock? |
| `date_id` | INT (FK) | Links to `date_dimension` |
| `scraped_at` | TIMESTAMP | When scraped |

### `date_dimension` — Pre-Computed Dates

| Column | Type | Description |
|--------|------|-------------|
| `date_id` | INT (PK) | Format: YYYYMMDD |
| `full_date` | DATE | Actual date |
| `year`, `month`, `day` | INT | Date parts |
| `day_of_week` | VARCHAR(10) | Monday, etc. |
| `is_weekend` | BOOLEAN | Sat/Sun? |
| `quarter` | INT | Q1-Q4 |

**Why a date dimension?** It makes time-based queries **10-100x faster** by pre-computing attributes instead of calculating them on every query.

---

##  Quick Start

### Prerequisites

- WSL2 with Ubuntu 22.04+
- Python 3.12+
- MariaDB 10.11+

### Installation

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/price_tracker.git
cd price_tracker

# 2. Virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Dependencies
pip install -r requirements.txt
playwright install chromium
sudo playwright install-deps chromium

# 4. Database setup
sudo mariadb
```

In MariaDB:
```sql
CREATE DATABASE price_tracker;
ALTER USER 'root'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('your_password');
FLUSH PRIVILEGES;
EXIT;
```

```bash
# 5. Configure environment
cp .env.example .env
nano .env  # Fill in your credentials

# 6. Create tables
python3 create_tables.py

# 7. Test
python3 scrape_and_save.py
```

---

#configuration

Create `.env` in the project root:

```bash
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=price_tracker

# Notifications (get from ntfy.sh)
NTFY_TOPIC=your_unique_topic
```

---

##  Automation with Cron

Run daily at 9:00 AM:

```bash
crontab -e
```

Add:
```
0 9 * * * cd /home/mande/price_tracker && source venv/bin/activate && python3 scrape_and_save.py >> /home/mande/price_tracker/cron.log 2>&1
```

**Verify:**
```bash
crontab -l
cat cron.log
```

---

##  Sample Queries

### Latest prices
```sql
SELECT p.product_name, ph.price, ph.scraped_at
FROM products p
JOIN price_history ph ON p.product_id = ph.product_id
ORDER BY ph.scraped_at DESC
LIMIT 10;
```

### Price changes over time
```sql
SELECT 
    p.product_name,
    d.full_date,
    ph.price,
    LAG(ph.price) OVER (PARTITION BY ph.product_id ORDER BY d.full_date) AS previous_price,
    ph.price - LAG(ph.price) OVER (PARTITION BY ph.product_id ORDER BY d.full_date) AS change
FROM price_history ph
JOIN products p ON p.product_id = ph.product_id
JOIN date_dimension d ON d.date_id = ph.date_id
ORDER BY p.product_name, d.full_date;
```

### Monthly averages
```sql
SELECT 
    p.product_name,
    d.year,
    d.month,
    AVG(ph.price) AS avg_price,
    COUNT(*) AS records
FROM price_history ph
JOIN products p ON p.product_id = ph.product_id
JOIN date_dimension d ON d.date_id = ph.date_id
GROUP BY p.product_name, d.year, d.month;
```

---

## 🛡️Reliability Features

| Feature | Implementation |
|---------|----------------|
| **Retry Logic** | 3 attempts, 5-10s delays |
| **Graceful Failures** | `try/except` on every selector |
| **Logging** | All runs in `scraper.log` |
| **Notifications** | Ntfy on success/failure |
| **Idempotent Writes** | Check before insert |
| **Transaction Safety** | `with engine.begin()` |

---

##  Lessons Learned

This project taught me:

-  **WSL2 ↔ Windows networking** — IP changes, port conflicts
-  **MySQL vs MariaDB** — authentication plugins, port management
-  **Playwright headless mode** — running browsers without display
-  **SQLAlchemy transactions** — context managers, rollback safety
-  **Cron scheduling** — 24-hour format, environment variables
-  **Time-series schema design** — date dimensions, indexes
-  **Error resilience** — retries, backoff, notifications

---

##  Roadmap

- [x] Core scraping pipeline
- [x] Database with time-series schema
- [x] Automated scheduling
- [x] Push notifications
- [ ] Streamlit dashboard for visualization
- [ ] Add more e-commerce sites (Jumia, Amazon)
- [ ] Price drop alerts via email
- [ ] Docker containerization
- [ ] Deploy to cloud (DigitalOcean/AWS)
- [ ] Automated tests with pytest

---

##  Contributing

This is a learning project, but suggestions are welcome! Open an issue or submit a PR.

---

##  License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**John** — First-year Data Science student, Tanzania 🇹🇿

Building toward becoming a **Data Systems Architect**.

- Email: johnmande2025@gmail.com
- LinkedIn: [linkedin.com/in/yourprofile](https://linkedin.com)
-  GitHub: [johnmande2025](https://github.com)

---

## Acknowledgments

- **Nova** —  mentor who guided this journey
- **Playwright team** — for an amazing automation tool
- **MariaDB Foundation** — for a stable database

---

<div align="center">

**If this project helped you, give it a star!**

*Built with ❤️love in Tanzania*

</div>
