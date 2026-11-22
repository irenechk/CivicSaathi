"""
Scheme Evaluator for Civicsaathi.
Applies deterministic rule predicates to citizen profiles.
Produces statuses:
- ELIGIBLE: All mandatory criteria pass and required evidence is verified.
- NOT_ELIGIBLE: At least one mandatory criterion demonstrably fails.
- NEEDS_VERIFICATION: Information is missing, uncertain, or conditional.
NEVER promises scheme approval.
"""

from typing import List, Dict, Any, Optional
from database.models import SchemeRecord, CitizenProfile, RuleEvaluationResult, SchemeEligibilityReport
from eligibility.rule_engine import RuleEngine


class SchemeEvaluator:
    @staticmethod
    def evaluate_scheme(scheme: SchemeRecord, profile: CitizenProfile) -> SchemeEligibilityReport:
        evaluated_rules: List[RuleEvaluationResult] = []
        missing_fields: List[str] = []
        has_failure = False
        has_unknown = False

        # 1. State / Residency Rule
        if scheme.state_or_ut and scheme.state_or_ut.lower() != "all":
            expected_state = scheme.state_or_ut
            user_state = profile.state
            status_bool, reason = RuleEngine.evaluate_predicate("in", user_state, [expected_state])
            if status_bool is True:
                rule_status = "PASS"
            elif status_bool is False:
                rule_status = "FAIL"
                has_failure = True
            else:
                rule_status = "UNKNOWN"
                has_unknown = True
                missing_fields.append("state")

            evaluated_rules.append(RuleEvaluationResult(
                rule="State/UT Domicile Requirement",
                expected_value=expected_state,
                user_value=user_state or "Not provided",
                verification_status="verified",
                status=rule_status,
                explanation=reason,
                source=scheme.official_scheme_url,
            ))

        # 2. Minimum Age
        if scheme.eligibility.age_min is not None:
            min_age = scheme.eligibility.age_min
            user_age = profile.age
            status_bool, reason = RuleEngine.evaluate_predicate("gte", user_age, min_age)
            if status_bool is True:
                rule_status = "PASS"
            elif status_bool is False:
                rule_status = "FAIL"
                has_failure = True
            else:
                rule_status = "UNKNOWN"
                has_unknown = True
                missing_fields.append("age")

            evaluated_rules.append(RuleEvaluationResult(
                rule="Minimum Age Requirement",
                expected_value=f">= {min_age} years",
                user_value=f"{user_age} years" if user_age is not None else "Not provided",
                verification_status="verified",
                status=rule_status,
                explanation=reason,
                source=scheme.official_scheme_url,
            ))

        # 3. Maximum Age
        if scheme.eligibility.age_max is not None:
            max_age = scheme.eligibility.age_max
            user_age = profile.age
            status_bool, reason = RuleEngine.evaluate_predicate("lte", user_age, max_age)
            if status_bool is True:
                rule_status = "PASS"
            elif status_bool is False:
                rule_status = "FAIL"
                has_failure = True
            else:
                rule_status = "UNKNOWN"
                has_unknown = True
                missing_fields.append("age")

            evaluated_rules.append(RuleEvaluationResult(
                rule="Maximum Age Requirement",
                expected_value=f"<= {max_age} years",
                user_value=f"{user_age} years" if user_age is not None else "Not provided",
                verification_status="verified",
                status=rule_status,
                explanation=reason,
                source=scheme.official_scheme_url,
            ))

        # 4. Income Limit
        if scheme.eligibility.income_limit is not None:
            income_cap = scheme.eligibility.income_limit
            user_income = profile.annual_family_income
            status_bool, reason = RuleEngine.evaluate_predicate("lte", user_income, income_cap)
            if status_bool is True:
                rule_status = "PASS"
            elif status_bool is False:
                rule_status = "FAIL"
                has_failure = True
            else:
                rule_status = "UNKNOWN"
                has_unknown = True
                missing_fields.append("annual_family_income")

            evaluated_rules.append(RuleEvaluationResult(
                rule="Annual Family Income Ceiling",
                expected_value=f"<= INR {income_cap:,.0f}",
                user_value=f"INR {user_income:,.0f}" if user_income is not None else "Not provided",
                verification_status="verified",
                status=rule_status,
                explanation=reason,
                source=scheme.official_scheme_url,
            ))

        # 5. Gender Requirement
        if scheme.eligibility.gender:
            expected_genders = scheme.eligibility.gender
            user_gender = profile.gender
            status_bool, reason = RuleEngine.evaluate_predicate("in", user_gender, expected_genders)
            if status_bool is True:
                rule_status = "PASS"
            elif status_bool is False:
                rule_status = "FAIL"
                has_failure = True
            else:
                rule_status = "UNKNOWN"
                has_unknown = True
                missing_fields.append("gender")

            evaluated_rules.append(RuleEvaluationResult(
                rule="Gender Eligibility",
                expected_value=f"Must be one of: {', '.join(expected_genders)}",
                user_value=user_gender or "Not provided",
                verification_status="verified",
                status=rule_status,
                explanation=reason,
                source=scheme.official_scheme_url,
            ))

        # 6. Machine Readable Custom Rules
        for r in scheme.eligibility.machine_readable_rules:
            field_name = r.field
            expected = r.value
            user_val = getattr(profile, field_name, None)
            status_bool, reason = RuleEngine.evaluate_predicate(r.operator, user_val, expected)
            if status_bool is True:
                rule_status = "PASS"
            elif status_bool is False:
                rule_status = "FAIL"
                if r.mandatory:
                    has_failure = True
            else:
                rule_status = "UNKNOWN"
                if r.mandatory:
                    has_unknown = True
                    missing_fields.append(field_name)

            evaluated_rules.append(RuleEvaluationResult(
                rule=f"Condition: {field_name.replace('_', ' ').capitalize()} ({r.operator})",
                expected_value=str(expected),
                user_value=str(user_val) if user_val is not None else "Not provided",
                verification_status=scheme.verification_status,
                status=rule_status,
                explanation=reason,
                source=r.source_url or scheme.official_scheme_url,
            ))

        # Determine overall status
        if has_failure:
            overall = "NOT_ELIGIBLE"
        elif has_unknown or len(evaluated_rules) == 0 or scheme.verification_status != "verified":
            overall = "NEEDS_VERIFICATION"
        else:
            overall = "ELIGIBLE"

        # Deduplicate missing fields
        unique_missing = list(set(missing_fields))

        return SchemeEligibilityReport(
            scheme_id=scheme.scheme_id,
            scheme_name=scheme.scheme_name,
            overall_status=overall,
            confidence="high" if not has_unknown else "medium",
            evaluated_rules=evaluated_rules,
            missing_fields=unique_missing,
            benefit_summary=scheme.benefit_amount or "See scheme details for benefit terms.",
            next_steps=[
                "Check document requirements before applying.",
                "Visit the official portal or nearest CSC to verify final enrollment.",
                "Note: Civicsaathi provides guidance based on published rules; official government verification is mandatory."
            ],
            documents_needed=scheme.required_documents[:5] if scheme.required_documents else ["Aadhaar Card", "Bank Passbook"],
        )
