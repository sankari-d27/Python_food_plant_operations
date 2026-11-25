
import pandas as pd


class ValidationService:

    # 1. BATCH VALIDATION
    def validate_batch(self, row):
        errors = []
        warnings = []

        batch_number = row.get("batch_number")

        if pd.isna(batch_number) or not str(batch_number).strip():
            errors.append("Batch number is missing")

        try:
            quantity_value = row.get("quantity")

            if pd.isna(quantity_value):
                raise ValueError

            quantity = float(quantity_value)

            if quantity <= 0:
                errors.append("Quantity must be greater than zero")

        except (ValueError, TypeError):
            errors.append("Invalid batch quantity")

        line_id = row.get("production_line_id")

        if pd.isna(line_id):
            warnings.append("Production line ID is missing")

        return errors, warnings

    # 2. QUALITY VALIDATION
    def validate_quality(self, row):
        errors = []
        warnings = []

        batch_id = row.get("batch_id")
        test_name = row.get("test_name")

        if pd.isna(batch_id):
            errors.append("Batch ID is missing")

        if pd.isna(test_name) or not str(test_name).strip():
            errors.append("Quality test name is missing")

        # Check missing moisture reading
        moisture = row.get("moisture_reading")

        if pd.isna(moisture):
            warnings.append(
                "Moisture reading missing; requires review"
            )
        else:
            try:
                moisture_value = float(moisture)

                if not 0 <= moisture_value <= 100:
                    errors.append(
                        "Moisture reading must be between 0 and 100"
                    )

            except (ValueError, TypeError):
                errors.append("Invalid moisture reading")

        # Check delayed quality results
        test_date = row.get("test_date")
        recorded_date = row.get("recorded_date")

        if pd.notna(test_date) and pd.notna(recorded_date):
            try:
                tested = pd.to_datetime(test_date)
                recorded = pd.to_datetime(recorded_date)

                if recorded.date() > tested.date():
                    warnings.append(
                        "Quality result recorded after test date"
                    )

            except (ValueError, TypeError):
                warnings.append("Invalid quality date format")

        return errors, warnings

    # 3. MACHINE VALIDATION
    def validate_machine(self, row):
        errors = []
        warnings = []

        machine_name = row.get("machine_name")
        machine_code = row.get("machine_code")

        if pd.isna(machine_name) or not str(machine_name).strip():
            errors.append("Machine name is missing")

        if pd.isna(machine_code) or not str(machine_code).strip():
            errors.append("Machine code is missing")

        status = row.get("status")

        if pd.isna(status):
            warnings.append("Machine status is missing")

        return errors, warnings

    # 4. RAW MATERIAL VALIDATION
    def validate_raw_material(self, row):
        errors = []
        warnings = []

        material_name = row.get("material_name")

        if pd.isna(material_name) or not str(material_name).strip():
            errors.append("Material name is missing")

        try:
            quantity_value = row.get("quantity")

            if pd.isna(quantity_value):
                raise ValueError

            quantity = float(quantity_value)

            if quantity < 0:
                errors.append("Quantity cannot be negative")

        except (ValueError, TypeError):
            errors.append("Invalid material quantity")

        try:
            reorder_value = row.get("reorder_level", 0)

            if pd.isna(reorder_value):
                reorder_value = 0

            reorder_level = float(reorder_value)

            if reorder_level < 0:
                errors.append("Reorder level cannot be negative")

        except (ValueError, TypeError):
            errors.append("Invalid reorder level")

        return errors, warnings
