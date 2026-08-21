import os
import re
import requests
import pandas as pd
import hashlib
from datetime import datetime
import time

RAW_TEXT = r'''
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_manhattan.xlsx)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_bronx.xlsx)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_brooklyn.xlsx)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_queens.xlsx)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2025/2025_staten_island.xlsx)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_manhattan.xlsx)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_bronx.xlsx)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_brooklyn.xlsx)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_queens.xlsx)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2024/2024_staten_island.xlsx)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2023/2023_manhattan.xlsx)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2023/2023_bronx.xlsx)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2023/2023_brooklyn.xlsx)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2023/2023_queens.xlsx)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2023/2023_staten_island.xlsx)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2022/2022_manhattan.xlsx)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2022/2022_bronx.xlsx)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2022/2022_brooklyn.xlsx)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2022/2022_queens.xlsx)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2022/2022_staten_island.xlsx)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2021/2021_manhattan.xlsx)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2021/2021_bronx.xlsx)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2021/2021_brooklyn.xlsx)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2021/2021_queens.xlsx)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2021/2021_staten_island.xlsx)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2020/2020_manhattan.xlsx)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2020/2020_bronx.xlsx)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2020/2020_brooklyn.xlsx)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2020/2020_queens.xlsx)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2020/2020_staten_island.xlsx)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2019/2019_manhattan.xlsx)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2019/2019_bronx.xlsx)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2019/2019_brooklyn.xlsx)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2019/2019_queens.xlsx)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2019/2019_statenisland.xlsx)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2018/2018_manhattan.xlsx)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2018/2018_bronx.xlsx)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2018/2018_brooklyn.xlsx)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2018/2018_queens.xlsx)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2018/2018_statenisland.xlsx)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2017/2017_manhattan.xls)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2017/2017_bronx.xls)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2017/2017_brooklyn.xls)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2017/2017_queens.xls)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2017/2017_statenisland.xls)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2016/2016_manhattan.xls)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2016/2016_bronx.xls)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2016/2016_brooklyn.xls)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2016/2016_queens.xls)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2016/2016_statenisland.xls)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2015/2015_manhattan.xls)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2015/2015_bronx.xls)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2015/2015_brooklyn.xls)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2015/2015_queens.xls)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2015/2015_statenisland.xls)
Manhattan [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2014/2014_manhattan.xls)
Bronx [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2014/2014_bronx.xls)
Brooklyn [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2014/2014_brooklyn.xls)
Queens [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2014/2014_queens.xls)
Staten Island [Download](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2014/2014_statenisland.xls)
Manhattan [7.02M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2013/2013_manhattan.xls)
Bronx [3.12M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2013/2013_bronx.xls)
Brooklyn [7.M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2013/2013_brooklyn.xls)
Queens [7.1M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2013/2013_queens.xls)
Staten Island [3.31M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2013/2013_statenisland.xls)
Manhattan [6.39M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2012/2012_manhattan.xls)
Bronx [1.37M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2012/2012_bronx.xls)
Brooklyn [5.96M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2012/2012_brooklyn.xls)
Queens [5.93M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2012/2012_queens.xls)
Staten Island [1.50M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2012/2012_statenisland.xls)
Manhattan [5.64M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2011/2011_manhattan.xls)
Bronx [1.41M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2011/2011_bronx.xls)
Brooklyn [5.66M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2011/2011_brooklyn.xls)
Queens [6.00M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2011/2011_queens.xls)
Staten Island [1.35M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2011/2011_statenisland.xls)
Manhattan [5.52M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2010/2010_manhattan.xls)
Bronx [1.43M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2010/2010_bronx.xls)
Brooklyn [5.50M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2010/2010_brooklyn.xls)
Queens [6.32M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2010/2010_queens.xls)
Staten Island [1.61M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2010/2010_statenisland.xls)
Manhattan [4.98M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2009_manhattan.xls)
Bronx [1.47M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2009_bronx.xls)
Brooklyn [5.45M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2009_brooklyn.xls)
Queens [6.66M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2009_queens.xls)
Staten Island [1.83M](https://www.nyc.gov/assets/finance/downloads/pdf/rolling_sales/annualized-sales/2009_statenisland.xls)
Manhattan [5.89M](https://www.nyc.gov/assets/finance/downloads/pdf/09pdf/rolling_sales/sales_2008_manhattan.xls)
Bronx [1.66M](https://www.nyc.gov/assets/finance/downloads/pdf/09pdf/rolling_sales/sales_2008_bronx.xls)
Brooklyn [5.55M](https://www.nyc.gov/assets/finance/downloads/pdf/09pdf/rolling_sales/sales_2008_brooklyn.xls)
Queens [6.43M](https://www.nyc.gov/assets/finance/downloads/pdf/09pdf/rolling_sales/sales_2008_queens.xls)
Staten Island [1.55M](https://www.nyc.gov/assets/finance/downloads/pdf/09pdf/rolling_sales/sales_2008_statenisland.xls)
Manhattan [6.70M](https://www.nyc.gov/assets/finance/downloads/excel/rolling_sales/sales_2007_manhattan.xls)
Bronx [2.75M](https://www.nyc.gov/assets/finance/downloads/excel/rolling_sales/sales_2007_bronx.xls)
Brooklyn [7.23M](https://www.nyc.gov/assets/finance/downloads/excel/rolling_sales/sales_2007_brooklyn.xls)
Queens [8.07M](https://www.nyc.gov/assets/finance/downloads/excel/rolling_sales/sales_2007_queens.xls)
Staten Island [2.60M](https://www.nyc.gov/assets/finance/downloads/excel/rolling_sales/sales_2007_statenisland.xls)
Manhattan [5.84M](https://www.nyc.gov/assets/finance/downloads/sales_manhattan_06.xls)
Bronx [3.62M](https://www.nyc.gov/assets/finance/downloads/sales_bronx_06.xls)
Brooklyn [7.98M](https://www.nyc.gov/assets/finance/downloads/sales_brooklyn_06.xls)
Queens [9.16M](https://www.nyc.gov/assets/finance/downloads/sales_queens_06.xls)
Staten Island [3.47M](https://www.nyc.gov/assets/finance/downloads/sales_si_06.xls)
Manhattan [6.29M](https://www.nyc.gov/assets/finance/downloads/sales_manhattan_05.xls)
Bronx [3.86M](https://www.nyc.gov/assets/finance/downloads/sales_bronx_05.xls)
Brooklyn [8.73M](https://www.nyc.gov/assets/finance/downloads/sales_brooklyn_05.xls)
Queens [10.1M](https://www.nyc.gov/assets/finance/downloads/sales_queens_05.xls)
Staten Island [3.77M](https://www.nyc.gov/assets/finance/downloads/sales_si_05.xls)
Manhattan [6.24M](https://www.nyc.gov/assets/finance/downloads/sales_manhattan_04.xls)
Bronx [3.86M](https://www.nyc.gov/assets/finance/downloads/sales_bronx_04.xls)
Brooklyn [8.9M](https://www.nyc.gov/assets/finance/downloads/sales_brooklyn_04.xls)
Queens [10.4M](https://www.nyc.gov/assets/finance/downloads/sales_queens_04.xls)
Staten Island [4.04M](https://www.nyc.gov/assets/finance/downloads/sales_si_04.xls)
Manhattan [5.64M](https://www.nyc.gov/assets/finance/downloads/sales_manhattan_03.xls)
Bronx [3.65M](https://www.nyc.gov/assets/finance/downloads/sales_bronx_03.xls)
Brooklyn [8.61M](https://www.nyc.gov/assets/finance/downloads/sales_brooklyn_03.xls)
Queens [10.0M](https://www.nyc.gov/assets/finance/downloads/sales_queens_03.xls)
Staten Island [4.05M](https://www.nyc.gov/assets/finance/downloads/sales_si_03.xls)
'''

