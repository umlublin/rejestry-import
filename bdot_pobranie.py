import os
import zipfile
import tempfile
import requests
import geopandas as gpd
from pathlib import Path
from datetime import datetime
from fnmatch import fnmatch

INPUT_PATH = r"input"
DATA_PATH = r"data"
OUTPUT_PATH = r"output"

fields_rename = {"X_DATAUTW": "DATAUTW", "LKOND": "LICZ_KONDY"}
fields_delete = ["X_*", "*_NIL", "NAZWA", "SKROT_KART", "INFO_DODAT", "UWAGI", "PRZES_NAZW", "WERSJA", "POCZ_WERSJA",
                 "ZRO_DANYCH", "PNAZW", "KOD25K", "KOD50K", "KOD100K", "KOD250K", "KOD500K", "KOD1000K", "KOD1000_NI",
                 "POCZWERS", "KONIECWERS", "OZNA_ZMIAN", "GMLID", "WERSJAID", "POCZ_WERSJ"]


def download_and_convert_bdot(teryt_powiat: str, rok: int, output_dir: str = ".") -> Path:
    teryt_powiat = str(teryt_powiat).zfill(4)
    teryt_woj = teryt_powiat[:2]

    if rok == datetime.now().year:
        url = f"https://opendata.geoportal.gov.pl/bdot10k/schemat2021/SHP/{teryt_powiat[:2]}/{teryt_powiat}_SHP.zip"
    else:
        url = f"https://opendata.geoportal.gov.pl/Archiwum/bdot10k/{rok}/SHP/{teryt_woj}/{teryt_powiat}_SHP_{rok}.zip"
    output_path = Path(output_dir) / f"{teryt_powiat}_{rok}_bud.parquet"

    if output_path.exists():
        print(f"Znaleziono plik: {output_path}")
        return output_path

    print(f"Pobieranie danych z: {url}")
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise FileNotFoundError(f"Nie znaleziono pliku na serwerze (HTTP {response.status_code}). Sprawdź rok i TERYT.")

    # Tworzymy tymczasowy katalog na rozpakowany plik ZIP
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = Path(tmp_dir) / "data.zip"

        # Zapis pliku ZIP na dysk
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("Rozpakowywanie archiwum...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

        # Wyszukanie pliku OT_BUBD_A.shp (niezależnie od prefiksu PL.PZGiK...)
        shp_files = list(Path(tmp_dir).rglob("*OT_BUBD_A.shp"))
        if not shp_files:
            raise FileNotFoundError("W pobranym archiwum ZIP nie znaleziono pliku *OT_BUBD_A.shp")

        target_shp = shp_files[0]
        print(f"Znaleziono plik: {target_shp.name}")

        print("Wczytywanie i przetwarzanie ...")
        gdf = gpd.read_file(target_shp)

        cols_delete = [col for col in gdf.columns if any(fnmatch(col, pattern) for pattern in fields_delete)]
        print(f"usuwam kolumny: {cols_delete}")
        gdf = gdf.rename(columns=fields_rename).drop(columns=cols_delete, errors="ignore")

        print(f"Zapisywanie do: {output_path}")
        gdf.to_parquet(output_path, index=False)

    return output_path


def main():
    pow = gpd.read_parquet(f"{DATA_PATH}/powiaty.parquet")
    Path(OUTPUT_PATH).mkdir(parents=True, exist_ok=True)

    for index, row in pow.iterrows():
        teryt = row["JPT_KOD_JE"]
        try:
            download_and_convert_bdot(teryt_powiat=teryt, rok=2024, output_dir=OUTPUT_PATH)
            download_and_convert_bdot(teryt_powiat=teryt, rok=2026, output_dir=OUTPUT_PATH)
        except FileNotFoundError:
            print(f"brak plików {teryt}")


if __name__ == "__main__":
    main()
