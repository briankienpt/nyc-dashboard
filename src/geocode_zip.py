import sqlite3
import pgeocode
import pandas as pd

DB_PATH = 'data/warehouse/nyc_warehouse.db'

# Get unique zip codes
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql("SELECT DISTINCT zip_code FROM dim_location WHERE zip_code IS NOT NULL AND zip_code != ''", conn)

nomi = pgeocode.Nominatim('us')
coords = []
for z in df['zip_code']:
    z_clean = str(z).replace('.0', '').strip()[:5]
    if len(z_clean) == 5:
        info = nomi.query_postal_code(z_clean)
        coords.append({'zip_code': z, 'lat': info.latitude, 'lon': info.longitude})
    else:
        coords.append({'zip_code': z, 'lat': None, 'lon': None})

coords_df = pd.DataFrame(coords)
coords_df.to_sql('dim_zipcode', conn, if_exists='replace', index=False)
print("Saved dim_zipcode to SQLite with", len(coords_df), "records.")
conn.close()