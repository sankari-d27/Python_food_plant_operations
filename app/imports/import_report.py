
class ImportReport:

    def __init__(self):
        self.results = []

    def add_result(
        self,
        row_number,
        status,
        errors=None,
        warnings=None
    ):
        self.results.append({
            "row_number": row_number,
            "status": status,
            "errors": errors or [],
            "warnings": warnings or []
        })

    def summary(self):

        total = len(self.results)

        accepted = sum(
            1 for item in self.results
            if item["status"] == "Accepted"
        )

        rejected = sum(
            1 for item in self.results
            if item["status"] == "Rejected"
        )

        warnings = sum(
            1 for item in self.results
            if item["warnings"]
        )

        return {
            "total_records": total,
            "accepted_records": accepted,
            "rejected_records": rejected,
            "records_with_warnings": warnings,
            "details": self.results
        }
