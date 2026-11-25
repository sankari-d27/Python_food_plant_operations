
from app.strategies.import_strategy import ImportStrategy


class QualityImportStrategy(ImportStrategy):

    def validate(self, row):

        errors = []

        if not row.get("batch_id"):
            errors.append("Batch ID is missing")

        if not row.get("test_name"):
            errors.append("Quality test name is missing")

        return errors

    def import_data(self, row):

        errors = self.validate(row)

        if errors:
            raise ValueError("; ".join(errors))

        moisture = row.get("moisture_reading")

        warnings = []

        if moisture is None or str(moisture).strip() == "":
            warnings.append("Moisture reading missing; requires review")

        return {
            "batch_id": int(row["batch_id"]),
            "test_name": str(row["test_name"]).strip(),
            "test_result": row.get("test_result"),
            "remarks": row.get("remarks"),
            "moisture_reading": moisture,
            "warnings": warnings
        }
