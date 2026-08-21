import duckdb
import os
import streamlit as st

@st.cache_resource
def get_duckdb_conn():
    """Tạo kết nối DuckDB an toàn, tự động chọn SQLite hoặc PostgreSQL."""
    conn = duckdb.connect()
    
    # Kiểm tra xem có DATABASE_URL không (PostgreSQL)
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        # Nếu có Postgres, cài đặt extension và attach
        conn.execute("INSTALL postgres;")
        conn.execute("LOAD postgres;")
        # DuckDB postgres format requires proper connection string
        conn.execute(f"ATTACH '{db_url}' AS db (TYPE POSTGRES);")
    else:
        # Nếu không có, dùng SQLite Local (2.1M rows)
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'warehouse', 'nyc_warehouse.db')
        conn.execute("INSTALL sqlite;")
        conn.execute("LOAD sqlite;")
        conn.execute(f"ATTACH '{sqlite_path}' AS db (TYPE SQLITE);")
        
    return conn

def execute_query(query, params=None):
    """Thực thi câu truy vấn và trả về DataFrame Pandas."""
    conn = get_duckdb_conn()
    if params:
        return conn.execute(query, params).df()
    return conn.execute(query).df()
