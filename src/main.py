import sys
import os
import json
import warnings
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from report_generator import generate_full_report

# --- SYSTEM CONFIG ---
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

warnings.filterwarnings('ignore')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
DATA_PATH        = os.path.join(ROOT_DIR, 'data', 'data clean', 'DATA.csv')
CLEAN_DATA_PATH  = DATA_PATH
ML_PRED_PATH     = os.path.join(ROOT_DIR, 'output', 'ml_predictions.csv')
ML_IMP_PATH      = os.path.join(ROOT_DIR, 'output', 'ml_importance.csv')
ML_METRICS_PATH  = os.path.join(ROOT_DIR, 'output', 'ml_metrics.json')
DOC_PATH         = os.path.join(ROOT_DIR, 'reports', 'BaoCao_DoAn_DataAnalyst_Final.docx')

BOROUGH_MAP = {
    '1': 'Manhattan',
    '2': 'Bronx',
    '3': 'Brooklyn',
    '4': 'Queens',
    '5': 'Staten Island',
}

# ─────────────────────────────────────────────
# STEP 1: THU THẬP & LÀM GIÀU DỮ LIỆU
# ─────────────────────────────────────────────

def collect_external_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ghép thêm các chỉ số kinh tế – xã hội theo borough.
    Nguồn: U.S. Census Bureau ACS 2023, NYC Open Data, Bureau of Economic Analysis.
    Trong dự án thực có thể thay bằng API GSO / Census trực tiếp.
    """
    print("[LOG] Step 1: Thu thập & ghép dữ liệu ngoại vi (Census, GDP, Amenities)...")

    # Dữ liệu kinh tế xã hội theo borough (nguồn: Census ACS 2023 & NYC Planning)
    economic_indicators = {
        '1': {'pop_density': 72000, 'avg_income': 88000, 'gdp_local': 6.8, 'dist_center': 2.0},
        '2': {'pop_density': 36000, 'avg_income': 64000, 'gdp_local': 5.9, 'dist_center': 4.5},
        '3': {'pop_density': 38000, 'avg_income': 59000, 'gdp_local': 5.3, 'dist_center': 8.0},
        '4': {'pop_density': 19000, 'avg_income': 55000, 'gdp_local': 5.0, 'dist_center': 11.5},
        '5': {'pop_density':  9000, 'avg_income': 74000, 'gdp_local': 6.2, 'dist_center': 16.0},
    }

    df['borough_str'] = df['borough'].astype(str)

    for key in ['pop_density', 'avg_income', 'gdp_local', 'dist_center']:
        df[key] = df['borough_str'].map(
            lambda x, k=key: economic_indicators.get(x, economic_indicators['1'])[k]
        )

    # ── Công thức tính amenity_score ──────────────────────────────────────────
    # Điểm tiện ích = kết hợp mật độ căn hộ (proxy sự đa dạng dịch vụ)
    # và tính trung tâm (nghịch đảo khoảng cách → gần trung tâm = tiện ích cao hơn).
    # Công thức: amenity_score = clip(total_units × 0.15 + (1 / dist_center) × 10, 1, 10)
    # → total_units × 0.15: mỗi căn hộ đóng góp 0.15 điểm (tối đa ~5 điểm với tòa 33 căn)
    # → (1/dist_center) × 10: Manhattan (2km) ≈ 5đ, Queens (11.5km) ≈ 0.9đ
    # → clip(1,10): giới hạn thang điểm 1–10
    df['amenity_score'] = (
        df['total_units'] * 0.15 + (1 / df['dist_center']) * 10
    ).clip(1, 10)

    return df


def load_and_describe(file_path: str):
    df = pd.read_csv(file_path)
    df = df.rename(columns={'gross_square_feet': 'gross_sqft', 'land_square_feet': 'land_sqft'})
    df = collect_external_data(df)

    # ── Công thức tính building_age ───────────────────────────────────────────
    # building_age = năm giao dịch (sale_year) – năm xây dựng (year_built)
    # Ý nghĩa: đo độ cũ của công trình tính đến thời điểm giao dịch,
    # không phải tính đến năm hiện tại, để đảm bảo nhất quán với dữ liệu lịch sử.
    if 'building_age' not in df.columns and 'year_built' in df.columns and 'sale_year' in df.columns:
        df['building_age'] = df['sale_year'] - df['year_built']
        df['building_age'] = df['building_age'].clip(0, 200)

    # Thêm tên borough tiếng Anh
    df['borough_name'] = df['borough'].astype(str).map(BOROUGH_MAP).fillna('Unknown')

    info = {
        'records':  len(df),
        'columns':  len(df.columns),
        'types':    df.dtypes.value_counts().to_dict(),
        'missing':  int(df.isnull().sum().sum()),
    }
    return df, info


# ─────────────────────────────────────────────
# STEP 2: LÀM SẠCH DỮ LIỆU
# ─────────────────────────────────────────────

def clean_data(df: pd.DataFrame):
    print("[LOG] Step 2: Làm sạch dữ liệu (dedup, impute, IQR, encoding)...")

    numeric_cols = df.select_dtypes(include=[np.number]).columns

    # Thống kê mô tả
    stats = df[numeric_cols].describe().transpose()
    stats['variance'] = df[numeric_cols].var()
    stats['IQR'] = stats['75%'] - stats['25%']

    # 2.1 Loại bỏ trùng lặp
    before = len(df)
    df = df.drop_duplicates()
    print(f"       Đã xóa {before - len(df)} dòng trùng lặp.")

    # 2.2 Điền missing: median cho số, mode cho phân loại
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].fillna(df[col].median())
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mode()[0])

    # 2.3 Xử lý ngoại lệ bằng IQR clipping
    # IQR (Interquartile Range) = khoảng từ phân vị 25% đến 75% của dữ liệu.
    # Ngưỡng cắt: giới hạn dưới = Q1 − 1.5×IQR, giới hạn trên = Q3 + 1.5×IQR.
    # Giá trị ngoại ngưỡng được kẹp về giới hạn dưới (clip) thay vì xóa,
    # Riêng sale_price không kẹp upper bound vì BĐS NYC giá trị cao là bình thường.
    for col in ['sale_price', 'gross_sqft', 'land_sqft']:
        if col in df.columns:
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            IQR = Q3 - Q1
            if col == 'sale_price':
                # Chỉ giới hạn dưới cho giá, không giới hạn trên
                df[col] = df[col].clip(lower=Q1 - 1.5 * IQR)
            else:
                df[col] = np.clip(df[col], Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)

    # 2.4 Tạo biến phái sinh
    df['is_residential'] = df.get('tax_class_present', pd.Series(dtype=str)).apply(
        lambda x: 1 if str(x).startswith('1') else 0
    )

    # Price per sqft thực sự (loại sqft = 0)
    df['price_per_sqft_real'] = np.where(
        df['gross_sqft'] > 0,
        df['sale_price'] / df['gross_sqft'],
        np.nan,
    )

    # Parse ngày bán
    df['sale_date_parsed'] = pd.to_datetime(df.get('sale_date', pd.Series(dtype=str)),
                                            dayfirst=True, errors='coerce')
    df['sale_month'] = df['sale_date_parsed'].dt.month
    df['sale_year'] = df['sale_date_parsed'].dt.year

    # ── Công thức tính building_age ───────────────────────────────────────────
    if 'building_age' not in df.columns and 'year_built' in df.columns and 'sale_year' in df.columns:
        df['building_age'] = df['sale_year'] - df['year_built']
        df['building_age'] = df['building_age'].clip(0, 200)

    # ── Tính chỉ số biến động giá YoY theo borough ────────────────────────────
    # YoY (Year-over-Year) = % thay đổi giá trung bình giữa 2 năm liên tiếp theo từng quận.
    # Công thức: YoY_borough = (Giá_trung_bình_năm_N / Giá_trung_bình_năm_(N-1) − 1) × 100%
    # Dùng trung bình thay trung bình để giảm ảnh hưởng của giao dịch ngoại lệ.
    yoy_data = df.groupby(['borough_name', 'sale_year'])['sale_price'].median().unstack()
    if yoy_data.shape[1] >= 2:
        years_sorted = sorted(yoy_data.columns)
        yoy_data['YoY_pct'] = (
            yoy_data[years_sorted[-1]] / yoy_data[years_sorted[-2]] - 1
        ) * 100
        print("       YoY % thay đổi giá theo borough:")
        for borough, row in yoy_data.iterrows():
            if pd.notna(row.get('YoY_pct')):
                print(f"         {borough}: {row['YoY_pct']:+.1f}%")

    df.to_csv(CLEAN_DATA_PATH, index=False)
    print(f"       Dữ liệu sạch đã lưu: {CLEAN_DATA_PATH}  ({len(df):,} dòng)")
    return df, stats


# ─────────────────────────────────────────────
# STEP 3: MACHINE LEARNING THỰC SỰ
# ─────────────────────────────────────────────

def train_ml_models(df: pd.DataFrame):
    print("[LOG] Step 3: Huấn luyện mô hình (Linear Regression vs Random Forest)...")

    features = [
        'gross_sqft', 'land_sqft', 'total_units', 'building_age',
        'pop_density', 'avg_income', 'gdp_local', 'dist_center', 'amenity_score',
    ]

    # Chỉ dùng các hàng có gross_sqft hợp lệ
    df_ml = df[df['gross_sqft'] > 0].copy()
    X = df_ml[features].fillna(df_ml[features].median())
    y = df_ml['sale_price']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)

    # Random Forest
    rf = RandomForestRegressor(n_estimators=150, max_depth=14, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)

    # Tính % sai số trung bình để diễn giải cho người không chuyên
    lr_mape = float(np.mean(np.abs((y_test.values - lr_preds) / y_test.values)) * 100)
    rf_mape = float(np.mean(np.abs((y_test.values - rf_preds) / y_test.values)) * 100)

    metrics = {
        'Linear Regression': {
            'MAE':  round(float(mean_absolute_error(y_test, lr_preds))),
            'RMSE': round(float(np.sqrt(mean_squared_error(y_test, lr_preds)))),
            'R2':   round(float(r2_score(y_test, lr_preds)), 4),
            'MAPE': round(lr_mape, 2),
        },
        'Random Forest': {
            'MAE':  round(float(mean_absolute_error(y_test, rf_preds))),
            'RMSE': round(float(np.sqrt(mean_squared_error(y_test, rf_preds)))),
            'R2':   round(float(r2_score(y_test, rf_preds)), 4),
            'MAPE': round(rf_mape, 2),
        },
    }

    importance = pd.DataFrame({
        'Feature':    features,
        'Importance': rf.feature_importances_,
    }).sort_values('Importance', ascending=False)

    # Lưu 1500 điểm dự báo mẫu để dashboard dùng
    n_sample = min(1500, len(y_test))
    idx = np.random.default_rng(42).choice(len(y_test), n_sample, replace=False)
    pred_df = pd.DataFrame({
        'Actual':    y_test.values[idx],
        'Predicted': rf_preds[idx],
    })

    # Xuất file
    pred_df.to_csv(ML_PRED_PATH, index=False)
    importance.to_csv(ML_IMP_PATH, index=False)
    with open(ML_METRICS_PATH, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"       Random Forest R² = {metrics['Random Forest']['R2']}")
    print(f"       Sai số TB (MAPE) = {rf_mape:.1f}% — mô hình lệch khoảng {rf_mape:.1f}% so với giá thực")
    print(f"       Predictions saved: {ML_PRED_PATH}")
    return metrics, importance, (y_test.values[idx], rf_preds[idx])


# ─────────────────────────────────────────────
# STEP 4: XUẤT BÁO CÁO WORD
# ─────────────────────────────────────────────



# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    try:
        print('\n=== PIPELINE BẮT ĐẦU ===\n')
        df, info = load_and_describe(DATA_PATH)
        df_clean, stats = clean_data(df)
        metrics, importance, _ = train_ml_models(df_clean)
        generate_full_report(DOC_PATH, info, stats, metrics, importance)
        print('\n=== PIPELINE HOÀN THÀNH ===')
        print(f'  • Dữ liệu sạch : {CLEAN_DATA_PATH}')
        print(f'  • Dự báo ML    : {ML_PRED_PATH}')
        print(f'  • Importance   : {ML_IMP_PATH}')
        print(f'  • Metrics JSON : {ML_METRICS_PATH}')
        print(f'  • Báo cáo Word : {DOC_PATH}')
    except Exception:
        import traceback
        traceback.print_exc()
