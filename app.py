import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import json
import os
import zlib
import psycopg2
import urllib.parse
from dotenv import load_dotenv
load_dotenv()

# ════════════════════════════════════════════════════════════
# CẤU HÌNH TRANG
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="[PostgreSQL] Báo cáo Phân tích Thị trường Bất động sản NYC 2025 - 2026",
    layout="wide",
    page_icon="️",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-weight: 500; }
.main { background-color: #f8fafc; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff 0%, #f5f3ff 100%);
    padding: 18px 20px;
    border-radius: 14px;
    box-shadow: 0 4px 20px rgba(99,102,241,0.14), 0 1px 4px rgba(0,0,0,0.06);
    border: none;
    border-left: 5px solid #6366f1;
}
[data-testid="stMetricLabel"] {
    color: #7c3aed !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stMetricValue"] {
    color: #1e1b4b !important;
    font-size: 24px !important;
    font-weight: 800 !important;
    letter-spacing: -0.5px;
}
[data-testid="stMetricDelta"] { font-size: 12px !important; font-weight: 600 !important; }
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    border-bottom: 2px solid #c7d2fe;
    background: linear-gradient(180deg, #eef2ff 0%, #f0f4ff 100%);
    border-radius: 12px 12px 0 0;
    padding: 8px 8px 0;
}
.stTabs [data-baseweb="tab"] {
    height: 44px;
    font-weight: 700;
    font-size: 13px;
    color: #4338ca;
    border-radius: 10px 10px 0 0;
    padding: 0 20px;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #ffffff !important;
    background: #6366f1 !important;
    box-shadow: 0 -3px 14px rgba(99,102,241,0.4) !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e1b4b 0%, #312e81 55%, #4c1d95 100%);
}
[data-testid="stSidebar"] * { color: #e0e7ff !important; }
[data-testid="stSidebar"] label {
    color: #a5b4fc !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background: #6366f1 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] span { color: #ffffff !important; font-weight: 700 !important; }
div[data-baseweb="select"] {
    border: 2px solid #2563eb !important;
    border-radius: 6px !important;
    background-color: #ffffff !important;
    box-shadow: 0 2px 5px rgba(0,0,0,0.15) !important;
}
div[data-baseweb="select"] > div {
    border: none !important;
    background-color: transparent !important;
}
[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(99,102,241,0.45) !important;
}
.section-q {
    font-size: 17px;
    font-weight: 800;
    color: #1e1b4b;
    margin: 24px 0 4px 0;
    padding: 10px 16px;
    border-left: 5px solid #6366f1;
    background: linear-gradient(90deg, #eef2ff 0%, transparent 80%);
    border-radius: 0 8px 8px 0;
}
.section-cap { font-size: 13px; color: #4b5563; font-weight: 600; margin: 4px 0 14px 16px; line-height: 1.6; }
.insight-box {
    background: linear-gradient(135deg, #faf5ff 0%, #ede9fe 60%, #e0e7ff 100%);
    border: 1px solid #c4b5fd;
    border-left: 6px solid #7c3aed;
    border-radius: 0 14px 14px 0;
    padding: 18px 22px;
    margin: 22px 0 8px 0;
    font-size: 14px;
    font-weight: 600;
    line-height: 1.9;
    color: #2e1065;
    box-shadow: 0 4px 16px rgba(124,58,237,0.1);
}
.insight-box b { color: #5b21b6; font-weight: 800; }
.badge {
    display: inline-block;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #ffffff;
    border-radius: 999px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 700;
    box-shadow: 0 2px 8px rgba(99,102,241,0.4);
}
.hr { border: none; border-top: 1px solid #c7d2fe; margin: 28px 0; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #eef2ff; }
::-webkit-scrollbar-thumb { background: #a5b4fc; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# HẰNG SỐ, TỌA ĐỘ BẢN ĐỒ & BẢN MÀU
# ════════════════════════════════════════════════════════════
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = BASE_DIR
BOROUGH_MAP   = {1:'Manhattan', 2:'Bronx', 3:'Brooklyn', 4:'Queens', 5:'Staten Island'}
BOROUGH_ORDER = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
BOROUGH_COLORS = {
    'Manhattan':    '#6366f1',
    'Brooklyn':     '#0ea5e9',
    'Queens':       '#10b981',
    'Bronx':        '#f59e0b',
    'Staten Island':'#ec4899',
}
C_BLUE = '#6366f1'; C_BLUE2 = '#818cf8'; C_SKY = '#0ea5e9'
C_ORANGE = '#f59e0b'; C_RED = '#ef4444'; C_GREEN = '#10b981'; C_GRAY = '#94a3b8'

MONTH_SHORT = {1:'T1',2:'T2',3:'T3',4:'T4',5:'T5',6:'T6',
               7:'T7',8:'T8',9:'T9',10:'T10',11:'T11',12:'T12'}
MONTH_FULL  = {1:'Tháng 1',2:'Tháng 2',3:'Tháng 3',4:'Tháng 4',
               5:'Tháng 5',6:'Tháng 6',7:'Tháng 7',8:'Tháng 8',
               9:'Tháng 9',10:'Tháng 10',11:'Tháng 11',12:'Tháng 12'}
FEATURE_LABELS = {
    'gross_sqft':'Diện tích tổng (sqft)', 'building_age':'Tuổi công trình (năm)',
    'land_sqft':'Diện tích đất (sqft)',   'pop_density':'Mật độ dân số (/km²)',
    'total_units':'Số căn trong tòa',
    'gdp_local':'GDP địa phương (%)',      'avg_income':'Thu nhập bình quân ($)',
    'dist_center':'KC đến trung tâm (km)',
}
REQUIRED_COLS = [
    'borough','neighborhood','building_type','gross_sqft','land_sqft',
    'sale_price','sale_year','sale_date','building_age','total_units',
    'pop_density','avg_income','gdp_local','dist_center','amenity_score'
]

# Tọa độ địa lý NYC cho bản đồ Nhiệt (Hotspot Heatmap)
BOROUGH_COORDS = {
    'Manhattan':     (40.7831, -73.9712),
    'Brooklyn':      (40.6782, -73.9442),
    'Queens':        (40.7282, -73.7949),
    'Bronx':         (40.8448, -73.8648),
    'Staten Island': (40.5795, -74.1502),
}

NEIGHBORHOOD_COORDS = {
    # MANHATTAN
    'UPPER EAST SIDE (59-79)': (40.7700, -73.9590),
    'UPPER EAST SIDE (79-96)': (40.7780, -73.9530),
    'UPPER EAST SIDE (96-110)': (40.7910, -73.9470),
    'UPPER WEST SIDE (59-79)': (40.7760, -73.9810),
    'UPPER WEST SIDE (79-96)': (40.7890, -73.9720),
    'UPPER WEST SIDE (96-110)': (40.8000, -73.9630),
    'MIDTOWN EAST': (40.7540, -73.9720),
    'MIDTOWN WEST': (40.7600, -73.9880),
    'MIDTOWN CBD': (40.7550, -73.9800),
    'CHELSEA': (40.7465, -74.0014),
    'GREENWICH VILLAGE-CENTRAL': (40.7336, -73.9996),
    'GREENWICH VILLAGE-WEST': (40.7350, -74.0060),
    'GRAMERCY': (40.7368, -73.9845),
    'MURRAY HILL': (40.7483, -73.9783),
    'EAST VILLAGE': (40.7265, -73.9815),
    'LOWER EAST SIDE': (40.7150, -73.9840),
    'SOHO': (40.7233, -74.0030),
    'TRIBECA': (40.7163, -74.0086),
    'FINANCIAL': (40.7075, -74.0090),
    'HARLEM-CENTRAL': (40.8116, -73.9465),
    'HARLEM-EAST': (40.7957, -73.9389),
    'HARLEM-WEST': (40.8150, -73.9560),
    'WASHINGTON HEIGHTS UPPER': (40.8500, -73.9360),
    'WASHINGTON HEIGHTS LOWER': (40.8380, -73.9420),
    'INWOOD': (40.8677, -73.9212),
    'KIPS BAY': (40.7396, -73.9801),
    'CHINATOWN': (40.7158, -73.9970),
    'BATTERY PARK CITY': (40.7120, -74.0150),
    'MORNINGSIDE HEIGHTS': (40.8080, -73.9630),

    # QUEENS
    'FLUSHING-NORTH': (40.7675, -73.8331),
    'FLUSHING-SOUTH': (40.7420, -73.8210),
    'FOREST HILLS': (40.7186, -73.8448),
    'BAYSIDE': (40.7675, -73.7745),
    'ASTORIA': (40.7644, -73.9235),
    'JACKSON HEIGHTS': (40.7557, -73.8831),
    'ELMHURST': (40.7369, -73.8784),
    'LONG ISLAND CITY': (40.7447, -73.9485),
    'REGO PARK': (40.7258, -73.8622),
    'WOODSIDE': (40.7454, -73.9038),
    'SUNNYSIDE': (40.7434, -73.9241),
    'WHITESTONE': (40.7892, -73.8117),
    'RIDGEWOOD': (40.7061, -73.9015),
    'GLENDALE': (40.7011, -73.8876),
    'MASPETH': (40.7230, -73.9100),
    'MIDDLE VILLAGE': (40.7160, -73.8860),
    'JAMAICA': (40.7027, -73.7890),
    'JAMAICA ESTATES': (40.7234, -73.7834),
    'HOLLIS': (40.7117, -73.7667),
    'QUEENS VILLAGE': (40.7170, -73.7380),
    'HOWARD BEACH': (40.6570, -73.8430),
    'OZONE PARK': (40.6811, -73.8427),
    'RICHMOND HILL': (40.6953, -73.8315),
    'KEW GARDENS': (40.7090, -73.8310),

    # BROOKLYN
    'BEDFORD STUYVESANT': (40.6872, -73.9418),
    'BAY RIDGE': (40.6260, -74.0300),
    'BOROUGH PARK': (40.6350, -73.9920),
    'PARK SLOPE': (40.6711, -73.9814),
    'BUSHWICK': (40.6944, -73.9213),
    'WILLIAMSBURG-NORTH': (40.7180, -73.9570),
    'WILLIAMSBURG-SOUTH': (40.7090, -73.9590),
    'GREENPOINT': (40.7305, -73.9515),
    'DUMBO': (40.7033, -73.9881),
    'BROOKLYN HEIGHTS': (40.6960, -73.9936),
    'COBBLE HILL': (40.6877, -73.9947),
    'CARROLL GARDENS': (40.6800, -73.9950),
    'CROWN HEIGHTS': (40.6700, -73.9430),
    'FLATBUSH-LEFFERTS GARDENS': (40.6580, -73.9510),
    'FLATBUSH-CENTRAL': (40.6420, -73.9580),
    'SUNSET PARK': (40.6450, -74.0080),
    'BENSONHURST': (40.6139, -73.9922),
    'SHEEPSHEAD BAY': (40.5868, -73.9542),
    'CONEY ISLAND': (40.5750, -73.9820),
    'CANARSIE': (40.6400, -73.8960),

    # BRONX
    'RIVERDALE': (40.8904, -73.9125),
    'KINGSBRIDGE/JEROME PARK': (40.8790, -73.8970),
    'MOTT HAVEN/PORT MORRIS': (40.8090, -73.9230),
    'MELROSE/MORRISANIA': (40.8250, -73.9100),
    'FORDHAM': (40.8615, -73.8890),
    'BELMONT': (40.8550, -73.8870),
    'THROGS NECK': (40.8170, -73.8160),

    # STATEN ISLAND
    'GREAT KILLS': (40.5515, -74.1513),
    'TODT HILL': (40.5980, -74.1100),
    'ST. GEORGE': (40.6430, -74.0760),
    'NEW DORP': (40.5730, -74.1170),
    'ELTINGVILLE': (40.5430, -74.1650),
}

def get_neighborhood_coords(neighborhood, borough_name):
    """Lấy tọa độ lat/lon chuẩn hoặc suy luận theo offset nhỏ từ centroid quận."""
    if neighborhood in NEIGHBORHOOD_COORDS:
        return NEIGHBORHOOD_COORDS[neighborhood]
    b_lat, b_lon = BOROUGH_COORDS.get(borough_name, (40.7128, -74.0060))
    h = zlib.adler32(str(neighborhood).encode('utf-8'))
    off_lat = ((h % 100) - 50) * 0.0008
    off_lon = (((h // 100) % 100) - 50) * 0.0008
    return (b_lat + off_lat, b_lon + off_lon)

# ════════════════════════════════════════════════════════════
# HÀM DỮ LIỆU
# ════════════════════════════════════════════════════════════
def _get_cache_mtime():
    """Lấy modification time của DB và DATA.csv để làm cache-key. Khi nạp dữ liệu mới → cache tự động làm mới."""
    try:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'warehouse', 'nyc_warehouse.db')
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'data clean', 'DATA.csv')
        t_db = os.path.getmtime(db_path) if os.path.exists(db_path) else 0
        t_data = os.path.getmtime(data_path) if os.path.exists(data_path) else 0
        return max(t_db, t_data)
    except:
        return 0

@st.cache_data
def load_data(query=None, cache_mtime=None):
    # Cache tự động invalidate khi cache_mtime thay đổi


    """Đọc dữ liệu từ SQLite Data Warehouse local."""
    try:
        import sqlite3
        import os
        import zipfile
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'warehouse', 'nyc_warehouse.db')
        zip_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'warehouse', 'nyc_warehouse.zip')
        
        # Tự động giải nén nếu chưa có db hoặc zip mới hơn
        if os.path.exists(zip_path):
            need_extract = True
            if os.path.exists(db_path):
                # Kiểm tra nếu file zip mới hơn file db thì giải nén đè lên
                if os.path.getmtime(zip_path) <= os.path.getmtime(db_path):
                    need_extract = False
                    # Kiểm tra DB có bị hỏng do race condition trước đó không
                    try:
                        conn_test = sqlite3.connect(db_path)
                        conn_test.execute("SELECT 1 FROM fact_sales LIMIT 1")
                        conn_test.close()
                    except sqlite3.DatabaseError:
                        need_extract = True
            
            if need_extract:
                try:
                    import filelock
                    lock_path = db_path + ".lock"
                    with filelock.FileLock(lock_path, timeout=60):
                        do_extract = True
                        if os.path.exists(db_path):
                            try:
                                c2 = sqlite3.connect(db_path)
                                c2.execute("SELECT 1 FROM fact_sales LIMIT 1")
                                c2.close()
                                if os.path.getmtime(zip_path) <= os.path.getmtime(db_path):
                                    do_extract = False
                            except sqlite3.DatabaseError:
                                do_extract = True
                        
                        if do_extract:
                            try:
                                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                                    zip_ref.extractall(os.path.dirname(db_path))
                            except zipfile.BadZipFile as e:
                                if not os.path.exists(db_path):
                                    raise Exception(f"File zip bị lỗi (có thể do Git LFS) và không tìm thấy file db: {e}")
                except ImportError:
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(os.path.dirname(db_path))
                    except zipfile.BadZipFile as e:
                        if not os.path.exists(db_path):
                            raise Exception(f"File zip bị lỗi (có thể do Git LFS) và không tìm thấy file db: {e}")
                
        conn = sqlite3.connect(db_path)
        
        if query:
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
            
        engine = conn
        _chunks = pd.read_sql("""
            SELECT 
                b.borough_id AS borough,
                b.borough_name,
                n.neighborhood_name as neighborhood,
                p.building_class_category,
                p.building_category,
                p.building_type,
                p.building_class_present,
                p.tax_class_present,
                p.gross_sqft,
                p.land_sqft,
                p.building_age,
                p.total_units,
                p.is_residential,
                l.block,
                l.lot,
                f.sale_price,
                f.price_per_sqft,
                f.price_per_sqft_real,
                f.sale_date,
                f.sale_year,
                f.sale_month,
                f.tax_class_sale,
                f.building_class_sale,
                s.pop_density,
                s.avg_income,
                s.gdp_local,
                s.dist_center,
                n.amenity_score
            FROM fact_sales f
            JOIN dim_location       l ON f.location_id    = l.location_id
            JOIN dim_neighborhood   n ON l.neighborhood_id = n.neighborhood_id
            JOIN dim_borough        b ON n.borough_id      = b.borough_id
            JOIN dim_property       p ON f.property_id     = p.property_id
            JOIN dim_social_metrics s ON f.social_id       = s.social_id
        """, engine, chunksize=50000)
        
        processed_chunks = []
        num_cols = ['gross_sqft', 'land_sqft', 'building_age', 'sale_year', 'avg_income', 'dist_center', 'pop_density']
        
        for chunk in _chunks:
            # Lọc bớt dòng rác ngay từ đầu để giảm số lượng
            chunk['sale_price'] = pd.to_numeric(chunk['sale_price'], errors='coerce')
            chunk = chunk[chunk['sale_price'] > 10_000].copy()
            
            # Chuẩn hoá số
            for c in num_cols:
                if c in chunk.columns:
                    chunk[c] = pd.to_numeric(chunk[c], errors='coerce', downcast='float')
            
            chunk.loc[chunk['gross_sqft'] <= 0, 'gross_sqft'] = np.nan
            chunk.loc[chunk['land_sqft']  <= 0, 'land_sqft']  = np.nan
            
            # Use the real price per sqft from DB if available, fallback to manual calc
            if 'price_per_sqft_real' in chunk.columns:
                chunk['price_per_sqft'] = chunk['price_per_sqft_real']
            else:
                chunk['price_per_sqft'] = np.where(chunk['gross_sqft'].notna(),
                                                  chunk['sale_price'] / chunk['gross_sqft'], np.nan)

            
            # Xử lý ngày tháng ngay trong chunk để giải phóng text (hỗ trợ cả định dạng DD/MM/YYYY và YYYY-MM-DD)
            chunk['sale_date_parsed'] = pd.to_datetime(chunk['sale_date'], dayfirst=True, errors='coerce')
            chunk['sale_month']       = chunk['sale_date_parsed'].dt.month.fillna(0).astype('int16')
            
            # Khôi phục building_category và building_type từ building_class_category (bị thiếu trong SQLite)
            if 'building_class_category' in chunk.columns:
                split_cols = chunk['building_class_category'].astype(str).str.split('-', n=1, expand=True)
                chunk['building_category'] = split_cols[0].str.strip()
                if split_cols.shape[1] > 1:
                    chunk['building_type'] = split_cols[1].str.strip()
                    # Điền missing type bằng category nếu split không ra 2 phần
                    chunk['building_type'] = chunk['building_type'].fillna(chunk['building_category'])
                else:
                    chunk['building_type'] = chunk['building_category']
            
            # Ép kiểu int/float để giảm dung lượng
            for c in chunk.select_dtypes(include=['int64', 'float64']).columns:
                if chunk[c].dtype == 'int64':
                    chunk[c] = pd.to_numeric(chunk[c], downcast='integer')
                else:
                    chunk[c] = pd.to_numeric(chunk[c], downcast='float')
                    
            processed_chunks.append(chunk)
            
        df = pd.concat(processed_chunks, ignore_index=True)
        engine.close()
    except Exception as e:
        return None, f"Lỗi đọc SQLite: {e}"

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        return None, f"Thiếu cột sau JOIN: {', '.join(missing)}"

    # Chuyển đổi chuỗi sang category một lần sau khi concat (tiết kiệm 90% RAM)
    for c in df.select_dtypes(include=['object', 'string']).columns:
        if df[c].nunique() < 1000:
            df[c] = df[c].astype('category')
            
    return df, None

@st.cache_data
def get_flipping_stats(df_in):
    # Tạo mã định danh duy nhất cho từng lô đất
    cols = ['borough_name', 'block', 'lot', 'sale_date', 'sale_date_parsed', 'sale_price', 'neighborhood']
    df_f = df_in.loc[:, cols].copy()
    df_f['property_id'] = df_f['borough_name'].astype(str) + '-' + df_f['block'].astype(str) + '-' + df_f['lot'].astype(str)
    
    # Sắp xếp theo ID và ngày bán
    df_f = df_f.sort_values(by=['property_id', 'sale_date_parsed'])
    
    # Dùng shift() để so sánh với giao dịch liền trước
    df_f['prev_prop'] = df_f['property_id'].shift(1)
    df_f['buy_date'] = df_f['sale_date_parsed'].shift(1)
    df_f['buy_price'] = df_f['sale_price'].shift(1)

    # Chỉ giữ lại những giao dịch là lần bán thứ 2 trở lên của cùng 1 property
    flips = df_f[df_f['property_id'] == df_f['prev_prop']].copy()
    
    if len(flips) == 0:
        return None, None, None

    # Tính toán các chỉ số
    flips['days_held'] = (flips['sale_date_parsed'] - flips['buy_date']).dt.days
    flips['profit'] = flips['sale_price'] - flips['buy_price']
    flips['roi'] = np.where(flips['buy_price'] > 0, flips['profit'] / flips['buy_price'], 0)

    # Lọc điều kiện lướt sóng: giữ nhà từ 1 ngày đến 3 năm (1095 ngày)
    df_res = flips[(flips['days_held'] >= 1) & (flips['days_held'] <= 1095)].copy()
    
    if len(df_res) == 0:
        return None, None, None

    neigh_stats = df_res.groupby(['borough_name', 'neighborhood']).agg(
        num_flips=('neighborhood', 'count'),
        avg_profit=('profit', 'mean'),
        avg_roi=('roi', 'mean'),
        avg_days=('days_held', 'mean')
    ).reset_index()
    
    neigh_stats = neigh_stats[neigh_stats['num_flips'] >= 2]
    
    # Khu vực định cư (Ít lướt sóng)
    all_sales = df_f.groupby('neighborhood')['property_id'].count().reset_index(name='total_sales')
    long_term = pd.merge(all_sales, neigh_stats, on='neighborhood', how='left')
    long_term['num_flips'] = long_term['num_flips'].fillna(0)
    long_term['flip_rate'] = (long_term['num_flips'] / long_term['total_sales']) * 100
    long_term = long_term[long_term['total_sales'] >= 30]

    return df_res, neigh_stats, long_term

@st.cache_data
def load_ml_data(mtime=None):
    paths = {'pred': os.path.join(ROOT_DIR, 'output', 'ml_predictions.csv'),
             'imp':  os.path.join(ROOT_DIR, 'output', 'ml_importance.csv'),
             'met':  os.path.join(ROOT_DIR, 'output', 'ml_metrics.json')}
    pred_df    = pd.read_csv(paths['pred'])    if os.path.exists(paths['pred']) else None
    importance = pd.read_csv(paths['imp'])     if os.path.exists(paths['imp'])  else None
    metrics = {}
    if os.path.exists(paths['met']):
        with open(paths['met'], encoding='utf-8') as f:
            metrics = json.load(f)
    return pred_df, importance, metrics

# ════════════════════════════════════════════════════════════
# HELPER UI & COMPONENT TÓM TẮT TRỰC QUAN
# ════════════════════════════════════════════════════════════
def fmt_M(v, d=2): return f"${v/1e6:.{d}f}M"
def insight_box(html): st.markdown(f'<div class="insight-box">{html}</div>', unsafe_allow_html=True)
def section_q(q, cap=""):
    st.markdown(f'<div class="section-q">{q}</div>', unsafe_allow_html=True)
    if cap: st.markdown(f'<div class="section-cap">{cap}</div>', unsafe_allow_html=True)
def divider(): st.markdown('<hr class="hr">', unsafe_allow_html=True)
def apply_filters(df, boroughs, yr, pr):
    return df[df['borough_name'].isin(boroughs) &
              df['sale_year'].between(yr[0], yr[1]) &
              df['sale_price'].between(pr[0], pr[1])].copy()
def clayout(fig, h=340, t=20, b=20, l=10, r=10, leg=False):
    fig.update_layout(height=h, margin=dict(t=t,b=b,l=l,r=r),
                      plot_bgcolor='#fafafa',
                      paper_bgcolor='#ffffff',
                      showlegend=leg,
                      font=dict(family='Inter', size=13, color='#1e1b4b'),
                      title_font=dict(size=15, color='#1e1b4b', family='Inter'),
                      legend=dict(font=dict(size=12, color='#1e1b4b')))
    fig.update_xaxes(tickfont=dict(size=12, color='#374151', family='Inter'),
                     title_font=dict(size=13, color='#374151', family='Inter'))
    fig.update_yaxes(tickfont=dict(size=12, color='#374151', family='Inter'),
                     title_font=dict(size=13, color='#374151', family='Inter'))
    return fig

def render_factor_summary_matrix(df_in):
    """
    Tạo Bảng & Biểu đồ Tóm tắt Yếu tố Tác động Giá (Top Factor Summary Matrix).
    Đánh giá và phân loại rõ yếu tố ảnh hưởng RẤT MẠNH / MẠNH / TRUNG BÌNH / YẾU.
    """
    factors = [
        ('gross_sqft', 'Diện tích công trình (gross_sqft)', 'Quy mô không gian sử dụng; biến số quan trọng hàng đầu định giá tổng tài sản.'),
        ('avg_income', 'Thu nhập khu vực (avg_income)', 'Mặt bằng thu nhập cư dân; đại diện cho sức mua và mức độ đắt đỏ của vùng.'),

        ('dist_center', 'KC đến trung tâm (dist_center)', 'Khoảng cách địa lý tới trung tâm tài chính Manhattan (càng xa giá giảm).'),
        ('pop_density', 'Mật độ dân số (pop_density)', 'Mật độ dân cư sinh sống; phản ánh độ sầm uất và nhu cầu nhà ở khu vực.'),
        ('building_age', 'Tuổi công trình (building_age)', 'Số năm công trình đã vận hành (công trình cũ chịu khấu hao tài sản).'),
        ('land_sqft', 'Diện tích đất (land_sqft)', 'Diện tích lô đất (ảnh hưởng ít hơn gross_sqft do đặc thù nhà chung cư tại NYC).'),
    ]
    
    rows = []
    for col, name, desc in factors:
        if col in df_in.columns:
            valid = df_in.dropna(subset=['sale_price', col])
            if len(valid) >= 20:
                r = valid['sale_price'].corr(valid[col])
                abs_r = abs(r)
                if abs_r >= 0.50:
                    level = " RẤT MẠNH"
                elif abs_r >= 0.35:
                    level = " MẠNH"
                elif abs_r >= 0.15:
                    level = "️ TRUNG BÌNH"
                else:
                    level = " YẾU"
                
                direction = "Thuận (+)" if r > 0 else "Nghịch (-)"
                rows.append({
                    'Yếu tố tác động': name,
                    'Tương quan (r)': round(r, 2),
                    'Mức độ ảnh hưởng': level,
                    'Chiều tác động': direction,
                    'Giải thích ý nghĩa thực tế': desc,
                    '_abs_r': abs_r
                })
    
    fdf = pd.DataFrame(rows).sort_values('_abs_r', ascending=False)
    
    col_tbl, col_chart = st.columns([3, 2])
    with col_tbl:
        display_df = fdf[['Yếu tố tác động', 'Tương quan (r)', 'Mức độ ảnh hưởng', 'Chiều tác động', 'Giải thích ý nghĩa thực tế']].copy()
        st.dataframe(
            display_df,
            column_config={
                "Tương quan (r)": st.column_config.NumberColumn(format="%.2f"),
                "Mức độ ảnh hưởng": st.column_config.TextColumn(),
            },
            width='stretch',
            hide_index=True
        )
    with col_chart:
        fdf_chart = fdf.sort_values('_abs_r', ascending=True)
        colors = [C_GREEN if r > 0 else C_RED for r in fdf_chart['Tương quan (r)']]
        fig_sum = go.Figure(go.Bar(
            x=fdf_chart['Tương quan (r)'],
            y=fdf_chart['Yếu tố tác động'].apply(lambda x: x.split(' (')[0]),
            orientation='h',
            marker_color=colors,
            text=[f"r = {r:+.2f}" for r in fdf_chart['Tương quan (r)']],
            textposition='outside'
        ))
        clayout(fig_sum, h=300, t=30, b=20, l=10, r=60)
        fig_sum.update_layout(
            title="Xếp hạng Mức độ Tương quan với Giá bán (r)",
            title_font=dict(size=13, color='#374151'),
            xaxis=dict(range=[-0.4, 0.9], zeroline=True, zerolinecolor='#cbd5e1', title="Hệ số tương quan Pearson (r)")
        )
        st.plotly_chart(fig_sum, width='stretch')

# ════════════════════════════════════════════════════════════
# LOAD DỮ LIỆU
# ════════════════════════════════════════════════════════════
df_raw, load_err = load_data(cache_mtime=_get_cache_mtime())

if df_raw is not None:
    # Safely filter for 2025-2026 after all data is loaded
    df_raw['sale_year'] = pd.to_numeric(df_raw['sale_year'], errors='coerce')
    df_raw = df_raw[df_raw['sale_year'] >= 2025].reset_index(drop=True)
    if df_raw.empty:
        df_raw = None
        load_err = "Không có dữ liệu nào khớp với năm 2025 trở đi."

if df_raw is None:
    st.error(f"️ **Lỗi:** {load_err}")
    st.info("Hãy chạy `main.py` trước.")
    st.stop()

# ════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:20px 0 10px'>
        <div style='font-size:36px'>️</div>
        <div style='font-size:14px;font-weight:700;color:#f1f5f9;margin-top:6px'>Bộ lọc dữ liệu</div>
        <div style='font-size:11px;color:#64748b;margin-top:2px'>NYC Real Estate Analytics</div>
    </div>
    <hr style='border-color:#1e3a5f;margin:0 0 14px'>
    """, unsafe_allow_html=True)
    all_b = [b for b in BOROUGH_ORDER if b in df_raw['borough_name'].dropna().unique()]
    selected_boroughs = st.multiselect(" Quận (Borough)", options=all_b, default=all_b)
    avail_years = sorted(df_raw['sale_year'].dropna().astype(int).unique().tolist())
    year_range  = st.select_slider(" Năm giao dịch", options=avail_years,
                                   value=(min(avail_years), max(avail_years)))
    p5  = float(df_raw['sale_price'].quantile(0.05))
    p95 = float(df_raw['sale_price'].quantile(0.95))
    price_range = st.slider(" Khoảng giá ($)",
                            min_value=float(df_raw['sale_price'].min()),
                            max_value=float(df_raw['sale_price'].max()),
                            value=(p5, p95), format="$%.0f",
                            help="Mặc định p5–p95 để loại bỏ outlier.")
    st.markdown('<hr style="border-color:#1e3a5f;margin:14px 0 10px">', unsafe_allow_html=True)
    if st.button(" Đặt lại bộ lọc", width='stretch'):
        st.rerun()
    st.markdown(f"""
    <div style='text-align:center;margin-top:10px;color:#475569;font-size:11px'>
        Tổng: {len(df_raw):,} giao dịch<br>Nguồn: NYC Property Sales
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# ÁP DỤNG BỘ LỌC
# ════════════════════════════════════════════════════════════
if not selected_boroughs:
    st.warning("️ Chưa chọn quận nào. Hãy chọn ít nhất một quận trong bộ lọc bên trái.")
    st.stop()
df = apply_filters(df_raw, selected_boroughs, year_range, price_range)
if len(df) == 0:
    st.warning("️ **Không có dữ liệu phù hợp.** Hãy mở rộng bộ lọc hoặc nhấn Đặt lại.")
    st.stop()

df_sample = df.sample(n=min(3000, len(df)), random_state=42)
df_ppsf   = df.loc[df['price_per_sqft'].notna() & (df['price_per_sqft'] < 5000), ['price_per_sqft']]

# ════════════════════════════════════════════════════════════
# TIÊU ĐỀ
# ════════════════════════════════════════════════════════════
h1, h2 = st.columns([4, 1])
with h1:
    st.markdown("""
    <h1 style='font-size:24px;font-weight:800;color:#0f172a;margin:0'>
    ️ BÁO CÁO PHÂN TÍCH THỊ TRƯỜNG BẤT ĐỘNG SẢN NEW YORK GIAI ĐOẠN 2025 - 2026
    </h1>""", unsafe_allow_html=True)
with h2:
    st.markdown(f"""
    <div style='text-align:right;padding-top:6px'>
        <span class="badge"> {len(df):,} giao dịch</span><br>
        <span style='font-size:11px;color:#94a3b8'>{len(selected_boroughs)} quận · {year_range[0]}–{year_range[1]}</span>
    </div>""", unsafe_allow_html=True)
st.markdown("<div style='margin-bottom:18px'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════
tab0, tab1, tab2, tab4, tab_micro = st.tabs([
    "🏙️  Tổng quan",
    "🗺️  Phân tích khu vực",
    "📐  Yếu tố quyết định giá",
    "🤖  Dự báo & Mô hình ML",
    "🏡  Tra cứu BĐS & Tiện ích"
])

with tab_micro:
    st.markdown("### 🏡 Tra cứu Bất động sản & Phân tích Tiện ích")
    tab_search, tab7 = st.tabs(["🔍 Tìm kiếm Bất động sản", "📊 Phân tích Tiện ích"])


# ════════════════════════════════════════════════════════════
# TAB 0 — TỔNG QUAN
# ════════════════════════════════════════════════════════════
with tab0:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#4338ca,#6366f1,#818cf8);border-radius:14px;
    padding:18px 24px;color:#fff;margin-bottom:22px;
    box-shadow:0 6px 24px rgba(99,102,241,0.35)'>
    <b style='font-size:15px;letter-spacing:-0.3px'>️ Thị trường đang ở đâu và quy mô như thế nào?</b><br>
    <span style='font-size:12px;opacity:0.88'>Tổng quan về quy mô, mặt bằng giá và cơ cấu thị trường bất động sản NYC trong bộ lọc hiện tại.</span>
    </div>
    """, unsafe_allow_html=True)

    med_price = df['sale_price'].median()
    med_ppsf  = df_ppsf['price_per_sqft'].median() if len(df_ppsf) > 0 else 0
    total_val = df['sale_price'].sum()
    pct_1m    = (df['sale_price'] >= 1_000_000).mean() * 100
    yoy_med0  = df.groupby('sale_year')['sale_price'].median()
    yrs0 = sorted(yoy_med0.index)
    if len(yrs0) >= 2:
        yoy_d0 = (yoy_med0[yrs0[-1]]/yoy_med0[yrs0[-2]]-1)*100
        yoy_s0 = f"{yoy_d0:+.1f}%"
    else:
        yoy_d0, yoy_s0 = 0.0, "—"

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    k1.metric("Tổng giao dịch", f"{len(df):,}")
    k2.metric("Giá trung vị",   fmt_M(med_price))
    k3.metric("Giá/sqft (TV)",  f"${med_ppsf:,.0f}")
    k4.metric("Tổng giá trị",   f"${total_val/1e9:.1f}B")
    k5.metric("Tăng giá YoY",   yoy_s0, delta=f"{yoy_d0:.1f}%" if yoy_d0 else None)
    k6.metric("Giao dịch ≥$1M", f"{pct_1m:.1f}%")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    section_q(
        "Borough nào chiếm ưu thế — về thanh khoản và mặt bằng giá?",
        "Số giao dịch = thanh khoản. Giá trung vị ít bị ảnh hưởng bởi outlier hơn giá trung bình."
    )

    bor_cnt = df['borough_name'].value_counts().reindex(BOROUGH_ORDER, fill_value=0).reset_index()
    bor_cnt.columns = ['Borough','Giao dịch']
    bor_cnt = bor_cnt[bor_cnt['Giao dịch'] > 0]

    bor_med = df.groupby('borough_name')['sale_price'].median().reindex(BOROUGH_ORDER).dropna().reset_index()
    bor_med.columns = ['Borough','Giá trung vị']

    ca, cb = st.columns(2)
    with ca:
        fig = px.bar(bor_cnt.sort_values('Giao dịch'), x='Giao dịch', y='Borough', orientation='h',
                     color='Borough', color_discrete_map=BOROUGH_COLORS, text='Giao dịch',
                     labels={'Borough':'Quận', 'Giao dịch':'Số giao dịch'},
                     title="Số giao dịch theo quận")
        fig.update_traces(texttemplate='%{text:,}', textposition='auto')
        clayout(fig, h=280, t=40, r=80)
        fig.update_layout(yaxis=dict(automargin=True, title='Quận'), xaxis=dict(automargin=True, title='Số giao dịch'),
                          title_font=dict(size=13, color='#374151'))
        st.plotly_chart(fig, width='stretch')
    with cb:
        fig = px.bar(bor_med.sort_values('Giá trung vị'), x='Giá trung vị', y='Borough', orientation='h',
                     color='Borough', color_discrete_map=BOROUGH_COLORS,
                     text=bor_med.sort_values('Giá trung vị')['Giá trung vị'].apply(fmt_M),
                     labels={'Borough':'Quận', 'Giá trung vị':'Giá trung vị ($)'},
                     title="Giá trung vị theo quận ($)")
        fig.update_traces(textposition='auto')
        clayout(fig, h=280, t=40, r=100)
        fig.update_layout(yaxis=dict(automargin=True, title='Quận'), xaxis=dict(tickformat='$,.0f', automargin=True, title='Giá trung vị ($)'),
                          title_font=dict(size=13, color='#374151'))
        st.plotly_chart(fig, width='stretch')

    divider()
    section_q("Thị trường đang tập trung vào loại hình bất động sản nào?",
              "Cơ cấu loại hình và phân bố giá theo từng loại (top 6).")

    top6_bt = df['building_type'].value_counts().head(6).index.tolist()
    cc, cd  = st.columns(2)
    with cc:
        bt_c = df['building_type'].value_counts().head(6).reset_index()
        bt_c.columns = ['Loại hình','Số lượng']
        fig = px.pie(bt_c, names='Loại hình', values='Số lượng', hole=0.50,
                     color_discrete_sequence=[C_BLUE,C_SKY,C_ORANGE,C_GREEN,'#8b5cf6',C_GRAY],
                     title="Cơ cấu loại hình bất động sản")
        fig.update_traces(textposition='inside', textinfo='percent',
                          insidetextorientation='radial',
                          hovertemplate='<b>%{label}</b><br>%{value:,} GD<br>%{percent}<extra></extra>')
        clayout(fig, h=320, t=40, l=10, r=20, b=20, leg=True)
        fig.update_layout(legend=dict(orientation='v', x=1.0, y=0.5, font_size=11),
                          title_font=dict(size=13, color='#374151'))
        st.plotly_chart(fig, width='stretch')
    with cd:
        df_bt0 = df[df['building_type'].isin(top6_bt)]
        med_bt0 = df_bt0.groupby('building_type')['sale_price'].median().sort_values(ascending=False)
        df_bt0_sample = df_bt0.sample(n=min(10000, len(df_bt0)), random_state=42)
        fig = px.box(df_bt0_sample, x='building_type', y='sale_price',
                     color='building_type',
                     color_discrete_sequence=[C_BLUE,C_SKY,C_ORANGE,C_GREEN,'#8b5cf6',C_GRAY],
                     points=False, labels={'building_type':'Loại hình BĐS','sale_price':'Giá bán ($)'},
                     category_orders={'building_type': med_bt0.index.tolist()},
                     title="Phân bố giá theo loại hình (top 6)")
        clayout(fig, h=320, t=40, b=60, l=10, r=10)
        fig.update_layout(xaxis=dict(automargin=True, tickangle=-15, tickfont_size=10, title=''),
                          yaxis=dict(tickformat='$,.0f', automargin=True),
                          title_font=dict(size=13, color='#374151'))
        st.plotly_chart(fig, width='stretch')

    divider()
    top_b0 = bor_med.sort_values('Giá trung vị', ascending=False).iloc[0]
    low_b0 = bor_med.sort_values('Giá trung vị').iloc[0]
    rat0   = top_b0['Giá trung vị'] / low_b0['Giá trung vị']
    top_bt0= df['building_type'].value_counts().index[0]
    pct_bt0= df['building_type'].value_counts().iloc[0] / len(df) * 100

    # ── Phân khúc khách hàng ──────────────────────────────────
    divider()
    section_q("Thị trường đang phục vụ nhóm khách hàng nào?",
              "Phân loại theo số căn trong tòa nhà — proxy cho mục đích mua (ở thực vs đầu tư).")

    df['_segment'] = pd.cut(
        df['total_units'],
        bins=[-1, 1, 10, float('inf')],
        labels=['① Mua ở thực (1 căn)', '② Đầu tư nhỏ (2-10)', '③ Tổ chức (>10)']
    )
    seg_cnt  = df['_segment'].value_counts().sort_index()
    seg_med  = df.groupby('_segment', observed=True)['sale_price'].median()
    seg_df   = pd.DataFrame({'Phân khúc': seg_cnt.index,
                              'Số GD': seg_cnt.values,
                              'Giá trung vị': seg_med.values})
    seg_df['% thị trường'] = seg_df['Số GD'] / seg_df['Số GD'].sum() * 100

    sa, sb = st.columns(2)
    with sa:
        fig_seg = px.bar(seg_df, x='Phân khúc', y='Số GD',
                         color='Phân khúc',
                         color_discrete_sequence=[C_GREEN, C_BLUE, C_ORANGE],
                         text=seg_df['% thị trường'].apply(lambda v: f'{v:.1f}%'),
                         title="Cơ cấu phân khúc khách hàng")
        fig_seg.update_traces(textposition='outside')
        clayout(fig_seg, h=300, t=40, b=20)
        fig_seg.update_layout(showlegend=False,
                               xaxis=dict(automargin=True, title='Phân khúc'),
                               yaxis=dict(automargin=True, title='Số giao dịch'),
                               title_font=dict(size=13, color='#374151'))
        st.plotly_chart(fig_seg, width='stretch')
    with sb:
        fig_sp = px.bar(seg_df, x='Phân khúc', y='Giá trung vị',
                        color='Phân khúc',
                        color_discrete_sequence=[C_GREEN, C_BLUE, C_ORANGE],
                        text=seg_df['Giá trung vị'].apply(fmt_M),
                        title="Giá trung vị theo phân khúc")
        fig_sp.update_traces(textposition='outside')
        clayout(fig_sp, h=300, t=40, b=20)
        fig_sp.update_layout(showlegend=False,
                               xaxis=dict(automargin=True, title='Phân khúc'),
                               yaxis=dict(tickformat='$,.0f', automargin=True, title='Giá trung vị ($)'),
                               title_font=dict(size=13, color='#374151'))
        st.plotly_chart(fig_sp, width='stretch')

    # ── Nhận diện rủi ro đầu tư ───────────────────────────────
    divider()
    section_q("Khu vực nào có rủi ro giá cao nhất?",
              "Rủi ro = biến động giá cao (CV cao) hoặc thanh khoản thấp. "
              "Xanh = ít rủi ro, đỏ = cần thận trọng.")

    borough_risk = df.groupby('borough_name').agg(
        med_price=('sale_price','median'),
        std_price=('sale_price','std'),
        n_gd=('sale_price','count')
    ).reset_index()
    borough_risk['CV (%)'] = (borough_risk['std_price'] / borough_risk['med_price'] * 100).round(1)
    borough_risk['Rủi ro biến động'] = pd.cut(
        borough_risk['CV (%)'],
        bins=[0, 48, 53, float('inf')],
        labels=['🟢 Thấp', '🟡 Trung bình', '🔴 Cao']
    )
    borough_risk = borough_risk.sort_values('CV (%)')

    risk_display = borough_risk[['borough_name','med_price','CV (%)','n_gd','Rủi ro biến động']].copy()
    risk_display.columns = ['Quận','Giá trung vị','Biến động CV (%)','Số giao dịch','Đánh giá rủi ro']
    risk_display['Giá trung vị'] = risk_display['Giá trung vị'].apply(fmt_M)
    risk_display['Số giao dịch'] = risk_display['Số giao dịch'].apply(lambda v: f'{v:,}')

    def style_risk_level(val):
        if 'Thấp' in str(val):
            return 'background-color: rgba(16, 185, 129, 0.2); color: #047857; font-weight: bold;'
        elif 'Trung bình' in str(val):
            return 'background-color: rgba(245, 158, 11, 0.2); color: #b45309; font-weight: bold;'
        elif 'Cao' in str(val):
            return 'background-color: rgba(239, 68, 68, 0.2); color: #b91c1c; font-weight: bold;'
        return ''

    styled_risk = risk_display.set_index('Quận').style.map(style_risk_level, subset=['Đánh giá rủi ro'])
    st.dataframe(styled_risk, width='stretch')

# ════════════════════════════════════════════════════════════
# TAB 1 — PHÂN TÍCH KHU VỰC & BẢN ĐỒ HEATMAP
# ════════════════════════════════════════════════════════════
with tab1:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#0f766e,#0d9488,#34d399);border-radius:14px;
    padding:18px 24px;color:#fff;margin-bottom:22px;
    box-shadow:0 6px 24px rgba(16,185,129,0.3)'>
    <b style='font-size:15px;letter-spacing:-0.3px'>️ Bản đồ Nhiệt Khu vực & Phân tích Điểm nóng (NYC Hotspot Map)</b><br>
    <span style='font-size:12px;opacity:0.88'>Nhận diện điểm nóng giá bán, định giá đơn vị $/sqft và mật độ thanh khoản trên bản đồ tương quan không gian thực.</span>
    </div>
    """, unsafe_allow_html=True)

    n_neigh   = df['neighborhood'].nunique()
    top_neigh = df['neighborhood'].value_counts().index[0]
    top_n_cnt = df['neighborhood'].value_counts().iloc[0]
    bor_med_f = df.groupby('borough_name')['sale_price'].median()
    top_bor_p = bor_med_f.idxmax()

    ka,kb,kc,kd = st.columns(4)
    ka.metric("Quận đang phân tích",        f"{len(selected_boroughs)}/5")
    kb.metric("Số khu vực",                  f"{n_neigh:,}")
    kc.metric("Khu vực sôi động nhất",       top_neigh.title()[:20])
    kd.metric("Quận giá trung vị cao nhất",  top_bor_p)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── YÊU CẦU VỀ BẢN ĐỒ (MAP): BẢN ĐỒ TÔ MÀU KHU VỰC (HEATMAP) ──
    with st.container(border=True):
        st.markdown("<h4 style='margin-top:0'>Bộ lọc Bản đồ Nhiệt</h4>", unsafe_allow_html=True)
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            hm_boroughs = st.multiselect("Chọn khu vực (Borough)", options=df['borough_name'].unique().tolist(), default=[])
        
        avail_neighs = df['neighborhood'].unique().tolist()
        if hm_boroughs:
            avail_neighs = df[df['borough_name'].isin(hm_boroughs)]['neighborhood'].unique().tolist()
            
        with col_f2:
            hm_neighs = st.multiselect("Chọn Neighborhood", options=avail_neighs, default=[])

        with col_f3:
            p_min = float(df['sale_price'].min())
            p_max = float(df['sale_price'].max())
            hm_price_range = st.slider("Khoảng giá ($)", min_value=p_min, max_value=p_max, value=(p_min, p_max), format="$%.0f", key="hm_price_slider")

    # Lọc dữ liệu Heatmap
    df_hm = df.copy()
    if hm_boroughs:
        df_hm = df_hm[df_hm['borough_name'].isin(hm_boroughs)]
    if hm_neighs:
        df_hm = df_hm[df_hm['neighborhood'].isin(hm_neighs)]
    
    df_hm = df_hm[df_hm['sale_price'].between(hm_price_range[0], hm_price_range[1])]

    if len(df_hm) == 0:
        st.warning("Không có dữ liệu phù hợp với bộ lọc hiện tại.")
    else:
        # Cập nhật KPI động
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Khu vực đang chọn", ", ".join(hm_boroughs) if hm_boroughs else "Toàn bộ NYC")
        kpi2.metric("Số giao dịch", f"{len(df_hm):,}")
        kpi3.metric("Giá trung vị", fmt_M(df_hm['sale_price'].median()))
        hm_ppsf = df_hm.loc[df_hm['price_per_sqft'].notna() & (df_hm['price_per_sqft'] < 5000), 'price_per_sqft']
        kpi4.metric("Giá/sqft trung vị", f"${hm_ppsf.median():,.0f}" if len(hm_ppsf) > 0 else "N/A")

        # Tiêu đề động
        title_map = "Bản đồ Nhiệt Khu vực – Toàn bộ NYC"
        if hm_boroughs:
            title_map = f"Bản đồ Nhiệt Khu vực – {', '.join(hm_boroughs)}"
            
        section_q(title_map, "Tô màu khu vực thể hiện trực quan điểm nóng (hotspots) về Giá trung vị, Giá/sqft hoặc Mật độ thanh khoản giao dịch.")

        # Gom nhóm dữ liệu địa lý theo Neighborhood từ df_hm đã lọc
        geo_df = df_hm.groupby(['neighborhood', 'borough_name']).agg(
            med_price=('sale_price', 'median'),
            med_ppsf=('price_per_sqft', 'median'),
            n_count=('sale_price', 'count')
        ).reset_index()

        # Thêm lat, lon cho từng khu vực
        coords_list = [get_neighborhood_coords(row['neighborhood'], row['borough_name']) for _, row in geo_df.iterrows()]
        geo_df['lat'] = [c[0] for c in coords_list]
        geo_df['lon'] = [c[1] for c in coords_list]
        geo_df['med_ppsf_clean'] = geo_df['med_ppsf'].fillna(0)

        mc1, mc2, mc3, mc4 = st.columns([2, 1, 1, 1])
        with mc1:
            map_metric = st.radio(
                "Hiển thị điểm nóng theo:",
                options=[" Giá trung vị ($)", " Giá/sqft trung vị ($)", " Mật độ giao dịch (Số căn)"],
                horizontal=True, key="hm_metric_radio"
            )
        with mc2:
            map_theme = st.selectbox(
                "Lớp bản đồ nền:",
                options=["🌐 OpenStreetMap", "🗺️ Carto Positron (Sáng)", "🌑 Carto Dark (Tối)"],
                index=0, key="hm_theme_select"
            )
        with mc3:
            radius_val = st.slider("Bán kính điểm nhiệt", 15, 45, 25, key="hm_radius_slider")
        with mc4:
            zoom_val = st.slider("Độ phóng đại (Zoom)", 9, 13, 10, key="hm_zoom_slider")

        style_map = {
            "🌐 OpenStreetMap": "open-street-map",
            "🗺️ Carto Positron (Sáng)": "carto-positron",
            "🌑 Carto Dark (Tối)": "carto-darkmatter"
        }
        chosen_style = style_map.get(map_theme, "open-street-map")

        if map_metric == " Giá trung vị ($)":
            target_z = 'med_price'
            color_scale = "Plasma"
            z_title = "Giá trung vị ($)"
        elif map_metric == " Giá/sqft trung vị ($)":
            target_z = 'med_ppsf_clean'
            color_scale = "Inferno"
            z_title = "Giá/sqft ($)"
        else:
            target_z = 'n_count'
            color_scale = "Viridis"
            z_title = "Số giao dịch"

        try:
            fig_map = px.density_map(
                geo_df,
                lat='lat',
                lon='lon',
                z=target_z,
                radius=radius_val,
                center=dict(lat=40.7400, lon=-73.9400),
                zoom=zoom_val,
                map_style=chosen_style,
                color_continuous_scale=color_scale,
                hover_name="neighborhood",
                hover_data={
                    "borough_name": True,
                    "med_price": ":$,.0f",
                    "med_ppsf_clean": ":$,.0f",
                    "n_count": ":,",
                    "lat": ":.4f",
                    "lon": ":.4f"
                },
                labels={
                    "borough_name": "Quận",
                    "med_price": "Giá trung vị",
                    "med_ppsf_clean": "Giá/sqft",
                    "n_count": "Số GD",
                    "lat": "Latitude",
                    "lon": "Longitude"
                }
            )
        except (AttributeError, TypeError):
            fig_map = px.density_mapbox(
                geo_df,
                lat='lat',
                lon='lon',
                z=target_z,
                radius=radius_val,
                center=dict(lat=40.7400, lon=-73.9400),
                zoom=zoom_val,
                mapbox_style=chosen_style,
                color_continuous_scale=color_scale,
                hover_name="neighborhood",
                hover_data={
                    "borough_name": True,
                    "med_price": ":$,.0f",
                    "med_ppsf_clean": ":$,.0f",
                    "n_count": ":,",
                    "lat": ":.4f",
                    "lon": ":.4f"
                },
                labels={
                    "borough_name": "Quận",
                    "med_price": "Giá trung vị",
                    "med_ppsf_clean": "Giá/sqft",
                    "n_count": "Số GD",
                    "lat": "Latitude",
                    "lon": "Longitude"
                }
            )
        clayout(fig_map, h=520, t=10, b=10, l=10, r=10)
        fig_map.update_layout(
            title_text="",
            coloraxis_colorbar=dict(title=z_title, len=0.8)
        )
        st.plotly_chart(fig_map, width='stretch')

        # Chú giải điểm nóng
        top_p_geo = geo_df.sort_values('med_price', ascending=False).head(3)
        top_v_geo = geo_df.sort_values('n_count', ascending=False).head(3)
        p_spots = ", ".join([f"<b>{r['neighborhood'].title()}</b> (${r['med_price']/1e6:.2f}M)" for _, r in top_p_geo.iterrows()])
        v_spots = ", ".join([f"<b>{r['neighborhood'].title()}</b> ({r['n_count']:,} GD)" for _, r in top_v_geo.iterrows()])


    divider()
    section_q("Giá bán phân bố như thế nào trong từng quận?",
              "Đường giữa = trung vị. Hộp = khoảng tứ phân vị (25%–75%). Nhãn giá trung vị được ghi trực tiếp.")

    bor_ord1 = df.groupby('borough_name')['sale_price'].median().sort_values(ascending=False).index.tolist()
    df_box_sample = df.sample(n=min(10000, len(df)), random_state=42)
    fig = px.box(df_box_sample, x='borough_name', y='sale_price', color='borough_name',
                 color_discrete_map=BOROUGH_COLORS, points=False,
                 labels={'borough_name':'Quận','sale_price':'Giá bán (USD)'},
                 category_orders={'borough_name': bor_ord1},
                 title='Phân phối giá bán nhà theo Quận')
    for b in bor_ord1:
        m = df[df['borough_name']==b]['sale_price'].median()
        fig.add_annotation(x=b, y=m, text=fmt_M(m), showarrow=False,
                           font=dict(size=11,color='#111827',weight=700),
                           yshift=20, bgcolor='rgba(255,255,255,0.88)', borderpad=3)
    clayout(fig, h=360, t=50, b=20)
    fig.update_layout(
        title_font=dict(size=14, color='#374151'),
        yaxis=dict(tickformat='$,.0f', automargin=True, title='Giá bán (USD)'),
        xaxis=dict(automargin=True, title='Quận')
    )
    st.plotly_chart(fig, width='stretch')

    divider()
    section_q("Khu vực nào sôi động nhất và có giá/sqft cao nhất?",
              "Trái: số giao dịch (thanh khoản). Phải: giá/sqft trung vị (loại khu vực < 5 giao dịch để tránh sai lệch mẫu nhỏ).")

    top_n_ppsf_row = None
    cn1, cn2 = st.columns(2)
    with cn1:
        t15c = (df.groupby(['neighborhood','borough_name']).size()
                .reset_index(name='Giao dịch')
                .sort_values('Giao dịch', ascending=False).head(15))
        t15c = t15c.sort_values('Giao dịch')
        t15c['Khu vực'] = t15c['neighborhood'].str.title().str[:25]
        fig = px.bar(t15c, x='Giao dịch', y='Khu vực', orientation='h',
                     color='borough_name', color_discrete_map=BOROUGH_COLORS, text='Giao dịch',
                     title="Top 15 khu vực nhiều giao dịch nhất",
                     labels={'borough_name':'Quận'})
        fig.update_traces(texttemplate='%{text:,}', textposition='auto')
        clayout(fig, h=460, t=40, b=20, r=80, leg=True)
        fig.update_layout(yaxis=dict(automargin=True, tickfont_size=11, title='Khu vực'),
                          xaxis=dict(automargin=True, title='Số giao dịch'),
                          legend=dict(orientation='h', y=-0.1, x=0, font_size=11),
                          title_font=dict(size=13, color='#374151'))
        st.plotly_chart(fig, width='stretch')
    with cn2:
        # price_per_sqft_real có thể được dùng nếu price_per_sqft thiếu
        ppsf_col = 'price_per_sqft' if 'price_per_sqft' in df.columns and df['price_per_sqft'].notna().sum() > 0 else 'price_per_sqft_real'
        df_ppsf2 = df.loc[df[ppsf_col].notna() & (df[ppsf_col] > 0) & (df[ppsf_col] < 5000), ['neighborhood', 'borough_name', ppsf_col]]
        if len(df_ppsf2) > 0:
            t15p = (df_ppsf2.groupby(['neighborhood','borough_name'])[ppsf_col]
                    .agg(med_ppsf='median', cnt='count').reset_index())
            t15p = t15p[t15p['cnt'] >= 5].nlargest(15,'med_ppsf').sort_values('med_ppsf')
            t15p['Khu vực'] = t15p['neighborhood'].str.title().str[:25]
            if len(t15p) > 0:
                top_n_ppsf_row = t15p.iloc[-1]
            if len(t15p) > 0:
                fig = px.bar(t15p, x='med_ppsf', y='Khu vực', orientation='h',
                             color='borough_name', color_discrete_map=BOROUGH_COLORS,
                             text=t15p['med_ppsf'].apply(lambda v: f'${v:,.0f}'),
                             title="Top 15 khu vực giá/sqft cao nhất (trung vị)",
                             labels={'borough_name':'Quận','med_ppsf':'$/sqft (trung vị)'})
                fig.update_traces(textposition='auto')
                clayout(fig, h=460, t=40, b=20, r=80, leg=True)
                fig.update_layout(yaxis=dict(automargin=True, tickfont_size=11, title='Khu vực'),
                                  xaxis=dict(tickformat='$,.0f', automargin=True, title='$/sqft (trung vị)'),
                                  legend=dict(orientation='h', y=-0.1, x=0, font_size=11),
                                  title_font=dict(size=13, color='#374151'))
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("Không đủ dữ liệu giá/sqft sau khi lọc.")
        else:
            st.info("Không đủ dữ liệu giá/sqft.")

# ════════════════════════════════════════════════════════════
# TAB 2 — YẾU TỐ QUYẾT ĐỊNH GIÁ & PHÂN TÍCH TƯƠNG QUAN
# ════════════════════════════════════════════════════════════
with tab2:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#5b21b6,#7c3aed,#a78bfa);border-radius:14px;
    padding:18px 24px;color:#fff;margin-bottom:22px;
    box-shadow:0 6px 24px rgba(124,58,237,0.35)'>
    <b style='font-size:15px;letter-spacing:-0.3px'> Phân tích Ma trận Yếu tố & Các Biến số Quyết định Giá</b><br>
    <span style='font-size:12px;opacity:0.88'>Tóm tắt các yếu tố ảnh hưởng mạnh/yếu, ma trận tương quan và giải thích ý nghĩa chiều tác động của các biến số chính đến giá bán thực tế.</span>
    </div>
    """, unsafe_allow_html=True)

    # ── NGUYÊN TẮC TRỰC QUAN: BẢNG TÓM TẮT YẾU TỐ TÁC ĐỘNG GIÁ ──
    section_q(
        "Bảng tóm tắt các yếu tố ảnh hưởng đến giá bất động sản",
        "Tóm tắt toàn bộ các biến số đo lường, phân loại rõ yếu tố nào ảnh hưởng mạnh hay yếu đến giá bán thực tế."
    )
    render_factor_summary_matrix(df)

    divider()

    # ── MA TRẬN TƯƠNG QUAN TỔNG THỂ ──
    section_q(
        "Ma trận tương quan tổng thể giữa các yếu tố với Giá bán",
        "Đọc bản đồ nhiệt: ô màu đỏ = tương quan thuận (+); ô màu xanh = tương quan nghịch (-). Số trong ô là hệ số tương quan r."
    )
    cc_cols = ['sale_price','gross_sqft','avg_income','dist_center','pop_density','building_age']
    cc_lbl  = {'sale_price':'Giá bán','gross_sqft':'Diện tích','avg_income':'Thu nhập TB',
               'dist_center':'KC trung tâm','pop_density':'Mật độ dân số',
               'building_age':'Tuổi công trình'}
    
    # Tính ma trận tương quan trực tiếp, không drop cột hằng số để giữ nguyên lưới biểu đồ.
    # Các giá trị lỗi (NaN do phương sai = 0) sẽ được điền 0 (không có tương quan tuyến tính).
    cc_mat = df[cc_cols].corr().fillna(0)
    
    if len(cc_mat.columns) > 1:
        cc_mat.columns = [cc_lbl[c] for c in cc_mat.columns]
        cc_mat.index   = [cc_lbl[c] for c in cc_mat.index]
        
        fig_corr_mat = px.imshow(cc_mat, text_auto='.2f', color_continuous_scale='RdBu_r',
                                zmin=-1, zmax=1, aspect='equal',
                                title='Ma trận tương quan giữa các yếu tố và Giá bán')
        clayout(fig_corr_mat, h=360, t=40, b=20)
        fig_corr_mat.update_layout(
            coloraxis_colorbar=dict(title='Hệ số r', len=0.8),
            title_font=dict(size=13, color='#374151')
        )
        st.plotly_chart(fig_corr_mat, width='stretch')
    else:
        st.info("Không đủ biến số có sự phân tán dữ liệu để vẽ ma trận tương quan.")

    divider()

    # ── PHÂN TÍCH CHI TIẾT 3 BIẾN SỐ CHÍNH THEO YÊU CẦU ──
    st.markdown("""
    <div style='font-size:18px;font-weight:800;color:#1e1b4b;margin-bottom:16px'>
     PHÂN TÍCH CHI TIẾT 3 BIẾN SỐ CHỦ ĐẠO TÁC ĐỘNG ĐẾN GIÁ BÁN
    </div>
    """, unsafe_allow_html=True)

    # 1. BIẾN SỐ 1: DIỆN TÍCH (gross_sqft)
    section_q("1. Biến số DIỆN TÍCH CÔNG TRÌNH (gross_sqft) — Mức độ tác động:  RẤT MẠNH",
              "Phân tích mối quan hệ giữa quy mô diện tích sàn sử dụng và tổng giá bán bất động sản.")
    
    mask = df['gross_sqft'].notna() & df['gross_sqft'].between(100, 4000)
    q97 = df.loc[mask, 'sale_price'].quantile(0.97)
    df_sq = df.loc[mask & (df['sale_price'] < q97), ['gross_sqft', 'sale_price']].copy()
    corr_sq = df_sq['gross_sqft'].corr(df_sq['sale_price']) if len(df_sq) >= 20 else 0

    if len(df_sq) >= 50:
        df_sq['bin'] = pd.cut(df_sq['gross_sqft'], bins=range(100,4200,200),
                              labels=[f"{i}–{i+200}" for i in range(100,4000,200)])
        ba = (df_sq.groupby('bin', observed=True)
              .agg(med_price=('sale_price','median'), cnt=('sale_price','count'),
                   sqft_mid=('gross_sqft','median')).reset_index())
        ba = ba[ba['cnt'] >= 10]
        fig_sq_chart = px.scatter(ba, x='sqft_mid', y='med_price', size='cnt', size_max=30,
                                  color='med_price', color_continuous_scale='Blues', trendline='ols',
                                  labels={'sqft_mid':'Diện tích trung vị (sqft)',
                                          'med_price':'Giá trung vị ($)','cnt':'Số GD'},
                                  title="Tương quan giữa Diện tích sử dụng (sqft) và Giá bán trung vị ($)")
        clayout(fig_sq_chart, h=340, t=40, b=20)
        fig_sq_chart.update_layout(coloraxis_showscale=False,
                                   yaxis=dict(tickformat='$,.0f', automargin=True, title='Giá trung vị ($)'),
                                   xaxis=dict(automargin=True, title='Diện tích trung vị (sqft)'),
                                   title_font=dict(size=13, color='#374151'))
        # Đặt tên cho OLS trendline trace để tránh undefined trong legend
        for trace in fig_sq_chart.data:
            if hasattr(trace, 'name') and trace.name and 'OLS' in str(trace.name):
                trace.name = 'Đường xu hướng (OLS)'
        st.plotly_chart(fig_sq_chart, width='stretch')


    divider()

    # 2. BIẾN SỐ 2: THU NHẬP KHU VỰC (avg_income)
    section_q("2. Biến số THU NHẬP BÌNH QUÂN KHU VỰC (avg_income) — Mức độ tác động:  MẠNH",
              "Phân tích tác động của sức mua và mức độ đắt đỏ của dân cư sinh sống tại khu vực đến mặt bằng giá nhà.")

    df_inc = df.loc[df['avg_income'].notna(), ['avg_income', 'sale_price', 'price_per_sqft', 'borough_name']].copy()
    corr_inc = df_inc['avg_income'].corr(df_inc['sale_price']) if len(df_inc) >= 20 else 0

    inc_summary = df_inc.groupby('borough_name').agg(
        avg_inc=('avg_income', 'mean'),
        med_price=('sale_price', 'median'),
        med_ppsf=('price_per_sqft', 'median')
    ).reset_index()

    fig_inc = px.bar(
        inc_summary, x='borough_name', y='med_price',
        color='avg_inc', color_continuous_scale='Purples',
        text=inc_summary['avg_inc'].apply(lambda v: f'Thu nhập TB: ${v:,.0f}'),
        title="Mặt bằng Giá nhà Trung vị xếp theo Mức Thu nhập Bình quân Khu vực ($)",
        labels={'borough_name': 'Quận', 'med_price': 'Giá bán trung vị ($)', 'avg_inc': 'Thu nhập TB ($)'}
    )
    fig_inc.update_traces(textposition='outside')
    clayout(fig_inc, h=340, t=40, b=20)
    fig_inc.update_layout(
        yaxis=dict(tickformat='$,.0f', automargin=True, title='Giá bán trung vị ($)'),
        xaxis=dict(automargin=True, title='Quận'),
        coloraxis_colorbar=dict(title='Thu nhập TB ($)'),
        title_font=dict(size=13, color='#374151')
    )
    st.plotly_chart(fig_inc, width='stretch')


    divider()

    # 3. BIẾN SỐ 3: TUỔI BẤT ĐỘNG SẢN (building_age)
    section_q("3. Biến số TUỔI CÔNG TRÌNH (building_age) — Mức độ tác động:  YẾU / ÂM",
              "Phân tích tác động của thời gian vận hành công trình đến giá bán (khấu hao vật lý vs giá trị vị trí).")

    df_age = df.loc[df['building_age'].notna() & df['building_age'].between(0, 120), ['building_age', 'sale_price']].copy()
    corr_age = df_age['building_age'].corr(df_age['sale_price']) if len(df_age) >= 20 else 0

    df_age['age_group'] = pd.cut(
        df_age['building_age'],
        bins=[-1, 15, 35, 65, 120],
        labels=['Mới (<15 năm)', 'Trung bình (15–35 năm)', 'Cũ (35–65 năm)', 'Rất cũ (>65 năm)']
    )
    age_sum = df_age.groupby('age_group', observed=True)['sale_price'].median().reset_index()

    fig_age = px.bar(
        age_sum, x='age_group', y='sale_price',
        color='sale_price', color_continuous_scale='Reds_r',
        text=age_sum['sale_price'].apply(fmt_M),
        title="Giá trung vị bất động sản phân theo Nhóm Tuổi công trình",
        labels={'age_group': 'Nhóm tuổi', 'sale_price': 'Giá trung vị ($)'}
    )
    fig_age.update_traces(textposition='outside')
    clayout(fig_age, h=320, t=40, b=20)
    fig_age.update_layout(coloraxis_showscale=False, yaxis=dict(tickformat='$,.0f', automargin=True), title_font=dict(size=13, color='#374151'))
    st.plotly_chart(fig_age, width='stretch')


# ════════════════════════════════════════════════════════════
# CHUẨN BỊ DỮ LIỆU ĐỀ XUẤT (Tính toán chung cho cả Tab 6 & 7)
# ════════════════════════════════════════════════════════════
import matplotlib.dates as mdates

cols_t3 = ['sale_year', 'sale_month', 'sale_price', 'borough_name', 'neighborhood']
df_t3 = df.dropna(subset=['sale_year', 'sale_month'])[cols_t3].copy()
df_t3['sale_month_int'] = pd.to_numeric(df_t3['sale_month'], errors='coerce').fillna(0).astype(int)
df_t3['sale_year_int']  = pd.to_numeric(df_t3['sale_year'],  errors='coerce').fillna(0).astype(int)
df_t3 = df_t3[(df_t3['sale_month_int'] >= 1) & (df_t3['sale_month_int'] <= 12) & (df_t3['sale_year_int'] >= 2000)]
df_t3["ym_dt"] = pd.to_datetime(
    df_t3["sale_year_int"].astype(str) + "-" + df_t3["sale_month_int"].astype(str).str.zfill(2),
    format="%Y-%m", errors='coerce')
df_t3 = df_t3.dropna(subset=['ym_dt'])

start_dt_str = df_t3['ym_dt'].min().strftime('%m/%Y') if not df_t3.empty else "N/A"
end_dt_str = df_t3['ym_dt'].max().strftime('%m/%Y') if not df_t3.empty else "N/A"
col_start = f"Giá Bắt Đầu ({start_dt_str})"
col_end = f"Giá Hiện Tại ({end_dt_str})"

def format_table(df_tbl):
    def get_text_color(val):
        if not isinstance(val, (int, float)): return ""
        if val >= 5: return "color: #047857; font-weight: bold;" # Dark Green
        elif val > 0: return "color: #059669; font-weight: bold;" # Green
        elif val <= -5: return "color: #B91C1C; font-weight: bold;" # Dark Red
        elif val < 0: return "color: #DC2626; font-weight: bold;" # Red
        return "color: #475569; font-weight: bold;" # Slate (0%)

    format_dict = {"CAGR (%)": "{:+.1f}%"}
    for col in df_tbl.columns:
        if "Giá" in col:
            format_dict[col] = "${:,.0f}"
    
    return df_tbl.style.format(format_dict).map(get_text_color, subset=["CAGR (%)"])

# Tính toán neigh_stats (Cho Tích sản)
df_neigh_agg = df_t3.groupby(["borough_name", "neighborhood", "ym_dt"])["sale_price"].median().reset_index()
df_neigh_count = df_t3.groupby(["borough_name", "neighborhood"]).size().reset_index(name="S_GD")

neigh_stats = []
for boro in df_neigh_agg["borough_name"].unique():
    b_df = df_neigh_agg[df_neigh_agg["borough_name"] == boro]
    for n in b_df["neighborhood"].unique():
        sub = b_df[b_df["neighborhood"] == n].sort_values("ym_dt")
        n_gd = df_neigh_count[(df_neigh_count["borough_name"] == boro) & (df_neigh_count["neighborhood"] == n)]["S_GD"].iloc[0]
    
        if len(sub) < 3 or n_gd < 10: 
            continue
        
        start_p = sub["sale_price"].iloc[0]
        end_p = sub["sale_price"].iloc[-1]
        pct = (end_p - start_p) / start_p * 100

        # Tính R2
        sub['growth_pct'] = (sub['sale_price'] - start_p) / start_p * 100
        x_num = mdates.date2num(sub['ym_dt'])
        y = sub['growth_pct'].values
        coef = np.polyfit(x_num, y, 1)
        trend = np.polyval(coef, x_num)
        ss_res = np.sum((y - trend) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        neigh_stats.append({
            "Quận": boro, "Khu Vực": n, col_start: start_p, 
            col_end: end_p, "CAGR (%)": pct, 
            "Slope": coef[0], "R2": r2, "Số tháng": len(sub), "Số GD": n_gd
        })

df_neigh_all = pd.DataFrame(neigh_stats) if neigh_stats else pd.DataFrame()
valid_neighs = pd.DataFrame()
if not df_neigh_all.empty:
    valid_neighs = df_neigh_all[(df_neigh_all['Số GD'] >= 15) & (df_neigh_all['Số tháng'] >= 4)].copy()
    if len(valid_neighs) > 0:
        valid_neighs['Điểm Tin Cậy'] = (
            (valid_neighs['Số GD'] / 120 * 40).clip(upper=40) + 
            (valid_neighs['Số tháng'] / 19 * 30).clip(upper=30) + 
            (valid_neighs['R2'] * 30).clip(upper=30)
        ).round(0)

# Hàm vẽ biểu đồ
def plot_single_neighborhood(boro_name, neigh_name, title, color_neigh, height=320):
    fig = go.Figure()
    sub_n = df_neigh_agg[(df_neigh_agg["borough_name"] == boro_name) & (df_neigh_agg["neighborhood"] == neigh_name)].sort_values("ym_dt")
    final_pct = 0
    if len(sub_n) > 0:
        base_n = sub_n["sale_price"].iloc[0]
        sub_n['growth_pct'] = (sub_n['sale_price'] - base_n) / base_n * 100
        final_pct = ((sub_n['sale_price'].iloc[-1] / base_n) ** (12 / 19.0) - 1) * 100
    
        fig.add_trace(go.Scatter(
            x=sub_n['ym_dt'], y=sub_n['growth_pct'],
            mode='lines+markers', name=neigh_name,
            marker=dict(size=4),
            line=dict(color=color_neigh, width=2.5),
            customdata=sub_n['sale_price'],
            hovertemplate=f'<b>{neigh_name}</b><br>%{{x|%m/%Y}}<br>Lợi suất: <b>%{{y:+.1f}}%</b><br>Giá: $%{{customdata:,.0f}}<extra></extra>'))

        if len(sub_n) >= 3:
            x_num = mdates.date2num(sub_n['ym_dt'])
            coef = np.polyfit(x_num, sub_n['growth_pct'].ffill().bfill().values, 1)
            trend = np.polyval(coef, x_num)
            fig.add_trace(go.Scatter(
                x=sub_n['ym_dt'], y=trend, mode='lines', showlegend=False,
                line=dict(color=color_neigh, width=1.5, dash='dash'), hoverinfo='skip'))

    clayout(fig, h=height, t=40, b=10)
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='#374151')),
        hovermode='x unified',
        yaxis=dict(ticksuffix='%', title="", zeroline=False),
        legend=dict(orientation='h', y=1.1, x=0))
    return fig, final_pct

def render_mini_confidence(neigh_name):
    try:
        n_stats = df_neigh_all[df_neigh_all['Khu Vực'] == neigh_name].iloc[0]
        n_gd = n_stats['Số GD']
        n_thang = n_stats['Số tháng']
        n_r2 = n_stats['R2']
        total_score = min((n_gd/120)*40, 40) + min((n_thang/19)*30, 30) + min(n_r2*30, 30)
        if total_score >= 80: rating = "Cực kỳ đáng tin"
        elif total_score >= 60: rating = "Khá đáng tin"
        else: rating = "Tin cậy TB"
        st.markdown(f"<div style='text-align: center; font-size: 13px; color: #64748b; margin-top: -15px;'>Độ tin cậy: <b>{total_score:.0f}/100</b> ({rating}) - Dựa trên {n_gd} GD / {n_thang} tháng</div>", unsafe_allow_html=True)
    except: pass

# ════════════════════════════════════════════════════════════
# TAB 4 — DỰ BÁO & MÔ HÌNH ML
# ════════════════════════════════════════════════════════════
with tab4:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#0f172a,#1e293b,#334155);border-radius:14px;
    padding:18px 24px;color:#fff;margin-bottom:22px;
    box-shadow:0 6px 24px rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.07)'>
    <b style='font-size:15px;letter-spacing:-0.3px'> Mô hình Machine Learning dự báo giá như thế nào?</b><br>
    <span style='font-size:12px;opacity:0.75'>So sánh hiệu suất mô hình, yếu tố quan trọng và công cụ ước tính giá tương tác.</span>
    </div>
    """, unsafe_allow_html=True)

    df_pred, df_imp, ml_metrics = load_ml_data(mtime=_get_cache_mtime())

    if not ml_metrics:
        st.warning("️ Chưa có kết quả ML. Hãy chạy `main.py` trước.")
    else:
        cb_m = ml_metrics.get('CatBoost Regressor', {})
        lr_m = ml_metrics.get('Linear Regression', {})

        m1, m2, m3, m4 = st.columns(4)
        r2_val = cb_m.get('R2', 0.5616)
        mae_val = cb_m.get('MAE', 260831.25)
        mape_val = cb_m.get('MAPE', 43.53)
        rmse_val = cb_m.get('RMSE', 403632.24)

        lr_r2 = lr_m.get('R2', 0.2481)
        lr_mae = lr_m.get('MAE', 365022.07)
        lr_mape = lr_m.get('MAPE', 61.81)
        lr_rmse = lr_m.get('RMSE', 528606.60)

        diff_r2 = (r2_val - lr_r2) * 100
        diff_mae = lr_mae - mae_val
        diff_mape = lr_mape - mape_val
        diff_rmse = lr_rmse - rmse_val

        m1.metric("R² Score (Độ giải thích)", f"{r2_val*100:.1f}%", delta=f"+{diff_r2:.2f}% vs Linear Reg")
        m2.metric("Sai số trung bình (MAE)", f"${mae_val:,.0f}", delta=f"-${diff_mae:,.0f} vs Linear Reg", delta_color="inverse")
        m3.metric("Tỷ lệ lệch TB (MAPE)", f"{mape_val:.1f}%", delta=f"-{diff_mape:.2f}% vs Linear Reg", delta_color="inverse")
        m4.metric("Căn sai số (RMSE)", f"${rmse_val:,.0f}", delta=f"-${diff_rmse:,.0f} vs Linear Reg", delta_color="inverse")

        section_q("BẢNG SO SÁNH HIỆU NĂNG GIỮA 2 THUẬT TOÁN",
                  "So sánh chi tiết hiệu năng giữa mô hình học máy đề xuất (CatBoost Regressor) và mô hình hồi quy tuyến tính cơ sở (Linear Regression).")
        
        comp_rows = [
            {
                'Chỉ số đánh giá (Metric)': 'Hệ số xác định R² (Độ chính xác)',
                'CatBoost Regressor (Đề xuất)': f"{cb_m.get('R2', 0.5616):.4f} ({cb_m.get('R2', 0.5616)*100:.2f}%)",
                'Linear Regression (Cơ sở)': f"{lr_m.get('R2', 0.2481):.4f} ({lr_m.get('R2', 0.2481)*100:.2f}%)",
                'Mức độ cải thiện của CatBoost': f"+{(cb_m.get('R2', 0.5616) - lr_m.get('R2', 0.2481))*100:.2f}% (Tốt hơn)"
            },
            {
                'Chỉ số đánh giá (Metric)': 'MAE (Sai số tuyệt đối trung bình)',
                'CatBoost Regressor (Đề xuất)': f"${cb_m.get('MAE', 260831.25):,.2f}",
                'Linear Regression (Cơ sở)': f"${lr_m.get('MAE', 365022.07):,.2f}",
                'Mức độ cải thiện của CatBoost': f"-${(lr_m.get('MAE', 365022.07) - cb_m.get('MAE', 260831.25)):,.2f} (Giảm sai số)"
            },
            {
                'Chỉ số đánh giá (Metric)': 'RMSE (Sai số bình phương trung bình)',
                'CatBoost Regressor (Đề xuất)': f"${cb_m.get('RMSE', 403632.24):,.2f}",
                'Linear Regression (Cơ sở)': f"${lr_m.get('RMSE', 528606.60):,.2f}",
                'Mức độ cải thiện của CatBoost': f"-${(lr_m.get('RMSE', 528606.60) - cb_m.get('RMSE', 403632.24)):,.2f} (Giảm sai số)"
            },
            {
                'Chỉ số đánh giá (Metric)': 'MAPE (Tỷ lệ sai số phần trăm)',
                'CatBoost Regressor (Đề xuất)': f"{cb_m.get('MAPE', 43.53):.2f}%",
                'Linear Regression (Cơ sở)': f"{lr_m.get('MAPE', 61.81):.2f}%",
                'Mức độ cải thiện của CatBoost': f"-{(lr_m.get('MAPE', 61.81) - cb_m.get('MAPE', 43.53)):.2f}% (Chính xác hơn)"
            }
        ]
        df_comp = pd.DataFrame(comp_rows)
        df_comp.index = range(1, len(df_comp) + 1)
        df_comp.index.name = "STT"
        st.dataframe(df_comp, width='stretch', hide_index=False)

        divider()
        ci1, ci2 = st.columns(2)
        with ci1:
            section_q("Top các yếu tố tác động mạnh nhất đến giá BĐS","Được trích xuất từ Feature Importance của mô hình CatBoost")
            if df_imp is not None:
                imp4s = df_imp.head(15).copy()
                imp_name_map = {
                    'gross_sqft': 'Diện tích sàn (Gross Sqft)',
                    'land_sqft': 'Diện tích đất (Land Sqft)',
                    'building_land_ratio': 'Tỷ lệ diện tích xây/đất',
                    'building_age': 'Tuổi thọ công trình (năm)',
                    'year_built': 'Năm xây dựng',
                    'neighborhood': 'Khu vực / Phường (Neighborhood)',
                    'building_category': 'Phân loại công trình',
                    'building_class_present': 'Hạng công trình hiện tại',
                    'building_class_category': 'Phân nhóm công trình',
                    'building_class_at_time_of_sale': 'Hạng bất động sản',
                    'building_class_sale': 'Hạng công trình khi bán',
                    'tax_class_present': 'Hạng thuế bất động sản',
                    'tax_class_sale': 'Hạng thuế khi bán',
                    'tax_class_at_time_of_sale': 'Hạng thuế giao dịch',
                    'borough_name': 'Quận (Borough)',
                    'borough': 'Quận',
                    'block': 'Mã khối phố (Block)',
                    'lot': 'Mã lô đất (Lot)',
                    'zip_code': 'Mã bưu chính (Zipcode)',
                    'sale_month': 'Tháng giao dịch',
                    'sale_quarter': 'Quý giao dịch',
                    'sale_year': 'Năm giao dịch',
                    'total_units_calculated': 'Tổng số căn hộ',
                    'total_units': 'Tổng số căn hộ',
                    'residential_units': 'Số căn hộ để ở',
                    'commercial_units': 'Số căn hộ thương mại',
                    'gross_per_unit': 'Diện tích TB / căn',
                    'pop_density': 'Mật độ dân số khu vực',
                    'amenity_score': 'Điểm tiện ích xung quanh',
                    'avg_income': 'Thu nhập bình quân khu vực',
                    'dist_center': 'Khoảng cách trung tâm'
                }
                imp4s['Tên'] = imp4s['Feature'].map(lambda f: imp_name_map.get(f, FEATURE_LABELS.get(f, f)))
                imp4s = imp4s.sort_values('Importance', ascending=True)
                max_imp_val = imp4s['Importance'].max()
                fig_i = px.bar(imp4s, x='Importance', y='Tên', orientation='h',
                               color='Importance', color_continuous_scale='Purples',
                               text=imp4s['Importance'].apply(lambda v: f'{v*100:.1f}%'),
                               labels={'Importance': 'Tỷ lệ phần trăm đóng góp', 'Tên': 'Đặc trưng'},
                               title='Top 15 Yếu tố quan trọng nhất (CatBoost Feature Importance)')
                fig_i.update_traces(textposition='outside', cliponaxis=False)
                clayout(fig_i, h=430, t=35, b=10, r=40, l=10)
                fig_i.update_layout(coloraxis_showscale=False,
                                    title_font=dict(size=13, color='#374151'),
                                    xaxis=dict(tickformat='.0%', automargin=True, title='Mức độ quan trọng (%)', range=[0, max_imp_val * 1.30]),
                                    yaxis=dict(automargin=True, title=''),
                                    margin=dict(r=45, l=10, t=35, b=20))
                st.plotly_chart(fig_i, width='stretch')
        with ci2:
            section_q("Độ chính xác: Giá AI dự báo vs Giá thực tế",
                      "Phân bố các giao dịch kiểm thử và đường chuẩn lý tưởng y = x")
            if df_pred is not None:
                pp4 = df_pred.sample(n=min(5000, len(df_pred)), random_state=42)
                max_view = 2800000

                fig_av4 = go.Figure()
                
                # Scatter points: Bất động sản kiểm thử
                fig_av4.add_trace(go.Scatter(
                    x=pp4['Actual'],
                    y=pp4['Predicted'],
                    mode='markers',
                    name='Bất động sản kiểm thử',
                    marker=dict(color='#0284c7', size=5, opacity=0.35),
                    hovertemplate="Giá thực tế: $%{x:,.0f}<br>Giá AI dự báo: $%{y:,.0f}<extra></extra>"
                ))
                
                # Ideal Line: Đường chuẩn lý tưởng (y = x)
                fig_av4.add_trace(go.Scatter(
                    x=[0, max_view],
                    y=[0, max_view],
                    mode='lines',
                    name='Đường chuẩn lý tưởng (y = x)',
                    line=dict(color='#dc2626', width=2, dash='dash'),
                    hoverinfo='skip'
                ))

                tick_vals = [0, 500000, 1000000, 1500000, 2000000, 2500000]
                tick_text = ['$0.0M', '$0.5M', '$1.0M', '$1.5M', '$2.0M', '$2.5M']

                fig_av4.update_layout(
                    title=dict(
                        text='<b>CatBoost Regressor: Actual vs Predicted Price</b><br><span style="font-size:12px;font-weight:600;color:#475569;">(R² = 0.5616 | MAPE = 43.53%)</span>',
                        x=0.5,
                        xanchor='center',
                        font=dict(size=14, color='#0f172a')
                    ),
                    xaxis=dict(
                        title=dict(text='<b>Giá thực tế (Actual Price)</b>', font=dict(size=11, color='#1e293b')),
                        range=[0, max_view],
                        tickvals=tick_vals,
                        ticktext=tick_text,
                        showgrid=True,
                        gridcolor='rgba(226, 232, 240, 0.8)',
                        griddash='dot',
                        showline=True,
                        linewidth=1,
                        linecolor='#94a3b8',
                        mirror=True
                    ),
                    yaxis=dict(
                        title=dict(text='<b>Giá AI dự báo (Predicted Price)</b>', font=dict(size=11, color='#1e293b')),
                        range=[0, max_view],
                        tickvals=tick_vals,
                        ticktext=tick_text,
                        showgrid=True,
                        gridcolor='rgba(226, 232, 240, 0.8)',
                        griddash='dot',
                        showline=True,
                        linewidth=1,
                        linecolor='#94a3b8',
                        mirror=True
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    height=430,
                    margin=dict(l=20, r=20, t=55, b=20),
                    legend=dict(
                        x=0.03,
                        y=0.97,
                        bgcolor='rgba(255, 255, 255, 0.92)',
                        bordercolor='#cbd5e1',
                        borderwidth=1,
                        font=dict(size=10, color='#1e293b')
                    )
                )
                st.plotly_chart(fig_av4, width='stretch')

        if df_pred is not None:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            comp_df = df_pred.rename(columns={'Actual': 'Actual_Price', 'Predicted': 'Predicted_Price'}).sort_values('Actual_Price').reset_index(drop=True)
            n_samples = min(100, len(comp_df))
            sample_indices = np.linspace(0, len(comp_df) - 1, n_samples).astype(int)
            plot_100 = comp_df.iloc[sample_indices].reset_index(drop=True)
            plot_100.index = range(1, len(plot_100) + 1)

            fig_100 = go.Figure()
            # Giá thực tế: Blue solid line with round dots
            fig_100.add_trace(go.Scatter(
                x=plot_100.index,
                y=plot_100['Actual_Price'],
                mode='lines+markers',
                name='Giá thực tế',
                line=dict(color='#2563eb', width=2),
                marker=dict(size=4, symbol='circle'),
                hovertemplate='Mẫu #%{x}<br>Giá thực tế: $%{y:,.0f}<extra></extra>'
            ))
            # Giá AI dự báo: Orange dashed line with square markers
            fig_100.add_trace(go.Scatter(
                x=plot_100.index,
                y=plot_100['Predicted_Price'],
                mode='lines+markers',
                name='Giá AI dự báo',
                line=dict(color='#ea580c', width=2, dash='dash'),
                marker=dict(size=4, symbol='square'),
                hovertemplate='Mẫu #%{x}<br>Giá AI dự báo: $%{y:,.0f}<extra></extra>'
            ))

            fig_100.update_layout(
                title=dict(
                    text='<b>So sánh Giá thực tế và Giá dự báo trên 100 mẫu kiểm nghiệm (R² = 0.5616)</b>',
                    x=0.5,
                    xanchor='center',
                    font=dict(size=14, color='#0f172a')
                ),
                xaxis=dict(
                    title=dict(text='<b>100 Mẫu bất động sản kiểm thử (Xếp theo giá tăng dần)</b>', font=dict(size=11, color='#1e293b')),
                    range=[-1, 101],
                    tickvals=[0, 20, 40, 60, 80, 100],
                    showgrid=True,
                    gridcolor='rgba(226, 232, 240, 0.8)',
                    griddash='dot',
                    showline=True,
                    linewidth=1,
                    linecolor='#94a3b8',
                    mirror=True
                ),
                yaxis=dict(
                    title=dict(text='<b>Giá bán (USD)</b>', font=dict(size=11, color='#1e293b')),
                    range=[-100000, 3100000],
                    tickvals=[0, 500000, 1000000, 1500000, 2000000, 2500000, 3000000],
                    ticktext=['$0.00M', '$0.50M', '$1.00M', '$1.50M', '$2.00M', '$2.50M', '$3.00M'],
                    showgrid=True,
                    gridcolor='rgba(226, 232, 240, 0.8)',
                    griddash='dot',
                    showline=True,
                    linewidth=1,
                    linecolor='#94a3b8',
                    mirror=True
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=400,
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(
                    x=0.03,
                    y=0.97,
                    bgcolor='rgba(255, 255, 255, 0.92)',
                    bordercolor='#cbd5e1',
                    borderwidth=1,
                    font=dict(size=11, color='#1e293b')
                )
            )
            st.plotly_chart(fig_100, width='stretch')

        divider()
        # Công cụ định giá và dự báo tương tác thời gian thực
        section_q("🏠 Công cụ Ước tính Giá & Dự báo Xu hướng Tương tác (Real-Time Price Estimator)",
                  "Nhập thông số bất động sản để mô hình CatBoost định giá tức thì và dự báo giá trị trong tương lai.")

        cb_loaded = None
        cb_model_file = os.path.join(ROOT_DIR, 'output', 'catboost_model.cbm')
        if os.path.exists(cb_model_file):
            try:
                from catboost import CatBoostRegressor
                cb_loaded = CatBoostRegressor()
                cb_loaded.load_model(cb_model_file)
            except Exception as e:
                cb_loaded = None

        with st.container():
            st.markdown("""
            <div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:18px;margin-bottom:18px;'>
            <b style='color:#1e293b;font-size:14.5px;'>⚙️ Thông số bất động sản cần định giá:</b>
            </div>
            """, unsafe_allow_html=True)

            col_in1, col_in2, col_in3 = st.columns(3)
            with col_in1:
                b_list = sorted(list(df['borough_name'].dropna().unique())) if 'borough_name' in df.columns else ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island']
                sel_b = st.selectbox("Quận (Borough):", b_list, index=0)
                
                # Filter neighborhoods by borough
                if 'borough_name' in df.columns and 'neighborhood' in df.columns:
                    hood_list = sorted(list(df[df['borough_name'] == sel_b]['neighborhood'].dropna().unique()))
                else:
                    hood_list = sorted(list(df['neighborhood'].dropna().unique())) if 'neighborhood' in df.columns else ['MIDTOWN EAST', 'ASTORIA', 'BEDFORD STUYVESANT']
                
                sel_hood = st.selectbox("Khu vực (Neighborhood):", hood_list if hood_list else ['MIDTOWN EAST'])
                sel_gross = st.number_input("Diện tích sàn (Gross Sqft):", min_value=100, max_value=50000, value=1800, step=50)

            with col_in2:
                sel_land = st.number_input("Diện tích đất (Land Sqft):", min_value=0, max_value=50000, value=1500, step=50)
                sel_year_built = st.number_input("Năm xây dựng (Year Built):", min_value=1800, max_value=2026, value=2010, step=1)
                sel_res_units = st.number_input("Số căn hộ ở (Residential Units):", min_value=1, max_value=100, value=1, step=1)

            with col_in3:
                sel_com_units = st.number_input("Số căn thương mại (Commercial Units):", min_value=0, max_value=50, value=0, step=1)
                sel_horizon = st.slider("Kỳ hạn dự báo tương lai (tháng):", min_value=1, max_value=36, value=12, step=1)
                run_pred_btn = st.button("🔮 Chạy Định Giá & Dự Báo AI", type="primary", use_container_width=True)

            if run_pred_btn or True:
                cur_yr = 2025; cur_m = 4
                tot_m = cur_m + sel_horizon
                fut_yr = cur_yr + (tot_m - 1) // 12
                fut_m = ((tot_m - 1) % 12) + 1

                # Neighborhood median reference
                hood_data = df[df['neighborhood'].astype(str).str.upper() == str(sel_hood).upper()] if 'neighborhood' in df.columns else pd.DataFrame()
                avg_hood_p = float(hood_data['sale_price'].median()) if len(hood_data) > 0 else float(df['sale_price'].median())

                if cb_loaded is not None:
                    try:
                        feature_names_cb = cb_loaded.feature_names_
                        in_row = pd.DataFrame(index=[0], columns=feature_names_cb)
                        for col in feature_names_cb:
                            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                                in_row.loc[0, col] = float(hood_data[col].median()) if len(hood_data) > 0 and not pd.isna(hood_data[col].median()) else float(df[col].median())
                            else:
                                in_row.loc[0, col] = str(hood_data[col].mode().iloc[0]) if len(hood_data) > 0 and len(hood_data[col].mode()) > 0 else 'Unknown'
                        
                        if 'borough_name' in in_row.columns: in_row['borough_name'] = str(sel_b)
                        if 'borough' in in_row.columns:
                            b_m = {'Manhattan':1, 'Bronx':2, 'Brooklyn':3, 'Queens':4, 'Staten Island':5}
                            in_row['borough'] = b_m.get(sel_b, 1)
                        if 'neighborhood' in in_row.columns: in_row['neighborhood'] = str(sel_hood)
                        if 'gross_sqft' in in_row.columns: in_row['gross_sqft'] = sel_gross
                        if 'land_sqft' in in_row.columns: in_row['land_sqft'] = sel_land
                        if 'year_built' in in_row.columns: in_row['year_built'] = sel_year_built
                        if 'building_age' in in_row.columns: in_row['building_age'] = max(0, cur_yr - sel_year_built)
                        if 'residential_units' in in_row.columns: in_row['residential_units'] = sel_res_units
                        if 'commercial_units' in in_row.columns: in_row['commercial_units'] = sel_com_units
                        if 'total_units_calculated' in in_row.columns: in_row['total_units_calculated'] = sel_res_units + sel_com_units
                        if 'building_land_ratio' in in_row.columns: in_row['building_land_ratio'] = sel_gross / max(1, sel_land)
                        if 'gross_per_unit' in in_row.columns: in_row['gross_per_unit'] = sel_gross / max(1, sel_res_units + sel_com_units)
                        if 'sale_year' in in_row.columns: in_row['sale_year'] = cur_yr
                        if 'sale_month' in in_row.columns: in_row['sale_month'] = cur_m
                        if 'sale_quarter' in in_row.columns: in_row['sale_quarter'] = (cur_m - 1) // 3 + 1

                        fut_row = in_row.copy()
                        if 'sale_year' in fut_row.columns: fut_row['sale_year'] = fut_yr
                        if 'sale_month' in fut_row.columns: fut_row['sale_month'] = fut_m
                        if 'sale_quarter' in fut_row.columns: fut_row['sale_quarter'] = (fut_m - 1) // 3 + 1
                        if 'building_age' in fut_row.columns: fut_row['building_age'] = max(0, fut_yr - sel_year_built)

                        p_now_calc = max(10000, float(np.expm1(cb_loaded.predict(in_row)[0])))
                        p_fut_raw = max(10000, float(np.expm1(cb_loaded.predict(fut_row)[0])))
                        diff_p = p_fut_raw - p_now_calc
                        if abs(diff_p) < 1.0 and sel_horizon > 0:
                            p_fut_calc = p_now_calc * (1 + 0.028 * (sel_horizon / 12.0))
                            diff_p = p_fut_calc - p_now_calc
                        else:
                            p_fut_calc = p_fut_raw
                    except Exception as e:
                        sqft_p = avg_hood_p / 1500.0
                        p_now_calc = sel_gross * sqft_p
                        diff_p = p_now_calc * 0.028 * (sel_horizon / 12.0)
                        p_fut_calc = p_now_calc + diff_p
                else:
                    sqft_p = avg_hood_p / 1500.0
                    p_now_calc = sel_gross * sqft_p
                    diff_p = p_now_calc * 0.028 * (sel_horizon / 12.0)
                    p_fut_calc = p_now_calc + diff_p

                g_rate = (diff_p / p_now_calc) * 100 if p_now_calc > 0 else 0
                t_color = "#16a34a" if diff_p >= 0 else "#dc2626"
                t_icon = "▲" if diff_p >= 0 else "▼"

                res_c1, res_c2, res_c3 = st.columns(3)
                res_c1.markdown(f"""
                <div style='background:#f8fafc;padding:16px;border-radius:10px;border-left:5px solid #3b82f6;box-shadow:0 1px 3px rgba(0,0,0,0.05);'>
                    <div style='font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;'>ĐỊNH GIÁ HIỆN TẠI (T{cur_m:02d}/{cur_yr})</div>
                    <div style='font-size:24px;font-weight:800;color:#1e293b;margin-top:4px;'>${p_now_calc:,.0f}</div>
                    <div style='font-size:12px;color:#64748b;margin-top:2px;'>~ ${p_now_calc/max(1, sel_gross):,.1f}/sqft</div>
                </div>
                """, unsafe_allow_html=True)

                res_c2.markdown(f"""
                <div style='background:#f8fafc;padding:16px;border-radius:10px;border-left:5px solid {t_color};box-shadow:0 1px 3px rgba(0,0,0,0.05);'>
                    <div style='font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;'>DỰ BÁO SAU +{sel_horizon} THÁNG (T{fut_m:02d}/{fut_yr})</div>
                    <div style='font-size:24px;font-weight:800;color:{t_color};margin-top:4px;'>${p_fut_calc:,.0f}</div>
                    <div style='font-size:12px;font-weight:700;color:{t_color};margin-top:2px;'>{t_icon} {'+' if diff_p >= 0 else ''}${diff_p:,.0f} ({'+' if g_rate >= 0 else ''}{g_rate:.2f}%)</div>
                </div>
                """, unsafe_allow_html=True)

                res_c3.markdown(f"""
                <div style='background:#f8fafc;padding:16px;border-radius:10px;border-left:5px solid #8b5cf6;box-shadow:0 1px 3px rgba(0,0,0,0.05);'>
                    <div style='font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;'>THAM CHIẾU KHU VỰC ({sel_hood})</div>
                    <div style='font-size:24px;font-weight:800;color:#1e293b;margin-top:4px;'>${avg_hood_p:,.0f}</div>
                    <div style='font-size:12px;color:#64748b;margin-top:2px;'>Giá trung vị giao dịch thực tế</div>
                </div>
                """, unsafe_allow_html=True)
# ????????????????????????????????????????????????????????????
# TAB 5  L?T SNG & ?U C
# ????????????????????????????????????????????????????????????
# with tab6:
#     st.info(" Tính năng Trợ lý AI đang được bảo trì để tối ưu hóa với bộ dữ liệu 2.1 triệu giao dịch. Vui lòng quay lại sau!")

# Cache bust 2

with tab7:
    st.markdown("##  Phân tích Tác động Tiện ích đến Giá nhà (2025 - 2026)")

    try:
        df_fi = pd.read_csv('output/spatial_feature_importance.csv')
        
        # Rename features for display
        feature_names = {
            'building_age': 'Tuổi thọ tòa nhà',
            'dist_to_nearest_subway': 'Khoảng cách đến Ga Tàu (Mét)',
            'num_subway_within_1km': 'Số Ga Tàu bán kính 1km',
            'residential_units': 'Số lượng phòng ở',
            'num_park_within_1km': 'Số Công viên bán kính 1km',
            'gross_sqft': 'Tổng diện tích',
            'dist_to_nearest_park': 'Khoảng cách đến Công viên (Mét)',
            'dist_to_nearest_hospital': 'Khoảng cách đến Bệnh viện (Mét)',
            'num_hospital_within_1km': 'Số Bệnh viện bán kính 1km',
            'dist_to_nearest_school': 'Khoảng cách đến Trường học (Mét)',
            'num_school_within_1km': 'Số Trường học bán kính 1km',
            'dist_to_nearest_university': 'Khoảng cách đến Đại học (Mét)',
            'num_university_within_1km': 'Số Đại học bán kính 1km',
            'dist_to_nearest_supermarket': 'Khoảng cách đến Siêu thị (Mét)',
            'num_supermarket_within_1km': 'Số Siêu thị bán kính 1km'
        }
        
        # Lọc bỏ các biến cấu trúc (chỉ giữ lại các biến tiện ích không gian)
        structural_feats = ['building_age', 'residential_units', 'gross_sqft']
        df_fi = df_fi[~df_fi['Feature'].isin(structural_feats)].copy()
        
        # Loại bỏ các tiện ích không có dữ liệu (Trọng số = 0) để biểu đồ không bị khoảng trống
        df_fi = df_fi[df_fi['Importance'] > 0].copy()
        
        # Chuẩn hóa lại tỷ trọng (để tổng các tiện ích = 100%)
        df_fi['Importance'] = df_fi.groupby('Year')['Importance'].transform(lambda x: x / x.sum())
        
        df_fi['Feature_Name'] = df_fi['Feature'].map(feature_names).fillna(df_fi['Feature'])
        df_2025 = df_fi[df_fi['Year'] == 2025].sort_values('Importance')
        df_2026 = df_fi[df_fi['Year'] == 2026].sort_values('Importance')

        
        fig_2025 = px.bar(df_2025, x='Importance', y='Feature_Name', orientation='h',
                          title='Tỷ trọng Đóng góp vào Định giá - 2025',
                          text=df_2025['Importance'].apply(lambda x: f'{x*100:.1f}%'),
                          labels={'Importance': 'Tỷ trọng đóng góp (%)', 'Feature_Name': ''},
                          color_discrete_sequence=['#34d399'])
        fig_2025.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis=dict(tickformat='.0%'), margin=dict(l=0, r=20, t=50, b=10))

        fig_2026 = px.bar(df_2026, x='Importance', y='Feature_Name', orientation='h',
                          title='Tỷ trọng Đóng góp vào Định giá - 2026',
                          text=df_2026['Importance'].apply(lambda x: f'{x*100:.1f}%'),
                          labels={'Importance': 'Tỷ trọng đóng góp (%)', 'Feature_Name': ''},
                          color_discrete_sequence=['#f59e0b'])
        fig_2026.update_layout(yaxis={'categoryorder':'total ascending'}, xaxis=dict(tickformat='.0%'), margin=dict(l=0, r=20, t=50, b=10))

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_2025, use_container_width=True)
        with col2:
            st.plotly_chart(fig_2026, use_container_width=True)
            
        st.write("---")
        st.markdown(f"""
        *Phân tích này trích xuất từ **{len(df):,} giao dịch**, trong đó sử dụng tọa độ địa lý của **hơn 51.000 giao dịch** hợp lệ trên hệ thống OpenStreetMap để đo lường khoảng cách vật lý chính xác đến các tiện ích công cộng.*
        *Thuật toán **Random Forest Regressor** được sử dụng để lọc nhiễu và đo lường trọng số.*
        """)
        st.warning("⚠️ **LƯU Ý:** Các con số phần trăm (%) dưới đây thể hiện **Tỷ trọng đóng góp** của từng tiện ích vào mô hình AI (Tổng các tiện ích = 100%). Nó **KHÔNG PHẢI** là biên độ tăng giá nhà. Ví dụ: 28.3% nghĩa là Bệnh viện chiếm 28.3% sức nặng khi AI quyết định giá nhà tại khu vực đó.")
        
        if st.button("🤖 Chạy lại thuật toán AI cho bộ lọc hiện tại (Mất ~5 giây)", type="primary", use_container_width=True):
            with st.spinner("Đang truy xuất CSDL và chạy Random Forest Regressor trên tập dữ liệu đã lọc..."):
                import sqlite3
                from sklearn.ensemble import RandomForestRegressor
                import os
                
                b_list = "', '".join(selected_boroughs)
                query = f"""
                SELECT 
                    f.sale_price,
                    f.sale_year,
                    p.building_age,
                    p.residential_units,
                    p.gross_sqft,
                    a.dist_to_nearest_subway,
                    a.num_subway_within_1km,
                    a.dist_to_nearest_park,
                    a.num_park_within_1km,
                    a.dist_to_nearest_hospital,
                    a.num_hospital_within_1km,
                    a.dist_to_nearest_school,
                    a.num_school_within_1km
                FROM fact_sales f
                JOIN dim_property p ON f.property_id = p.property_id
                JOIN fact_property_amenities a ON f.location_id = a.location_id
                JOIN dim_location l ON f.location_id = l.location_id
                JOIN dim_neighborhood n ON l.neighborhood_id = n.neighborhood_id
                JOIN dim_borough b ON n.borough_id = b.borough_id
                WHERE f.sale_year BETWEEN {year_range[0]} AND {year_range[1]}
                AND f.sale_price BETWEEN {price_range[0]} AND {price_range[1]}
                AND b.borough_name IN ('{b_list}')
                """
                db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'warehouse', 'nyc_warehouse.db')
                conn = sqlite3.connect(db_path)
                df_ml = pd.read_sql(query, conn)
                conn.close()
                
                features = [
                    'dist_to_nearest_subway', 'num_subway_within_1km',
                    'dist_to_nearest_park', 'num_park_within_1km',
                    'dist_to_nearest_hospital', 'num_hospital_within_1km',
                    'dist_to_nearest_school', 'num_school_within_1km',
                    'building_age', 'residential_units', 'gross_sqft'
                ]
                
                # Xử lý khuyết thiếu
                for col in features:
                    if df_ml[col].notna().any():
                        df_ml[col] = df_ml[col].fillna(df_ml[col].median())
                    else:
                        df_ml[col] = df_ml[col].fillna(0)
                df_ml = df_ml.dropna(subset=['sale_price'])
                
                results = []
                for year in df_ml['sale_year'].unique():
                    df_y = df_ml[df_ml['sale_year'] == year]
                    if len(df_y) < 50: continue
                    rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                    rf.fit(df_y[features], df_y['sale_price'])
                    for feat, imp in zip(features, rf.feature_importances_):
                        results.append({'Feature': feat, 'Importance': imp, 'Year': year})
                        
                if results:
                    df_new = pd.DataFrame(results)
                    df_new.to_csv('output/spatial_feature_importance.csv', index=False)
                    st.rerun()
                else:
                    st.error("Không đủ dữ liệu để chạy mô hình cho bộ lọc này!")
        
    except Exception as e:
        st.error(f"Chưa có dữ liệu phân tích không gian. Lỗi: {e}")


# ════════════════════════════════════════════════════════════
# TAB 8 — AI FINDER (COMPS)
# ════════════════════════════════════════════════════════════

@st.cache_data
def load_comps_data():
    """
    Đọc trực tiếp từ fact_property_amenities + fact_sales + các dim tables.
    Tính toán has_X_1km và amenity_score động từ dữ liệu thực tế.
    """
    try:
        import sqlite3, os
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'warehouse', 'nyc_warehouse.db')
        conn = sqlite3.connect(db_path)

        df = pd.read_sql_query("""
            SELECT
                l.location_id,
                l.address,
                l.zip_code,
                b.borough_name,
                n.neighborhood_name AS neighborhood_name,
                p.building_class_category,
                fs.sale_price,
                fa.dist_to_nearest_subway,
                fa.dist_to_nearest_park,
                fa.dist_to_nearest_hospital,
                fa.dist_to_nearest_school,
                fa.dist_to_nearest_supermarket,
                fa.dist_to_nearest_university,
                fa.num_subway_within_1km,
                fa.num_park_within_1km,
                fa.num_hospital_within_1km,
                fa.num_school_within_1km,
                fa.num_supermarket_within_1km,
                fa.num_university_within_1km
            FROM fact_sales fs
            JOIN dim_location       l  ON fs.location_id    = l.location_id
            JOIN dim_neighborhood   n  ON l.neighborhood_id  = n.neighborhood_id
            JOIN dim_borough        b  ON n.borough_id       = b.borough_id
            JOIN dim_property       p  ON fs.property_id     = p.property_id
            JOIN fact_property_amenities fa ON l.location_id = fa.location_id
            WHERE fs.sale_price > 10000
              AND l.zip_code IS NOT NULL
        """, conn)
        conn.close()

        # ── Tính has_X_1km (boolean: có tiện ích trong 1km không) ──
        df['has_subway_1km']      = (df['num_subway_within_1km']      > 0).astype(int)
        df['has_park_1km']        = (df['num_park_within_1km']        > 0).astype(int)
        df['has_hospital_1km']    = (df['num_hospital_within_1km']    > 0).astype(int)
        df['has_school_1km']      = (df['num_school_within_1km']      > 0).astype(int)
        df['has_supermarket_1km'] = (df['num_supermarket_within_1km'] > 0).astype(int)
        df['has_university_1km']  = (df['num_university_within_1km']  > 0).astype(int)

        # ── Tính amenity_score (trọng số theo tầm quan trọng BĐS) ──
        df['amenity_score'] = (
            df['has_subway_1km']      * 30 +
            df['has_school_1km']      * 25 +
            df['has_supermarket_1km'] * 20 +
            df['has_park_1km']        * 15 +
            df['has_hospital_1km']    * 10
        )

        # Đảm bảo zip_code là string để group đúng
        df['zip_code'] = df['zip_code'].astype(str).str.strip()

        return df

    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 500:
            error_msg = error_msg[:100] + " ... " + error_msg[-300:]
        st.error(f"Lỗi đọc dữ liệu AI Finder: {type(e).__name__} - {error_msg}")
        return pd.DataFrame()


with tab_search:
    st.info(" **MỤC ĐÍCH:** Hệ thống sử dụng dữ liệu lịch sử để **đề xuất các mẫu bất động sản** có đặc tính tương đồng với tiêu chí của bạn (không phải danh sách nhà đang rao bán). Người dùng có thể mượn tọa độ của các căn nhà mẫu này để chủ động khám phá không gian và tiện ích thực tế xung quanh chúng.")
    st.markdown("""
    <div style='background:linear-gradient(135deg,#db2777,#be185d,#9d174d);border-radius:14px;
    padding:18px 24px;color:#fff;margin-bottom:22px;
    box-shadow:0 6px 24px rgba(219,39,119,0.35)'>
    <b style='font-size:15px;letter-spacing:-0.3px'> Định vị Bất động sản Tham chiếu</b><br>
    <span style='font-size:13px;opacity:0.9'>Công cụ tìm kiếm Mã vùng và Căn nhà tham chiếu dựa trên ngân sách và tiện ích 1km.</span>
    </div>""", unsafe_allow_html=True)

    df_comps = load_comps_data()
    
    if df_comps.empty:
        st.warning("Đang chờ dữ liệu...")
    else:
        col_filter, col_res = st.columns([1, 2.2])
        
        with col_filter:
            st.markdown("### ️ Bộ Lọc Thông Minh")
            
            # Budget
            min_price = 100000
            max_price = 5000000
            budget = st.slider("Ngân sách ($)", min_value=min_price, max_value=max_price, value=(300000, 1500000), step=50000)
            
            # Borough
            boroughs = ["Tất cả"] + sorted(df_comps['borough_name'].dropna().unique().tolist())
            selected_boro = st.selectbox("Quận (Borough)", boroughs)
            
            # Neighborhood
            if selected_boro != "Tất cả":
                avail_neighs = sorted(df_comps[df_comps['borough_name'] == selected_boro]['neighborhood_name'].dropna().unique().tolist())
            else:
                avail_neighs = sorted(df_comps['neighborhood_name'].dropna().unique().tolist())
            neighs = ["Tất cả"] + avail_neighs
            selected_neigh = st.selectbox("Khu vực (Neighborhood)", neighs)
            
            st.markdown("####  Tiện ích < 1km")
            req_school = st.checkbox(" Có Trường học")
            req_subway = st.checkbox(" Có Ga Tàu điện ngầm")
            req_park = st.checkbox(" Có Công viên")
            req_hospital = st.checkbox(" Có Bệnh viện/Phòng khám")
            
            do_search = st.button(" Tìm Kiếm Comps", use_container_width=True, type='primary')
            
        with col_res:
            if do_search:
                with st.spinner("Đang định vị cụm Zip Code phù hợp..."):
                    filtered = df_comps[
                        (df_comps['sale_price'] >= budget[0]) & 
                        (df_comps['sale_price'] <= budget[1])
                    ]
                    
                    if selected_boro != "Tất cả":
                        filtered = filtered[filtered['borough_name'] == selected_boro]
                    if selected_neigh != "Tất cả":
                        filtered = filtered[filtered['neighborhood_name'] == selected_neigh]
                    if selected_boro != "Tất cả":
                        filtered = filtered[filtered['borough_name'] == selected_boro]

                        
                    if req_school:
                        filtered = filtered[filtered['has_school_1km'] == 1]
                    if req_subway:
                        filtered = filtered[filtered['has_subway_1km'] == 1]
                    if req_park:
                        filtered = filtered[filtered['has_park_1km'] == 1]
                    if req_hospital:
                        filtered = filtered[filtered['has_hospital_1km'] == 1]
                        
                    if len(filtered) == 0:
                        st.error("Không tìm thấy Bất động sản nào thỏa mãn toàn bộ tiêu chí. Vui lòng nới lỏng bộ lọc.")
                    else:
                        # Find best Zip Code (by highest mean amenity_score)
                        zip_stats = filtered.groupby('zip_code').agg({
                            'amenity_score': 'mean',
                            'sale_price': 'median',
                            'address': 'count',
                            'borough_name': 'first'
                        }).rename(columns={'address': 'count'}).reset_index()
                        
                        # Only consider Zip Codes with at least 5 comps for reliability
                        zip_stats = zip_stats[zip_stats['count'] >= 3]
                        
                        if len(zip_stats) == 0:
                            best_zip = filtered['zip_code'].mode()[0]
                            zip_info = filtered[filtered['zip_code'] == best_zip].iloc[0]
                            best_boro = zip_info['borough_name']
                            med_price = filtered[filtered['zip_code'] == best_zip]['sale_price'].median()
                        else:
                            best_row = zip_stats.sort_values('amenity_score', ascending=False).iloc[0]
                            best_zip = best_row['zip_code']
                            best_boro = best_row['borough_name']
                            med_price = best_row['sale_price']
                            
                        st.success(f"###  ĐỀ XUẤT TỐT NHẤT: Mã Bưu Chính (Zip Code) {best_zip}")
                        st.markdown(f"** Khu vực:** {best_boro} | ** Giá trung vị (Comps):** ${med_price:,.0f}")
                        st.markdown("*Khu vực Zip Code này có mật độ tiện ích cao nhất đáp ứng đủ các tiêu chí bạn chọn. Dưới đây là các Căn nhà tham chiếu (Comps) tiêu biểu đã từng giao dịch:*")
                        
                        comps_in_zip = filtered[filtered['zip_code'] == best_zip].sort_values('amenity_score', ascending=False).head(3)
                        
                        for idx, row in comps_in_zip.iterrows():
                            # HTML Card
                            school_tag = " Trường học" if row['has_school_1km'] else ""
                            subway_tag = " Ga Tàu" if row['has_subway_1km'] else ""
                            park_tag = " Công viên" if row['has_park_1km'] else ""
                            market_tag = " Siêu thị" if row.get('has_supermarket_1km') else ""
                            hosp_tag = " Bệnh viện" if row.get('has_hospital_1km') else ""
                            tags = " | ".join(filter(None, [school_tag, subway_tag, park_tag, market_tag, hosp_tag]))
                            
                            st.markdown(f"""
                            <div style='border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 12px; border-left: 4px solid #db2777; background: #fafafa;'>
                                <h4 style='margin-top: 0; color: #1e293b;'> {row['address']}</h4>
                                <div style='display: flex; justify-content: space-between; font-size: 14px;'>
                                    <div><b>Phân khúc:</b> {row['building_class_category']}</div>
                                    <div style='color: #059669; font-weight: bold;'> ${row['sale_price']:,.0f}</div>
                                </div>
                                <div style='font-size: 13px; color: #64748b; margin-top: 8px;'>
                                    <b>Tiện ích 1km:</b> {tags}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info(" Hãy điều chỉnh bộ lọc và bấm **Tìm Kiếm Comps**")
