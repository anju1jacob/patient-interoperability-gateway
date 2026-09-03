import json

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


class EncryptionService:
    """
    Application-level encryption for sensitive PHI.

    Fernet provides authenticated symmetric encryption.
    """

    def __init__(self):
        if not settings.ENCRYPTION_KEY:
            raise RuntimeError(
                "ENCRYPTION_KEY is not configured."
            )

        self.fernet = Fernet(
            settings.ENCRYPTION_KEY.encode()
        )

    def encrypt(self, value: str | None) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        return self.fernet.encrypt(
            value.encode("utf-8")
        ).decode("utf-8")

    def decrypt(self, value: str | None) -> str | None:
        if value is None:
            return None

        try:
            return self.fernet.decrypt(
                value.encode("utf-8")
            ).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError(
                "Unable to decrypt protected data."
            ) from exc


encryption_service = EncryptionService()


class EncryptedTextField(models.TextField):
    """
    Transparently encrypts values before database storage
    and decrypts them when loaded.
    """

    def get_prep_value(self, value):
        value = super().get_prep_value(value)

        if value is None:
            return None

        return encryption_service.encrypt(value)

    def from_db_value(
        self,
        value,
        expression,
        connection,
    ):
        if value is None:
            return None

        return encryption_service.decrypt(value)


class EncryptedJSONField(EncryptedTextField):
    """
    Stores JSON data as encrypted text in the database.

    Django/Python sees a normal dictionary/list, but the
    database stores encrypted ciphertext.
    """

    def get_prep_value(self, value):
        if value is None:
            return None

        json_value = json.dumps(
            value,
            separators=(",", ":"),
        )

        return encryption_service.encrypt(json_value)

    def from_db_value(
        self,
        value,
        expression,
        connection,
    ):
        if value is None:
            return None

        decrypted_value = encryption_service.decrypt(value)

        return json.loads(decrypted_value)