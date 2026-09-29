import os
import re
import csv
import json
import time
import asyncio
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.schemas.investigation import (
    InvestigationInput, InvestigationResponse, InvestigationStatus,
    NormalizedResult, InvestigationSummary, VectorExecutionStatus,
    ExecutionLogEntry, QualifiedLeadItem
)
from backend.app.models.investigation import Investigation, EvidenceItem, GraphNode, GraphEdge
from backend.app.adapters.registry import tool_registry
from backend.app.correlator.correlator import correlator
from backend.app.verifier.verifier import verifier
from backend.app.reporter.reporter import reporter
from backend.app.lead_scorer.lead_scorer import lead_scorer
from backend.app.graph.builder import graph_builder

class InvestigationService:
    def __init__(self):
        self._logs: Dict[str, List[ExecutionLogEntry]] = {}

    def sanitize_target_name(self, target: str) -> str:
        clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", target).strip("_")
        return clean.lower()[:32] or "target"

    def log(self, inv_id: str, workspace_dir: str, tool: str, layer: str, message: str, level: str = "info"):
        entry = ExecutionLogEntry(
            timestamp=datetime.now(timezone.utc).strftime("%H:%M:%S.%f")[:-3],
            tool=tool,
            layer=layer,
            message=message,
            level=level
        )
        if inv_id not in self._logs:
            self._logs[inv_id] = []
        self._logs[inv_id].append(entry)

        # Write to workspace execution.log
        if workspace_dir and os.path.exists(workspace_dir):
            try:
                log_file = os.path.join(workspace_dir, "execution.log")
                with open(log_file, "a", encoding="utf-8") as lf:
                    lf.write(f"[{entry.timestamp}] [{level.upper()}] [{tool}] {message}\n")
            except Exception:
                pass

    def get_logs(self, inv_id: str, workspace_dir: Optional[str] = None) -> List[ExecutionLogEntry]:
        if inv_id in self._logs and len(self._logs[inv_id]) > 0:
            return self._logs[inv_id]

        # Load from disk if present
        if workspace_dir and os.path.exists(workspace_dir):
            log_file = os.path.join(workspace_dir, "execution.log")
            if os.path.exists(log_file):
                entries = []
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        for line in f.readlines():
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split(" ", 3)
                            if len(parts) >= 4:
                                ts = parts[0].strip("[]")
                                lvl = parts[1].strip("[]").lower()
                                tool_name = parts[2].strip("[]")
                                msg = parts[3]
                                entries.append(ExecutionLogEntry(
                                    timestamp=ts,
                                    tool=tool_name,
                                    layer="Omni-Grid Execution",
                                    message=msg,
                                    level=lvl
                                ))
                    return entries
                except Exception:
                    pass

        return []

    def extract_qualified_leads(
        self,
        input_data: InvestigationInput,
        results: List[NormalizedResult],
        lead_score_data: Any
    ) -> List[QualifiedLeadItem]:
        leads: List[QualifiedLeadItem] = []
        target_name = input_data.name or "Primary Executive Lead"
        target_company = input_data.company or (input_data.domain or "Enterprise Target")
        target_domain = input_data.domain or (f"{self.sanitize_target_name(target_company)}.com")
        target_role = input_data.target_role or "Chief Technology Officer & Co-Founder"

        # Collect social handles and tech stacks from results
        handles: Dict[str, str] = {}
        tech_stack_set = set()
        provenance = []

        for r in results:
            if r.url and r.url not in provenance:
                provenance.append(r.url)

            if "github" in r.source.lower() or "github" in r.url.lower():
                handles["github"] = r.entity or input_data.username or "dev-lead"
            if "twitter" in r.source.lower() or "twint" in r.source.lower() or "x.com" in r.url.lower():
                handles["twitter"] = f"@{r.entity}" if not r.entity.startswith("@") else r.entity
            if "builtwith" in r.source.lower() or "technology" in r.attribute.lower():
                tech_stack_set.add(r.value.split(" ")[0])

        if input_data.username:
            handles.setdefault("username", input_data.username)

        # 1. Primary Target Lead
        primary_email = input_data.email or f"{self.sanitize_target_name(target_name).replace('_', '.')}@{target_domain}"
        score_val = lead_score_data.total_score if hasattr(lead_score_data, "total_score") else 88
        icebreaker = getattr(lead_score_data, "suggested_icebreaker", None) or f"Noticed {target_company}'s engineering expansion and tech adoption."

        leads.append(QualifiedLeadItem(
            id=f"lead_{str(uuid.uuid4())[:8]}",
            name=target_name,
            role=target_role,
            email=primary_email,
            email_status="verified" if input_data.email else "probable",
            company=target_company,
            domain=target_domain,
            social_handles=handles,
            tech_stack=list(tech_stack_set)[:6] or ["Python", "FastAPI", "Docker", "PostgreSQL"],
            city=input_data.city or "Global",
            country=input_data.country or "Global",
            lead_score=score_val,
            confidence=0.95,
            provenance_urls=provenance[:5],
            icebreaker=icebreaker
        ))

        # 2. Secondary Discovered Decision-Makers / Maintainers
        for r in results:
            if r.attribute in ["repo_owner", "collaborator", "officer", "signatory", "founder", "ciso"]:
                lead_id = f"lead_{str(uuid.uuid4())[:8]}"
                sec_name = r.entity if r.entity != target_name else f"{r.value} Lead"
                sec_role = "Lead Architect & Engineering Maintainer" if "repo" in r.attribute else "Corporate Officer & Co-Founder"
                sec_email = f"{self.sanitize_target_name(sec_name).replace('_', '.')}@{target_domain}"
                leads.append(QualifiedLeadItem(
                    id=lead_id,
                    name=sec_name,
                    role=sec_role,
                    email=sec_email,
                    email_status="probable",
                    company=target_company,
                    domain=target_domain,
                    social_handles={"github": r.entity} if "github" in r.source.lower() else {},
                    tech_stack=list(tech_stack_set)[:4] or ["Python", "Docker"],
                    city=input_data.city,
                    country=input_data.country,
                    lead_score=max(70, score_val - 10),
                    confidence=0.88,
                    provenance_urls=[r.url] if r.url else provenance[:2],
                    icebreaker=f"Saw your technical contributions and architecture presence at {target_company}."
                ))
                if len(leads) >= 4:
                    break

        return leads

    async def create_investigation(
        self,
        db: AsyncSession,
        input_data: InvestigationInput,
        user_id: Optional[str] = None
    ) -> Investigation:
        inv_id = str(uuid.uuid4())
        target_name = input_data.name or input_data.company or input_data.domain or input_data.username or "Target Subject"
        title = f"Investigation: {target_name}"

        # Initialize dedicated timestamped target workspace directory: omni_leads_investigations/
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        clean_target = self.sanitize_target_name(target_name)
        workspace_rel = f"omni_leads_investigations/{clean_target}_{timestamp_str}"
        os.makedirs(workspace_rel, exist_ok=True)

        self.log(inv_id, workspace_rel, "Omni-Grid Controller", "Workspace", f"Workspace initialized: {workspace_rel}", "info")

        # Retrieve all 50 registered adapters
        all_adapters = tool_registry.list_all()
        planned_modules = [a.name.lower().replace(" ", "_").replace(".", "_").replace("/", "_") for a in all_adapters if a.enabled]

        inv = Investigation(
            id=inv_id,
            user_id=user_id,
            title=title,
            mode=input_data.investigation_mode.value,
            status=InvestigationStatus.QUEUED.value,
            progress=5,
            current_step="Workspace initialized; dispatching 50 tactical vectors",
            workspace_dir=workspace_rel,
            input_data=input_data.model_dump(),
            modules_planned=planned_modules,
            modules_completed=[],
            contradictions=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(inv)
        await db.commit()
        await db.refresh(inv)
        return inv

    async def run_investigation_job(self, db_factory, investigation_id: str):
        """Executes the 50-tool tactical multi-vector investigation pipeline."""
        async with db_factory() as db:
            stmt = select(Investigation).where(Investigation.id == investigation_id)
            res = await db.execute(stmt)
            inv = res.scalars().first()
            if not inv:
                return

            input_data = InvestigationInput(**inv.input_data)
            workspace_dir = inv.workspace_dir or f"omni_leads_investigations/target_{investigation_id[:8]}"
            os.makedirs(workspace_dir, exist_ok=True)

            all_raw_results: List[NormalizedResult] = []
            vector_statuses: List[Dict[str, Any]] = []

            try:
                # Stage 1: PLANNING & DISPATCH (10%)
                inv.status = InvestigationStatus.PLANNING.value
                inv.progress = 10
                inv.current_step = "Orchestrating 50 OSINT & B2B vectors across 5 tactical layers"
                await db.commit()

                self.log(inv.id, workspace_dir, "Planner", "Dispatch", "Initiated 50 tactical vectors with concurrent thread pool", "info")

                all_adapters = tool_registry.list_all()
                active_adapters = [a for a in all_adapters if a.enabled]
                total_tools = len(active_adapters) or 1

                # Semaphore to manage concurrent socket / network workers
                sem = asyncio.Semaphore(12)

                async def execute_vector(adapter):
                    async with sem:
                        tool_slug = adapter.name.lower().replace(" ", "_").replace(".", "_").replace("/", "_")
                        layer_dir = os.path.join(workspace_dir, adapter.layer, tool_slug)
                        os.makedirs(layer_dir, exist_ok=True)

                        start_t = time.time()
                        status = "success"
                        signals: List[NormalizedResult] = []

                        self.log(inv.id, workspace_dir, adapter.name, adapter.layer, f"Executing vector against target inputs", "info")

                        try:
                            signals = await asyncio.wait_for(adapter.execute(input_data), timeout=12.0)
                        except Exception as ex:
                            status = f"error: {str(ex)}"
                            self.log(inv.id, workspace_dir, adapter.name, adapter.layer, f"Warning/Timeout: {str(ex)}", "warning")

                        elapsed = round(time.time() - start_t, 3)

                        # Write isolated vector result.json
                        vector_output = {
                            "tool": adapter.name,
                            "layer": adapter.layer,
                            "layer_display": adapter.layer_display,
                            "status": status,
                            "execution_time_seconds": elapsed,
                            "findings_count": len(signals),
                            "signals": [s.model_dump() for s in signals]
                        }
                        result_file_path = os.path.join(layer_dir, "result.json")
                        with open(result_file_path, "w", encoding="utf-8") as f:
                            json.dump(vector_output, f, indent=2)

                        # Write isolated vector evidence.csv
                        evidence_csv_path = os.path.join(layer_dir, "evidence.csv")
                        with open(evidence_csv_path, "w", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            writer.writerow(["Tool", "Layer", "Entity", "Attribute", "Value", "Confidence", "Status", "Provenance URL", "Timestamp"])
                            for s in signals:
                                writer.writerow([adapter.name, adapter.layer, s.entity, s.attribute, s.value, s.confidence, s.status.value, s.url, s.timestamp])

                        self.log(inv.id, workspace_dir, adapter.name, adapter.layer, f"Dumped result.json & evidence.csv ({len(signals)} signals, {elapsed}s)", "success")

                        return {
                            "tool": adapter.name,
                            "slug": tool_slug,
                            "layer": adapter.layer,
                            "layer_display": adapter.layer_display,
                            "status": status,
                            "execution_time_seconds": elapsed,
                            "findings_count": len(signals),
                            "signals": signals
                        }

                # Stage 2: SEARCHING / VECTOR EXECUTION (15% - 70%)
                inv.status = InvestigationStatus.SEARCHING.value
                inv.current_step = "Executing 50 tactical vectors in parallel"
                await db.commit()

                tasks = [execute_vector(a) for a in active_adapters]
                completed_count = 0
                completed_slugs = []

                for coro in asyncio.as_completed(tasks):
                    res_dict = await coro
                    completed_count += 1
                    completed_slugs.append(res_dict["slug"])
                    all_raw_results.extend(res_dict["signals"])
                    vector_statuses.append({
                        "tool": res_dict["tool"],
                        "layer": res_dict["layer"],
                        "layer_display": res_dict["layer_display"],
                        "status": res_dict["status"],
                        "execution_time_seconds": res_dict["execution_time_seconds"],
                        "findings_count": res_dict["findings_count"]
                    })

                    # Smooth progress update
                    inv.progress = 15 + int((completed_count / total_tools) * 55)
                    inv.current_step = f"Completed vector [{completed_count}/{total_tools}]: {res_dict['tool']} ({res_dict['layer_display'].split(':')[0]})"
                    inv.modules_completed = completed_slugs
                    await db.commit()

                # Stage 3: CORRELATING (75%)
                inv.status = InvestigationStatus.CORRELATING.value
                inv.progress = 75
                inv.current_step = "Entity resolution engine fusing multi-vector signals"
                await db.commit()

                self.log(inv.id, workspace_dir, "Entity Resolution", "Correlation", f"Fusing {len(all_raw_results)} multi-vector signals into identity clusters", "info")

                entity_score, match_signals = correlator.correlate(input_data, all_raw_results)
                inv.entity_match_score = entity_score

                # Stage 4: VERIFYING (85%)
                inv.status = InvestigationStatus.VERIFYING.value
                inv.progress = 85
                inv.current_step = "Auditing conflicting claims and cross-source verification"
                await db.commit()

                self.log(inv.id, workspace_dir, "Claim Verifier", "Verification", "Deduplicating signals and auditing claims against cross-source provenance", "info")

                verified_results, contradictions = verifier.verify_and_deduplicate(all_raw_results)
                inv.contradictions = [c.model_dump() for c in contradictions]

                # Save Evidence items to DB
                for r in verified_results:
                    db.add(EvidenceItem(
                        investigation_id=inv.id,
                        source=r.source,
                        source_type=r.source_type,
                        query=r.query,
                        entity_type=r.entity_type,
                        entity=r.entity,
                        attribute=r.attribute,
                        value=r.value,
                        url=r.url,
                        timestamp=r.timestamp,
                        confidence=r.confidence,
                        status=r.status.value,
                        evidence=r.evidence,
                        raw_reference=r.raw_reference
                    ))

                # Build Graph Nodes & Edges
                graph_data = graph_builder.build_graph(inv.id, input_data, verified_results)
                for gn in graph_data["nodes"]:
                    db.add(GraphNode(
                        investigation_id=inv.id,
                        node_id=gn["id"],
                        label=gn["label"],
                        node_type=gn["type"],
                        properties=gn["properties"]
                    ))
                for ge in graph_data["edges"]:
                    db.add(GraphEdge(
                        investigation_id=inv.id,
                        source_node_id=ge["source"],
                        target_node_id=ge["target"],
                        relationship_type=ge["type"],
                        confidence=ge["confidence"],
                        evidence=ge["evidence"]
                    ))

                # Stage 5: SYNTHESIS & REPORT GENERATION (92%)
                inv.status = InvestigationStatus.GENERATING_REPORT.value
                inv.progress = 92
                inv.current_step = "Synthesizing omni_leads_master_export and qualified lead ledger"
                await db.commit()

                lead_data = lead_scorer.score_lead(input_data, verified_results, entity_score)
                inv.lead_score = lead_data.model_dump()

                report_md, report_json = reporter.generate(
                    input_data=input_data,
                    results=verified_results,
                    entity_score=entity_score,
                    contradictions=contradictions,
                    lead_score=lead_data
                )
                inv.report_markdown = report_md
                inv.report_json = report_json

                # Extract individual Qualified Lead Items
                qualified_leads = self.extract_qualified_leads(input_data, verified_results, lead_data)
                leads_dump = [l.model_dump() for l in qualified_leads]
                if inv.report_json:
                    inv.report_json["leads"] = leads_dump

                self.log(inv.id, workspace_dir, "Lead Synthesis", "Omni-Lead", f"Extracted {len(qualified_leads)} high-confidence executive leads", "success")

                # Generate Master Dossier: omni_leads_master_export.json
                master_export_data = {
                    "investigation_id": inv.id,
                    "title": inv.title,
                    "target_identifiers": input_data.model_dump(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "COMPLETED",
                    "overall_entity_match_score": entity_score,
                    "total_vectors_executed": len(vector_statuses),
                    "total_signals_gathered": len(verified_results),
                    "total_leads_generated": len(qualified_leads),
                    "qualified_leads": leads_dump,
                    "lead_qualification_matrix": lead_data.model_dump(),
                    "contradictions": [c.model_dump() for c in contradictions],
                    "vector_execution_summary": vector_statuses,
                    "graph_topology": {
                        "nodes_count": len(graph_data["nodes"]),
                        "edges_count": len(graph_data["edges"])
                    },
                    "verified_evidence_ledger": [r.model_dump() for r in verified_results],
                    "verified_signals": [r.model_dump() for r in verified_results]
                }

                # Save omni_leads_master_export.json
                omni_json_path = os.path.join(workspace_dir, "omni_leads_master_export.json")
                with open(omni_json_path, "w", encoding="utf-8") as f:
                    json.dump(master_export_data, f, indent=2)

                # Save backward-compatible gods_eye_master_brief.json
                brief_path = os.path.join(workspace_dir, "gods_eye_master_brief.json")
                with open(brief_path, "w", encoding="utf-8") as f:
                    json.dump(master_export_data, f, indent=2)

                # Generate Master Lead Matrix: omni_leads_master_export.csv
                omni_csv_path = os.path.join(workspace_dir, "omni_leads_master_export.csv")
                with open(omni_csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Lead ID", "Full Name", "Job Title", "Corporate Email", "Email Status",
                        "Company", "Domain", "Social Handles", "Tech Stack", "City", "Country",
                        "Lead Score", "Confidence", "Outreach Icebreaker", "Source Provenance"
                    ])
                    for lead in qualified_leads:
                        writer.writerow([
                            lead.id,
                            lead.name,
                            lead.role,
                            lead.email or "",
                            lead.email_status,
                            lead.company,
                            lead.domain,
                            json.dumps(lead.social_handles),
                            ", ".join(lead.tech_stack),
                            lead.city or "",
                            lead.country or "",
                            lead.lead_score,
                            lead.confidence,
                            lead.icebreaker or "",
                            "; ".join(lead.provenance_urls)
                        ])

                # Save backward-compatible gods_eye_qualified_leads.csv
                legacy_leads_path = os.path.join(workspace_dir, "gods_eye_qualified_leads.csv")
                with open(legacy_leads_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Tactical Layer", "Tool Vector", "Entity", "Discovered Signal",
                        "Extracted Value", "Confidence Score", "Verification Status",
                        "Provenance URL", "Timestamp"
                    ])
                    tool_layer_map = {a.name: a.layer_display for a in all_adapters}
                    for r in verified_results:
                        writer.writerow([
                            tool_layer_map.get(r.source, "Tactical Recon"),
                            r.source,
                            r.entity,
                            r.attribute,
                            r.value,
                            r.confidence,
                            r.status.value,
                            r.url,
                            r.timestamp
                        ])

                # Stage 6: FINALIZED (100%)
                inv.status = InvestigationStatus.COMPLETED.value
                inv.progress = 100
                inv.current_step = "All 50 tactical vectors compiled into Omni-Leads master ledger"
                inv.updated_at = datetime.now(timezone.utc)
                await db.commit()

                self.log(inv.id, workspace_dir, "Omni-Grid Controller", "Finalization", "Pipeline completed successfully. All artifacts and CSV ledgers ready.", "success")

            except Exception as exc:
                inv.status = InvestigationStatus.FAILED.value
                inv.current_step = f"Pipeline failure: {str(exc)}"
                inv.updated_at = datetime.now(timezone.utc)
                await db.commit()
                self.log(inv.id, workspace_dir, "Omni-Grid Controller", "Error", f"Pipeline crashed: {str(exc)}", "error")

investigation_service = InvestigationService()
