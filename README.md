# Market Basket Analysis - E-Commerce Web App

Full-stack MBA application using Flask + React + FP-Growth for real-time product recommendations.

## Project Structure

```text
mba_project/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── database.py
│   ├── rule_cache.py
│   ├── fp_growth_engine.py
│   ├── data_generator.py
│   └── routes/
│       ├── auth.py
│       ├── admin.py
│       ├── products.py
│       └── recommendations.py
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/axios.js
│   │   ├── context/AuthContext.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Storefront.jsx
│   │   │   ├── Cart.jsx
│   │   │   └── admin/
│   │   │       ├── Dashboard.jsx
│   │   │       ├── UploadData.jsx
│   │   │       ├── RulesManager.jsx
│   │   │       └── Reports.jsx
│   │   └── components/
│   │       ├── Navbar.jsx
│   │       ├── ProductCard.jsx
│   │       ├── CartItem.jsx
│   │       └── RecommendationWidget.jsx
│   └── package.json
└── data/
    └── transactions.csv
```

## Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install flask flask-cors flask-jwt-extended sqlalchemy pymysql mlxtend pandas numpy
pip install cryptography
```

### Create MySQL Database

```sql
mysql -u root -p
CREATE DATABASE mba_ecommerce;
```

### Configure Backend

Update `backend/config.py` (or set environment variables):

- `MYSQL_URI = "mysql+pymysql://root:password@localhost/mba_ecommerce"`
- `JWT_SECRET_KEY = "your-secret-key"`

### Initialize DB, Generate CSV, Run API

```bash
python database.py
python data_generator.py
python app.py
```

Flask runs on port `5000`.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Vite runs on port `3000`.

## Daily One-Command Startup

From the project root, run:

```powershell
cd c:\codebase\new_projects\mba_project
python start_all.py
```

The script starts backend and frontend, then prints runtime status plus URLs:

- Backend process status and health check
- Frontend process status and URL check
- Direct links for backend, backend health, and frontend

Optional flags:

- `--install-deps` installs backend/frontend dependencies before starting.
- `--generate-data` regenerates `data/transactions.csv` before starting.
- `--backend-only` starts only backend.

Example:

```powershell
python start_all.py --install-deps --generate-data
```

## Database Setup + Migration Script

Use the root script to create the database and import SQL dump with custom MySQL credentials:

```powershell
cd c:\codebase\new_projects\mba_project
python setup_db_migration.py --mysql-user root --mysql-password YOUR_PASSWORD --db-name mba_ecommerce
```

Optional flags:

- `--dump-file data/mba_ecommerce_full_dump.sql` to use a different dump file path.
- `--skip-import` to only create the database.
- `--mysql-host` and `--mysql-port` for remote/local custom MySQL servers.
- `--mysql-client-path "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"` if `mysql` is not in PATH.
- `--write-env-files` to generate `backend_env.ps1` and `backend_env.cmd` with current credentials.

Example with env helper files:

```powershell
python setup_db_migration.py --mysql-user root --mysql-password YOUR_PASSWORD --write-env-files
```

## API Endpoints

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Admin (JWT + admin role)

- `POST /api/admin/upload` (multipart form with `file`)
- `POST /api/admin/train`
- `GET /api/admin/rules`
- `PATCH /api/admin/rules/<id>`
- `GET /api/admin/stats`

### Products

- `GET /api/products`
- `GET /api/products/<sku>`

### Recommendations

- `POST /api/recommend` body: `{ "cart_items": ["SKU-001", "SKU-004"] }`
- `POST /api/discount` body: `{ "cart_items": ["SKU-001", "SKU-005"] }`

## End-to-End Flow

1. Register/login as admin.
2. Upload generated CSV from `data/transactions.csv` in Admin Upload page.
3. Train model with `min_support=0.02`, `min_confidence=0.30`.
4. Open storefront and add products to cart.
5. See real-time "Frequently Bought Together" results from in-memory cache.
6. If high-confidence bundle condition is met, discount endpoint returns promo code.

## Notes

- Recommendations are cache-first using module-level in-memory dictionary.
- Rules are persisted in MySQL and loaded into cache at app startup.
- Admin can enable/disable rules in Rules Manager.
