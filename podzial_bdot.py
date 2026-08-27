import geopandas as gpd
from pathlib import Path

# Ścieżki
input_file = """D:/GIS NCBR/BDOT/OT_BUBD_A.parquet"""
output_dir = Path("bdot-budynki_powiaty")
output_dir.mkdir(exist_ok=True)

# Nazwa kolumny, według której dzielimy plik
attribute_column = "TERYT"  # zamień na swoją kolumnę

# Format docelowy: 'parquet' (rekomendowany) lub 'gpkg'
target_format = "parquet"

print("Wczytywanie pliku SHP...")
gdf = gpd.read_parquet(input_file)
# gdf = gdf.drop(columns=["ID_IIP"])
# gdf["TERYT_POW"] = gdf["TERYT_GMI"].astype(str).str.zfill(6).str[:4]

print(f"Dzielenie i zapisywanie danych wg atrybutu: {attribute_column}...")
for teryt, group in gdf.groupby(attribute_column):
    out_file = output_dir / f"{teryt}_bud.parquet"
    group.to_parquet(out_file, index=False)

print("Gotowe!")

