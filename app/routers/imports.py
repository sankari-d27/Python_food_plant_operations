
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.imports.import_service import ImportService

import os
import tempfile


router = APIRouter(
    prefix="/imports",
    tags=["Historical Data Imports"]
)


# Initialize existing import service
import_service = ImportService()


def process_import(file: UploadFile, import_method):
    """
    Save uploaded file temporarily and process it
    using the existing ImportService.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is missing."
        )

    # Check file extension
    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are supported."
        )

    temp_path = None

    try:
        # Read uploaded file
        content = file.file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty."
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=extension,
            delete=False
        ) as temp_file:

            temp_file.write(content)
            temp_path = temp_file.name

        # Call the existing ImportService method
        report = import_method(temp_path)

        return report

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Import processing failed: {str(exc)}"
        )

    finally:
        # Remove temporary file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


# 1. Batch Upload
@router.post("/batches")
def upload_batches(file: UploadFile = File(...)):

    report = process_import(
        file,
        import_service.import_batches
    )

    return {
        "message": "Batch import validation completed successfully.",
        "data_type": "Batches",
        "report": report
    }


# 2. Quality Upload
@router.post("/quality")
def upload_quality(file: UploadFile = File(...)):

    report = process_import(
        file,
        import_service.import_quality
    )

    return {
        "message": "Quality import validation completed successfully.",
        "data_type": "Quality",
        "report": report
    }


# 3. Machine Upload
@router.post("/machines")
def upload_machines(file: UploadFile = File(...)):

    report = process_import(
        file,
        import_service.import_machines
    )

    return {
        "message": "Machine import validation completed successfully.",
        "data_type": "Machines",
        "report": report
    }


# 4. Raw Material Upload
@router.post("/raw-materials")
def upload_raw_materials(file: UploadFile = File(...)):

    report = process_import(
        file,
        import_service.import_raw_materials
    )

    return {
        "message": "Raw material import validation completed successfully.",
        "data_type": "Raw Materials",
        "report": report
    }
