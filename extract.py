import os
import json, xmltodict

def download_files():
    # Change this list to the years that you want to retrieve data from
    year_list = [2023]

    ftp = ftp_connection(url='ted.europa.eu', user='guest', passwd='guest')
    ftp.cwd('daily-packages')
    years = ftp.nlst()

    try:
        for year in years:
            if int(year) in year_list:
                ftp.cwd(year)
                months = ftp.nlst()

                for month in months:
                    ftp.cwd(month)
                    files = ftp.nlst()

                    save_directory = os.path.join(str(year), str(month))
                    os.makedirs(save_directory, exist_ok=True)

                    for filename in files:
                        file_path = os.path.join(save_directory, filename)
                        file_full_path = os.path.join(os.getcwd(), file_path)
                        # Save the file
                        with open(file_full_path, 'wb') as file:
                            ftp.retrbinary('RETR ' + filename, file.write)
                        # Extract the folders
                        if filename.endswith('.tar.gz'):
                            extract_tar_gz(file_full_path, save_directory)
                            os.remove(file_full_path)

                    # Convert XML to JSON format
                    # Might not be needed for some usecases
                    process_extracted_files(save_directory)

                    ftp.cwd("..")
                ftp.cwd("..")
            else:
                pass
        ftp.cwd("..")
        ftp.quit()

    except Exception as e:
        ftp.quit()
        print(e)

def process_extracted_files(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.xml'):
                xml_file_path = os.path.join(root, filename)
                json_file_path = os.path.join(root, os.path.splitext(filename)[0] + '.json')
                convert_xml_to_json(xml_file_path, json_file_path)
                os.remove(xml_file_path)  # Remove the XML file

                # Load the JSON data
                with open(json_file_path, 'r') as json_file:
                    json_data = json.load(json_file)

                def remove_translation_section(data):
                    if isinstance(data, dict):
                        if 'TRANSLATION_SECTION' in data:
                            del data['TRANSLATION_SECTION']
                        for key, value in data.items():
                            if isinstance(value, (dict, list)):
                                remove_translation_section(value)
                    elif isinstance(data, list):
                        for item in data:
                            remove_translation_section(item)

                remove_translation_section(json_data)

                # Write the modified JSON data back to the file
                with open(json_file_path, 'w') as json_file:
                    json.dump(json_data, json_file, indent=4)

# Convert the retrieved .xml file to .json
def convert_xml_to_json(xml_file_path, json_file_path):
    with open(xml_file_path, 'r', encoding='utf-8') as xml_file:
        xml_string = xml_file.read()

    # Parse the XML string.
    parsed_xml = xmltodict.parse(xml_string)

    # Convert the parsed XML to a JSON string.
    json_data = json.dumps(parsed_xml, indent=4)

    # Write the JSON data to a file.
    with open(json_file_path, 'w') as json_file:
        json_file.write(json_data)

# Extract the tar file in destination folder
def extract_tar_gz(file_path, destination):
    import tarfile
    with tarfile.open(file_path, 'r:gz') as tar:
        tar.extractall(destination)

# Connect to the TED FTP server
def ftp_connection(url, user, passwd):
    from ftplib import FTP
    ftp = FTP(url)
    ftp.login(user=user, passwd=passwd)
    return ftp

download_files()