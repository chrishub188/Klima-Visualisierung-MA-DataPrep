# Data Prep 

## Dependecies 
- Benötigt wird DuckdB: [Installlations Guide](https://duckdb.org/docs/installation/?version=stable&environment=cli&platform=macos&download_method=package_manager)

- Python Dependencies: ```pip install -r requirements.txt```

- Rohdaten müssen alle in /rawdata/Tagesgang/Full entpackt werden. 

## Skripte 

1. Skript Transformation der Rohdaten in CSV: ```python transform_to_csv.py```

2. Skript Transformation der Rohdaten in eine einzelne CSV-Datei: ```python merge_to_single_csv.py```

3. Generierung der Aggregierten Daten: ```duckdb``` starten anschließend Queries aus build_db.sql auf der DuckDB Konsole ausführen.

4. Skript Transformation der CSV Daten in EPSG:3857: ```python transform_csv_to_epsg3857.py```

5. Skript für die Generierung der Bilder mit GeoJSON filter für den Gesamten Umriss: ```python heatmap_generator_unified.py ./csvdata/multiple_files/epsg3857 ./heatmaps/epsg3857/unified/full ./geodata/epsg3857/Gemarkungsgrenzen.geojson --resolution 2560 --cmap RdBu_r --vmin 10 --vmax 36 --max_workers 4```

6. Skript für die Generierung der Bilder mit GeoJSON filter für einzelne Bezirke: ```python heatmap_generator_unified.py ./csvdata/multiple_files/epsg3857 ./heatmaps/epsg3857/unified/district ./geodata/epsg3857/statistische_bezirke_2020.geojson --resolution 2560 --cmap RdBu_r --vmin 10 --vmax 36 --max_workers 4```

7. Zum entfernen der Dateinamen-Prefix von den Rohdaten ```rename_images.py``` Format für Gesamtumriss: "2023_08_21_03uhr.png", Format für Bezirk: "2023_08_20_22uhr_59.png"

8. Skript für die Generierung der Bounding Box für den jeweiligen statistischen Bezirk: ```python calc_bounding_box_leaflet_bezirke.py ./geodata/epsg3857/statistische_bezirke_2020.geojson output_bounds.json```

