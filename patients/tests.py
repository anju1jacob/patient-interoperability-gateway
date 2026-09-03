from datetime import date

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from django.db import connection
from .models import AccessLog, PatientRecord


User = get_user_model()


class PatientAPITestCase(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword",
        )

        self.client = APIClient()

        self.client.force_authenticate(
            user=self.user
        )

        self.patient_payload = {
            "resourceType": "Patient",
            "id": "example-123",
            "active": True,
            "name": [
                {
                    "use": "official",
                    "family": "Chalmers",
                    "given": [
                        "Peter",
                        "James",
                    ],
                }
            ],
            "gender": "male",
            "birthDate": "1980-12-25",
            "identifier": [
                {
                    "system": (
                        "http://hl7.org/fhir/sid/us-ssn"
                    ),
                    "value": "000-12-3456",
                }
            ],
            "telecom": [
                {
                    "system": "phone",
                    "value": "(555) 555-5555",
                    "use": "home",
                }
            ],
        }

    def test_patient_intake_success(self):

        response = self.client.post(
            "/api/v1/patient-intake/",
            self.patient_payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertEqual(
            PatientRecord.objects.count(),
            1,
        )

        patient = PatientRecord.objects.get(
            fhir_id="example-123"
        )

        self.assertEqual(
            patient.ssn,
            "000-12-3456",
        )

    def test_under_18_patient_rejected(self):

        payload = {
            **self.patient_payload,
            "id": "minor-123",
            "birthDate": "2015-01-01",
        }

        response = self.client.post(
            "/api/v1/patient-intake/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "birthDate",
            response.data,
        )

        self.assertEqual(
            PatientRecord.objects.count(),
            0,
        )

    def test_invalid_resource_type_rejected(self):

        payload = {
            **self.patient_payload,
            "resourceType": "Observation",
        }

        response = self.client.post(
            "/api/v1/patient-intake/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_get_masks_ssn(self):

        self.client.post(
            "/api/v1/patient-intake/",
            self.patient_payload,
            format="json",
        )

        response = self.client.get(
            "/api/v1/patients/example-123/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["masked_ssn"],
            "***-**-3456",
        )

        self.assertNotIn(
            "ssn",
            response.data,
        )

    def test_get_creates_access_log(self):

        self.client.post(
            "/api/v1/patient-intake/",
            self.patient_payload,
            format="json",
        )

        response = self.client.get(
            "/api/v1/patients/example-123/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            AccessLog.objects.count(),
            1,
        )

        log = AccessLog.objects.first()

        self.assertEqual(
            log.user,
            self.user,
        )

        self.assertEqual(
            log.patient.fhir_id,
            "example-123",
        )

        self.assertIsNotNone(
            log.ip_address
        )

    def test_unknown_patient_returns_404(self):

        response = self.client.get(
            "/api/v1/patients/not-found/"
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_unauthenticated_access_rejected(self):

        self.client.force_authenticate(
            user=None
        )

        response = self.client.get(
            "/api/v1/patients/example-123/"
        )

        self.assertEqual(
            response.status_code,
            401,
        )
    def test_raw_payload_is_encrypted_in_database(self):
        self.client.post(
            "/api/v1/patient-intake/",
            self.patient_payload,
            format="json",
        )

        patient = PatientRecord.objects.get(
            fhir_id="example-123"
        )

        self.assertEqual(
            patient.raw_payload["identifier"][0]["value"],
            "000-12-3456",
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT raw_payload
                FROM patients_patientrecord
                WHERE fhir_id = %s
                """,
                ["example-123"],
            )

            encrypted_payload = cursor.fetchone()[0]

        self.assertNotIn(
            "000-12-3456",
            encrypted_payload,
        )

        self.assertNotIn(
            "Chalmers",
            encrypted_payload,
        )