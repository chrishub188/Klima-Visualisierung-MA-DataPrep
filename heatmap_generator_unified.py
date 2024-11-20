import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import logging
from tqdm import tqdm
from matplotlib.colors import ListedColormap
import geopandas as gpd
from shapely.geometry import Point
from rasterio import features
from affine import Affine
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_custom_colormap(cmap_name):
    base_cmap = plt.get_cmap(cmap_name)
    colors = base_cmap(np.linspace(0, 1, 256))
    colors = np.vstack(([0, 0, 0, 1], colors))  # Add black color at the beginning!!
    return ListedColormap(colors)

def create_raster_mask(geometry, width, height, bounds):
    """Create a raster mask for a geometry."""
    x_min, y_min, x_max, y_max = bounds
    transform = Affine.translation(x_min, y_min) * Affine.scale(
        (x_max - x_min) / width, 
        (y_max - y_min) / height
    )
    
    mask = features.rasterize(
        [(geometry, 1)],
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8
    )
    return mask.astype(bool)

def create_heatmap(df, output_png, geometry, area_name, resolution=5120, cmap='RdBu_r', vmin=10, vmax=36):
    try:
        # Filter points within geometry first
        points = gpd.GeoDataFrame(
            geometry=[Point(x, y) for x, y in zip(df['x'], df['y'])],
            data={'temp': df['temperatur'], 'ntzg': df['ntzg']}
        )
        points_within = points[points.geometry.within(geometry)]
        
        if len(points_within) == 0:
            logging.warning(f"No points found within geometry for {area_name}")
            return
        
        x_coords = points_within.geometry.x.values
        y_coords = points_within.geometry.y.values
        temps = points_within['temp'].values
        ntzg = points_within['ntzg'].values
        
        # Calculate bounds based on geometry
        bounds = geometry.bounds
        x_min, y_min, x_max, y_max = bounds
        
        # Calculate grid dimensions with higher resolution
        data_aspect_ratio = (y_max - y_min) / (x_max - x_min)
        
        # Calculate dimensions while maintaining aspect ratio
        if data_aspect_ratio > 9/16:
            height = resolution
            width = int(height / data_aspect_ratio)
        else:
            width = resolution
            height = int(width * data_aspect_ratio)
            
        logging.info(f"Creating grid with dimensions: {width}x{height} pixels")
        
        # Create higher resolution grid
        x_grid, y_grid = np.meshgrid(
            np.linspace(x_min, x_max, width),
            np.linspace(y_min, y_max, height)
        )
        
        # Create geometry mask first
        geometry_mask = create_raster_mask(geometry, width, height, bounds)
        
        # Create building mask using nearest neighbor interpolation
        building_mask = np.isin(ntzg, [20, 21, 30, 32])
        building_grid = griddata(
            (x_coords, y_coords),
            building_mask,
            (x_grid, y_grid),
            method='nearest',
            fill_value=False
        )
        
        # Ensure building grid is boolean
        building_grid = building_grid > 0.5
        
        # Interpolate temperatures only for non-building points
        non_building_mask = ~building_mask
        temp_grid = griddata(
            (x_coords[non_building_mask], y_coords[non_building_mask]),
            temps[non_building_mask],
            (x_grid, y_grid),
            method='linear',
            fill_value=np.nan
        )
        
        # Apply masks in correct order
        temp_grid[~geometry_mask] = np.nan  # Outside geometry
        temp_grid[building_grid & geometry_mask] = vmin - 1  # Buildings within geometry
        
        # Set up figure with higher DPI
        dpi = 100  # Increased DPI
        
        # Calculate figure size to maintain pixel dimensions
        fig_width = width / dpi
        fig_height = height / dpi
        
        plt.figure(figsize=(fig_width, fig_height), dpi=dpi)
        custom_cmap = create_custom_colormap(cmap)
        
        # Plot with specific settings to avoid border artifacts
        im = plt.imshow(
            temp_grid,
            extent=(x_min, x_max, y_min, y_max),
            origin='lower',
            cmap=custom_cmap,
            vmin=vmin - 1,
            vmax=vmax,
            interpolation='none'  # Keep 'none' to prevent interpolation artifacts
        )
        
        # Handle transparency and colors
        im.cmap.set_bad(color=(0, 0, 0, 0))  # Transparent for NaN values
        custom_cmap.set_under('black')  # Black for buildings
        
        plt.axis('off')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        
        # Save with high quality settings
        plt.savefig(output_png, 
                   dpi=dpi, 
                   bbox_inches='tight', 
                   pad_inches=0, 
                   transparent=True,
                   format='png',
                   metadata={'Software': 'Python matplotlib'})
        plt.close()
        
        logging.info(f"Successfully created high-resolution heatmap for {area_name}")
        
        # Log the output image dimensions
        from PIL import Image
        with Image.open(output_png) as img:
            logging.info(f"Output image dimensions: {img.size}")
            
    except Exception as e:
        logging.error(f"Error in create_heatmap for {area_name}: {str(e)}")
        raise

