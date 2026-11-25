
from app.strategies.import_strategy import ImportStrategy


class MachineImportStrategy(ImportStrategy):

    def validate(self, row):

        errors = []

        if not row.get("machine_name"):
            errors.append("Machine name is missing")

        if not row.get("machine_code"):
            errors.append("Machine code is missing")

        return errors

    def import_data(self, row):

        errors = self.validate(row)

        if errors:
            raise ValueError("; ".join(errors))

        return {
            "machine_name": str(row["machine_name"]).strip(),
            "machine_code": str(row["machine_code"]).strip(),
            "status": row.get("status") or "Operational"
        }
