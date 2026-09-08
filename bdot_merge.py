import geopandas as gpd
from pathlib import Path

base_dir = Path(r"input")
teryt = "0663"

base_file = base_dir / f"{teryt}_2026_bud.parquet"
print(f"Wczytywanie pliku bazowego: {base_file.name}")
gdf_base = gpd.read_parquet(base_file)

gdf_base["area_base"] = gdf_base.geometry.area

for year in [2024]:
    year_file = base_dir / f"{teryt}_{year}_bud.parquet"
    if not year_file.exists():
        print(f"Pomiędzy: Brak pliku {year_file.name}")
        continue
    gdf_year = gpd.read_parquet(year_file)

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
    for index, row in found_by_id.iterrows():
        gdf_base.loc[index, "ZABYTEK"] = row['ZABYTEK']
        gdf_base.loc[index, "UTWORZONO"] = str(row['DATAUTW'])[:4]

    # found_by_id.to_parquet(f"dopasowane_id_{year}.parquet")
    missing_by_id = merged[merged['geometry_year'].isna()].copy()

    print(f"Dopasowane po LOKALNYID: {len(found_by_id)} / {len(gdf_base)}")
    print(f"Brak dopasowania po ID (szukanie przestrzenne): {len(missing_by_id)}")

    # KROK 2: Dopasowanie przestrzenne dla brakujących (>90% nałożenia)
    found_by_spatial = 0

    if len(missing_by_id) > 0:
        # Odrzucamy kolumnę geometry_year powstałą z merge
        missing_gdf = missing_by_id.drop(columns=['geometry_year'])

        candidates = gpd.sjoin(
            missing_gdf,
            gdf_year[['LOKALNYID', 'geometry', 'DATAUTW','KODKST', 'FUNOGBUD']],
            how='inner',
            predicate='intersects'
        )
        # candidates.to_parquet(f"dopasowane_{year}.parquet")
        for index, row in candidates.iterrows():
            geom_base = row.geometry
            # Pobieramy geometrię kandydata z pliku rocznego
            geom_year = gdf_year.loc[gdf_year['LOKALNYID'] == row['LOKALNYID_right'], 'geometry'].values[0]
            # Obliczenie pola części wspólnej
            intersection_area = geom_base.intersection(geom_year).area
            overlap_ratio = round(intersection_area / row['area_base'],2)
            if overlap_ratio > 0.95:
                print(f"{overlap_ratio}%: {intersection_area} {geom_year.area}")

                gdf_base.loc[index, "ZABYTEK"] = row['ZABYTEK']
                gdf_base.loc[index, "UTWORZONO"] = str(row['DATAUTW_right'])[:4]
                found_by_spatial = found_by_spatial + 1

    print(f"Dopasowane przestrzennie: {found_by_spatial}")

print("\nGotowe! Analiza zakończona.")
gdf_base.to_parquet(f"bdot_rzb.parquet")