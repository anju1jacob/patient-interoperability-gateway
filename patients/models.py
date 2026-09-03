from django.conf import settings
from django.db import models

from .encryption import (EncryptedJSONField,EncryptedTextField)


class PatientRecord(models.Model):
    """
    Stores normalized patient information extracted from a FHIR Patient
    resource.
    """

    fhir_id = models.CharField(max_length=255,unique=True,db_index=True)
    active = models.BooleanField(default=True)
    family_name = models.CharField(max_length=255,blank=True)
    given_names = models.JSONField(default=list,blank=True)
    gender = models.CharField(max_length=50,blank=True)
    birth_date = models.DateField()
    phone = models.CharField(max_length=100,blank=True)
    email = models.EmailField(blank=True)
    ssn = EncryptedTextField(blank=True,null=True)
    passport_number = EncryptedTextField(blank=True,null=True)
    raw_payload = EncryptedJSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.fhir_id}"


class AccessLog(models.Model):
    """
    Records every successful retrieval of a patient record.
    """
    patient = models.ForeignKey(PatientRecord,on_delete=models.CASCADE,related_name="access_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="patient_access_logs",)
    timestamp = models.DateTimeField(auto_now_add=True,)
    ip_address = models.GenericIPAddressField()

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return (
            f"{self.user} accessed "
            f"{self.patient.fhir_id} "
            f"from {self.ip_address}"
        )