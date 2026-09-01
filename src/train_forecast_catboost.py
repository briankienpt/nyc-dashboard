# -*- coding: utf-8 -*-
import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from catboost import CatBoostRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("🏙️  DỰ BÁO GIÁ BẤT ĐỘNG SẢN NEW YORK (NYC REAL ESTATE FORECASTING)")
print("   Mô hình: CatBoost Regressor vs Baseline Linear Regression")
print("=" * 70)

# 1. Đọc dữ liệu
data_paths = [
    os.path.join("data", "data clean", "DATA.csv"),
    os.path.join("..", "NYC_Dashboard", "data", "data clean", "DATA.csv"),
    os.path.join("..", "DATA.csv")
]

file_path = None
for p in data_paths:
    if os.path.exists(p):
        file_path = p
        break

if not file_path:
    raise FileNotFoundError("Không tìm thấy file DATA.csv!")

print(f"\n📂 1. Đang đọc dữ liệu sạch: {file_path}...")
df = pd.read_csv(file_path, low_memory=False)
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('-', '_')

# 2. Xử lý target
target = "sale_price"
if target not in df.columns:
    raise ValueError(f"Không tìm thấy cột '{target}' trong dữ liệu.")

df[target] = pd.to_numeric(df[target], errors="coerce")
df = df.dropna(subset=[target])
df = df[df[target] >= 10000].copy()

if len(df) > 60000:
    df = df.sample(n=60000, random_state=42).reset_index(drop=True)

date_check = pd.to_datetime(df.get('sale_date_parsed', df.get('sale_date')), errors='coerce')
min_date = date_check.min().strftime('%m/%Y') if date_check.notna().any() else '04/2025'
max_date = date_check.max().strftime('%m/%Y') if date_check.notna().any() else '03/2026'

print(f"📊 Số lượng bản ghi hợp lệ: {len(df):,} dòng x {df.shape[1]} cột")
print(f"📅 Giai đoạn dữ liệu ghi nhận: từ {min_date} đến {max_date} (NYC 2025 - 2026)")
print(f"💰 Khoảng giá: từ ${df[target].min():,.0f} đến ${df[target].max():,.0f}")
print(f"📍 Giá trung bình (Median): ${df[target].median():,.0f}")

# 3. Feature Engineering
print("\n⚙️ 2. Trích xuất đặc trưng (Feature Engineering)...")
if 'sale_date_parsed' in df.columns:
    date_series = pd.to_datetime(df['sale_date_parsed'], errors='coerce')
elif 'sale_date' in df.columns:
    date_series = pd.to_datetime(df['sale_date'], errors='coerce')
else:
    date_series = pd.Series(pd.to_datetime('2025-04-01'), index=df.index)

df['sale_year'] = date_series.dt.year.fillna(2025).astype(int)
df['sale_month'] = date_series.dt.month.fillna(6).astype(int)
df['sale_quarter'] = date_series.dt.quarter.fillna(2).astype(int)

if 'year_built' in df.columns and 'sale_year' in df.columns:
    df['year_built'] = pd.to_numeric(df['year_built'], errors='coerce').fillna(1950)
    df['building_age'] = df['sale_year'] - df['year_built']
    df.loc[df['building_age'] < 0, 'building_age'] = 0
else:
    df['building_age'] = pd.to_numeric(df.get('building_age', 20), errors='coerce').fillna(20)
    df.loc[df['building_age'] < 0, 'building_age'] = 0

if 'residential_units' in df.columns and 'commercial_units' in df.columns:
    res_units = pd.to_numeric(df['residential_units'], errors='coerce').fillna(0)
    com_units = pd.to_numeric(df['commercial_units'], errors='coerce').fillna(0)
    df['total_units_calculated'] = res_units + com_units
    df['commercial_units'] = com_units
    df['residential_units'] = res_units
else:
    df['total_units_calculated'] = pd.to_numeric(df.get('total_units', 1), errors='coerce').fillna(1)

if 'gross_sqft' in df.columns and 'land_sqft' in df.columns:
    gross = pd.to_numeric(df['gross_sqft'], errors='coerce').fillna(0)
    land = pd.to_numeric(df['land_sqft'], errors='coerce').replace(0, np.nan)
    df['gross_sqft'] = gross
    df['land_sqft'] = land.fillna(0)
    df['building_land_ratio'] = (gross / land).fillna(1.0)
    df['gross_per_unit'] = (gross / df['total_units_calculated'].clip(lower=1)).fillna(0)

