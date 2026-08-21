import os
import requests
import pandas as pd
import hashlib
from datetime import datetime
import time

URLS = {
    '2024': {
        'Manhattan': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_manhattan.xlsx',
        'Bronx': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_bronx.xlsx',
        'Brooklyn': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_brooklyn.xlsx',
        'Queens': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_queens.xlsx',
        'Staten Island': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_staten_island.xlsx'
    },
    '2025': {
        'Manhattan': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_manhattan.xlsx',
        'Bronx': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_bronx.xlsx',
        'Brooklyn': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_brooklyn.xlsx',
        'Queens': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_queens.xlsx',
        'Staten Island': 'https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_staten_island.xlsx'
    }
}

OUTPUT_CSV = os.path.join("data", "Data crawl", "Crawl_data_NYC.csv")
TEMP_DIR = os.path.join("data", "Data crawl", "annualized")
os.makedirs(TEMP_DIR, exist_ok=True)

def download_file(url, filepath):
    if os.path.exists(filepath):
        print(f"Already exists: {filepath}")
        return True
    print(f"Downloading {url} ...")
    try:
        response = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Failed: {url} -> {e}")
        return False

def get_hash(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:16]

all_dfs = []
for year, b_dict in URLS.items():
    for borough, url in b_dict.items():
        fname = url.split('/')[-1]
        fpath = os.path.join(TEMP_DIR, fname)
        if download_file(url, fpath):
            try:
                # NYC Gov Excel files typically have 4 rows of headers before data
                df = None
                for skip in [4, 3, 5, 6, 7]:
                    try:
                        temp = pd.read_excel(fpath, skiprows=skip)
                        if not temp.empty and len(temp.columns) > 5:
                            df = temp
                            break
                    except:
                        pass
                
                if df is None:
                    print(f"Could not parse {fpath}")
                    continue

                df.columns = [str(c).strip().upper() for c in df.columns]
                
                # Sửa cột EASE-MENT thành EASEMENT
                if 'EASE-MENT' in df.columns:
                    df.rename(columns={'EASE-MENT': 'EASEMENT'}, inplace=True)
                
                df['BOROUGH'] = borough
                df['SOURCE_URL'] = url
                df['CRAWL_DATE'] = datetime.now().strftime('%Y-%m-%d')
                df['CRAWL_TIMESTAMP'] = datetime.now().isoformat()
                df['FILE_HASH'] = get_hash(fpath)
                
                # Cleanup neighborhood
                if 'NEIGHBORHOOD' in df.columns:
                    df['NEIGHBORHOOD'] = df['NEIGHBORHOOD'].astype(str).str.strip().str.upper()
                
                # Numeric conversions
                for col in ['SALE PRICE', 'GROSS SQUARE FEET', 'LAND SQUARE FEET', 'YEAR BUILT', 'TOTAL UNITS', 'RESIDENTIAL UNITS', 'COMMERCIAL UNITS']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Data enrich
                if 'SALE PRICE' in df.columns and 'GROSS SQUARE FEET' in df.columns:
                    df['SALE PRICE PER SQFT'] = df['SALE PRICE'] / df['GROSS SQUARE FEET']
                if 'YEAR BUILT' in df.columns:
                    df['BUILDING_AGE'] = datetime.now().year - df['YEAR BUILT']
                if 'SALE DATE' in df.columns:
                    df['SALE DATE PARSED'] = pd.to_datetime(df['SALE DATE'], errors='coerce')
                    df['SALE YEAR'] = df['SALE DATE PARSED'].dt.year
                    df['SALE MONTH'] = df['SALE DATE PARSED'].dt.month
                    df['SALE QUARTER'] = df['SALE DATE PARSED'].dt.quarter
                    df['SALE DAY OF WEEK'] = df['SALE DATE PARSED'].dt.dayofweek
                if 'SALE PRICE' in df.columns:
                    df['PRICE_CATEGORY'] = pd.cut(df['SALE PRICE'], bins=[0, 100000, 500000, 1000000, 5000000, float('inf')], labels=['Under $100K', '$100K-$500K', '$500K-$1M', '$1M-$5M', 'Over $5M'])
                if 'BUILDING_AGE' in df.columns:
                    df['AGE_CATEGORY'] = pd.cut(df['BUILDING_AGE'], bins=[0, 5, 20, 50, 100, float('inf')], labels=['New (0-5)', 'Modern (5-20)', 'Established (20-50)', 'Old (50-100)', 'Historic (100+)'])
                if 'TOTAL UNITS' in df.columns and 'GROSS SQUARE FEET' in df.columns:
                    df['SQFT_PER_UNIT'] = df['GROSS SQUARE FEET'] / df['TOTAL UNITS']
                if 'RESIDENTIAL UNITS' in df.columns and 'TOTAL UNITS' in df.columns:
                    df['RESIDENTIAL_RATIO'] = df['RESIDENTIAL UNITS'] / df['TOTAL UNITS']

                all_dfs.append(df)
                print(f"Processed {fpath} - {len(df)} rows")
            except Exception as e:
                print(f"Error on {fpath}: {e}")

if all_dfs:
    new_data = pd.concat(all_dfs, ignore_index=True)
    print(f"Total new rows: {len(new_data)}")
    
    # Load old data
    print("Loading existing Crawl_data_NYC.csv...")
    old_data = pd.read_csv(OUTPUT_CSV)
    print(f"Existing rows: {len(old_data)}")
    
    combined = pd.concat([old_data, new_data], ignore_index=True)
    print(f"Combined rows: {len(combined)}")
    
    # Deduplicate based on primary identifiers
    dedup_cols = ['BOROUGH', 'ADDRESS', 'SALE DATE', 'SALE PRICE']
    combined = combined.drop_duplicates(subset=dedup_cols, keep='last')
    print(f"After deduplication: {len(combined)} rows")
    
    combined.to_csv(OUTPUT_CSV, index=False)
    print("Saved to Crawl_data_NYC.csv")
else:
    print("No new data was downloaded/processed.")