import os
import pandas as pd
from pyproj import Transformer
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Define input and output folders
input_folder = './csvdata/multiple_files/epsg25832'
output_folder = './csvdata/multiple_files/epsg3857'

# Create transformer object to convert EPSG:25832 to EPSG:3857
transformer = Transformer.from_crs("epsg:25832", "epsg:3857", always_xy=True)

# Ensure output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Function to process a single CSV file without chunking
def transform_file(filename):
    input_file_path = os.path.join(input_folder, filename)
    output_file_path = os.path.join(output_folder, filename)

    # Start timing the transformation
    start_time = time.time()
    print(f"Starting transformation for {filename}...")

    # Read the entire CSV file at once
    df = pd.read_csv(input_file_path)

    # Transform the coordinates
    transformed_coords = transformer.transform(df['x'].values, df['y'].values)

    # Replace the x and y columns with the transformed coordinates
    df['x'], df['y'] = transformed_coords

    # Save the transformed data to a new CSV file in the output folder
    df.to_csv(output_file_path, index=False)

    # End timing the transformation
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Finished transformation for {filename} in {elapsed_time:.2f} seconds.")
    return filename, elapsed_time

# Main entry point for the script
if __name__ == '__main__':
    # Collect all CSV files
    csv_files = [f for f in os.listdir(input_folder) if f.endswith(".csv")]

    # Define the number of processes you want to run in parallel
    MAX_PROCESSES = min(10, len(csv_files))  # Use 10 processes (for 10 cores), or less if there are fewer files

    # Use ProcessPoolExecutor to transform files in parallel with a limited number of processes
    with ProcessPoolExecutor(max_workers=MAX_PROCESSES) as executor:
        futures = [executor.submit(transform_file, filename) for filename in csv_files]

        # As each file finishes, print its result
        for future in as_completed(futures):
            filename, elapsed_time = future.result()
            print(f"{filename} completed in {elapsed_time:.2f} seconds.")

    print("Coordinate transformation completed for all files.")
