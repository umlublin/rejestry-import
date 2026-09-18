def move_columns(gdf, columns, after):
    """
    Przenosi wskazane kolumny za kolumnę `after`.

    Przykład:
        gdf = move_columns(gdf, ["kol1", "kol2"], after="ID")
    """

    # Sprawdzenie, czy kolumna `after` istnieje
    if after not in gdf.columns:
        raise ValueError(f"Kolumna '{after}' nie istnieje.")

    # Sprawdzenie, czy przenoszone kolumny istnieją
    missing = [col for col in columns if col not in gdf.columns]
    if missing:
        raise ValueError(f"Nie znaleziono kolumn: {missing}")

    # Usuwamy przenoszone kolumny z obecnej kolejności
    cols = [col for col in gdf.columns if col not in columns]

    # Pozycja, za którą mają zostać wstawione
    idx = cols.index(after) + 1

    # Nowa kolejność
    cols = cols[:idx] + columns + cols[idx:]

    return gdf[cols]