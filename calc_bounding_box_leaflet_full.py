import pandas as pd
import logging
from shapely.geometry import Point
import geopandas as gpd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def filter_points_with_geojson(df, geojson_path):
    try:
        # Load the GeoJSON file as a GeoDataFrame
        gdf = gpd.read_file(geojson_path)

        # Create a GeoDataFrame from the CSV data
        points = [Point(xy) for xy in zip(df['x'], df['y'])]
        df_geo = gpd.GeoDataFrame(df, geometry=points, crs=gdf.crs)

        # Ensure CRS matches
        if df_geo.crs != gdf.crs:
            df_geo = df_geo.to_crs(gdf.crs)

        # Perform spatial join to filter points that are within the GeoJSON boundaries
        filtered_df = df_geo[df_geo.within(gdf.unary_union)]

        # Drop geometry column and return the filtered DataFrame
        return pd.DataFrame(filtered_df.drop(columns='geometry'))
    except Exception as e:
        logging.error(f"Error filtering points with GeoJSON: {str(e)}")
        raise

def calculate_bounds_from_file(csv_file, geojson_path):
    try:
        df = pd.read_csv(csv_file)

        # Filter points using the GeoJSON file
        df_filtered = filter_points_with_geojson(df, geojson_path)

        if df_filtered.empty:
            logging.warning(f"No points remain after filtering with GeoJSON for file {csv_file}.")
            return None

        # Calculate bounds
        x_min, x_max = df_filtered['x'].min(), df_filtered['x'].max()
        y_min, y_max = df_filtered['y'].min(), df_filtered['y'].max()

        bounds = {
            "x_min": x_min,
            "x_max": x_max,
            "y_min": y_min,
            "y_max": y_max
        }

        logging.info(f"Bounds for {csv_file}: {bounds}")
        return bounds

    except Exception as e:
        logging.error(f"Error calculating bounds for {csv_file}: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    csv_file = "./csvdata/multiple_files/epsg25832/Tagesgang_TefmoNN_P1P2_rndm_E190-200_P0_Testdaten_2023_08_23_01uhr_N305.csv"  # Path to your CSV file
    geojson_path = "./geodata/epsg25832/Gemarkungsgrenzen.geojson"  # Path to your GeoJSON file

    bounds = calculate_bounds_from_file(csv_file, geojson_path)

    if bounds:
        print("Bounds:")
        print(f"x_min: {bounds['x_min']}, x_max: {bounds['x_max']}")
        print(f"y_min: {bounds['y_min']}, y_max: {bounds['y_max']}")