def process_file_and_district(args):
    """Process a single CSV file for a single district."""
    filename, district_info, input_folder, output_folder, resolution, cmap, vmin, vmax = args
    
    try:
        # Read the CSV file
        input_file = os.path.join(input_folder, filename)
        df = pd.read_csv(input_file)
        
        # Extract district information
        district_gid = district_info['gid']
        district_geometry = district_info['geometry']
        
        # Create output filename using CSV name and district GID
        # Check name!! 
        csv_base = os.path.splitext(filename)[0]
        output_png = os.path.join(output_folder, f"{csv_base}_district{district_gid}.png")
        
        # Create heatmap
        create_heatmap(df, output_png, district_geometry, f"{csv_base}_district{district_gid}", 
                      resolution, cmap, vmin, vmax)
        
        logging.info(f"Successfully processed {filename} for district {district_gid}")
        return True
    except Exception as e:
        logging.error(f"Error processing {filename} for district {district_gid}: {str(e)}")
        return False

def process_all_files(input_folder, output_folder, geojson_path, resolution, cmap, vmin, vmax, max_workers=8):
    logging.info(f"Starting to process files from {input_folder}")
    logging.info(f"Output will be saved to {output_folder}")

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        logging.info(f"Created output folder: {output_folder}")

    # Read all CSV files
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    logging.info(f"Found {len(csv_files)} CSV files")

    if not csv_files:
        logging.warning("No CSV files found in the input folder!")
        return

    # Read GeoJSON file and prepare district information
    gdf = gpd.read_file(geojson_path)
    districts = [{'gid': row['gid'], 'geometry': row['geometry']} 
                for _, row in gdf.iterrows()]
    logging.info(f"Found {len(districts)} districts in GeoJSON")

    # Create all combinations of CSV files and districts
    combinations = list(product(csv_files, districts))
    logging.info(f"Total number of combinations to process: {len(combinations)}")

    # Prepare arguments for parallel processing
    process_args = [
        (filename, district, input_folder, output_folder, resolution, cmap, vmin, vmax)
        for filename, district in combinations
    ]

    # Process files in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_file_and_district, args) for args in process_args]

        # Track progress with tqdm
        successful = 0
        failed = 0
        for future in tqdm(as_completed(futures), total=len(futures), 
                         desc="Processing file-district combinations"):
            try:
                if future.result():
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                logging.error(f"Error in future: {str(e)}")
                failed += 1

    logging.info(f"Processing completed. Successful: {successful}, Failed: {failed}")

#Logging
if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Generate heatmaps from CSV data with GeoJSON filters")
    parser.add_argument("input_folder", help="Path to folder containing input CSV files")
    parser.add_argument("output_folder", help="Path to folder for output files")
    parser.add_argument("geojson_path", help="Path to GeoJSON file containing district geometries")
    parser.add_argument("--resolution", type=int, default=5120, help="Resolution of the output image")
    parser.add_argument("--cmap", default="RdBu_r", help="Colormap for the heatmap")
    parser.add_argument("--vmin", type=float, default=10, help="Minimum temperature for color scaling")
    parser.add_argument("--vmax", type=float, default=36, help="Maximum temperature for color scaling")
    parser.add_argument("--max_workers", type=int, default=4, help="Number of parallel workers")

    args = parser.parse_args()
    
    logging.info("Script started with the following arguments:")
    logging.info(f"Input folder: {args.input_folder}")
    logging.info(f"Output folder: {args.output_folder}")
    logging.info(f"GeoJSON path: {args.geojson_path}")
    logging.info(f"Resolution: {args.resolution}")
    logging.info(f"Colormap: {args.cmap}")
    logging.info(f"vmin: {args.vmin}")
    logging.info(f"vmax: {args.vmax}")
    logging.info(f"max_workers: {args.max_workers}")

    process_all_files(args.input_folder, args.output_folder, args.geojson_path, 
                     args.resolution, args.cmap, args.vmin, args.vmax, args.max_workers)

    logging.info("Script execution completed")