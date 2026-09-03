from rest_framework import serializers

from .models import PatientRecord


class PatientRecordSerializer(serializers.ModelSerializer):
    """
    Serializer used for sanitized patient retrieval.
    """

    masked_ssn = serializers.SerializerMethodField()

    class Meta:
        model = PatientRecord

        fields = [
            "fhir_id",
            "active",
            "family_name",
            "given_names",
            "gender",
            "birth_date",
            "phone",
            "email",
            "masked_ssn",
            "passport_number",
            "created_at",
            "updated_at",
        ]

        extra_kwargs = {
            "passport_number": {
                "write_only": True,
            },
        }

    def get_masked_ssn(self, obj):
        if not obj.ssn:
            return None

        # Remove common formatting characters.
        normalized = "".join(
            character
            for character in obj.ssn
            if character.isalnum()
        )

        if len(normalized) < 4:
            return "***"

        return f"***-**-{normalized[-4:]}"