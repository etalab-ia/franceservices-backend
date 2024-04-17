import json
import os
import shutil
import uuid

current_file_dir = os.path.dirname(os.path.abspath(__file__))
currrent_parent_dir = os.path.dirname(current_file_dir)
MAILJET_FOLDER = os.path.join(currrent_parent_dir, "tests/test_data/mailjet")


def create_mailjet_folder():
    os.makedirs(MAILJET_FOLDER, exist_ok=True)


def remove_mailjet_folder():
    try:
        shutil.rmtree(MAILJET_FOLDER)
    except FileNotFoundError:
        pass


def _send_create_mockup(self, data):
    filename = str(len(os.listdir(MAILJET_FOLDER))) + "_" + uuid.uuid4().hex
    filepath = os.path.join(MAILJET_FOLDER, filename)
    with open(filepath, mode="w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def install_mailjet_mockup():
    from app.clients.mailjet_client import MailjetClient

    MailjetClient._send_create = _send_create_mockup
    remove_mailjet_folder()
    create_mailjet_folder()