# 4. Loại bỏ rò rỉ & chuẩn bị X, y
drop_columns = [
    'sale_price', 'price_per_sqft', 'price_per_sqft_real',
    'address', 'sale_date', 'sale_date_parsed', 'ease_ment', 'easement'
]

X = df.drop(columns=[col for col in drop_columns if col in df.columns]).copy()
y_original = df[target].copy()
y = np.log1p(y_original)

categorical_columns = X.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
numerical_columns = X.select_dtypes(include=np.number).columns.tolist()

for col in categorical_columns:
    X[col] = X[col].fillna('Unknown').astype(str)

for col in numerical_columns:
    X[col] = X[col].replace([np.inf, -np.inf], np.nan)
    median_val = X[col].median()
    if pd.isna(median_val):
        median_val = 0
    X[col] = X[col].fillna(median_val)

print(f"🎯 Tổng số đặc trưng đầu vào (Features): {X.shape[1]}")
print(f"📌 Biến phân loại (Categorical): {len(categorical_columns)} | Biến số học (Numerical): {len(numerical_columns)}")

# 5. Chia train / test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"🏋️ Tập Train (80%): {X_train.shape[0]:,} dòng | 🧪 Tập Test (20%): {X_test.shape[0]:,} dòng")

# 6. Huấn luyện CatBoost
print("\n⏳ 3. Đang huấn luyện mô hình CatBoost Regressor...")
model = CatBoostRegressor(
    iterations=2000,
    learning_rate=0.03,
    depth=8,
    loss_function='RMSE',
    l2_leaf_reg=5,
    random_seed=42,
    verbose=200
)

model.fit(
    X_train, y_train,
    cat_features=categorical_columns,
    eval_set=(X_test, y_test),
    early_stopping_rounds=150,
    verbose=200
)
print("🎉 Huấn luyện CatBoost hoàn tất!")

# 7. Đánh giá CatBoost
y_pred_log = model.predict(X_test)
y_pred = np.maximum(0, np.expm1(y_pred_log))
y_actual = np.expm1(y_test).values

MAE = mean_absolute_error(y_actual, y_pred)
RMSE = np.sqrt(mean_squared_error(y_actual, y_pred))
R2 = r2_score(y_actual, y_pred)
mask = y_actual != 0
MAPE = np.mean(np.abs((y_actual[mask] - y_pred[mask]) / y_actual[mask])) * 100

print("\n" + "=" * 55)
print("         KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH CATBOOST")
print("=" * 55)
print(f"🔹 MAE  (Sai số tuyệt đối trung bình):  ${MAE:,.2f}")
print(f"🔹 RMSE (Sai số bình phương trung bình): ${RMSE:,.2f}")
print(f"🔹 R²   (Hệ số xác định):                {R2:.4f} ({R2*100:.2f}%)")
print(f"🔹 MAPE (Tỷ lệ sai số phần trăm TB):     {MAPE:.2f}%")
print("=" * 55)

# 8. Mẫu 10 kết quả dự báo
results = pd.DataFrame({
    "Giá thực tế (Actual)": y_actual,
    "Giá AI dự báo (Predicted)": y_pred
})
results["Sai số tuyệt đối ($)"] = np.abs(results["Giá thực tế (Actual)"] - results["Giá AI dự báo (Predicted)"])
results["Tỷ lệ sai số (%)"] = (results["Sai số tuyệt đối ($)"] / results["Giá thực tế (Actual)"]) * 100

print("\n📋 10 Mẫu kết quả dự báo ngẫu nhiên trên tập test:")
sample_df = results.sample(10, random_state=42).reset_index(drop=True)
for idx, row in sample_df.iterrows():
    print(f"  #{idx+1:02d}: Thực tế = ${row['Giá thực tế (Actual)']:>12,.0f} | AI dự báo = ${row['Giá AI dự báo (Predicted)']:>12,.0f} | Sai số = {row['Tỷ lệ sai số (%)']:>6.2f}%")

# 9. Huấn luyện baseline Linear Regression (Ridge)
print("\n⏳ 4. Đang huấn luyện Baseline Linear Regression (Ridge)...")
cat_cols_lr = ['borough_name'] if 'borough_name' in X.columns else ['borough']
if 'building_category' in X.columns:
    cat_cols_lr.append('building_category')

num_cols_lr = [
    c for c in ['gross_sqft', 'land_sqft', 'building_age', 'total_units_calculated', 
                'building_land_ratio', 'sale_year', 'sale_month'] if c in X.columns
]

