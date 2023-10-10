from mailjet_rest import Client

from app.config import MJ_API_KEY, MJ_API_SECRET


class MailjetClient:
    def __init__(self):
        self.mailjet = Client(auth=(MJ_API_KEY, MJ_API_SECRET))

    def _send_create(self, data):
        result = self.mailjet.send.create(data=data)
        return result.json()

    def _send(self, to, subject, text):
        data = {
            "FromEmail": "language_model@data.gouv.fr",
            "Recipients": [{"Email": to}],
            "Subject": subject,
            "Text-part": text,
        }
        return self._send_create(data)

    def send_create_user_me_email(self, to):
        subject = "Welcome!"
        text = "An admin will review your account creation"
        return self._send(to, subject, text)

    def send_create_user_me_notify_admin_email(self, to, email):
        subject = "New user"
        text = f"Account email: {email}"
        return self._send(to, subject, text)

    def send_confirm_user_email(self, to):
        subject = "Account created"
        text = "Now you can sign in"
        return self._send(to, subject, text)

    def send_reset_password_email(self, to, token):
        subject = "Reset Password"
        text = f"Password Reset Token: {token}"
        return self._send(to, subject, text)
