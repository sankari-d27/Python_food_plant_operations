
import pandas as pd

from app.imports.validation_service import ValidationService
from app.imports.import_report import ImportReport


class ImportService:

    def __init__(self):
        self.validator = ValidationService()

    def read_file(self, file_path):

        if file_path.lower().endswith(".csv"):
            return pd.read_csv(file_path)

        elif file_path.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(file_path)

        else:
            raise ValueError("Unsupported file format")

    def import_batches(self, file_path):

        data = self.read_file(file_path)
        report = ImportReport()

        for index, row in data.iterrows():

            row_data = row.to_dict()

            errors, warnings = (
                self.validator.validate_batch(row_data)
            )

            status = "Rejected" if errors else "Accepted"

            report.add_result(
                row_number=index + 2,
                status=status,
                errors=errors,
                warnings=warnings
            )

        return report.summary()

    def import_quality(self, file_path):

        data = self.read_file(file_path)
        report = ImportReport()

        for index, row in data.iterrows():

            row_data = row.to_dict()

            errors, warnings = (
                self.validator.validate_quality(row_data)
            )

            status = "Rejected" if errors else "Accepted"

            report.add_result(
                row_number=index + 2,
                status=status,
                errors=errors,
                warnings=warnings
            )

        return report.summary()

    def import_machines(self, file_path):

        data = self.read_file(file_path)
        report = ImportReport()

        for index, row in data.iterrows():

            row_data = row.to_dict()

            errors, warnings = (
                self.validator.validate_machine(row_data)
            )

            status = "Rejected" if errors else "Accepted"

            report.add_result(
                row_number=index + 2,
                status=status,
                errors=errors,
                warnings=warnings
            )

        return report.summary()

    def import_raw_materials(self, file_path):

        data = self.read_file(file_path)
        report = ImportReport()

        for index, row in data.iterrows():

            row_data = row.to_dict()

            errors, warnings = (
                self.validator.validate_raw_material(row_data)
            )

            status = "Rejected" if errors else "Accepted"

            report.add_result(
                row_number=index + 2,
                status=status,
                errors=errors,
                warnings=warnings
            )

        return report.summary()
