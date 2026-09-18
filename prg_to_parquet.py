from pathlib import Path

import geopandas as gpd

# https://opendata.geoportal.gov.pl/prg/adresy/PRG-punkty_adresowe_shp.zip
prg_dir = Path(r"prg")
output_dir = Path(r"output")

msc = gpd.read_file(prg_dir / "PRG_Miejscowosci_POLSKA.shp")
msc.to_parquet(output_dir / "data/miejscowosci.parquet", index=False)

woj = gpd.read_file(prg_dir / "A01_Granice_wojewodztw.shp")
woj.to_parquet(output_dir / "wojewodztwa.parquet", index=False)

pow = gpd.read_file(prg_dir / "A02_Granice_powiatow.shp")
pow.to_parquet(output_dir / "powiaty.parquet", index=False)

gmi = gpd.read_file(prg_dir / "A03_Granice_gmin.shp")
gmi.to_parquet(output_dir / "gminy.parquet", index=False)

uli = gpd.read_file(prg_dir / "PRG_Ulice_POLSKA.shp")
uli.to_parquet(output_dir / "ulice.parquet", index=False)