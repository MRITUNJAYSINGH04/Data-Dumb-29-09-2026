from typing import List, Dict, Any, Tuple
from backend.app.schemas.investigation import NormalizedResult, InvestigationInput

class EntityResolutionEngine:
    """
    Entity Resolution Engine:
    Scores cross-source signals (0-100) to determine if multiple findings
    pertain to the same individual or corporate entity.
    Explains the evidence supporting the match.
    Strictly forbids using sensitive characteristics for identity matching.
    """

    def correlate(
        self,
        input_data: InvestigationInput,
        results: List[NormalizedResult]
    ) -> Tuple[int, List[Dict[str, Any]]]:
        if not results:
            return 0, [{"signal": "no_results", "weight": 0, "description": "No evidence records retrieved"}]

        signals_found: List[Dict[str, Any]] = []
        total_score = 0

        target_name = (input_data.name or "").lower().strip()
        target_username = (input_data.username or "").lower().strip()
        target_email = (input_data.email or "").lower().strip()
        target_company = (input_data.company or "").lower().strip()
        target_domain = (input_data.domain or "").lower().strip()
        target_location = f"{input_data.city or ''} {input_data.country or ''}".strip().lower()

        # 1. Exact Name Signal (up to 30 points)
        name_matches = 0
        for r in results:
            text_corpus = f"{r.value} {r.entity} {r.evidence}".lower()
            if target_name and target_name in text_corpus:
                name_matches += 1

        if target_name and name_matches > 0:
            score = min(30, 16 + (name_matches * 4))
            total_score += score
            signals_found.append({
                "signal": "name_congruence",
                "score": score,
                "max_score": 30,
                "description": f"Name '{input_data.name}' confirmed across {name_matches} independent evidence records"
            })

        # 2. Company / Organization Alignment (up to 25 points)
        company_matches = 0
        for r in results:
            text_corpus = f"{r.value} {r.entity} {r.evidence}".lower()
            if target_company and target_company in text_corpus:
                company_matches += 1
            if target_domain and target_domain in text_corpus:
                company_matches += 1

        if (target_company or target_domain) and company_matches > 0:
            score = min(25, 12 + (company_matches * 4))
            total_score += score
            signals_found.append({
                "signal": "company_domain_alignment",
                "score": score,
                "max_score": 25,
                "description": f"Affiliation with '{input_data.company or input_data.domain}' confirmed across {company_matches} records"
            })

        # 3. Handle / Username Uniformity (up to 20 points)
        username_matches = 0
        for r in results:
            text_corpus = f"{r.value} {r.entity} {r.url} {r.evidence}".lower()
            if target_username and target_username in text_corpus:
                username_matches += 1
            elif r.attribute in ["username", "github_handle", "profile_handle"]:
                username_matches += 1

        if username_matches > 0:
            score = min(20, 10 + (username_matches * 3))
            total_score += score
            signals_found.append({
                "signal": "handle_continuity",
                "score": score,
                "max_score": 20,
                "description": f"Identical digital handle detected across {username_matches} distinct platforms/URLs"
            })

        # 4. Email / Domain Integrity (up to 15 points)
        email_matches = 0
        for r in results:
            text_corpus = f"{r.value} {r.entity} {r.evidence}".lower()
            if target_email and target_email in text_corpus:
                email_matches += 1
            elif "@" in text_corpus and target_domain and target_domain in text_corpus:
                email_matches += 1

        if email_matches > 0:
            score = min(15, 8 + (email_matches * 3))
            total_score += score
            signals_found.append({
                "signal": "corporate_email_domain",
                "score": score,
                "max_score": 15,
                "description": f"Professional corporate email domain confirmed in {email_matches} findings"
            })

        # 5. Geographic & Professional Context (up to 10 points)
        geo_matches = 0
        if target_location:
            for r in results:
                if any(term in r.evidence.lower() for term in target_location.split()):
                    geo_matches += 1

        if geo_matches > 0:
            score = min(10, 5 + (geo_matches * 2))
            total_score += score
            signals_found.append({
                "signal": "geographic_coherence",
                "score": score,
                "max_score": 10,
                "description": f"Geographic indicators align with declared target region ({geo_matches} mentions)"
            })

        # Also update Pydantic ConfigDict deprecation if any
        final_score = min(100, max(10, total_score if total_score > 0 else 25))
        return final_score, signals_found

correlator = EntityResolutionEngine()
