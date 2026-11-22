"""
Deterministic Rule Engine for Civicsaathi Eligibility.
AI must NEVER make final eligibility decisions.
Supports operators:
- eq / equals
- neq / not_equals
- lte / less_than_or_equal
- gte / greater_than_or_equal
- lt / less_than
- gt / greater_than
- in / member_of
- not_in / not_member_of
"""

from typing import Any, Tuple, Optional


class RuleEngine:
    @staticmethod
    def evaluate_predicate(
        operator: str,
        user_value: Any,
        expected_value: Any,
    ) -> Tuple[Optional[bool], str]:
        """
        Evaluates a single rule predicate.
        Returns:
            (True, "pass") if condition demonstrably passes
            (False, "fail") if condition demonstrably fails
            (None, "unknown") if user_value is missing or cannot be verified
        """
        if user_value is None:
            return None, "Value missing from citizen profile"

        op = operator.lower().strip()

        try:
            # 1. Equality
            if op in ("eq", "equals", "=="):
                if isinstance(expected_value, str) and isinstance(user_value, str):
                    passed = user_value.strip().lower() == expected_value.strip().lower()
                else:
                    passed = user_value == expected_value
                return passed, "Condition matched" if passed else "Value does not match requirement"

            # 2. Inequality
            elif op in ("neq", "not_equals", "!="):
                if isinstance(expected_value, str) and isinstance(user_value, str):
                    passed = user_value.strip().lower() != expected_value.strip().lower()
                else:
                    passed = user_value != expected_value
                return passed, "Inequality confirmed" if passed else "Value matches excluded requirement"

            # 3. Less than or equal to
            elif op in ("lte", "<="):
                passed = float(user_value) <= float(expected_value)
                return passed, f"Value {user_value} <= {expected_value}" if passed else f"Value {user_value} exceeds maximum {expected_value}"

            # 4. Greater than or equal to
            elif op in ("gte", ">="):
                passed = float(user_value) >= float(expected_value)
                return passed, f"Value {user_value} >= {expected_value}" if passed else f"Value {user_value} is below minimum {expected_value}"

            # 5. Less than
            elif op in ("lt", "<"):
                passed = float(user_value) < float(expected_value)
                return passed, f"Value {user_value} < {expected_value}" if passed else f"Value {user_value} is not strictly less than {expected_value}"

            # 6. Greater than
            elif op in ("gt", ">"):
                passed = float(user_value) > float(expected_value)
                return passed, f"Value {user_value} > {expected_value}" if passed else f"Value {user_value} is not strictly greater than {expected_value}"

            # 7. In (Membership)
            elif op in ("in", "contains"):
                if isinstance(expected_value, (list, tuple, set)):
                    norm_expected = [str(x).strip().lower() for x in expected_value]
                    passed = str(user_value).strip().lower() in norm_expected
                elif isinstance(user_value, (list, tuple, set)):
                    norm_user = [str(x).strip().lower() for x in user_value]
                    passed = str(expected_value).strip().lower() in norm_user
                else:
                    passed = str(user_value).strip().lower() in str(expected_value).strip().lower()
                return passed, "Found in approved categories" if passed else "Not in approved list"

            # 8. Not In
            elif op in ("not_in", "excludes"):
                if isinstance(expected_value, (list, tuple, set)):
                    norm_expected = [str(x).strip().lower() for x in expected_value]
                    passed = str(user_value).strip().lower() not in norm_expected
                else:
                    passed = str(user_value).strip().lower() not in str(expected_value).strip().lower()
                return passed, "Excluded category avoided" if passed else "Belongs to excluded category"

            else:
                return None, f"Unsupported operator: {operator}"

        except (ValueError, TypeError) as e:
            return None, f"Evaluation error: {str(e)}"
