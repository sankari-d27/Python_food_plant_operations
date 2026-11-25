
from app.strategies.import_strategy import ImportStrategy


class RawMaterialImportStrategy(ImportStrategy):

    def validate(self, row):

        errors = []

        if not row.get("material_name"):
            errors.append("Material name is missing")

        try:
            quantity = float(row.get("quantity", 0))

            if quantity < 0:
                errors.append("Quantity cannot be negative")

        except (ValueError, TypeError):
            errors.append("Invalid material quantity")

        return errors

    def import_data(self, row):

        errors = self.validate(row)

        if errors:
            raise ValueError("; ".join(errors))

        return {
            "material_name": str(row["material_name"]).strip(),
            "material_code": row.get("material_code"),
            "supplier_id": row.get("supplier_id"),
            "quantity": float(row["quantity"]),
            "unit": row.get("unit"),
            "reorder_level": float(row.get("reorder_level") or 0)
        }
