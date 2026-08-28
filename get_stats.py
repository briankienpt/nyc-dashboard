import pandas as pd

df = pd.read_csv('DATA.csv')
print('=== KPI METRICS ===')
print('Total transactions:', len(df))
print('Median price:', df['sale_price'].median())
print('Total value (Billion USD):', df['sale_price'].sum() / 1e9)
print('Pct >= 1M:', (df['sale_price'] >= 1_000_000).mean() * 100)

if 'price_per_sqft' in df.columns:
    df_ppsf = df.dropna(subset=['price_per_sqft'])
    print('Median ppsf:', df_ppsf['price_per_sqft'].median())

print('\n=== BOROUGH: TRANSACTION COUNT & MEDIAN PRICE ===')
bor = df.groupby('borough_name')['sale_price'].agg(count='count', median='median').sort_values('median', ascending=False)
print(bor)

print('\n=== BUILDING TYPE (TOP 6) ===')
bt_cnt = df['building_type'].value_counts().head(6)
print('Counts & %:')
for k, v in bt_cnt.items():
    print(f"  {k}: {v:,} ({v/len(df)*100:.1f}%)")

print('\nMedian price by building type:')
bt_med = df.groupby('building_type')['sale_price'].median().loc[bt_cnt.index]
for k, v in bt_med.items():
    print(f"  {k}: ${v:,.0f}")

print('\n=== SEGMENTATION ===')
df['_segment'] = pd.cut(
    df['total_units'],
    bins=[-1, 1, 10, float('inf')],
    labels=['① Mua ở thực (1 căn)', '② Đầu tư nhỏ (2-10)', '③ Tổ chức (>10)']
)
seg = df.groupby('_segment', observed=True)['sale_price'].agg(count='count', median='median')
for idx, row in seg.iterrows():
    print(f"  {idx}: {row['count']:,} GD ({row['count']/len(df)*100:.1f}%) - Median Price: ${row['median']:,.0f}")

print('\n=== RISK CV ===')
borough_risk = df.groupby('borough_name').agg(
    med_price=('sale_price','median'),
    std_price=('sale_price','std'),
    n_gd=('sale_price','count')
).reset_index()
borough_risk['CV (%)'] = (borough_risk['std_price'] / borough_risk['med_price'] * 100).round(1)
print(borough_risk)
