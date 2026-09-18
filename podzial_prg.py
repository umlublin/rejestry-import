import geopandas as gpd
from pathlib import Path

# TODO pobierac z plikow powiatowych zamiast cala polske na raz
# https://opendata.geoportal.gov.pl/prg/adresy/PunktyAdresowe/02/0201.zip
input_shp = "input/PRG_PunktyAdresowe_POLSKA.shp"
output_dir = Path("dane")
output_dir.mkdir(exist_ok=True)

attribute_column = "TERYT_POW"
target_format = "parquet"

print("Wczytywanie pliku SHP...")
gdf = gpd.read_file(input_shp, encoding="utf-8")
gdf = gdf.drop(columns=["ID_IIP"])
gdf["TERYT_POW"] = gdf["TERYT_GMI"].astype(str).str.zfill(6).str[:4]

print(f"Dzielenie i zapisywanie danych wg atrybutu: {attribute_column}...")
for teryt, group in gdf.groupby(attribute_column):
    out_file = output_dir / f"{teryt}_pktadr.parquet"
    group.to_parquet(out_file, index=False)

print("Gotowe!")

