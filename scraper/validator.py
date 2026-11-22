"""
Scheme record validator against the canonical 30-field schema.
Ensures no unverified data is silently transformed into verified rules.
"""

from typing import Dict, Any, List, Tuple
from pydantic import ValidationError
from database.models import SchemeRecord


class SchemeValidator:
    REQUIRED_FIELDS = [
        "scheme_id",
        "scheme_name",
        "scheme_level",
        "description",
        "verification_status",
        "research_confidence",
    ]

    ALLOWED_VERIFICATION_STATUSES = {
        "verified",
        "partially_verified",
        "unverified",
        "outdated",
        "conflicting",
    }

    ALLOWED_APPLICATION_STATUSES = {
        "ACTIVE_CONFIRMED",
        "ACTIVE_STATUS_UNCONFIRMED",
        "APPLICATION_CLOSED",
        "DISCONTINUED_CONFIRMED",
        "MERGED_OR_REPLACED",
        "UNKNOWN",
    }

    @classmethod
    def validate_record(cls, record_dict: Dict[str, Any]) -> Tuple[bool, List[str], Optional[SchemeRecord]]:
        errors = []

        # Check required fields
        for field in cls.REQUIRED_FIELDS:
            if field not in record_dict or record_dict[field] is None or record_dict[field] == "":
                errors.append(f"Missing mandatory field: {field}")

        # Check verification status enum
        v_status = record_dict.get("verification_status")
        if v_status not in cls.ALLOWED_VERIFICATION_STATUSES:
            errors.append(f"Invalid verification_status: '{v_status}'. Allowed: {cls.ALLOWED_VERIFICATION_STATUSES}")

        # Check application status enum
        app_status = record_dict.get("application_status")
        if app_status not in cls.ALLOWED_APPLICATION_STATUSES:
            errors.append(f"Invalid application_status: '{app_status}'. Allowed: {cls.ALLOWED_APPLICATION_STATUSES}")

        # Check rules integrity: unverified schemes cannot have verified status
        if record_dict.get("scheme_id") == "GOI-CEN-030" and v_status == "verified":
            errors.append("Audit violation: IGNOAPS Central baseline must remain unverified until primary NSAP circular verification.")

        if errors:
            return False, errors, None

        try:
            scheme = SchemeRecord(**record_dict)
            return True, [], scheme
        except ValidationError as e:
            for err in e.errors():
                loc = " -> ".join(str(l) for l in err["loc"])
                errors.append(f"{loc}: {err['msg']}")
            return False, errors, None
