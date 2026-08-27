import geopandas as gpd
import pandas as pd
from pathlib import Path

def normalize_geometry_column(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Zapewnia, że aktywna kolumna geometrii w GeoDataFrame nazywa się 'geometry'."""
    current_geom_name = gdf.geometry.name  # Pobiera aktualną nazwę kolumny przestrzennej
    if current_geom_name != 'geometry':
        gdf = gdf.rename_geometry('geometry')
    return gdf.to_crs(epsg=2180)

# Ustawienia
base_dir = Path(r".\bdot-budynki_powiaty")  # Zmień na swój katalog
teryt = "0663"
# teryt = "0201"
years = range(2015, 2025)  # 2015-2024
years = range(2024, 2025)  # 2015-2024

# 1. Wczytanie pliku bazowego
base_file = base_dir / f"{teryt}_bud.parquet"
print(f"Wczytywanie pliku bazowego: {base_file.name}")
gdf_base = normalize_geometry_column(gpd.read_parquet(base_file))

# Obliczamy powierzchnię obiektów bazowych (wymagane do warunku >90%)
gdf_base["area_base"] = gdf_base.geometry.area

# Słownik na wyniki dla każdego roku
results_by_year = {}

for year in years:
    year_file = base_dir / f"{teryt}_{year}_bud.parquet"
    if not year_file.exists():
        print(f"Pomiędzy: Brak pliku {year_file.name}")
        continue

    print(f"\n--- Przetwarzanie roku: {year} ---")
    gdf_year = normalize_geometry_column(gpd.read_parquet(year_file))

    # print(f"bazowy: {gdf_base.geometry.name}")
    # print(f"{year}: {gdf_year.geometry.name}")
    # KROK 1: Dopasowanie po LOKALNYID
    # Łączymy po LOKALNYID
    merged = gdf_base.merge(
        gdf_year,
        # gdf_year[['LOKALNYID', 'geometry']],
        on='LOKALNYID',
        how='left',
        suffixes=('', '_year'),
        indicator=True
    )
    # print(merged.columns)
    # Rozdzielamy na znalezione po ID i nieznalezione
    found_by_id = merged[merged['geometry_year'].notna()].copy()
    missing_by_id = merged[merged['geometry_year'].isna()].copy()

    print(f"Dopasowane po LOKALNYID: {len(found_by_id)} / {len(gdf_base)}")
    print(f"Brak dopasowania po ID (szukanie przestrzenne): {len(missing_by_id)}")

    # KROK 2: Dopasowanie przestrzenne dla brakujących (>90% nałożenia)
    found_by_spatial = []

    if len(missing_by_id) > 0:
        # Odrzucamy kolumnę geometry_year powstałą z merge
        missing_gdf = missing_by_id.drop(columns=['geometry_year'])

        # Spatial Join (s-join) na podstawie nachodzenia obiektów (intersects)
        # sjoin_neighbor zawiera dopasowania przestrzenne z pliku rocznego
        candidates = gpd.sjoin(
            missing_gdf,
            gdf_year[['LOKALNYID', 'geometry']],
            how='inner',
            predicate='intersects'
        )

        # Obliczamy pole powierzchni części wspólnej (intersection)
        for idx, row in candidates.iterrows():
            geom_base = row.geometry
            # Pobieramy geometrię kandydata z pliku rocznego
            # print(row)
            geom_year = gdf_year.loc[gdf_year['LOKALNYID'] == row['LOKALNYID_right'], 'geometry'].values[0]

            # Obliczenie pola części wspólnej
            intersection_area = geom_base.intersection(geom_year).area
            overlap_ratio = intersection_area / row['area_base']
            if overlap_ratio > 0.90:
                print(f"{overlap_ratio}%: {row}")
                found_by_spatial.append({
                    'LOKALNYID_base': row['LOKALNYID_left'],
                    'LOKALNYID_found': row['LOKALNYID_right'],
                    'overlap_ratio': overlap_ratio
                })

    df_spatial = pd.DataFrame(found_by_spatial)
    print(f"Dopasowane przestrzennie (>90%): {len(df_spatial)}")

    # Zapis wyniku dla danego roku
    results_by_year[year] = {
        'matched_id': found_by_id[['LOKALNYID']],
        'matched_spatial': df_spatial
    }

print("\nGotowe! Analiza zakończona.")