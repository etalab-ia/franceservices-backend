from app.db import base  # noqa: F401  # pylint: disable=unused-import
from app.db.base_class import Base
from app.db.init_db import init_db
from app.db.session import engine
from app.mockups import install_mockups
from app.mockups.mailjet_mockup import remove_mailjet_folder


class TestClass:
    def setup_method(self):
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        init_db()
        install_mockups()

    def teardown_method(self):
        remove_mailjet_folder()
