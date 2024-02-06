import requests as r
from urllib.parse import urlparse
import json
import re
import os

# Root directory:
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

"""
This file contains all postprocessing functions.
These functions aim to correct during the stream all wrong URLs, phone numbers and mails that are generated, by using the whitelist.json file.

- URLs correction steps:
    1- Checking if the url's domain name is written in a good format
    2- Checking if the url's domain name is included in the whitelist or if it ends with ".gouv.fr"
    3- Checking if the url has a status code equal to 200, then it returns the full URL in the "new_url_full" key. 
       Else, it only returns the domain name.
    4- Else, the URL is replaced by: "[URL]"

- Phone numbers correction:
    1- Checking if the phone number is in the whitelist
    2- Else, the number is replaced by: "[PHONE NUMBER]"

- Mails correction:
    1- Checking if the mail is in the whitelist
    2- Else, the URL is replaced by: "[MAIL]"
"""


def check_url(
    url: str, directory_path: str = f"{ROOT_DIR}/_data/directory", check_status_code: bool = False
) -> str:
    """Check, correct and return the url if its domain name is in the whitelist or if domain name ends with .gouv.fr. Else, returns [URL] .

    Args:
        url : url to check
        directory_path : path of the directory which contains whitelist.json
        check_status_code : allows the checking of the url's status code
    """

    ## Loading whitelist.json
    with open(f"{directory_path}/whitelist.json") as json_file:
        whitelist = json.load(json_file)["domain_url_whitelist"]

    url_out = "[URL]"
    protocols = ["http", "https"]

    ## URL format correction

    if url.startswith("www."):  # If the url starts with: www.example...
        url_out = "http://" + url  # www.example.fr become http://www.example.fr

    if not url.startswith("www.") and not url.startswith(
        "http"
    ):  # If the url starts with: example...
        for good_url in whitelist:
            for protocol in protocols:
                if "/" in urlparse(url).path:  # If the url is like: example.../...
                    if urlparse(f"http://{url}").netloc.endswith(".gouv.fr"):
                        url_out = f"http://{url}"  # By default urls like: example.gouv.fr/.. will become http://example.gouv.fr/..

                    elif (
                        f"{protocol}://www.{urlparse(f'{protocol}://{url}').netloc}"
                        == f"{protocol}://{urlparse(good_url).netloc}"
                    ):
                        url_out = f"{protocol}://www.{url}"  # example../.. becomes http(s)://www.example.../..

                    elif (
                        f"{protocol}://{urlparse(f'{protocol}://{url}').netloc}"
                        == f"{protocol}://{urlparse(good_url).netloc}"
                    ):
                        url_out = (
                            f"{protocol}://{url}"  # example../.. becomes http(s)://example.../..
                        )

                else:  # If the url is like: example..., then it is considered as the name of an url and not as an url. Exemple: "Allez sur votre compte Ameli.fr", Ameli.fr here is the name of the url https://www.ameli.fr
                    if urlparse(f"http://{url}").netloc.endswith(".gouv.fr"):
                        url_out = url

                    elif urlparse(f"{protocol}://www.{url}").netloc == urlparse(good_url).netloc:
                        url_out = url

                    elif urlparse(f"{protocol}://{url}").netloc == urlparse(good_url).netloc:
                        url_out = url

                    if url_out != "[URL]":
                        return url_out

    if url.startswith("https://") or url.startswith("http://"):
        if urlparse(url).netloc.startswith("www"):  # If the url is like : http(s)://www.example...
            for good_url in whitelist:
                for protocol in protocols:
                    if (
                        f"{protocol}://{urlparse(url).netloc}"
                        == f"{urlparse(good_url).scheme}://{urlparse(good_url).netloc}"
                    ):  # Correcting protocol
                        url_out = protocol + "://" + url.partition(f"{urlparse(url).scheme}://")[2]

                    elif (
                        f"{protocol}://{url.partition('www.')[2]}"
                        == f"{urlparse(good_url).scheme}://{urlparse(good_url).netloc}"
                    ):
                        url_out = protocol + "://" + url.partition(f"www.")[2]

        elif not urlparse(url).netloc.startswith(
            "www"
        ):  # If the url is like : http(s)://example...
            for good_url in whitelist:
                for protocol in protocols:
                    if (
                        f"{protocol}://www.{urlparse(url).netloc}"
                        == f"{urlparse(good_url).scheme}://{urlparse(good_url).netloc}"
                    ):  # Checking if "www." is missing in the url
                        url_out = (
                            protocol + "://www." + url.partition(f"{urlparse(url).scheme}://")[2]
                        )  # https://example.fr/... become https://www.example.fr/... if in the whitelist

                    elif (
                        f"{protocol}://{urlparse(url).netloc}"
                        == f"{urlparse(good_url).scheme}://{urlparse(good_url).netloc}"
                    ):  # Checking if the url has the good protocol:
                        url_out = protocol + "://" + url.partition(f"{urlparse(url).scheme}://")[2]

    if url_out == "[URL]":
        domain = urlparse(url).scheme + "://" + urlparse(url).netloc
    else:
        if url_out.startswith("http"):
            domain = urlparse(url_out).scheme + "://" + urlparse(url_out).netloc
        else:
            domain = "http://" + urlparse("http://" + url_out).netloc

    ## Whitelist check
    if urlparse(domain).netloc.endswith(".gouv.fr") or domain in whitelist:
        url_out = domain
        if check_status_code:
            if urlparse(url).path:
                try:
                    response = r.get(url)
                    if response.status_code == 200:
                        url_out = url
                except Exception:
                    pass

    elif not urlparse(domain).netloc.endswith(".gouv.fr") and domain not in whitelist:
        url_out = "[URL]"

    return url_out


