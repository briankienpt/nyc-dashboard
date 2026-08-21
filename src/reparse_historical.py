import os
import pandas as pd
import re

TEMP_DIR = os.path.join("data", "Data crawl", "historical")
OUTPUT_CSV = os.path.join("data", "Data crawl", "Crawl_data_NYC_Historical.csv")

def normalize_columns(columns):
    norm = []
    for c in columns:
        if pd.isna(c):
            norm.append("")
            continue
        c_str = str(c).upper().replace('\n', ' ').strip()
        c_str = re.sub(r'\s+', ' ', c_str)
        # Fix known variations
        if 'EASE-MENT' in c_str: c_str = 'EASEMENT'
        if c_str == 'SALE_PRICE': c_str = 'SALE PRICE'
        if c_str == 'SALE_DATE': c_str = 'SALE DATE'
        if c_str == 'ZIPCODE': c_str = 'ZIP CODE'
        if c_str == 'APARTMENT_NUMBER': c_str = 'APARTMENT NUMBER'
        if c_str == 'TAX CLASS AT TIME OF SALE': c_str = 'TAX CLASS AT TIME OF SALE'
        if c_str == 'BUILDING CLASS AT TIME OF SALE': c_str = 'BUILDING CLASS AT TIME OF SALE'
        if c_str == 'BUILDING CLASS AT PRESENT': c_str = 'BUILDING CLASS AT PRESENT'
        norm.append(c_str)
    return norm

all_dfs = []
files = os.listdir(TEMP_DIR)
for i, fname in enumerate(files):
    fpath = os.path.join(TEMP_DIR, fname)
    if not (fname.endswith('.xls') or fname.endswith('.xlsx')):
        continue
        
    engine = 'xlrd' if fname.endswith('.xls') else 'openpyxl'
    try:
        raw_top = pd.read_excel(fpath, engine=engine, nrows=10, header=None)
        
        header_row = -1
        for idx, row in raw_top.iterrows():
            row_str = ' '.join(str(x).upper() for x in row.values)
            # A strict condition for header: must contain multiple key columns
            if 'BLOCK' in row_str and 'LOT' in row_str and ('SALE PRICE' in row_str or 'PRICE' in row_str):
                header_row = idx
                break
                
        if header_row == -1:
            # fallback
            header_row = 4 # Common in NYC sales
            
        df = pd.read_excel(fpath, engine=engine, skiprows=header_row)
        df.columns = normalize_columns(df.columns)
        
        # Add metadata
        borough_name = "UNKNOWN"
        fname_lower = fname.lower()
        if 'manhattan' in fname_lower: borough_name = 'Manhattan'
        elif 'bronx' in fname_lower: borough_name = 'Bronx'
        elif 'brooklyn' in fname_lower: borough_name = 'Brooklyn'
        elif 'queens' in fname_lower: borough_name = 'Queens'
        elif 'staten' in fname_lower or 'si' in fname_lower: borough_name = 'Staten Island'
        
        df['BOROUGH_NAME'] = borough_name
        df['SOURCE_FILE'] = fname
        
        if 'SALE PRICE' in df.columns:
            df['SALE PRICE'] = pd.to_numeric(df['SALE PRICE'], errors='coerce')
            
        all_dfs.append(df)
        print(f"[{i+1}/{len(files)}] {fname} -> Found header at {header_row}, added {len(df)} rows")
    except Exception as e:
        print(f"Failed parsing {fname}: {e}")

if all_dfs:
    combined = pd.concat(all_dfs, ignore_index=True)
    # Drop rows where 'BLOCK' or 'LOT' is null, these are likely footer rows or empty rows
    if 'BLOCK' in combined.columns:
        combined = combined.dropna(subset=['BLOCK'])
    
    print(f"Total rows gathered: {len(combined)}")
    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved to {OUTPUT_CSV}")