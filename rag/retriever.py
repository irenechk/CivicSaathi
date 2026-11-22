"""
Hybrid Retriever combining lexical keyword search and local vector semantic search.
Ensures strict provenance retention (scheme_id, source_url, verification_status).
Enhanced with exact scheme/acronym recognition, query intent section boosting,
and multilingual domain-concept mapping (farming, health, maternity, enterprise, housing, pensions).
"""

import re
from typing import List, Dict, Any, Optional
from rag.vector_store import LocalVectorStore


class HybridRetriever:
    # Domain keyword boosts to relevant scheme IDs
    DOMAIN_MAPPINGS = {
        ("farmer", "farming", "crop", "krishi", "kisan", "किसान", "खेती", "कृषि", "शेतकरी", "शेती", "पीक"): [
            "GOI-CEN-004", "GOI-CEN-008", "GOI-CEN-007"
        ],
        ("maternity", "pregnant", "pregnancy", "mother", "women", "girl", "महिला", "गर्भवती", "माता", "स्त्री", "मुलगी"): [
            "GOI-CEN-001", "GOI-CEN-019", "GOI-CEN-021", "GOI-CEN-029"
        ],
        ("student", "scholarship", "education", "college", "study", "छात्र", "विद्यार्थी", "स्कॉलरशिप", "छात्रवृत्ति", "शिक्षण"): [
            "GOI-CEN-009", "GOI-CEN-022", "GOI-CEN-023", "GOI-CEN-024", "GOI-CEN-027"
        ],
        ("loan", "business", "vendor", "artisan", "mudra", "svanidhi", "ऋण", "कर्ज", "मुद्रा", "व्यापार", "दुकान", "व्यवसाय", "कारागीर"): [
            "GOI-CEN-006", "GOI-CEN-011", "GOI-CEN-010", "GOI-CEN-026", "GOI-CEN-028"
        ],
        ("housing", "house", "awas", "home", "आवास", "घर", "मकान", "घरकुल"): [
            "GOI-CEN-005", "GOI-CEN-013"
        ],
        ("solar", "electricity", "bijli", "rooftop", "सौर", "सोलर", "बिजली", "वीज"): [
            "GOI-CEN-014"
        ],
        ("health", "hospital", "ayushman", "treatment", "swasthya", "इलाज", "दवा", "अस्पताल", "आरोग्य", "दवाखाना"): [
            "GOI-CEN-017"
        ],
        ("food", "ration", "grain", "wheat", "rice", "राशन", "अनाज", "धान्य", "रेशन"): [
            "GOI-CEN-015"
        ],
        ("insurance", "accident", "life", "bima", "विमा", "बीमा"): [
            "GOI-CEN-002", "GOI-CEN-003", "GOI-CEN-007"
        ],
        ("pension", "old age", "elderly", "senior", "वृद्ध", "पेंशन", "पेन्शन", "म्हातारपण"): [
            "GOI-CEN-012", "GOI-CEN-030"
        ],
        ("employment", "job", "work", "wage", "rozgar", "रोजगार", "मजदूरी", "कामगार"): [
            "GOI-CEN-016", "GOI-CEN-020"
        ],
    }

    def __init__(self, vector_store: LocalVectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        state_filter: Optional[str] = None,
        verification_filter: Optional[str] = None,
        benefit_type_filter: Optional[str] = None,
        beneficiary_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. Semantic vector search from LocalVectorStore
        2. Exact scheme acronym & canonical title matching boost
        3. Multilingual domain-concept keyword mapping boost
        4. Intent-driven section weighting (Overview vs Eligibility vs Application)
        5. State & beneficiary cohort filters
        6. Source provenance ranking boost (verified gov.in prioritized, unverified penalized)
        7. Deduplication across scheme sections
        8. Retrieval confidence scoring (high, medium, low)
        """
        semantic_results = self.vector_store.similarity_search(
            query=query,
            top_k=max(top_k * 4, 30),
            state_filter=state_filter,
            verification_filter=verification_filter,
            benefit_type_filter=benefit_type_filter,
        )

        q_lower = query.lower()
        query_terms = set(re.findall(r"\w+", q_lower))

        # Detect user intent
        intent_app = bool(re.search(r"\b(apply|application|process|steps|portal|website|link|register|form|how to apply|कुठे अर्ज करावा|अर्ज|आवेदन|फॉर्म|नोंदणी)\b", q_lower))
        intent_doc = bool(re.search(r"\b(document|documents|paper|papers|paperwork|certificate|card|proof|aadhaar|कागदपत्रे|कागदपत्र|दस्तावेज|प्रमाणपत्र)\b", q_lower))
        intent_elig = bool(re.search(r"\b(eligible|eligibility|criteria|age|income|condition|who can|qualification|पात्रता|अटी|शर्ती|पात्र)\b", q_lower))
        intent_benefit = bool(re.search(r"\b(benefit|benefits|amount|money|cash|pension|insurance|subsidy|rate|लाभ|फायदे|पैसे|अनुदान|पेन्शन|विमा)\b", q_lower))

        # Identify targeted domain scheme IDs
        boosted_domain_scheme_ids = set()
        for keywords, target_ids in self.DOMAIN_MAPPINGS.items():
            for kw in keywords:
                if kw in q_lower or kw in query_terms:
                    boosted_domain_scheme_ids.update(target_ids)

        ranked_results = []
        for item in semantic_results:
            meta = item.get("metadata", {})
            section = meta.get("section", "")
            scheme_id = meta.get("scheme_id", "")
            scheme_name = meta.get("scheme_name", "").lower()
            alt_names = [a.lower() for a in meta.get("alternate_names", [])]
            state_scope = meta.get("state_or_ut", "all").lower()

            # State filtering penalty
            if state_filter and state_scope != "all" and state_scope != state_filter.lower():
                continue

            # 1. Base semantic score
            score = float(item.get("score", 0.0))

            # 2. Text keyword overlap
            text_terms = set(re.findall(r"\w+", item["text"].lower()))
            overlap = len(query_terms.intersection(text_terms))
            score += overlap * 0.15

            # 3. Exact Scheme Name / Acronym Boost
            scheme_matched = False
            for alt in alt_names:
                alt_clean = re.sub(r"[^\w\s]", "", alt)
                if (alt and alt in q_lower) or (alt_clean and alt_clean in q_lower):
                    score += 9.0
                    scheme_matched = True
                    break
                alt_tokens = set(re.findall(r"\w+", alt))
                if alt_tokens and alt_tokens.issubset(query_terms):
                    score += 8.0
                    scheme_matched = True
                    break

            if not scheme_matched:
                if scheme_name and scheme_name in q_lower:
                    score += 8.0
                    scheme_matched = True
                else:
                    name_tokens = set(re.findall(r"\w+", scheme_name))
                    distinctive_name_tokens = name_tokens - {"yojana", "pradhan", "mantri", "national", "scheme", "mission", "kendriya"}
                    matched_distinctive = len(distinctive_name_tokens.intersection(query_terms))
                    if matched_distinctive >= 1:
                        score += 3.0 + (matched_distinctive * 2.5)

            # 4. Domain Concept Boost
            if scheme_id in boosted_domain_scheme_ids:
                score += 3.5

            # 5. Intent-driven Section Boosting
            if (intent_app or intent_doc) and section == "Application & Documents":
                score += 3.0
            elif intent_elig and section == "Eligibility & Exclusions":
                score += 3.0
            elif intent_benefit and section == "Overview & Benefits":
                score += 3.0

            # 6. Beneficiary Cohort Filter / Boost
            if beneficiary_filter:
                target_b = [b.lower() for b in meta.get("target_beneficiaries", [])]
                if any(beneficiary_filter.lower() in tb for tb in target_b):
                    score += 2.5

            # 7. Source Provenance Ranking (Trust Boost)
            v_status = meta.get("verification_status", "verified")
            if v_status == "verified":
                score += 1.0
            elif v_status == "partially_verified":
                score += 0.5
            elif v_status in ("unverified", "outdated", "conflicting"):
                score -= 1.5

            src_url = meta.get("source_url", "")
            if "gov.in" in src_url or "nic.in" in src_url:
                score += 0.8

            # Confidence evaluation
            if score >= 5.5 and v_status in ("verified", "partially_verified"):
                conf = "high"
            elif score >= 2.0:
                conf = "medium"
            else:
                conf = "low"

            item_copy = dict(item)
            item_copy["hybrid_score"] = round(score, 4)
            item_copy["retrieval_confidence"] = conf
            ranked_results.append(item_copy)

        ranked_results.sort(key=lambda x: x["hybrid_score"], reverse=True)

        # 8. Duplicate Removal: Keep highest scored passage per scheme section
        deduped = []
        seen_keys = set()
        for r in ranked_results:
            key = (r.get("metadata", {}).get("scheme_id", ""), r.get("metadata", {}).get("section", ""))
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped.append(r)
            if len(deduped) >= top_k:
                break

        return deduped
