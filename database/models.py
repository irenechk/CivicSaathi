"""
Database models and Pydantic schemas for Civicsaathi.
Defines canonical 30-field Scheme schema, SourceRegistry, CrawlDocument, and CitizenProfile.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class MachineReadableRule(BaseModel):
    field: str
    operator: str  # eq, neq, lte, gte, lt, gt, in, not_in
    value: Union[str, int, float, bool, List[Any]]
    unit: Optional[str] = None
    mandatory: bool = True
    source_url: Optional[str] = None
    source_section: Optional[str] = None


class EligibilityCriteria(BaseModel):
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    income_limit: Optional[float] = None
    occupation: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    residency: List[str] = Field(default_factory=list)
    gender: List[str] = Field(default_factory=list)
    category: List[str] = Field(default_factory=list)
    other_conditions: List[str] = Field(default_factory=list)
    machine_readable_rules: List[MachineReadableRule] = Field(default_factory=list)


class SchemeRecord(BaseModel):
    """
    Canonical 30-field Scheme Schema for Civicsaathi Master Knowledge Base.
    """
    scheme_id: str
    scheme_name: str
    alternate_names: List[str] = Field(default_factory=list)
    scheme_level: str = "central"  # central, state, union_territory, district, local
    state_or_ut: str = "all"
    districts: List[str] = Field(default_factory=list)
    ministry: Optional[str] = None
    department: Optional[str] = None
    description: str
    objective: Optional[str] = None
    target_beneficiaries: List[str] = Field(default_factory=list)
    benefit_type: List[str] = Field(default_factory=list)  # cash, loan, subsidy, insurance, pension, scholarship, in_kind, training, guarantee, service
    benefit_amount: Optional[str] = None
    benefit_frequency: Optional[str] = None
    eligibility: EligibilityCriteria = Field(default_factory=EligibilityCriteria)
    exclusion_conditions: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    application_process: List[str] = Field(default_factory=list)
    application_mode: Optional[str] = None  # online, offline, online_and_offline
    official_application_url: Optional[str] = None
    official_scheme_url: Optional[str] = None
    official_source_urls: List[str] = Field(default_factory=list)
    guidelines_document_urls: List[str] = Field(default_factory=list)
    application_status: str = "ACTIVE_CONFIRMED"  # ACTIVE_CONFIRMED, ACTIVE_STATUS_UNCONFIRMED, APPLICATION_CLOSED, DISCONTINUED_CONFIRMED, MERGED_OR_REPLACED, UNKNOWN
    launch_date: Optional[str] = None
    last_updated_date: Optional[str] = None
    research_verified_date: str = "2026-11-21"
    verification_status: str = "verified"  # verified, partially_verified, unverified, outdated, conflicting
    source_notes: List[str] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)
    research_confidence: str = "high"  # high, medium, low


class CitizenProfile(BaseModel):
    user_id: Optional[str] = None
    full_name: Optional[str] = None
    language: str = "en"  # en, hi, mr
    state: Optional[str] = None
    district: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    annual_family_income: Optional[float] = None
    category: Optional[str] = None  # General, SC, ST, OBC, EBC, DNT, Minority
    education_level: Optional[str] = None
    is_disabled: Optional[bool] = None
    has_bpl_card: Optional[bool] = None
    owns_cultivable_land: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class RuleEvaluationResult(BaseModel):
    rule: str
    expected_value: Any
    user_value: Any
    verification_status: str
    status: str  # PASS, FAIL, UNKNOWN
    explanation: str
    source: Optional[str] = None


class SchemeEligibilityReport(BaseModel):
    scheme_id: str
    scheme_name: str
    overall_status: str  # ELIGIBLE, NOT_ELIGIBLE, NEEDS_VERIFICATION
    confidence: str
    evaluated_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    benefit_summary: Optional[str] = None
    next_steps: List[str] = Field(default_factory=list)
    documents_needed: List[str] = Field(default_factory=list)


class SchemeVersion(BaseModel):
    version_id: Optional[int] = None
    scheme_id: str
    version_tag: str = "1.0"
    previous_eligibility: Dict[str, Any] = Field(default_factory=dict)
    current_eligibility: Dict[str, Any] = Field(default_factory=dict)
    previous_benefits: Optional[str] = None
    current_benefits: Optional[str] = None
    source_document: Optional[str] = None
    change_notes: Optional[str] = None
    verification_status: str = "verified"
    created_by: str = "system"
    created_at: Optional[str] = None


class AdminReviewFlag(BaseModel):
    flag_id: Optional[int] = None
    scheme_id: str
    flag_type: str  # outdated, conflicting, source_gap, scraper_error
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, resolved, dismissed
    flagged_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


class DocumentReadinessReport(BaseModel):
    scheme_id: str
    scheme_name: str
    total_required: int
    mandatory_count: int
    available_count: int
    missing_mandatory: List[str] = Field(default_factory=list)
    available_documents: List[str] = Field(default_factory=list)
    conditional_documents: List[str] = Field(default_factory=list)
    readiness_percentage: float
    readiness_level: str  # High, Moderate, Low
    next_steps: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Notice: Document readiness indicates application preparation only and does not guarantee government approval or disbursement."
    )


class SchemeComparisonItem(BaseModel):
    scheme_id: str
    scheme_name: str
    ministry: Optional[str] = None
    benefit_summary: str
    benefit_amount: Optional[str] = None
    benefit_frequency: Optional[str] = None
    age_criteria: str
    income_limit: str
    target_beneficiaries: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    application_process: List[str] = Field(default_factory=list)
    application_mode: Optional[str] = None
    state_applicability: str
    application_status: str
    official_source_url: str
    verification_status: str


class SchemeComparisonReport(BaseModel):
    schemes: List[SchemeComparisonItem]
    generated_at: str
    comparison_summary: str


class CitizenDashboardData(BaseModel):
    profile: CitizenProfile
    saved_schemes: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_schemes: List[Dict[str, Any]] = Field(default_factory=list)
    eligibility_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    missing_documents: List[str] = Field(default_factory=list)
    recently_viewed: List[Dict[str, Any]] = Field(default_factory=list)
    consent_given: bool = True