def correct_url(text: str, check_status_code: bool = False) -> str:
    """Correct all urls in the text and return the text and a list of dictionnaries.

    Dictionnary keys description:
        old_url : url that was initially generated by the model
        new_url : corrects old_url by using the check_url function
        new_url_full : equal to old_url if checked by check_url and if old_url's status code = 200. Empty string by default, but fullfilled during the stream.
        new_url_index : index of this specific new_url value among the total number of occurences of new_url in the text.
                        Useful to replace the correct new_url by his new_url_full value in the Front, or to replace the correct new_url=[URL] by his old_url value in the Front.

    Args:
        text : input text
        check_status_code : allows the checking of the url's status code. This parameter is mainly useful for tests.
    """

    url_pattern = r"((?:http[s]?://|w{3}\.)(?:\w|[$-_@.&+#]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+(?<![\.,])|(?<!\S)[\w\-\.]+\.[a-z]{2,3}\S*)"
    text_out = text
    url_dict_list = []
    all_url_dict_list = []

    def replace_url(match):
        count = 1
        url = match.group(0)
        url_dict = {}
        url_dict["old_url"] = url
        url_dict["new_url"] = check_url(url, check_status_code=check_status_code)
        url_dict["new_url_full"] = ""

        if all_url_dict_list:
            for k in range(len(all_url_dict_list)):
                if all_url_dict_list[k]["new_url"] == url_dict["new_url"]:
                    count += 1

        url_dict["new_url_index"] = count

        if url_dict["old_url"] != url_dict["new_url"]:
            url_dict_list.append(url_dict)

        all_url_dict_list.append(url_dict)

        return check_url(url=url, check_status_code=check_status_code)

    text_out = re.sub(url_pattern, replace_url, text_out)

    return text_out, url_dict_list


def check_number(number: str, directory_path: str = f"{ROOT_DIR}/_data/directory") -> str:
    """Check and returns the number if in the whitelist. Else, returns [PHONE NUMBER] .

    Args:
        number: number to check
        directory_path : path of the directory which contains whitelist.json
    """

    # Opening whitelist.json
    with open(f"{directory_path}/whitelist.json") as json_file:
        whitelist = json.load(json_file)["phone_number_whitelist"]

    formated_number = number.replace(
        " ", ""
    )  # Formatting number because all numbers are formated in the whitelist
    formated_number = formated_number.replace(".", "")
    formated_number = formated_number.replace("-", "")

    number_out = "[PHONE NUMBER]"
    if formated_number in whitelist:
        number_out = formated_number

        if len(number_out) == 10 and number_out.startswith("0"):
            beautiful_number = ""
            for k in range(0, len(number_out), 2):
                beautiful_number += number_out[k : k + 2] + " "
            if len(beautiful_number) > 0 and beautiful_number[-1] == " ":
                beautiful_number = beautiful_number[:-1]

            number_out = beautiful_number

    return number_out


