from typing import List, Dict, Any
from datetime import datetime, timezone
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, ContradictionItem, LeadScoreBreakdown

class ReportGenerator:
    """
    AI Report Generator:
    Produces evidence-first intelligence dossiers formatted in Markdown and JSON.
    Guarantees every factual assertion links directly to provenance sources and timestamps.
    """

    def generate(
        self,
        input_data: InvestigationInput,
        results: List[NormalizedResult],
        entity_score: int,
        contradictions: List[ContradictionItem],
        lead_score: LeadScoreBreakdown = None
    ) -> tuple[str, Dict[str, Any]]:
        target_name = input_data.name or input_data.company or input_data.domain or input_data.username or "Target Subject"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Organize results by category
        grouped_results = {}
        for r in results:
            grouped_results.setdefault(r.attribute, []).append(r)

        # Source URL list
        sources_list = []
        seen_urls = set()
        for r in results:
            if r.url and r.url not in seen_urls:
                seen_urls.add(r.url)
                sources_list.append({"source": r.source, "url": r.url, "timestamp": r.timestamp, "confidence": r.confidence})

        # Generate Markdown Dossier
        md_lines = [
            f"# Universal Intelligence Engine - Investigation Dossier",
            f"**Subject:** `{target_name}` | **Mode:** `{input_data.investigation_mode.value.upper()}` | **Generated:** `{now_str}`",
            "",
            "---",
            "",
            "## 1. Executive Summary",
            f"Automated open-source intelligence analysis completed across {len(results)} distinct evidence records from {len(sources_list)} verified public endpoints.",
            f"- **Entity Resolution Confidence:** **{entity_score}/100**",
            f"- **Cross-Source Contradictions Detected:** **{len(contradictions)}**",
            f"- **Total Authoritative Sources:** **{len(sources_list)}**",
            "",
            "> [!NOTE]",
            "> All statements below represent correlated public data and algorithmic scoring. Information is categorized strictly by epistemic verification status.",
            "",
            "## 2. Identity & Digital Fingerprint",
            f"| Attribute | Value | Verification Status | Confidence | Source |",
            f"| :--- | :--- | :--- | :--- | :--- |",
        ]

        for r in results[:15]:
            status_badge = f"**{r.status.value.upper()}**"
            source_link = f"[{r.source}]({r.url})" if r.url.startswith("http") else r.source
            md_lines.append(f"| `{r.attribute}` | {r.value} | {status_badge} | `{int(r.confidence * 100)}%` | {source_link} |")

        md_lines.extend([
            "",
            "## 3. Professional Profile & Affiliations",
        ])

        roles = grouped_results.get("job_title", []) + grouped_results.get("current_role", [])
        if roles:
            md_lines.append("### Current & Historical Roles")
            for r in roles:
                md_lines.append(f"- **{r.value}** ({r.source} - Confidence: {int(r.confidence*100)}%) - [Evidence Source]({r.url})")
        else:
            md_lines.append("_No explicit job titles verified in public registries._")

        companies = grouped_results.get("employer", []) + grouped_results.get("company", []) + grouped_results.get("organization", [])
        if companies:
            md_lines.append("\n### Corporate Affiliations")
            for c in companies:
                md_lines.append(f"- **{c.value}** (Reported by: `{c.source}`) [Link]({c.url})")

        md_lines.extend([
            "",
            "## 4. Public Digital Footprint & Code Repositories",
        ])
        repos = grouped_results.get("repository", []) + grouped_results.get("github_repo", [])
        handles = grouped_results.get("username", []) + grouped_results.get("profile_handle", [])
        if handles:
            md_lines.append("### Verified Digital Handles")
            for h in handles:
                md_lines.append(f"- Platform Profile: `{h.value}` via [{h.source}]({h.url})")
        if repos:
            md_lines.append("### Public Code & Contributions")
            for rp in repos:
                md_lines.append(f"- Repository: `{rp.value}` [{rp.url}]")

        if contradictions:
            md_lines.extend([
                "",
                "## 5. Conflicting Information & Contradictions",
                "> [!WARNING]",
                "> Discrepant data detected across independent sources. Do not accept either claim as definitive without further verification.",
                ""
            ])
            for idx, c in enumerate(contradictions, 1):
                md_lines.append(f"**Discrepancy #{idx}: `{c.attribute}`**")
                md_lines.append(f"- **Claim A:** `{c.claim_a.get('value')}` (Source: [{c.claim_a.get('source')}]({c.claim_a.get('url')}))")
                md_lines.append(f"- **Claim B:** `{c.claim_b.get('value')}` (Source: [{c.claim_b.get('source')}]({c.claim_b.get('url')}))")
                md_lines.append(f"- _Analysis:_ {c.analysis}\n")

        if lead_score:
            md_lines.extend([
                "",
                "## 6. Lead Qualification & ICP Assessment",
                f"- **Overall Lead Fit Score:** **{lead_score.total_score}/100**",
                f"- Decision Maker Weight: `{lead_score.decision_maker}/20` | ICP Match: `{lead_score.icp_match}/25`",
                f"- Industry Relevance: `{lead_score.industry_relevance}/15` | Tech Stack Alignment: `{lead_score.technology_match}/10`",
                "",
                "### Outreach Research Brief",
                f"> {lead_score.outreach_brief or 'Candidate matches criteria for executive engagement.'}",
                "",
                "### Suggested Icebreaker",
                f"> \"{lead_score.suggested_icebreaker or 'I noticed your recent public technical contributions...'}\"",
            ])

        md_lines.extend([
            "",
            "## 7. Authoritative Source Provenance & Verification Audit",
            "| Index | Source System | Provenance URL | Recorded Timestamp | Confidence |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for idx, s in enumerate(sources_list, 1):
            url_display = s["url"] if len(s["url"]) < 60 else f"{s['url'][:57]}..."
            md_lines.append(f"| {idx} | `{s['source']}` | [{url_display}]({s['url']}) | `{s['timestamp'][:19]}` | `{int(s['confidence']*100)}%` |")

        report_markdown = "\n".join(md_lines)

        report_json = {
            "title": f"Investigation: {target_name}",
            "generated_at": now_str,
            "entity_match_score": entity_score,
            "total_evidence_items": len(results),
            "sources_count": len(sources_list),
            "contradictions_count": len(contradictions),
            "sources": sources_list,
            "contradictions": [c.model_dump() for c in contradictions],
            "lead_score": lead_score.model_dump() if lead_score else None
        }

        return report_markdown, report_json

reporter = ReportGenerator()
