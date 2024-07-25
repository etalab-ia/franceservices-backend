from api.app.keycloak.clients import client_admin


class KeycloakMailClient:
    def __init__(self):
        self.keycloak = client_admin()

    def send_create_user_me_email(self, email):
        return self.keycloak.send_verify_email(email)

    def send_reset_password_email(self, user_id):
        try:
            return self.keycloak.send_update_account(user_id=user_id, payload=["UPDATE_PASSWORD"])
        except Exception as e:
            raise Exception(str(e))
