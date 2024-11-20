import os
import json
import pandas as pd
import geopandas as gpd
import logging
from pyproj import Transformer
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_district_bounds(geojson_file, output_file):
    try:
        # Read the GeoJSON file with UTF-8 encoding
        gdf = gpd.read_file(geojson_file, encoding='utf-8')
        
        # Ensure the GeoDataFrame is in Web Mercator (EPSG:3857)
        if gdf.crs is None:
            logging.warning("No CRS found in GeoJSON, assuming EPSG:3857")
            gdf.set_crs(epsg=3857, inplace=True)
        elif gdf.crs.to_string() != 'EPSG:3857':
            gdf = gdf.to_crs(epsg=3857)

        # Create transformer from EPSG:3857 to EPSG:4326 (for Leaflet)
        transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
        
        # List to store results
        districts = []
        
        # Calculate bounds for each district
        for idx, district in gdf.iterrows():
            bounds = district.geometry.bounds  # Returns (minx, miny, maxx, maxy)
            
            # Transform bounds to lat/lng
            sw_lng, sw_lat = transformer.transform(bounds[0], bounds[1])
            ne_lng, ne_lat = transformer.transform(bounds[2], bounds[3])
            
            district_name = str(district['name'])
            district_gid = str(district['gid']) if 'gid' in district else None
            
            if district_gid is None:
                logging.warning(f"No GID found for district {district_name}")
            
            districts.append({
                'name': district_name,
                'gid': district_gid,
                'bbox': [[sw_lat, sw_lng], [ne_lat, ne_lng]],
                'centroid': [(sw_lat + ne_lat) / 2, (sw_lng + ne_lng) / 2]
            })
        
        # Save to JSON file with UTF-8 encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(districts, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Successfully saved bounds for {len(districts)} districts to {output_file}")
              
    except Exception as e:
        logging.error(f"Error processing districts: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate bounding boxes for districts")
    parser.add_argument("geojson_file", help="Path to GeoJSON file with district boundaries")
    parser.add_argument("output_file", help="Path to output JSON file")
    
    args = parser.parse_args()
    
    logging.info("Script started with the following arguments:")
    logging.info(f"GeoJSON file: {args.geojson_file}")
    logging.info(f"Output file: {args.output_file}")
    
    calculate_district_bounds(args.geojson_file, args.output_file)
    
    logging.info("Script execution completed")