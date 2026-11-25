
from app.imports import ImportService

service = ImportService()

files = [
    ("BATCH IMPORT", service.import_batches,
     "imports/historical_batches.csv"),

    ("QUALITY IMPORT", service.import_quality,
     "imports/historical_quality.csv"),

    ("MACHINE IMPORT", service.import_machines,
     "imports/historical_machines.csv"),

    ("RAW MATERIAL IMPORT", service.import_raw_materials,
     "imports/historical_raw_materials.csv")
]

for title, import_function, file_path in files:

    print("\n" + "=" * 45)
    print(title)
    print("=" * 45)

    result = import_function(file_path)

    print("Total:", result["total_records"])
    print("Accepted:", result["accepted_records"])
    print("Rejected:", result["rejected_records"])
    print("Warnings:", result["records_with_warnings"])

    print("\nDetails:")

    for item in result["details"]:
        print(item)