def correct_number(text: str) -> str:
    """Correct all numbers in the text and return the text

    Dictionnary keys description:
        old_number : number that was initially generated by the model
        new_number : corrects old_number by using the check_number function
        new_number_index : index of this specific new_number value among the total number of occurences of new_number in the text.

    Args:
        text: input text
    """

    phone_pattern = r"""((?:\+?\d{2,3}|0|\(\d+\))\s*\d(?:[\s\.\-]*\d{2}){4}(?<![\.,])|(?:\+\d{2,3}|0)\s*\d(?:[\s\.\-]*\d{2,3}){3}(?<![\.,])|\b(?<!\S)(?<!\d\s)(?<!en\s)(?<!depuis\s)(?<!de\s)(?<!janvier\s)(?<!février\s)(?<!mars\s)(?<!avril\s)(?<!mai\s)(?<!juin\s)(?<!juillet\s)(?<!août\s)(?<!septembre\s)(?<!octobre\s)(?<!novembre\s)(?<!décembre\s)(?:[\s\.\-]*\d{2}){2}(?<![\.,])(?!\s(euros?|eur|USD|dollars?|livres?|GBP|€|\$|£|habitants?|fois|années?|ans?))\b)"""
    text_out = text
    num_dict_list = []
    all_number_dict_list = []

    def replace_number(match):
        if (
            len(match.group(0)) == 4 and int(match.group(0)) >= 1900 and int(match.group(0)) < 2100
        ):  # If a 4 digit number is between 1900 and 2100, it can be a year, so we don't consider it as a number. We do this to be more rigorous and complete phone_patern.
            return match.group(0)
        count = 1
        number = match.group(0)
        num_dict = {}
        num_dict["old_number"] = number
        num_dict["new_number"] = check_number(number)

        if all_number_dict_list:
            for k in range(len(all_number_dict_list)):
                if all_number_dict_list[k]["new_number"] == num_dict["new_number"]:
                    count += 1
        num_dict["new_number_index"] = count

        if num_dict["old_number"] != num_dict["new_number"]:
            num_dict_list.append(num_dict)
        else:
            return match.group(0)

        all_number_dict_list.append(num_dict)

        return check_number(number)

    text_out = re.sub(phone_pattern, replace_number, text_out, flags=re.IGNORECASE)

    return text_out, num_dict_list


def check_mail(mail: str, directory_path: str = f"{ROOT_DIR}/_data/directory") -> str:
    """Check and returns the mail if in the whitelist. Else, returns [MAIL].

    Args:
        mail: mail to check
        directory_path : path of the directory which contains whitelist.json
    """

    # Opening whitelist.json
    with open(f"{directory_path}/whitelist.json") as json_file:
        whitelist = json.load(json_file)["mail_whitelist"]

    mail_out = "[MAIL]"
    if mail in whitelist:
        mail_out = mail

    return mail_out


def correct_mail(text: str) -> str:
    """Correct all mails in the text and return the text

    Dictionnary keys description:
        old_mail : mail that was initially generated by the model
        new_mail : corrects old_mail by using the check_mail function
        new_mail_index : index of this specific new_mail value among the total number of occurences of new_mail in the text.

    Args:
        text: input text
    """

    mail_pattern = r"(?:[\w\+\-\.]+@[\w-]+\.[\w\-\.]+)(?<![\.,])"
    text_out = text
    mail_dict_list = []
    all_mail_dict_list = []

    def replace_mail(match):
        mail = match.group(0)
        mail_dict = {}
        mail_dict["old_mail"] = mail
        mail_dict["new_mail"] = check_mail(mail)
        count = 1

        if all_mail_dict_list:
            for k in range(len(all_mail_dict_list)):
                if all_mail_dict_list[k]["new_mail"] == mail_dict["new_mail"]:
                    count += 1
        mail_dict["new_mail_index"] = count

        if mail_dict["old_mail"] != mail_dict["new_mail"]:
            mail_dict_list.append(mail_dict)

        all_mail_dict_list.append(mail_dict)

        return check_mail(mail)

    text_out = re.sub(mail_pattern, replace_mail, text_out, flags=re.IGNORECASE)

    return text_out, mail_dict_list
