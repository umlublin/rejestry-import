import geopandas as gpd
from pathlib import Path

# Pobranie danych aktualnych z BDOT i podzial wg. powiatu
# nowe podejscie to bdot_pobranie.py


# https://opendata.geoportal.gov.pl/bdot10k/schemat2021/GeoParquet/OT_BUBD_A.parquet
input_file = "input/OT_BUBD_A.parquet"
output_dir = Path("dane")
output_dir.mkdir(exist_ok=True)

attribute_column = "TERYT"

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

