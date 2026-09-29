from typing import List, Dict, Any, Tuple
from collections import defaultdict
from backend.app.schemas.investigation import NormalizedResult, VerificationStatus, ContradictionItem

class EvidenceVerificationEngine:
    """
    Evidence Verification Engine:
    - Deduplicates identical findings across modules.
    - Audits conflicting claims across sources (e.g. diverging job titles or companies).
    - Refines confidence scores based on multi-source corroborate frequency.
    - Categorizes findings strictly into VERIFIED, LIKELY, POSSIBLE, UNCONFIRMED.
    """

    def verify_and_deduplicate(
        self,
        results: List[NormalizedResult]
    ) -> Tuple[List[NormalizedResult], List[ContradictionItem]]:
        if not results:
            return [], []

        # 1. Deduplicate by (source, attribute, value, url)
        seen_keys = set()
        deduped: List[NormalizedResult] = []
        for r in results:
            dedup_key = (r.source, r.attribute, r.value.strip().lower(), r.url)
            if dedup_key not in seen_keys:
                seen_keys.add(dedup_key)
                deduped.append(r)

        # 2. Group by attribute to detect cross-source contradictions
        attribute_groups: Dict[str, List[NormalizedResult]] = defaultdict(list)
        for r in deduped:
            attribute_groups[r.attribute].append(r)

        contradictions: List[ContradictionItem] = []

        # Check job_title / role contradictions
        for attr in ["job_title", "current_role", "employer", "location"]:
            items = attribute_groups.get(attr, [])
            if len(items) >= 2:
                distinct_values = set(i.value.strip().lower() for i in items)
                if len(distinct_values) > 1:
                    # Flag contradiction
                    i1 = items[0]
                    i2 = next(i for i in items if i.value.strip().lower() != i1.value.strip().lower())
                    contradictions.append(ContradictionItem(
                        attribute=attr,
                        claim_a={
                            "source": i1.source,
                            "value": i1.value,
                            "url": i1.url,
                            "confidence": i1.confidence
                        },
                        claim_b={
                            "source": i2.source,
                            "value": i2.value,
                            "url": i2.url,
                            "confidence": i2.confidence
                        },
                        analysis=f"Discrepancy detected for '{attr}': '{i1.value}' (Source: {i1.source}) vs '{i2.value}' (Source: {i2.source}). Further validation advised."
                    ))

        # 3. Refine Verification Status based on cross-source reinforcement
        # Count value frequency across different sources
        value_source_count: Dict[Tuple[str, str], set] = defaultdict(set)
        for r in deduped:
            value_source_count[(r.attribute, r.value.strip().lower())].add(r.source)

        verified_results: List[NormalizedResult] = []
        for r in deduped:
            sources_confirming = len(value_source_count[(r.attribute, r.value.strip().lower())])
            new_r = r.model_copy()

            if sources_confirming >= 2:
                new_r.confidence = min(0.98, max(new_r.confidence, 0.88))
                new_r.status = VerificationStatus.VERIFIED
            elif new_r.confidence >= 0.75:
                new_r.status = VerificationStatus.LIKELY
            elif new_r.confidence >= 0.45:
                new_r.status = VerificationStatus.POSSIBLE
            else:
                new_r.status = VerificationStatus.UNCONFIRMED

            verified_results.append(new_r)

        return verified_results, contradictions

verifier = EvidenceVerificationEngine()
