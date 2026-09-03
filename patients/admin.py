from django.contrib import admin

from .models import AccessLog, PatientRecord


@admin.register(PatientRecord)
class PatientRecordAdmin(admin.ModelAdmin):

    list_display = (
        "fhir_id",
        "family_name",
        "gender",
        "birth_date",
        "created_at",
    )

    search_fields = (
        "fhir_id",
        "family_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):

    list_display = (
        "patient",
        "user",
        "timestamp",
        "ip_address",
    )

    readonly_fields = (
        "patient",
        "user",
        "timestamp",
        "ip_address",
    )