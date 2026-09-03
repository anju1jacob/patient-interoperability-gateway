from django.urls import path

from .views import (
    PatientDetailAPIView,
    PatientIntakeAPIView,
)


urlpatterns = [
    path(
        "patient-intake/",
        PatientIntakeAPIView.as_view(),
        name="patient-intake",
    ),
    path(
        "patients/<str:patient_id>/",
        PatientDetailAPIView.as_view(),
        name="patient-detail",
    ),
]