"""
etl_to_sqlite.py
================
ETL Pipeline: Đọc file CSV đã làm sạch → Tách bảng → Ghi vào SQLite (Star-Schema)

Cấu trúc Star-Schema:
    dim_borough         (5 quận)
    dim_neighborhood    (các khu phố)
    dim_location        (địa chỉ, zipcode, block, lot)
    dim_property        (loại nhà, diện tích, năm xây)
    dim_social_metrics  (chỉ số kinh tế-xã hội theo quận)
    fact_sales          (giao dịch bất động sản - trung tâm)

Chạy:
    python src/etl_to_sqlite.py
"""

import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime

# ── Cấu hình encoding UTF-8 trên Windows ─────────────────────────────────────
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ── Đường dẫn ─────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_CSV      = os.path.join(BASE_DIR, 'data', 'data clean', 'DATA.csv')
WAREHOUSE_DIR  = os.path.join(BASE_DIR, 'data', 'warehouse')
DB_PATH        = os.path.join(WAREHOUSE_DIR, 'nyc_warehouse.db')
RAW_DIR        = os.path.join(BASE_DIR, 'data', 'raw')
SOCIAL_JSON    = os.path.join(RAW_DIR, 'social_metrics.json')

# ── Hàm tiện ích ─────────────────────────────────────────────────────────────
def log(msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")


def safe_int(val, default=0):
    try:
        v = int(float(val))
        return v if not np.isnan(v) else default
    except Exception:
        return default


# ═════════════════════════════════════════════════════════════════════════════
# BƯỚC 1: Load CSV sạch
# ═════════════════════════════════════════════════════════════════════════════
def load_clean_csv() -> pd.DataFrame:
    log(f"Đang đọc file CSV sạch: {os.path.basename(CLEAN_CSV)}")
    df = pd.read_csv(CLEAN_CSV, low_memory=False)
    log(f"  → Tải thành công: {len(df):,} dòng × {len(df.columns)} cột")
    
    df['sale_year_temp'] = pd.to_datetime(df['sale_date'], dayfirst=True, errors='coerce').dt.year
    df = df[df['sale_year_temp'].notna()].copy()
    
    # Do NOT filter by year 2024-2025. Keep all 2.1 million historical records.
    log(f"  → Đang xử lý toàn bộ dữ liệu lịch sử: {len(df):,} dòng")
    
    return df


# ═════════════════════════════════════════════════════════════════════════════
# BƯỚC 2: Khởi tạo SQLite và tạo Schema
# ═════════════════════════════════════════════════════════════════════════════
CREATE_SQL = """
-- Bảng Quận
CREATE TABLE IF NOT EXISTS dim_borough (
    borough_id    INTEGER PRIMARY KEY,
    borough_name  TEXT NOT NULL UNIQUE
);

-- Bảng Khu phố
CREATE TABLE IF NOT EXISTS dim_neighborhood (
    neighborhood_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    neighborhood_name TEXT NOT NULL,
    borough_id        INTEGER NOT NULL,
    amenity_score     REAL,
    FOREIGN KEY (borough_id) REFERENCES dim_borough(borough_id),
    UNIQUE (neighborhood_name, borough_id)
);

-- Bảng Địa chỉ
CREATE TABLE IF NOT EXISTS dim_location (
    location_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    address         TEXT,
    zip_code        TEXT,
    block           TEXT,
    lot             TEXT,
    neighborhood_id INTEGER NOT NULL,
    latitude        REAL,
    longitude       REAL,
    FOREIGN KEY (neighborhood_id) REFERENCES dim_neighborhood(neighborhood_id),
    UNIQUE(neighborhood_id, block, lot)
);

-- Bảng Bất động sản (tính chất vật lý)
CREATE TABLE IF NOT EXISTS dim_property (
    property_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    building_class_category  TEXT,
    building_category        TEXT,
    building_type            TEXT,
    building_class_present   TEXT,
    tax_class_present        TEXT,
    gross_sqft               REAL,
    land_sqft                REAL,
    year_built               INTEGER,
    building_age             INTEGER,
    residential_units        INTEGER,
    commercial_units         INTEGER,
    total_units              INTEGER,
    is_residential           INTEGER
);

-- Bảng Chỉ số kinh tế-xã hội (theo Quận)
CREATE TABLE IF NOT EXISTS dim_social_metrics (
    social_id        INTEGER PRIMARY KEY,
    borough_id       INTEGER NOT NULL UNIQUE,
    pop_density      REAL,
    avg_income       REAL,
    gdp_local        REAL,
    dist_center      REAL,
    num_parks        INTEGER,
    num_hospitals    INTEGER,
    num_supermarkets INTEGER,
    source_census    TEXT,
    source_osm       TEXT,
    FOREIGN KEY (borough_id) REFERENCES dim_borough(borough_id)
);

-- Bảng Giao dịch (Fact Table - trung tâm Star-Schema)
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id          INTEGER NOT NULL,
    property_id          INTEGER NOT NULL,
    social_id            INTEGER NOT NULL,
    sale_price           REAL,
    price_per_sqft       REAL,
    price_per_sqft_real  REAL,
    sale_date            TEXT,
    sale_year            INTEGER,
    sale_month           INTEGER,
    tax_class_sale       TEXT,
    building_class_sale  TEXT,
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (property_id) REFERENCES dim_property(property_id),
    FOREIGN KEY (social_id)   REFERENCES dim_social_metrics(social_id)
);
"""

BOROUGH_MAP = {
    1: 'Manhattan',
    2: 'Bronx',
    3: 'Brooklyn',
    4: 'Queens',
    5: 'Staten Island',
}

def init_db(conn: sqlite3.Connection):
    log("Khởi tạo schema SQLite (Star-Schema 5+1 bảng)...")
    conn.executescript(CREATE_SQL)
    conn.commit()
    log("  → Schema tạo thành công.")


# ═════════════════════════════════════════════════════════════════════════════
# BƯỚC 3: Điền từng bảng Dimension
# ═════════════════════════════════════════════════════════════════════════════
def load_dim_borough(conn: sqlite3.Connection, df: pd.DataFrame) -> dict:
    """Trả về dict: borough_name → borough_id"""
    log("Nạp dim_borough...")
    rows = []
    for bid, bname in BOROUGH_MAP.items():
        rows.append((bid, bname))
    conn.executemany(
        "INSERT OR IGNORE INTO dim_borough (borough_id, borough_name) VALUES (?, ?)",
        rows
    )
    conn.commit()
    cur = conn.execute("SELECT borough_id, borough_name FROM dim_borough")
    result = {row[1]: row[0] for row in cur.fetchall()}
    log(f"  → {len(result)} quận đã nạp.")
    return result


def load_dim_neighborhood(conn: sqlite3.Connection, df: pd.DataFrame, borough_map: dict) -> dict:
    """Trả về dict: (neighborhood_name, borough_id) → neighborhood_id"""
    log("Nạp dim_neighborhood...")
    
    # Nạp điểm số không gian thực từ json
    true_scores = {}
    try:
        with open('data/true_amenity_scores.json', 'r', encoding='utf-8') as f:
            true_scores = json.load(f)
    except Exception as e:
        log(f"  → Cảnh báo: Lỗi đọc true_amenity_scores.json: {e}")

    unique_neighborhoods = df[['neighborhood', 'borough', 'borough_name']].drop_duplicates()
    rows = []
    for _, row in unique_neighborhoods.iterrows():
        bid = safe_int(row.get('borough', 1))
        if bid not in [1, 2, 3, 4, 5]:
            bid = 1
        nname = str(row['neighborhood']).strip()
        bname = BOROUGH_MAP.get(bid, 'Unknown')
        
        # Tra cứu điểm tiện ích
        am_score = true_scores.get(f"{bname}_{nname}", 10.0)
        
        rows.append((nname, bid, am_score))

    conn.executemany(
        "INSERT OR IGNORE INTO dim_neighborhood (neighborhood_name, borough_id, amenity_score) VALUES (?, ?, ?)",
        rows
    )
    conn.commit()

    cur = conn.execute("SELECT neighborhood_id, neighborhood_name, borough_id FROM dim_neighborhood")
    result = {(row[1], row[2]): row[0] for row in cur.fetchall()}
    log(f"  → {len(result)} khu phố đã nạp.")
    return result


def load_dim_location(conn, df, neighborhood_map, borough_map):
    log("Nạp dim_location...")
    sub = df[['address', 'zip_code', 'block', 'lot', 'neighborhood', 'borough']].copy()
    
    def clean_zip(z):
        if pd.isna(z) or z == '': return ''
        z_str = str(z).strip()
        if '.' in z_str: z_str = z_str.split('.')[0]
        if len(z_str) > 0 and len(z_str) <= 5: return z_str.zfill(5)
        return z_str[:5]
    
    sub['address']  = sub['address'].apply(lambda x: str(x)[:200] if pd.notna(x) else '')
    sub['zip_code'] = sub['zip_code'].apply(clean_zip)
    sub['block']    = sub['block'].apply(lambda x: str(x)[:20] if pd.notna(x) else '').str.strip()
    sub['lot']      = sub['lot'].apply(lambda x: str(x)[:20] if pd.notna(x) else '').str.strip()
    
    cur = conn.cursor()
    location_cache = {}
    location_ids = []
    
    log("  → Đang xử lý địa điểm duy nhất...")
    for idx, row in sub.iterrows():
        bname = str(row['borough'])
        bid = safe_int(row.get('borough', 1))
        nname = str(row['neighborhood']).strip()
        
        nid = neighborhood_map.get(f"{BOROUGH_MAP.get(bid, 'Unknown')}_{nname}", 1)
        # fallback if not mapped correctly
        if nid == 1 and (nname, bid) in neighborhood_map:
            nid = neighborhood_map[(nname, bid)]
            
        block = str(row['block'])
        lot = str(row['lot'])
        address = str(row['address'])
        zip_code = str(row['zip_code'])
        
        cache_key = (nid, block, lot)
        
        if cache_key not in location_cache:
            location_cache[cache_key] = {
                'address': address,
                'zip_code': zip_code
            }
    
    log(f"  → Có {len(location_cache):,} địa điểm duy nhất. Tiến hành insert...")
    
    insert_data = []
    for k, v in location_cache.items():
        nid, block, lot = k
        insert_data.append((v['address'], v['zip_code'], block, lot, nid, None, None))
        
    cur.executemany("""
        INSERT OR IGNORE INTO dim_location (address, zip_code, block, lot, neighborhood_id, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, insert_data)
    conn.commit()
    
    log("  → Đọc lại ID của location_id...")
    cur.execute("SELECT neighborhood_id, block, lot, location_id FROM dim_location")
    db_locations = cur.fetchall()
    db_cache = {(str(r[0]), str(r[1]), str(r[2])): r[3] for r in db_locations}
    
    log("  → Gắn location_id cho bảng fact...")
    for idx, row in sub.iterrows():
        bid = safe_int(row.get('borough', 1))
        nname = str(row['neighborhood']).strip()
        nid = neighborhood_map.get(f"{BOROUGH_MAP.get(bid, 'Unknown')}_{nname}", 1)
        if nid == 1 and (nname, bid) in neighborhood_map:
            nid = neighborhood_map[(nname, bid)]
            
        block = str(row['block'])
        lot = str(row['lot'])
        location_ids.append(db_cache.get((str(nid), str(block), str(lot)), 1))
        
    log(f"  ✅ Đã tạo/nạp {len(location_cache):,} địa điểm duy nhất (location).")
    return pd.Series(location_ids, index=df.index)

def load_dim_property(conn: sqlite3.Connection, df: pd.DataFrame) -> pd.Series:
    """Nạp dim_property, trả về Series property_id theo index gốc của df"""
    log("Nạp dim_property...")
    prop_cols = [
        'building_class_category', 'building_category', 'building_type',
        'building_class_present', 'tax_class_present',
        'gross_sqft', 'land_sqft', 'year_built', 'building_age',
        'residential_units', 'commercial_units', 'total_units', 'is_residential'
    ]
    sub = df[[c for c in prop_cols if c in df.columns]].copy()

    # Điền cột còn thiếu nếu không tồn tại
    for col in prop_cols:
        if col not in sub.columns:
            sub[col] = None

    rows = []
    for _, row in sub.iterrows():
        rows.append((
            str(row['building_class_category'])[:100],
            str(row.get('building_category', ''))[:100],
            str(row.get('building_type', ''))[:100],
            str(row['building_class_present'])[:20],
            str(row['tax_class_present'])[:20],
            float(row['gross_sqft']) if pd.notna(row['gross_sqft']) else None,
            float(row['land_sqft'])  if pd.notna(row['land_sqft'])  else None,
            safe_int(row['year_built']),
            safe_int(row['building_age']),
            safe_int(row['residential_units']),
            safe_int(row['commercial_units']),
            safe_int(row['total_units']),
            safe_int(row.get('is_residential', 0)),
        ))

    conn.executemany(
        """INSERT INTO dim_property
           (building_class_category, building_category, building_type,
            building_class_present, tax_class_present,
            gross_sqft, land_sqft, year_built, building_age,
            residential_units, commercial_units, total_units, is_residential)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows
    )
    conn.commit()

    first_id = conn.execute("SELECT MIN(property_id) FROM dim_property").fetchone()[0]
    property_ids = list(range(first_id, first_id + len(rows)))
    log(f"  → {len(rows):,} bản ghi property đã nạp.")
    return pd.Series(property_ids, index=df.index)


def load_dim_social_metrics(conn: sqlite3.Connection, df: pd.DataFrame, borough_map: dict) -> dict:
    """Nạp dim_social_metrics, trả về dict: borough_id → social_id"""
    log("Nạp dim_social_metrics (từ social_metrics.json)...")
    
    if not os.path.exists(SOCIAL_JSON):
        raise FileNotFoundError(f"Không tìm thấy file {SOCIAL_JSON}. Hãy chạy crawl_social_metrics.py trước.")
        
    with open(SOCIAL_JSON, 'r', encoding='utf-8') as f:
        social_data = json.load(f)

    rows = []
    for bid_str, data in social_data.items():
        bid = int(bid_str)
        rows.append((
            bid,  # social_id = borough_id (1-5)
            bid,
            float(data.get('pop_density',  0)),
            float(data.get('avg_income',   0)),
            float(data.get('gdp_local',    0)),
            float(data.get('dist_center',  0)),
            int(data.get('num_parks', 0)),
            int(data.get('num_hospitals', 0)),
            int(data.get('num_supermarkets', 0)),
            str(data.get('source_census', '')),
            str(data.get('source_osm', ''))
        ))

    conn.executemany(
        """INSERT OR IGNORE INTO dim_social_metrics
           (social_id, borough_id, pop_density, avg_income, gdp_local, dist_center,
            num_parks, num_hospitals, num_supermarkets, source_census, source_osm)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows
    )
    conn.commit()
    log(f"  → {len(rows)} bộ chỉ số xã hội (real crawled data) đã nạp.")
    return {row[1]: row[0] for row in rows}  # borough_id → social_id


# ═════════════════════════════════════════════════════════════════════════════
# BƯỚC 4: Điền bảng Fact
# ═════════════════════════════════════════════════════════════════════════════
def load_fact_sales(conn: sqlite3.Connection, df: pd.DataFrame,
                    location_ids: pd.Series, property_ids: pd.Series,
                    social_map: dict, borough_map: dict):
    log("Nạp fact_sales...")
    rows = []
    for idx, row in df.iterrows():
        bid   = safe_int(row.get('borough', 1))
        if bid not in [1, 2, 3, 4, 5]:
            bid = 1
        sid   = social_map.get(bid, bid)

        rows.append((
            int(location_ids[idx]),
            int(property_ids[idx]),
            int(sid),
            float(row['sale_price'])           if pd.notna(row['sale_price'])           else None,
            float(row.get('price_per_sqft', 0))      if pd.notna(row.get('price_per_sqft', None)) else None,
            float(row.get('price_per_sqft_real', 0)) if pd.notna(row.get('price_per_sqft_real', None)) else None,
            str(row.get('sale_date', ''))[:20],
            safe_int(row.get('sale_year', 0)),
            safe_int(row.get('sale_month', 0)),
            str(row.get('tax_class_sale', ''))[:20],
            str(row.get('building_class_sale', ''))[:20],
        ))

    # Insert theo batch để nhanh hơn
    BATCH = 5000
    total = len(rows)
    for i in range(0, total, BATCH):
        conn.executemany(
            """INSERT INTO fact_sales
               (location_id, property_id, social_id,
                sale_price, price_per_sqft, price_per_sqft_real,
                sale_date, sale_year, sale_month,
                tax_class_sale, building_class_sale)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            rows[i:i+BATCH]
        )
        conn.commit()
        log(f"  → Đã insert: {min(i+BATCH, total):,}/{total:,}")

    log(f"  ✅ fact_sales hoàn tất: {total:,} giao dịch.")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════
def run_etl():
    print()
    print("=" * 60)
    print("  ETL PIPELINE: CSV → SQLite Star-Schema")
    print(f"  Source : {os.path.basename(CLEAN_CSV)}")
    print(f"  Target : {DB_PATH}")
    print("=" * 60)
    start = datetime.now()

    # Tạo thư mục warehouse nếu chưa có
    os.makedirs(WAREHOUSE_DIR, exist_ok=True)

    # Xóa DB cũ để build lại từ đầu (idempotent)
    # Kết nối SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    
    # DROP existing tables
    tables = ['fact_sales', 'dim_location', 'dim_neighborhood', 'dim_borough', 'dim_property', 'dim_social_metrics']
    for t in tables:
        conn.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()

    conn.execute("PRAGMA synchronous=NORMAL")

    try:
        # 1. Đọc CSV
        df = load_clean_csv()
        df = df.reset_index(drop=True)

        # 2. Schema
        init_db(conn)

        # 3. Dimensions
        borough_map      = load_dim_borough(conn, df)
        neighborhood_map = load_dim_neighborhood(conn, df, borough_map)
        location_ids     = load_dim_location(conn, df, neighborhood_map, borough_map)
        property_ids     = load_dim_property(conn, df)
        social_map       = load_dim_social_metrics(conn, df, borough_map)

        # 4. Parse sale_year và sale_month từ sale_date (hỗ trợ định dạng DD/MM/YYYY)
        df['sale_date_dt'] = pd.to_datetime(df['sale_date'], dayfirst=True, errors='coerce')
        df['sale_year']  = df['sale_date_dt'].dt.year.fillna(0).astype(int)
        df['sale_month'] = df['sale_date_dt'].dt.month.fillna(0).astype(int)
        log(f"  → Đã parse sale_year/sale_month từ sale_date: {df['sale_year'].between(2000,2030).sum():,} dòng hợp lệ")

        # 5. Fact
        load_fact_sales(conn, df, location_ids, property_ids, social_map, borough_map)


    finally:
        conn.close()

    elapsed = (datetime.now() - start).total_seconds()
    db_size = os.path.getsize(DB_PATH) / 1024 / 1024
    print()
    print("=" * 60)
    print(f"  ✅ ETL HOÀN TẤT!")
    print(f"  Thời gian  : {elapsed:.1f} giây")
    print(f"  File DB    : {DB_PATH}")
    print(f"  Kích thước : {db_size:.1f} MB")
    print("=" * 60)
    print()


if __name__ == '__main__':
    run_etl()