# Extract URLs
urls = re.findall(r'https://[^\)]+\.xls[x]?', RAW_TEXT)
print(f"Extracted {len(urls)} URLs")

OUTPUT_CSV = os.path.join("data", "Data crawl", "Crawl_data_NYC_Historical.csv")
TEMP_DIR = os.path.join("data", "Data crawl", "historical")
os.makedirs(TEMP_DIR, exist_ok=True)

def download_file(url):
    fname = url.split('/')[-1]
    fpath = os.path.join(TEMP_DIR, fname)
    if os.path.exists(fpath):
        return fpath
    try:
        r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        with open(fpath, 'wb') as f:
            f.write(r.content)
        return fpath
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

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

def find_header_and_parse(fpath, url):
    try:
        # Determine engine
        engine = 'xlrd' if fpath.endswith('.xls') else 'openpyxl'
        # Read first 10 rows to find header
        raw_top = pd.read_excel(fpath, engine=engine, nrows=10, header=None)
        
        header_row = 0
        for i, row in raw_top.iterrows():
            row_str = ' '.join(str(x).upper() for x in row.values)
            if 'BOROUGH' in row_str or 'NEIGHBORHOOD' in row_str or 'BLOCK' in row_str:
                header_row = i
                break
                
        df = pd.read_excel(fpath, engine=engine, skiprows=header_row)
        df.columns = normalize_columns(df.columns)
        
        # Add metadata
        borough_name = "UNKNOWN"
        fname = fpath.lower()
        if 'manhattan' in fname: borough_name = 'Manhattan'
        elif 'bronx' in fname: borough_name = 'Bronx'
        elif 'brooklyn' in fname: borough_name = 'Brooklyn'
        elif 'queens' in fname: borough_name = 'Queens'
        elif 'staten' in fname or 'si' in fname: borough_name = 'Staten Island'
        
        df['BOROUGH_NAME'] = borough_name
        df['SOURCE_URL'] = url
        
        # Basic cleanup
        if 'SALE PRICE' in df.columns:
            df['SALE PRICE'] = pd.to_numeric(df['SALE PRICE'], errors='coerce')
            
        return df
    except Exception as e:
        print(f"Failed parsing {fpath}: {e}")
        return None

all_dfs = []
for i, url in enumerate(urls):
    print(f"[{i+1}/{len(urls)}] Processing {url}...")
    fpath = download_file(url)
    if fpath:
        df = find_header_and_parse(fpath, url)
        if df is not None and not df.empty:
            all_dfs.append(df)
            print(f"  -> Added {len(df)} rows")

if all_dfs:
    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"Total rows gathered: {len(combined)}")
    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved to {OUTPUT_CSV}")
else:
    print("No data processed.")