preprocessor_lr = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_cols_lr),
        ('cat', OneHotEncoder(drop='first', handle_unknown='ignore'), cat_cols_lr)
    ]
)

ridge_model = Pipeline(steps=[
    ('preprocessor', preprocessor_lr),
    ('regressor', Ridge(alpha=1.0))
])

ridge_model.fit(X_train[num_cols_lr + cat_cols_lr], y_train)
y_pred_lr_log = ridge_model.predict(X_test[num_cols_lr + cat_cols_lr])
y_pred_lr = np.maximum(0, np.expm1(y_pred_lr_log))

MAE_lr = mean_absolute_error(y_actual, y_pred_lr)
RMSE_lr = np.sqrt(mean_squared_error(y_actual, y_pred_lr))
R2_lr = r2_score(y_actual, y_pred_lr)
MAPE_lr = np.mean(np.abs((y_actual[mask] - y_pred_lr[mask]) / y_actual[mask])) * 100

print("\n" + "=" * 80)
print("             BẢNG SO SÁNH HIỆU NĂNG: CATBOOST vs LINEAR REGRESSION")
print("=" * 80)
print(f"{'Chỉ số (Metric)':<35} | {'CatBoost Regressor':<20} | {'Linear Regression':<20}")
print("-" * 80)
print(f"{'Hệ số xác định R²':<35} | {f'{R2:.4f} ({R2*100:.1f}%)':<20} | {f'{R2_lr:.4f} ({R2_lr*100:.1f}%)':<20}")
print(f"{'MAE (Sai số tuyệt đối TB)':<35} | {f'${MAE:,.2f}':<20} | {f'${MAE_lr:,.2f}':<20}")
print(f"{'RMSE (Sai số bình phương TB)':<35} | {f'${RMSE:,.2f}':<20} | {f'${RMSE_lr:,.2f}':<20}")
print(f"{'MAPE (Tỷ lệ sai số %)':<35} | {f'{MAPE:.2f}%':<20} | {f'{MAPE_lr:.2f}%':<20}")
print("=" * 80)
print(f"🏆 CatBoost tăng R² thêm +{(R2 - R2_lr)*100:.2f}%, giảm sai số MAPE {(MAPE_lr - MAPE):.2f}% so với Linear Regression!")

# 5. VẼ VÀ LƯU 4 BIỂU ĐỒ TRỰC QUAN
print("\n🎨 5. Đang tạo và lưu 4 biểu đồ trực quan...")

# Biểu đồ 1: Scatter plot Thực tế vs Dự báo
plt.figure("Biểu đồ 1: Giá thực tế vs AI dự báo", figsize=(8, 6))
plt.scatter(y_actual, y_pred, alpha=0.35, color='#0284c7', edgecolors='none', s=25, label='Bất động sản kiểm thử')
max_view = min(max(np.percentile(y_actual, 99.5), np.percentile(y_pred, 99.5)), 15000000)
plt.plot([0, max_view], [0, max_view], '--', color='#dc2626', linewidth=2, label='Đường chuẩn lý tưởng (y = x)')
plt.xlim(0, max_view)
plt.ylim(0, max_view)
plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x*1e-6:.1f}M"))
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f"${y*1e-6:.1f}M"))
plt.xlabel('Giá thực tế (Actual Price)', fontsize=11, fontweight='bold', labelpad=10)
plt.ylabel('Giá AI dự báo (Predicted Price)', fontsize=11, fontweight='bold', labelpad=10)
plt.title(f'CatBoost Regressor: Actual vs Predicted Price\n(R² = {R2:.4f} | MAPE = {MAPE:.2f}%)', fontsize=12, fontweight='bold', pad=12)
plt.legend(frameon=True, facecolor='white', loc='upper left')
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('chart_1_actual_vs_pred.png', dpi=300)
print("  ✅ Đã lưu: chart_1_actual_vs_pred.png")

# Biểu đồ 2: So sánh 100 mẫu bất động sản
comparison = pd.DataFrame({"Actual_Price": y_actual, "Predicted_Price": y_pred}).sort_values("Actual_Price").reset_index(drop=True)
number_samples = min(100, len(comparison))
indices = np.linspace(0, len(comparison) - 1, number_samples).astype(int)
plot_data = comparison.iloc[indices].reset_index(drop=True)

