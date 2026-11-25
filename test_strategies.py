from app.strategies import (
    BatchImportStrategy,
    MachineImportStrategy,
    QualityImportStrategy,
    RawMaterialImportStrategy
)


batch = BatchImportStrategy()

print("Batch validation:")
print(batch.validate({
    "batch_number": "BATCH001",
    "quantity": 500
}))


quality = QualityImportStrategy()

print("\nQuality validation:")
print(quality.import_data({
    "batch_id": 1,
    "test_name": "Moisture Test",
    "test_result": "Passed"
}))