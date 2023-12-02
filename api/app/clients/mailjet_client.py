from mailjet_rest import Client

from app.config import FRONT_URL, MJ_API_KEY, MJ_API_SECRET


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

    def send_contact_email(self, user, subject, text, institution=None):
        text = "An admin will review your account creation"
        to = "language_model@data.gouv.fr"
        text = f'''
        username: {user.username}
        email: {user.email}
        institution: {institution}

        {text}
        '''
        return self._send(to, subject, text)

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

    def send_reset_password_email(self, to, token, app):
        subject = "Reset Password"
        if app == "spp":
            url = f"{FRONT_URL}/new-password?token={token}"
        else:
            url = f"{FRONT_URL}/albert/new-password?token={token}"
        text = f"Click on this link to set your new password: {url}"
        return self._send(to, subject, text)
