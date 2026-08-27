import os
import zipfile
import tempfile
import requests
import geopandas as gpd
from pathlib import Path


def download_and_convert_bdot(teryt_powiat: str, rok: int, output_dir: str = ".") -> Path:
    teryt_powiat = str(teryt_powiat).zfill(4)
    teryt_woj = teryt_powiat[:2]

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

        print("Wczytywanie i przetwarzanie GeoPandas...")
        gdf = gpd.read_file(target_shp)

        # Usunięcie zbędnego pola ID_IIP
        # if "ID_IIP" in gdf.columns:
        #     gdf = gdf.drop(columns=["ID_IIP"])

        # Zapis do Parqueta (bez indeksu Pandas)
        print(f"Zapisywanie do: {output_path}")
        gdf.to_parquet(output_path, index=False)

    return output_path


# --- PRZYKŁAD UŻYCIA ---
if __name__ == "__main__":
    # Przykład: powiat oswiecimski (1213) lub lubelski (0609), rok 2023 / 2024
    POWIAT = "0663"  # 4-znakowy TERYT powiatu
    # ROK = 2023
    KATALOG_WYJSCIOWY = r"C:\ProjektyNCBR\podzialShape\bdotarch-budynki_powiaty"

    Path(KATALOG_WYJSCIOWY).mkdir(parents=True, exist_ok=True)
    for rok in range(2014,2025):
        try:
            download_and_convert_bdot(teryt_powiat=POWIAT, rok=rok, output_dir=KATALOG_WYJSCIOWY)
        except FileNotFoundError:
            print(f"brak {rok} {POWIAT}")