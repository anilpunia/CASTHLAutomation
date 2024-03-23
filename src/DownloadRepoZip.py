####################################################################################################################    
#    # This script is used to download the repository as a ZIP file from GitHub, it use Excel file to get the URL  #
#    # and then download the repository as a ZIP file. This script takes following arguments: -excel_file, -batch, #
#    # -token, -log_dir.                                                                                           #
#    # https://docs.github.com/en/enterprise-cloud@latest/rest/repos/repos?apiVersion=2022-11-28#get-a-repository  #  
#    # Use the Metadata output to find the archive_url and then use archive_format as either zipball or tarball    #
#    # then do not put extension at the end .                                                                      #
#    # "archive_url": "https://api.github.com/repos/lmigtech/sd-bamboo-linked-repo-converter/{archive_format}{/ref}#
#    # Example: https://api.github.com/repos/cast/dislocationresearch/zipball/master                           #
####################################################################################################################

import os
import datetime
from argparse import ArgumentParser
import requests
import openpyxl

def read_excel_data(file_path):
    """
    Reads data from an Excel file.
    Parameters:
        file_path (str): The path to the Excel file.
    Returns:
        list: A list containing tuples of data extracted from the Excel file.
    """
    data = []
    try:
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            data.append((row[0], row[1], row[2], row[3]))  # Including GitHub URL directly
        workbook.close()
    except Exception as e:
        print(f"Error reading Excel file: {e}")
    return data

def create_directory_if_not_exists(directory_path):
    """
    Creates a directory if it doesn't already exist.
    Parameters:
        directory_path (str): The path to the directory.
    """
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            print(f"Directory '{directory_path}' created successfully.\n")
        except OSError as e:
            print(f"Error: {e}")
    else:
        print(f"Directory '{directory_path}' already exists.\n")

def log_start_end_time(repository_name, start_time, end_time, total_time, log_file):
    """
    Logs start and end time of a process.
    Parameters:
        repository_name (str): The name of the repository or process.
        start_time (datetime): The start time of the process.
        end_time (datetime): The end time of the process.
        total_time (timedelta): The total time taken for the process.
        log_file (str): The path to the log file.
    """
    log_message = f"{repository_name} | {start_time} | {end_time} | {total_time} |"
    with open(log_file, "a") as f:
        f.write(log_message + "\n")

def log_processing(repository_name, status, log_file):
    """
    Logs the processing status of a repository.
    Parameters:
        repository_name (str): The name of the repository.
        status (str): The processing status.
        log_file (str): The path to the log file.
    """    
    log_message = f"{repository_name} | {status}"
    with open(log_file, "a") as f:
        f.write(log_message + "\n")

def download_zip_archive(repository_url, repository_path, token):
    """
    Downloads a ZIP archive from a given URL.
    Parameters:
        repository_url (str): The URL of the repository.
        repository_path (str): The path to save the ZIP archive.
        token (str): The GitHub access token.
        
    Returns:
        bool: True if download is successful, False otherwise.
    """
    headers = {'Authorization': f'token {token}'}
    response = requests.get(repository_url, headers=headers)
    
    if response.status_code == 200:
        with open(repository_path, 'wb') as f:
            f.write(response.content)
        return True
    else:
        return False

def download_and_save_code(application_name, repository_url, server_location, token, start_end_log_file, processing_log_file):
    """
    Downloads and saves code from a repository.
    Parameters:
        application_name (str): The name of the application or repository.
        repository_url (str): The URL of the repository.
        server_location (str): The location to save the repository.
        token (str): The GitHub access token.
        start_end_log_file (str): The path to the log file for start and end times.
        processing_log_file (str): The path to the log file for processing status.
    """

    application_name_directory = os.path.join(server_location, application_name)
    create_directory_if_not_exists(application_name_directory)

    repository_zip_path = os.path.join(application_name_directory, application_name + '.zip')
    
    if os.path.exists(repository_zip_path):
        log_processing(application_name, "Skipped: ZIP file already exists", processing_log_file)
        print(f"Skipping repository '{application_name}'. ZIP file already exists.\n")
    else:
        start_time = datetime.datetime.now()
        try:
            if download_zip_archive(repository_url, repository_zip_path, token):
                end_time = datetime.datetime.now()
                total_time = end_time - start_time
                log_start_end_time(application_name, start_time, end_time, total_time, start_end_log_file)
                log_processing(application_name, "Successful", processing_log_file)
                print(f"Repository '{application_name}' downloaded successfully as ZIP file to '{repository_zip_path}'.\n")
            else:
                print(f"Failed to download repository '{application_name}'.")
        except Exception as e:
            end_time = datetime.datetime.now()
            total_time = end_time - start_time
            log_start_end_time(application_name, start_time, end_time, total_time, start_end_log_file)
            log_processing(application_name, f"Failed: {e}", processing_log_file)
            print(f"Error downloading repository: {e}")

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument('-excel_file', '--excel_file', required=True, help='Excel File Name')
    parser.add_argument('-batch', '--batch', required=True, help='Batch Number')
    parser.add_argument('-token', '--token', required=True, help='GitHub Access Token')
    parser.add_argument('-log_dir', '--log_dir', required=True, help='Log Directory')

    args = parser.parse_args()

    # Create log directory if it doesn't exist
    create_directory_if_not_exists(args.log_dir)

    start_end_log_file = os.path.join(args.log_dir, "TimetoClone.txt")
    processing_log_file = os.path.join(args.log_dir, "ExecutionLog.txt")

    # Clear log files if they already exist
    open(start_end_log_file, 'w').close()
    open(processing_log_file, 'w').close()

    data = read_excel_data(args.excel_file)

    for repository in data:
        if repository[2] == int(args.batch):
            download_and_save_code(repository[0], repository[1], repository[3], args.token, start_end_log_file, processing_log_file)
