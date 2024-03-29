import json
import re
from urllib.parse import urlparse

from pyalbert import Logging


def create_whitelist(storage_dir: str, config_file: str, debug: bool = False):
    """Creating a .json whitelist file which contains:
    - All phone numbers
    - All mail
    - All domain URL
    Extracted from local and national directory.

    Args:
        storage_dir (str): path where to download the files.
        config_file (str): configuration path file.
        debug (bool, optional): print debug logs. Defaults to False.
    """

    logging = Logging(level="DEBUG" if debug else "INFO")
    logger = logging.get_logger()

    logger.info("creating whitelist file ...")
    whitelist = dict()
    phone_list = []
    mail_list = []
    domain_list = []

    # Open whitelist_config
    file = open(config_file, "r")
    whitelist_config = json.load(file)
    file.close()

    ### Loading directories
    directory = []
    for ressource, values in whitelist_config["directories"].items():
        filename = values["output"]

        if directory:
            with open(f"{storage_dir}/{filename}", encoding="utf-8") as json_file:
                directory.extend(json.load(json_file)["service"])
        else:
            with open(f"{storage_dir}/{filename}", encoding="utf-8") as json_file:
                directory = json.load(json_file)["service"]

    ### Creating domain URL whitelist
    url_pattern = r"((?:http[s]?://|w{3}\.)(?:\w|[$-_@.&+#]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+(?<![\.,])|(?<!\S)[\w\-\.]+\.[a-z]{2,3}\S*)"
    for k, contact in enumerate(directory):  # Picking from directory, contact is a dict
        try:
            url = re.findall(pattern=url_pattern, string=contact["site_internet"][0]["valeur"])[0]
            if url.startswith("www."):
                url = "https://" + url
            parsed_url = urlparse(url)
            domain = (
                parsed_url.scheme + "://" + parsed_url.netloc
            )  # scheme is the url protocole (http or https)
            if domain == "://":
                pass
            elif domain not in domain_list:
                domain_list.append(domain)
        except KeyError:
            continue
        except IndexError:
            continue
        except Exception as e:
            print(e)

    list_url = whitelist_config[
        "missing_urls"
    ]  # List of all important urls that are not in public directories and have to be added in the whitelist
    for url in list_url:
        if url not in domain_list:
            domain_list.append(url)

    ### Creating phone numbers whitelist
    number_pattern = [
        r"(?:\+\d{,3}|0)?\s*\([\d\s]*\)(?:[\s\.\-]*\d{2,}){2,}",
        r"(?<!\d)(?:\+\d{,3}|0)[\s\.\-]*\d(?:[\s\.\-]*\d{2,3}){4,}(?<![\.,])",
        r"(?<!\+)(?<!\-)(?<!\d)(?<!\d\s)(?<!\d\)\s)\d{2}[\s\-\.]*\d{2}(?!\s\d)(?!\d\s)(?!\-\d)(?!\d)",
        r"(?<!\d)0\s*(?:[\s\.\-]*\d{3}){3}(?<![\.,])",
        r"(?<!\d)0\d\s*\d{2}(?:[\s\.\-]*\d{3}){2}(?<![\.,])",
    ]

    # Regex used to replace all caracters in this patern => we will then have all whitelist's numbers in the same format
    replace_pattern = r"([\-\.\s])"

    for k, contact in enumerate(directory):  # Picking from directory, contact is a dict
        try:
            for pat in number_pattern:
                matches = re.findall(pat, contact["telephone"][0]["valeur"])
                for match in matches:
                    match = re.sub(
                        replace_pattern, "", match
                    )  # Replacing all characters from the pattern by ""
                    if match not in phone_list:
                        phone_list.append(match)
        except ValueError:
            continue
        except IndexError:
            continue
        except Exception as e:
            print(e)

    ### Creating mail whitelist
    mail_pattern = r"(?:[\w\+\-\.]+@[\w-]+\.[\w\-\.]+)(?<![\.,])"

    for k, contact in enumerate(directory):  # Picking from directory, contact is a dict
        try:
            matches = re.findall(mail_pattern, contact["adresse_courriel"][0])
            for match in matches:
                if match not in mail_list:
                    mail_list.append(match)
        except ValueError:
            continue
        except IndexError:
            continue
        except Exception as e:
            print(e)

    whitelist["phone_number_whitelist"] = phone_list
    whitelist["mail_whitelist"] = mail_list
    whitelist["domain_url_whitelist"] = domain_list

    whitelist_json = json.dumps(whitelist, ensure_ascii=False, indent=4)
    with open(f"{storage_dir}/whitelist.json", "w", encoding="utf-8") as file:
        file.write(whitelist_json)

    return logger.info("Whitelist file successfuly created ")
