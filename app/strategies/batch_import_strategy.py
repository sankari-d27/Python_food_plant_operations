
from app.strategies.import_strategy import ImportStrategy


class BatchImportStrategy(ImportStrategy):

    def validate(self, row):

        errors = []

        if not row.get("batch_number"):
            errors.append("Batch number is missing")

        try:
            quantity = float(row.get("quantity", 0))

            if quantity <= 0:
                errors.append("Quantity must be greater than zero")

        except (ValueError, TypeError):
            errors.append("Invalid batch quantity")

        return errors

    def import_data(self, row):

        errors = self.validate(row)

        if errors:
            raise ValueError("; ".join(errors))

        return {
            "batch_number": str(row["batch_number"]).strip(),
            "quantity": float(row["quantity"]),
            "status": "Planned"
        }
