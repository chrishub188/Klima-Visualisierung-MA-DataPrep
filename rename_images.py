import os

# Set the path to the folder containing the files to rename
#folder_path = './heatmaps/bezirke/epsg3857/temperature/dpi100'
folder_path = './heatmaps/epsg3857/temperature'

# Set the filename part to remove
part_to_remove = 'Tagesgang_TefmoNN_P1P2_rndm_E190-200_P0_'

# Loop through all files in the folder
for filename in os.listdir(folder_path):
    # Check if the file has the part to remove
    if part_to_remove in filename:
        # Remove the part from the filename
        new_filename = filename.replace(part_to_remove, '')
        
        # Get the full path of the original file
        original_file_path = os.path.join(folder_path, filename)
        
        # Get the full path of the new file
        new_file_path = os.path.join(folder_path, new_filename)
        
        # Rename the file
        os.rename(original_file_path, new_file_path)

print('Files renamed successfully!')