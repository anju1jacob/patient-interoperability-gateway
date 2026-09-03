from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AccessLog, PatientRecord
from .serializers import PatientRecordSerializer
from .services import validate_fhir_patient

try:
    from .tasks import send_welcome_email
except ImportError:
    send_welcome_email = None


def get_client_ip(request):
    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get(
        "REMOTE_ADDR",
        "0.0.0.0",
    )


class PatientIntakeAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request):

        if not isinstance(request.data, dict):
            return Response(
                {
                    "detail": (
                        "Request body must be a JSON object."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient_data = validate_fhir_patient(
                request.data
            )
        except ValidationError as exc:
            return Response(
                exc.detail,
                status=status.HTTP_400_BAD_REQUEST,
            )

        patient, created = PatientRecord.objects.update_or_create(
            fhir_id=patient_data["fhir_id"],
            defaults=patient_data,
        )

        if send_welcome_email:
            try:
                send_welcome_email.delay(
                    patient.id
                )
            except Exception:
                pass

        serializer = PatientRecordSerializer(
            patient
        )

        return Response(
            {
                "message": (
                    "Patient created successfully."
                    if created
                    else "Patient updated successfully."
                ),
                "patient": serializer.data,
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            ),
        )


class PatientDetailAPIView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, patient_id):

        try:
            patient = PatientRecord.objects.get(
                fhir_id=patient_id
            )
        except PatientRecord.DoesNotExist:
            return Response(
                {
                    "detail": "Patient not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        AccessLog.objects.create(
            patient=patient,
            user=request.user,
            ip_address=get_client_ip(request),
        )

        serializer = PatientRecordSerializer(
            patient
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )