"""Clean output folders of dev models."""

import os


if __name__ == "__main__":
    # Get the current directory
    current_directory = os.getcwd()

    # List all folders in the current directory that start with "dev_"
    folders = [folder for folder in os.listdir(current_directory) if os.path.isdir(folder) and folder.startswith("dev_")]

    # Iterate through the "dev_" folders and remove content from the "output" folder
    for folder in folders:
        output_folder = os.path.join(folder, "output")

        # Check if the "output" folder exists in the "dev_" folder
        if os.path.exists(output_folder) and os.path.isdir(output_folder):
            # Remove all content from the "output" folder
            for item in os.listdir(output_folder):
                item_path = os.path.join(output_folder, item)
                os.remove(item_path)
            os.rmdir(output_folder)
            print(f"The 'output' folder and its content removed in '{folder}'.")
        else:
            print(f"There is no 'output' folder in '{folder}'.")
