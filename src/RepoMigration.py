import os
import pandas as pd
import shutil
import logging
import configparser
import sys
from datetime import datetime

def setup_logger(log_file):

    # Setup logger for migration process
    logger = logging.getLogger('migration_logger')
    logger.setLevel(logging.INFO)

    # Create file handler for migration log
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Create console handler for migration log
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatter for migration log
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def create_summary_logger(summary_log_file):
    # Setup logger for application summary
    summary_logger = logging.getLogger('summary_logger')
    summary_logger.setLevel(logging.INFO)

    # Create file handler for summary log
    summary_handler = logging.FileHandler(summary_log_file)
    summary_handler.setLevel(logging.INFO)

    # Create formatter for summary log
    summary_formatter = logging.Formatter('%(asctime)s - %(message)s')
    summary_handler.setFormatter(summary_formatter)

    # Add file handler to summary logger
    summary_logger.addHandler(summary_handler)

    return summary_logger

def clean_folder_name(name):
    # Replace characters that are not allowed in directory names
    forbidden_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|','(',')',',']
    for char in forbidden_chars:
        name = name.replace(char, '_')
    return name

def move_and_delete_folders(root_dir, logger):
    # Iterate over subdirectories recursively
    for subdir, dirs, files in os.walk(root_dir):
        for folder in dirs:
            if folder.startswith('lmigtech-'):
                source_dir = os.path.join(subdir, folder)
                destination_dir = os.path.dirname(source_dir)
                # Move contents of source directory to parent directory
                for item in os.listdir(source_dir):
                    item_path = os.path.join(source_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            shutil.move(item_path, destination_dir)
                        elif os.path.isdir(item_path):
                            shutil.move(item_path, os.path.join(destination_dir, item))
                    except Exception as e:
                        logger.error(f"Failed to move {item_path}: {e}")
                # Remove the now empty source directory
                try:
                    os.rmdir(source_dir)
                except Exception as e:
                    logger.error(f"Failed to remove directory {source_dir}: {e}")

def create_application_folders(mapping_sheet, repo_folder, output_folder, logger, summary_logger):
    # Read the mapping sheet
    mapping_df = pd.read_excel(mapping_sheet)
    
    # Loop through each row in the mapping sheet
    for index, row in mapping_df.iterrows():
        repo_name = row['Repo Name']
        app_name = row['Application']
        
        # Check if app_name is NaN
        if pd.isna(app_name):
            logger.warning(f"Skipping row {index + 1}: Application Name is missing.")
            continue

        # Convert app_name to string to handle NaN
        app_name = str(app_name).strip()

        # Clean up the application name for folder creation
        app_folder_name = clean_folder_name(app_name)
        
        # Create application folder if it doesn't exist
        app_folder_path = os.path.join(output_folder, app_folder_name)
        if not os.path.exists(app_folder_path):
            os.makedirs(app_folder_path)
            logger.info(f"Application folder '{app_name}' created.")
        else:
            logger.info(f"Application folder '{app_name}' already exists.")
        
        # Move entire directory from repo to application folder
        repo_folder_path = os.path.join(repo_folder, repo_name)
        if os.path.exists(repo_folder_path):
            shutil.move(repo_folder_path, app_folder_path)
            logger.info(f"Repository '{repo_name}' moved to application folder '{app_name}'.")
            summary_logger.info(f"{app_name};{repo_name};Passed")
           
            new_repo_folder = os.path.join(app_folder_path, repo_name)
            if os.path.exists(new_repo_folder):
                # Call the function to move and delete folders in the app folder
                move_and_delete_folders(new_repo_folder, logger)
            else:
                logger.warning(f"Repository '{repo_name}' was not moved to application '{app_name}'.")
                summary_logger.info(f"{app_name};{repo_name};Failed")
        else:
            logger.warning(f"Repository '{repo_name}' does not exist for application '{app_name}'.")
            summary_logger.info(f"{app_name};{repo_name};Failed")

if __name__ == "__main__":
    # Read configuration from config.properties
    config = configparser.ConfigParser()
    config_file = input("Enter the path of the configuration file: ")
    config.read(config_file)

    mapping_sheet_path = config['migration']['mapping_sheet']
    repo_folder_path = config['migration']['repo_folder']
    output_folder_path = config['migration']['output_folder']
    log_dir_path = config['migration']['log_dir']

    # Get current date and time
    current_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    # Setup logger
    log_file=os.path.join(log_dir_path, f"migration_log_{current_datetime}.log")
    logger = setup_logger(log_file)

    # Create summary log file in the same directory as the migration log
    summary_log_file = os.path.join(log_dir_path, f"summary_log_{current_datetime}.txt")
    summary_logger = create_summary_logger(summary_log_file)

    # Create application folders and move content
    create_application_folders(mapping_sheet_path, repo_folder_path, output_folder_path, logger, summary_logger)
    logger.info("Migration process completed.")
