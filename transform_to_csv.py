import os
import pandas as pd

# Define input and output folders
input_folder = './rawdata/Tagesgang/Full'
output_folder = './csvdata/multiple_files/epsg25832/'

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# Column headers
headers = ['x', 'y', 'temperatur', 'messung', 'genauigkeit', 'ntzg']

index = 0

# Loop through all files in the input folder
for filename in os.listdir(input_folder):
    if filename.endswith('.txt') and 'Testdaten' in filename:
        # Construct full input file path
        input_filepath = os.path.join(input_folder, filename)
        
        # Read the input data
        data = pd.read_csv(input_filepath, sep='\t', header=None)
        data.columns = headers
        
        # Construct output filename by replacing .txt with .csv
        output_filename = filename.replace('.txt', '.csv')
        output_filepath = os.path.join(output_folder, output_filename)
        
        # Save the data to the output CSV file
        data.to_csv(output_filepath, index=False)
        
        print(f"{index} Converted {filename} to {output_filename}")

        index += 1

print("All files converted successfully!")
