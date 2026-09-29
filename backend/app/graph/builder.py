from typing import List, Dict, Any, Tuple
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult

class GraphBuilder:
    """
    Graph Builder:
    Constructs an interactive Neo4j-compatible knowledge graph from investigation evidence.
    Generates nodes, relationships with confidence/evidence, and exportable Cypher statements.
    """

    def build_graph(
        self,
        investigation_id: str,
        input_data: InvestigationInput,
        results: List[NormalizedResult]
    ) -> Dict[str, Any]:
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: List[Dict[str, Any]] = []

        # 1. Primary Target Node
        root_id = "root_target"
        root_label = input_data.name or input_data.company or input_data.domain or input_data.username or "Target Entity"
        root_type = "Person" if input_data.name else ("Company" if input_data.company else "Domain")
        nodes[root_id] = {
            "id": root_id,
            "label": root_label,
            "type": root_type,
            "properties": {"primary": True, "query": root_label}
        }

        # 2. Add input identifier nodes if provided
        if input_data.email:
            email_id = f"email_{input_data.email}"
            nodes[email_id] = {"id": email_id, "label": input_data.email, "type": "Email", "properties": {}}
            edges.append({
                "source": root_id, "target": email_id,
                "type": "ASSOCIATED_WITH", "confidence": 0.95,
                "evidence": "Declared primary contact identifier"
            })

        if input_data.company and root_type != "Company":
            comp_id = f"comp_{input_data.company}"
            nodes[comp_id] = {"id": comp_id, "label": input_data.company, "type": "Company", "properties": {}}
            edges.append({
                "source": root_id, "target": comp_id,
                "type": "WORKS_AT", "confidence": 0.9,
                "evidence": "Declared current company organization"
            })

        if input_data.domain:
            dom_id = f"dom_{input_data.domain}"
            nodes[dom_id] = {"id": dom_id, "label": input_data.domain, "type": "Domain", "properties": {}}
            edges.append({
                "source": root_id, "target": dom_id,
                "type": "OWNS_DOMAIN" if root_type == "Company" else "ASSOCIATED_WITH",
                "confidence": 0.85, "evidence": "Associated web domain infrastructure"
            })

        # 3. Add nodes and relationships from Normalized Results
        for idx, r in enumerate(results):
            # Target node type
            target_type = "PublicProfile"
            rel_type = "ASSOCIATED_WITH"

            if r.attribute in ["repository", "github_repo"]:
                target_type = "GitHubRepository"
                rel_type = "MAINTAINS"
            elif r.attribute in ["organization", "employer"]:
                target_type = "Company"
                rel_type = "WORKS_AT"
            elif r.attribute in ["news_mention", "headline"]:
                target_type = "NewsArticle"
                rel_type = "MENTIONED_IN"
            elif r.attribute in ["publication", "paper"]:
                target_type = "Publication"
                rel_type = "AUTHORED"
            elif r.attribute in ["username", "profile_handle"]:
                target_type = "Username"
                rel_type = "POSSIBLY_SAME_ENTITY"
            elif r.attribute in ["subdomain", "dns_record"]:
                target_type = "Domain"
                rel_type = "ASSOCIATED_WITH"

            node_key = f"{target_type.lower()}_{idx}"
            clean_label = r.value if len(r.value) < 40 else f"{r.value[:37]}..."
            
            nodes[node_key] = {
                "id": node_key,
                "label": clean_label,
                "type": target_type,
                "properties": {
                    "source": r.source,
                    "url": r.url,
                    "confidence": r.confidence,
                    "status": r.status.value
                }
            }

            edges.append({
                "source": root_id,
                "target": node_key,
                "type": rel_type,
                "confidence": r.confidence,
                "evidence": f"Reported by {r.source}: {r.evidence[:100]}"
            })

        return {
            "investigation_id": investigation_id,
            "nodes": list(nodes.values()),
            "edges": edges
        }

    def to_cypher(self, graph_data: Dict[str, Any]) -> str:
        """Converts graph dictionary to Neo4j Cypher query batch."""
        cypher_lines = ["// Neo4j Cypher Export - Universal Intelligence Engine"]
        
        # Create nodes
        for node in graph_data.get("nodes", []):
            clean_label = node['label'].replace("'", "\\'")
            cypher_lines.append(
                f"MERGE (n:{node['type']} {{id: '{node['id']}'}}) "
                f"ON CREATE SET n.label = '{clean_label}', n.updatedAt = timestamp();"
            )

        # Create edges
        for edge in graph_data.get("edges", []):
            cypher_lines.append(
                f"MATCH (a {{id: '{edge['source']}'}}), (b {{id: '{edge['target']}'}}) "
                f"MERGE (a)-[r:{edge['type']} {{confidence: {edge['confidence']}}}]->(b);"
            )

        return "\n".join(cypher_lines)

graph_builder = GraphBuilder()
