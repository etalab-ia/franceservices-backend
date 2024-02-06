import wget
import os
import shutil
import json
import requests


def download_directory(storage_path: str, config_path: str , force_download: bool = False):
    """
    A download public local and national directory to create whitelist file.

    Args:
        storage_path (str): path where to download the files. 
        config_path (str,): configuration path file.
        force_download (bool, optional): force download if files already exists. Default: False.
    """

    os.makedirs(storage_path, exist_ok=True)

    # Open whitelist_config
    file = open(config_path,"r")
    whitelist_config = json.load(file)
    file.close()

    for ressource, values in whitelist_config['data'].items():

        file_path = os.path.join(storage_path, values["file_name"])
        if os.path.exists(file_path):
            
            if force_download:
                print(f"info: {values['file_name']} already exists, deleting and downloading again.")
                os.remove(file_path)

            else:
                print(f"info:  {values['file_name']} already exists, skipping.")
                continue
        
        print(f"info: downloading {ressource} archive...")
        url = requests.head(values["url"], allow_redirects=True).url
        file_name = url.split("/")[-1]
        wget.download(values["url"], os.path.join(storage_path, file_name))
        
        files_in_directory = os.listdir(storage_path)

        print(f"\ninfo: unpacking {ressource} archive...")
        shutil.unpack_archive(os.path.join(storage_path, file_name), storage_path)

        files_in_directory = [x for x in os.listdir(storage_path) if x not in files_in_directory]

        print(f"info: deleting {ressource} archive...")
        os.remove((os.path.join(storage_path, file_name)))

        for file in os.listdir(storage_path):
            if file.endswith(".zip"):
                os.remove(os.path.join(f"{storage_path}", file))

            if file.endswith(".json") and file in files_in_directory:
                os.rename(os.path.join(f"{storage_path}", file), os.path.join(f"{storage_path}", f"{values['file_name']}"))