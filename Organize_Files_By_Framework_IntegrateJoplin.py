#!/usr/bin/env python3

"""
Organizing Frameworks Script

This script automates the classification of files into framework-specific directories and integrates with Joplin for tagging and documentation. It includes a rollback mechanism for safe file handling and supports a flexible, expandable framework structure.
"""

import os
import shutil
from datetime import datetime
from joplin_api import JoplinApi

# Read Joplin API token securely from environment variables
import dotenv
dotenv.load_dotenv()
JOPLIN_API_TOKEN = os.getenv("JOPLIN_API_TOKEN")
joplin = JoplinApi(token=JOPLIN_API_TOKEN)

# Base directories
BASE_DIR = "/home/dan/Business"
DEST_DIR = f"{BASE_DIR}/Compliance_Frameworks"
LOG_FILE = "classification_log.txt"
ROLLBACK_LOG = "rollback_log.txt"

# Framework-specific folders
FRAMEWORKS = {
    "FFIEC": ["ffiec", "federal financial institutions"],
    "NIST": ["nist", "cybersecurity framework"],
    "ISO": ["iso 27001", "international standards organization"],
    "FTC": ["ftc safeguard", "federal trade commission"],
    "GLBA": ["glba", "gramm-leach-bliley"],
    "CIS": ["cis controls", "center for internet security"]
}

# Helper function to create directories
def ensure_dir(directory):
    """
    Ensures a directory exists. If it does not, creates it.

    Args:
        directory (str): Path of the directory to ensure.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to log file movements
def log_action(action, src, dest):
    """
    Logs the file movement action and records rollback commands.

    Args:
        action (str): Action performed (e.g., COPY or MOVE).
        src (str): Source file path.
        dest (str): Destination file path.
    """
    with open(LOG_FILE, "a") as log:
        log.write(f"{datetime.now()} - {action}: {src} -> {dest}\n")

    with open(ROLLBACK_LOG, "a") as rollback:
        rollback.write(f"mv '{dest}' '{src}'\n")

# Function to classify files
def classify_file(file_path):
    """
    Classifies a file based on framework keywords and handles duplicates.

    Args:
        file_path (str): Full path to the file to classify.
    """
    file_name = os.path.basename(file_path)
    matched_frameworks = []

    # Check for framework matches
    for framework, keywords in FRAMEWORKS.items():
        if any(keyword.lower() in file_name.lower() for keyword in keywords):
            matched_frameworks.append(framework)

    if matched_frameworks:
        for framework in matched_frameworks:
            dest_folder = f"{DEST_DIR}/{framework}"
            ensure_dir(dest_folder)
            dest_path = os.path.join(dest_folder, file_name)

            # Copy the file to each relevant framework folder
            shutil.copy2(file_path, dest_path)

            # Assign Joplin tags for each framework
            assign_joplin_tags(file_path, [f"framework:{framework}"])
            log_action("COPY", file_path, dest_path)
    else:
        # If no match, leave file in place and tag as Unclassified
        assign_joplin_tags(file_path, ["status:Unclassified"])
        log_action("LEAVE", file_path, file_path)

# Function to assign Joplin tags
def assign_joplin_tags(file_path, tags):
    """
    Assigns tags to a Joplin note linked to the file.

    Args:
        file_path (str): Full path to the file being tagged.
        tags (list): List of tags to assign to the file.
    """
    title = os.path.basename(file_path)
    content = f"File: {file_path}\nLocated in: {os.path.dirname(file_path)}"
    note = joplin.create_note(title=title, body=content)

    for tag in tags:
        joplin.create_tag(tag)
        joplin.add_tag_to_note(tag, note["id"])

# Main processing loop
def process_files(base_dir):
    """
    Walks through the base directory to process and classify all files.

    Args:
        base_dir (str): The base directory containing files to classify.
    """
    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)
            classify_file(file_path)

# Rollback mechanism
def rollback():
    """
    Executes the rollback mechanism to undo file movements based on the rollback log.
    """
    with open(ROLLBACK_LOG, "r") as rollback:
        commands = rollback.readlines()

    for command in reversed(commands):
        os.system(command.strip())

    print("Rollback complete.")

# Run the script
if __name__ == "__main__":
    try:
        #production directory
        #process_files(BASE_DIR)
        #test directory
        process_files("/home/dan/Business/BanksArchive/SSB_ProjectMgmt")
        print("File classification complete.")
    except Exception as e:
        print(f"An error occurred: {e}")
