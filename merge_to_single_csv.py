import os
import pandas as pd

# Define paths
input_folder = './rawdata/Tagesgang/Full'
output_file = './csvdata/merged_data.csv'

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)

# Initialize CSV file
if os.path.exists(output_file):
    os.remove(output_file)

# Iterate over each file in the input folder
for filename in os.listdir(input_folder):
    # Only process files that match the pattern
    #Avoid .gitkeep file
    if filename.startswith('Tagesgang_TefmoNN_P1P2_rndm_E190-200_P0_Testdaten_') and filename.endswith('.txt'):
        # Extract the date and hour from the filename
        try:
            # Split based on underscores and parse the date and hour part
            parts = filename.split('_')
            date_string = f"{parts[7]}-{parts[8]}-{parts[9]}"  # YYYY-MM-DD
            hour_part = parts[10]  # "22uhr" in the example
            
            # Extract hour by removing 'uhr' and converting to an integer
            hour = int(hour_part.replace('uhr', ''))
            
            # Create a datetime string including the hour
            date_string_iso = pd.to_datetime(f"{date_string} {hour}:00:00", format="%Y-%m-%d %H:%M:%S").isoformat()
        except Exception as e:
            print(f"Skipping file {filename} due to parsing error: {e}")
            continue

        # Create full path for the file
        file_path = os.path.join(input_folder, filename)

        # Load data into a DataFrame (assuming tab-separated format)
        try:
            df = pd.read_csv(file_path, sep='\t', header=None, names=['x', 'y', 'temperatur', 'messung', 'genauigkeit', 'ntzg'])
        except Exception as e:
            print(f"Skipping file {filename} due to read error: {e}")
            continue
        
        # Add date column to the DataFrame
        df['date'] = date_string_iso

        # Append the dataframe to the output CSV
        # Write headers only for the first file
        write_header = not os.path.exists(output_file)
        
        try:
            df.to_csv(output_file, mode='a', index=False, header=write_header)
            print(f"Appended file: {filename} with date: {date_string_iso}")
        except Exception as e:
            print(f"Failed to write data for file {filename}: {e}")

print(f"Data merging completed. Output written to {output_file}")