plt.figure("Biểu đồ 2: So sánh 100 căn mẫu", figsize=(14, 6))
plt.plot(plot_data.index, plot_data["Actual_Price"], marker="o", markersize=3, color='#2563eb', linewidth=2, label="Giá thực tế")
plt.plot(plot_data.index, plot_data["Predicted_Price"], marker="s", markersize=3, color='#ea580c', linewidth=2, linestyle='--', label="Giá AI dự báo")
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, p: f"${y*1e-6:.2f}M"))
plt.xlabel("100 Mẫu bất động sản kiểm thử (Xếp theo giá tăng dần)", fontsize=11, fontweight='bold')
plt.ylabel("Giá bán (USD)", fontsize=11, fontweight='bold')
plt.title(f"So sánh Giá thực tế và Giá dự báo trên 100 mẫu kiểm nghiệm (R² = {R2:.4f})", fontsize=13, fontweight='bold')
plt.legend(frameon=True, facecolor='white')
plt.grid(True, linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('chart_2_sample_comparison.png', dpi=300)
print("  ✅ Đã lưu: chart_2_sample_comparison.png")

# Biểu đồ 3: Top 20 yếu tố ảnh hưởng giá
importance = pd.DataFrame({"Feature": X.columns, "Importance (%)": model.feature_importances_}).sort_values("Importance (%)", ascending=False)
top20 = importance.head(20).sort_values("Importance (%)", ascending=True)

plt.figure("Biểu đồ 3: Top 20 Yếu tố tác động giá", figsize=(10, 8))
bars = plt.barh(top20["Feature"], top20["Importance (%)"], color='#6366f1', edgecolor='#4338ca')
plt.xlabel("Tỷ lệ phần trăm đóng góp (%)", fontsize=11, fontweight='bold')
plt.title("Top 20 Biến có tác động mạnh nhất đến Định giá BĐS New York", fontsize=13, fontweight='bold', pad=12)
for bar in bars:
    w = bar.get_width()
    plt.text(w + 0.15, bar.get_y() + bar.get_height()/2, f"{w:.2f}%", va='center', fontsize=9, color='#1e1b4b')
plt.grid(axis='x', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('chart_3_feature_importance.png', dpi=300)
print("  ✅ Đã lưu: chart_3_feature_importance.png")

# Biểu đồ 4: So sánh CatBoost vs Linear Regression
fig, axes = plt.subplots(1, 2, figsize=(14, 5), num="Biểu đồ 4: So sánh CatBoost vs Linear Regression")
models = ['Linear Regression', 'CatBoost Regressor']
r2_values = [max(0, R2_lr), R2]
colors = ['#8b5cf6', '#0284c7']
axes[0].bar(models, r2_values, color=colors, width=0.5, edgecolor='#1e1b4b')
axes[0].set_title('So sánh Hệ số xác định R² (Càng cao càng tốt)', fontsize=12, fontweight='bold')
axes[0].set_ylabel('R² Score', fontsize=11, fontweight='bold')
axes[0].set_ylim(0, max(R2, R2_lr) * 1.3)
for i, v in enumerate(r2_values):
    axes[0].text(i, v + 0.01, f"{v:.4f}\n({v*100:.1f}%)", ha='center', fontweight='bold', fontsize=10)
axes[0].grid(axis='y', linestyle=':', alpha=0.6)

mape_values = [MAPE_lr, MAPE]
axes[1].bar(models, mape_values, color=['#f43f5e', '#10b981'], width=0.5, edgecolor='#1e1b4b')
axes[1].set_title('So sánh Tỷ lệ sai số MAPE % (Càng thấp càng tốt)', fontsize=12, fontweight='bold')
axes[1].set_ylabel('MAPE (%)', fontsize=11, fontweight='bold')
axes[1].set_ylim(0, max(mape_values) * 1.25)
for i, v in enumerate(mape_values):
    axes[1].text(i, v + 0.8, f"{v:.2f}%", ha='center', fontweight='bold', fontsize=10)
axes[1].grid(axis='y', linestyle=':', alpha=0.6)
plt.tight_layout()
plt.savefig('chart_4_model_comparison.png', dpi=300)
print("  ✅ Đã lưu: chart_4_model_comparison.png")

print("\n" + "=" * 80)
print("✅ QUÁ TRÌNH HUẤN LUYỆN VÀ CHẠY DỰ BÁO HOÀN TẤT THÀNH CÔNG!")
print("🖼️  Đã lưu 4 file ảnh biểu đồ PNG vào thư mục hiện tại.")
print("📊 Đang mở các cửa sổ biểu đồ (Hãy xem hoặc tắt cửa sổ để kết thúc)...")
print("=" * 80)

plt.show()
