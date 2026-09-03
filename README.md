# Patient Interoperability Gateway (PIGW)

The Patient Interoperability Gateway (PIGW) accepts FHIR R4 Patient resources, validates the incoming data, rejects patients under 18 years of age, encrypts sensitive PHI before storing it in PostgreSQL, and securely exposes patient information through REST APIs.

The application also maintains an audit trail of patient-detail access using a dedicated `AccessLog` model.

## Technology Stack

* Python 3.10+
* Django 5.0+
* Django REST Framework
* PostgreSQL
* Cryptography (Fernet)
* python-dotenv
* Basic Authentication

## Features

* FHIR R4 Patient resource validation
* Rejects patients under 18 years old
* Validates `birthDate`
* Extracts patient demographic information
* Extracts SSN and Passport Number from FHIR identifiers
* Encrypts SSN before database storage
* Encrypts Passport Number before database storage
* Encrypts the complete raw FHIR JSON payload
* Masks SSN in API responses
* Prevents Passport Number from being returned
* Supports patient creation and update using the FHIR patient ID
* Retrieves patient details by FHIR patient ID
* Logs every successful patient-detail GET request
* Records authenticated user, timestamp, patient, and IP address
* Django Admin interface for patient records and access logs
* Automated tests for core functionality and security requirements

## API Endpoints

### Patient Intake

**POST**

```text
/api/v1/patient-intake/
```

Accepts a FHIR R4 Patient resource.

Example:

```json
{
  "resourceType": "Patient",
  "id": "patient-1001",
  "active": true,
  "name": [
    {
      "use": "official",
      "family": "Chalmers",
      "given": [
        "Peter",
        "James"
      ]
    }
  ],
  "gender": "male",
  "birthDate": "1985-06-15",
  "telecom": [
    {
      "system": "phone",
      "value": "+1-555-123-4567"
    },
    {
      "system": "email",
      "value": "peter.chalmers@example.com"
    }
  ],
  "identifier": [
    {
      "system": "http://hl7.org/fhir/sid/us-ssn",
      "value": "000-12-3456"
    },
    {
      "system": "http://hl7.org/fhir/sid/passport",
      "value": "P1234567"
    }
  ]
}
```

Successful creation returns:

```text
201 Created
```

If the same FHIR patient ID is submitted again, the existing patient record is updated.

### Get Patient

**GET**

```text
/api/v1/patients/<patient_id>/
```

Returns the patient details.

Sensitive information is protected:

* SSN is returned in masked form, for example `***-**-3456`
* Passport Number is not returned

Every successful GET creates an `AccessLog` record.

## Authentication

The API requires authentication using Django REST Framework Basic Authentication.

For local testing with Postman:

1. Create a Django superuser.
2. Select **Basic Auth** in Postman.
3. Enter the Django username and password.
4. Send the API request.

Unauthenticated requests return:

```text
401 Unauthorized
```

## Age Validation

The patient's age is calculated from the FHIR `birthDate`.

Patients under 18 years old are rejected.

Example:

```json
{
  "resourceType": "Patient",
  "id": "patient-1002",
  "birthDate": "2012-06-15"
}
```

Expected response:

```text
400 Bad Request
```

Future birth dates and invalid date formats are also rejected.

## Encryption Design

Sensitive PHI is encrypted at the application layer using Fernet symmetric encryption from the `cryptography` package.

The encryption key is provided through an environment variable:

```text
ENCRYPTION_KEY=<fernet-key>
```

The following fields are encrypted before being stored in PostgreSQL:

* `PatientRecord.ssn`
* `PatientRecord.passport_number`
* `PatientRecord.raw_payload`

### How encryption works

The application uses custom Django model fields.

Before database storage:

```text
Plaintext PHI
      ↓
Fernet Encryption
      ↓
Encrypted Ciphertext
      ↓
PostgreSQL
```

When the application reads the encrypted field:

```text
PostgreSQL
      ↓
Encrypted Ciphertext
      ↓
Fernet Decryption
      ↓
Application
```

The complete raw FHIR JSON payload is also encrypted before storage so that sensitive information is not stored as plaintext in the database.

The encryption key is stored outside the database using environment configuration.

## PHI Protection

The implementation follows a least-exposure approach:

* SSN is encrypted at rest.
* Passport Number is encrypted at rest.
* Raw FHIR payload is encrypted at rest.
* SSN is masked in API responses.
* Passport Number is not returned by the API.
* Authentication is required for API access.
* Patient-detail access is recorded in `AccessLog`.
* Secrets are provided through environment variables.

## Audit Logging

Patient-detail GET requests create an `AccessLog` record containing:

* Patient
* Authenticated user
* Timestamp
* IP address

The access logs can be viewed through Django Admin.

## Database Models

### PatientRecord

Stores normalized patient information:

* FHIR ID
* Active status
* Family name
* Given names
* Gender
* Birth date
* Phone
* Email
* Encrypted SSN
* Encrypted Passport Number
* Encrypted raw FHIR payload
* Created timestamp
* Updated timestamp

### AccessLog

Stores patient access information:

* Patient
* User
* Timestamp
* IP address


## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd PIGW
```

### 2. Create a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Example:

```text
SECRET_KEY=your-django-secret-key
DEBUG=True

DB_NAME=pigw_db
DB_USER=postgres
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432

ENCRYPTION_KEY=your-fernet-encryption-key
```

Generate a Fernet encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Do not commit `.env` or real secrets to GitHub.

### 5. Create the PostgreSQL database

Create a PostgreSQL database named:

```text
pigw_db
```

Make sure the database credentials in `.env` match your local PostgreSQL configuration.

### 6. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a Django superuser

```bash
python manage.py createsuperuser
```

### 8. Start the server

```bash
python manage.py runserver
```

The application will be available at:

```text
http://127.0.0.1:8000/
```

## Django Admin

Django Admin is available at:

```text
http://127.0.0.1:8000/admin/
```

The admin interface provides access to:

* Patient Records
* Access Logs

## Testing

Run the automated tests:

```bash
python manage.py test
```

The test suite covers:

* Successful patient intake
* Under-18 patient rejection
* Invalid FHIR resource rejection
* Patient retrieval
* SSN masking
* Access log creation
* Unknown patient handling
* Authentication requirement
* Encrypted raw payload storage

## Manual Postman Testing

### Successful patient intake

```text
POST http://127.0.0.1:8000/api/v1/patient-intake/
```

Use Basic Authentication and send a valid FHIR Patient JSON payload.

Expected:

```text
201 Created
```

### Retrieve patient

```text
GET http://127.0.0.1:8000/api/v1/patients/patient-1001/
```

Expected:

* Patient details are returned.
* SSN is masked.
* Passport Number is not returned.
* An AccessLog entry is created.

### Under-18 patient

Send a Patient resource with a birth date resulting in an age below 18.

Expected:

```text
400 Bad Request
```

### Invalid resource type

Send:

```json
{
  "resourceType": "Observation",
  "id": "test-001"
}
```

Expected:

```text
400 Bad Request
```

### Unauthenticated request

Send an API request without Basic Authentication.

Expected:

```text
401 Unauthorized
```

## Optional Feature

The optional background Welcome Email feature was not implemented.

