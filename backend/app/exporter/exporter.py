import io
import csv
import json
from typing import Dict, Any, List
from backend.app.schemas.investigation import InvestigationResponse, NormalizedResult
from backend.app.schemas.export import ExportFormat, ExportRequest

class ExportEngine:
    """
    Export Engine:
    Exports investigation intelligence into JSON, CSV, Markdown, and printable HTML/PDF reports.
    """

    def export_json(self, investigation: InvestigationResponse, results: List[NormalizedResult]) -> str:
        data = {
            "investigation": investigation.model_dump(mode="json"),
            "evidence": [r.model_dump(mode="json") for r in results],
            "exported_at": investigation.updated_at.isoformat()
        }
        return json.dumps(data, indent=2)

    def export_csv(self, results: List[NormalizedResult]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Source", "Source Type", "Query", "Entity Type", "Entity",
            "Attribute", "Value", "URL", "Timestamp", "Confidence", "Status", "Evidence"
        ])
        for r in results:
            writer.writerow([
                r.source, r.source_type, r.query, r.entity_type, r.entity,
                r.attribute, r.value, r.url, r.timestamp, r.confidence, r.status.value, r.evidence
            ])
        return output.getvalue()

    def export_markdown(self, investigation: InvestigationResponse) -> str:
        return investigation.report_markdown or f"# Investigation: {investigation.title}\nNo report generated."

    def export_html(self, investigation: InvestigationResponse, results: List[NormalizedResult]) -> str:
        rows = ""
        for r in results:
            rows += f"""
            <tr>
                <td><strong>{r.source}</strong></td>
                <td><code>{r.attribute}</code></td>
                <td>{r.value}</td>
                <td><span class="badge {r.status.value}">{r.status.value.upper()}</span></td>
                <td>{int(r.confidence * 100)}%</td>
                <td><a href="{r.url}" target="_blank">Link</a></td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{investigation.title} - Intelligence Dossier</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #090d16; color: #e2e8f0; margin: 40px; }}
        h1, h2, h3 {{ color: #38bdf8; }}
        .header {{ border-bottom: 2px solid #1e293b; padding-bottom: 20px; margin-bottom: 30px; }}
        .badge {{ padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; }}
        .verified {{ background: #065f46; color: #34d399; }}
        .likely {{ background: #075985; color: #38bdf8; }}
        .possible {{ background: #854d0e; color: #facc15; }}
        .unconfirmed {{ background: #374151; color: #9ca3af; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }}
        th, td {{ border: 1px solid #1e293b; padding: 10px; text-align: left; }}
        th {{ background: #0f172a; color: #94a3b8; }}
        tr:nth-child(even) {{ background: #0b1120; }}
        a {{ color: #38bdf8; text-decoration: none; }}
        .metric-card {{ background: #0f172a; border: 1px solid #1e293b; padding: 15px; border-radius: 8px; display: inline-block; margin-right: 15px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Universal Intelligence Engine (UIE)</h1>
        <h2>Investigation Dossier: {investigation.title}</h2>
        <p>Mode: <strong>{investigation.mode.value}</strong> | Status: <strong>{investigation.status.value}</strong> | Entity Match Score: <strong>{investigation.entity_match_score}/100</strong></p>
    </div>

    <div>
        <div class="metric-card">
            <div>Confidence Score</div>
            <h2 style="margin: 5px 0;">{investigation.entity_match_score}/100</h2>
        </div>
        <div class="metric-card">
            <div>Evidence Items</div>
            <h2 style="margin: 5px 0;">{len(results)}</h2>
        </div>
        <div class="metric-card">
            <div>Contradictions</div>
            <h2 style="margin: 5px 0;">{len(investigation.contradictions)}</h2>
        </div>
    </div>

    <h2>Correlated Evidence & Provenance</h2>
    <table>
        <thead>
            <tr>
                <th>Source</th>
                <th>Attribute</th>
                <th>Value</th>
                <th>Status</th>
                <th>Confidence</th>
                <th>Provenance</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>"""
        return html

exporter = ExportEngine()
