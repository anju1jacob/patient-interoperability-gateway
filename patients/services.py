from datetime import date

from django.utils import timezone
from rest_framework.exceptions import ValidationError


SSN_SYSTEM = "http://hl7.org/fhir/sid/us-ssn"


def calculate_age(birth_date: date) -> int:
    """
    Calculate patient's age based on today's date.
    """

    today = timezone.localdate()

    age = today.year - birth_date.year

    if (today.month, today.day) < (
        birth_date.month,
        birth_date.day,
    ):
        age -= 1

    return age


def extract_identifier(
    identifiers: list,
    system: str,
) -> str | None:
    """
    Find an identifier by FHIR system.
    """

    for identifier in identifiers:
        if identifier.get("system") == system:
            return identifier.get("value")

    return None


def extract_passport(
    identifiers: list,
) -> str | None:
    """
    Extract passport number.

    FHIR does not require one universal passport system URI,
    so this implementation accepts common passport representations.
    """

    passport_systems = {
        "http://hl7.org/fhir/sid/passport",
        "passport",
    }

    for identifier in identifiers:
        system = identifier.get("system", "").lower()

        if system in passport_systems:
            return identifier.get("value")

        if "passport" in system:
            return identifier.get("value")

    return None


def validate_fhir_patient(payload: dict) -> dict:
    """
    Validate and normalize a FHIR R4 Patient resource.
    """

    if not isinstance(payload, dict):
        raise ValidationError(
            {"detail": "Payload must be a JSON object."}
        )

    if payload.get("resourceType") != "Patient":
        raise ValidationError(
            {
                "resourceType": (
                    "resourceType must be 'Patient'."
                )
            }
        )

    fhir_id = payload.get("id")

    if not fhir_id:
        raise ValidationError(
            {"id": "Patient resource must contain an id."}
        )

    birth_date_raw = payload.get("birthDate")

    if not birth_date_raw:
        raise ValidationError(
            {
                "birthDate": (
                    "birthDate is required."
                )
            }
        )

    try:
        birth_date = date.fromisoformat(
            birth_date_raw
        )
    except (TypeError, ValueError):
        raise ValidationError(
            {
                "birthDate": (
                    "birthDate must be in YYYY-MM-DD format."
                )
            }
        )

    if birth_date > timezone.localdate():
        raise ValidationError(
            {
                "birthDate": (
                    "birthDate cannot be in the future."
                )
            }
        )

    age = calculate_age(birth_date)

    if age < 18:
        raise ValidationError(
            {
                "birthDate": (
                    "Patients under 18 years old "
                    "are not accepted."
                )
            }
        )

    identifiers = payload.get("identifier", [])

    if not isinstance(identifiers, list):
        raise ValidationError(
            {
                "identifier": (
                    "identifier must be a list."
                )
            }
        )

    ssn = extract_identifier(
        identifiers,
        SSN_SYSTEM,
    )

    passport_number = extract_passport(
        identifiers
    )

    names = payload.get("name", [])

    family_name = ""
    given_names = []

    if names:
        official_name = names[0]

        family_name = official_name.get(
            "family",
            "",
        )

        given_names = official_name.get(
            "given",
            [],
        )

    telecom = payload.get("telecom", [])

    phone = ""
    email = ""

    for item in telecom:
        if item.get("system") == "phone" and not phone:
            phone = item.get("value", "")

        if item.get("system") == "email" and not email:
            email = item.get("value", "")

    return {
        "fhir_id": fhir_id,
        "active": payload.get(
            "active",
            True,
        ),
        "family_name": family_name,
        "given_names": given_names,
        "gender": payload.get(
            "gender",
            "",
        ),
        "birth_date": birth_date,
        "phone": phone,
        "email": email,
        "ssn": ssn,
        "passport_number": passport_number,
        "raw_payload": payload,
    }