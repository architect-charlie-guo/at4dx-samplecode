"""
This script recursively scans a Salesforce source directory and compiles a Markdown table.
It includes all files found—even if they don't match any known Salesforce metadata type—by leaving the type field empty.

How it works:
- Recursively scans all files in the specified directory (including subdirectories).
- Uses an extended SALESFORCE_METADATA_TYPES mapping to classify files by their extension.
- For files that match a known extension, it removes the extension from the filename for clarity.
- For files that do not match any known extension, the type is set to an empty string.
- Uses Git (if available) to determine if a file is "Created", "Changed", or "Unmodified".
- Compiles the collected information into a Markdown table with columns: State, Name, Type, and Path.
- Prints usage instructions if no directory argument is provided.
"""

import os
import re
import sys
import subprocess

# Extended mapping of file extensions to Salesforce metadata types.
# This dictionary maps common Salesforce file extensions to their corresponding metadata types.
SALESFORCE_METADATA_TYPES = {
    # Apex & Visualforce
    ".cls": "ApexClass",
    ".cls-meta.xml": "ApexClass",
    ".trigger": "ApexTrigger",
    ".trigger-meta.xml": "ApexTrigger",
    ".component": "ApexComponent",
    ".component-meta.xml": "ApexComponent",
    ".page": "VisualforcePage",
    ".page-meta.xml": "VisualforcePage",

    # Aura Components
    ".cmp": "AuraComponent",
    ".cmp-meta.xml": "AuraComponent",
    ".evt": "AuraEvent",
    ".evt-meta.xml": "AuraEvent",
    ".app": "AuraApplication",
    ".app-meta.xml": "AuraApplication",
    ".design": "AuraDesign",
    ".design-meta.xml": "AuraDesign",

    # Lightning Web Components (LWC)
    # The -meta.xml file is used to identify Lightning Web Components.
    ".js-meta.xml": "LightningWebComponent",

    # Objects and Fields
    ".object-meta.xml": "CustomObject",
    ".field-meta.xml": "CustomField",

    # Other Metadata Types
    ".tab-meta.xml": "CustomTab",
    ".layout-meta.xml": "Layout",
    ".listView-meta.xml": "ListView",
    ".webLink-meta.xml": "WebLink",
    ".fieldSet-meta.xml": "FieldSet",
    ".profile-meta.xml": "Profile",
    ".permissionset-meta.xml": "PermissionSet",
    ".resource-meta.xml": "StaticResource",
    ".flow-meta.xml": "Flow",
    ".flowDefinition-meta.xml": "FlowDefinition",
    ".email-meta.xml": "EmailTemplate",
    ".report-meta.xml": "Report",
    ".dashboard-meta.xml": "Dashboard",
    ".customSite-meta.xml": "CustomSite",
    ".assignmentRules-meta.xml": "AssignmentRules",
    ".escalationRules-meta.xml": "EscalationRules",
    ".remoteSite-meta.xml": "RemoteSiteSetting",
    ".certificate-meta.xml": "Certificate",
    ".labels-meta.xml": "CustomLabels",
    ".recordType-meta.xml": "RecordType",
    ".compactLayout-meta.xml": "CompactLayout",
    ".connectedApp-meta.xml": "ConnectedApp",
    ".translation-meta.xml": "Translations",
    ".site-meta.xml": "SiteDotCom",
    ".networkBranding-meta.xml": "NetworkBranding",
    ".territory2Rule-meta.xml": "Territory2Rule",
    ".territory2Type-meta.xml": "Territory2Type",
    ".customPermission-meta.xml": "CustomPermission",
    ".quickAction-meta.xml": "QuickAction",
}

def detect_file_state(file_path, base_dir):
    """
    Determines whether the file is newly created, modified, or unchanged using Git.
    
    How it works:
    - Calls 'git status --porcelain' on the file (using its relative path).
    - If the status code starts with "A", returns "Created".
    - If the status code starts with "M", returns "Changed".
    - Otherwise, defaults to "Unmodified".
    - If Git is not available or an error occurs, it returns "Unmodified".
    """
    try:
        rel_path = os.path.relpath(file_path, base_dir)
        git_status = subprocess.run(["git", "status", "--porcelain", rel_path],
                                    capture_output=True, text=True)
        status_code = git_status.stdout.strip()[:2]  # Extract status code (e.g., "A ", "M ")

        if status_code.startswith("A"):
            return "Created"
        elif status_code.startswith("M"):
            return "Changed"
    except Exception:
        pass  # If Git isn't available or an error occurs, assume "Unmodified"

    return "Unmodified"

def categorize_files(base_dir):
    """
    Recursively scans the directory and categorizes files.
    
    How it works:
    - Uses os.walk to traverse all subdirectories.
    - For each file, checks if its name ends with any known Salesforce metadata extension.
    - If a match is found, assigns the corresponding type and removes the extension from the name.
    - If no match is found, includes the file with an empty type.
    - Determines the file state using the detect_file_state function.
    - Collects a tuple (state, name, type, relative path) for each file.
    """
    file_data = []

    for root, _, files in os.walk(base_dir):
        for file in files:
            file_path = os.path.join(root, file)

            metadata_type = ""
            stripped_name = file  # Default: use the full filename
            matched_ext = None

            for ext, sf_type in SALESFORCE_METADATA_TYPES.items():
                if file.endswith(ext):
                    metadata_type = sf_type
                    matched_ext = ext
                    break
            
            # If a known extension is found, remove it from the file name for clarity.
            if matched_ext:
                stripped_name = file[:-len(matched_ext)]
            
            state = detect_file_state(file_path, base_dir)
            relative_path = os.path.relpath(file_path, base_dir)
            file_data.append((state, stripped_name, metadata_type, relative_path))

    return file_data

def generate_markdown_table(file_data):
    """
    Generates a Markdown table from the file data.
    
    How it works:
    - Creates the header row and a separator row.
    - Iterates over each file entry and creates a table row with columns: State, Name, Type, and Path.
    - Joins all rows into a single string representing the Markdown table.
    """
    markdown_table = []
    markdown_table.append("| State       | Name         | Type        | Path                     |")
    markdown_table.append("|-------------|--------------|-------------|--------------------------|")

    for row in file_data:
        markdown_table.append(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |")

    return "\n".join(markdown_table)

def print_usage():
    """
    Prints the usage instructions for the script.
    
    How it works:
    - Informs the user how to run the script with the required directory argument.
    """
    print("Usage: python generate-component-table.py <directory>")
    print("Scans a Salesforce source directory and generates a Markdown table.")

def main():
    """
    Main entry point for the script.
    
    How it works:
    - Checks command-line arguments for a directory.
    - If no valid directory is provided, prints usage instructions and exits.
    - Otherwise, calls categorize_files to gather file data, generates the Markdown table, and prints it.
    """
    if len(sys.argv) != 2:
        print_usage()
        sys.exit(1)

    base_dir = sys.argv[1]

    if not os.path.isdir(base_dir):
        print(f"Error: Directory '{base_dir}' not found.")
        sys.exit(1)

    file_data = categorize_files(base_dir)
    markdown_table = generate_markdown_table(file_data)

    print(markdown_table)

if __name__ == "__main__":
    main()
