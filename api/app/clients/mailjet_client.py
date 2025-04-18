from mailjet_rest import Client

from pyalbert.config import CONTACT_EMAIL, FRONT_URL, MJ_API_KEY, MJ_API_SECRET


class MailjetClient:
    def __init__(self):
        try:
            self.mailjet = Client(auth=(MJ_API_KEY, MJ_API_SECRET))
            print("Mailjet client initialized successfully")
        except Exception as e:
            print("Error initializing Mailjet client:", e)
            raise e

    def _send_create(self, data):
        try:
            result = self.mailjet.send.create(data=data)
            return result.json()
        except Exception as e:
            print("Error sending email:", e)
            return None

    def _send(self, to, subject, text):
        data = {
            "FromEmail": "language_model@data.gouv.fr",
            "Recipients": [{"Email": to}],
            "Subject": subject,
            "Text-part": text,
        }
        try:
            print("Sending email:", data)
            return self._send_create(data)
        except Exception as e:
            print("Error sending email:", e)
            return None

    def send_contact_email(self, user, subject, text, institution=None):
        to = CONTACT_EMAIL
        msg = "---\n"
        msg += f"username: {user.username}\n"
        msg += f"email: {user.email}\n"
        msg += f"institution: {institution}\n"
        msg += f"server: {FRONT_URL}\n"
        msg += "---\n\n"

        msg += text

        return self._send(to, subject, msg)

    def send_create_user_me_email(self, to):
        subject = "[Albert] Bienvenue !"
        text = "Un administrateur va examiner la création de votre compte."
        return self._send(to, subject, text)

    def send_create_user_me_notify_admin_email(self, to, email):
        subject = f"New user: {email}"
        text = f"Account email to validate: {email}\n"
        text += f"Server: {FRONT_URL}\n"
        return self._send(to, subject, text)

    def send_confirm_user_email(self, to):
        subject = "[Albert] Compte créé"
        text = f"Votre compte a été validé, vous pouvez maintenant vous connecter à l'addresse suivante : {FRONT_URL}"
        return self._send(to, subject, text)

    def send_reset_password_email(self, to, token, app):
        subject = "Reset Password"
        url = f"{FRONT_URL}/new-password?token={token}"
        text = f"Click on this link to set your new password: {url}"
        return self._send(to, subject, text)
