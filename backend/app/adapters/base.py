from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.schemas.investigation import InvestigationInput, NormalizedResult, VerificationStatus

class BaseAdapter(ABC):
    name: str = "base_adapter"
    layer: str = "layer1_infrastructure"
    layer_display: str = "Layer 1: Infrastructure & Perimeter Recon"
    category: str = "general"
    description: str = "Base OSINT Adapter"
    version: str = "1.0.0"
    license: str = "MIT"
    supported_identifiers: List[str] = []

    def __init__(self):
        self.enabled: bool = True
        self.last_execution: Optional[datetime] = None
        self.execution_count: int = 0
        self.success_count: int = 0
        self.total_execution_time: float = 0.0

    def is_installed(self) -> bool:
        """Check if local CLI tool, library, or API endpoint is available."""
        return True

    @abstractmethod
    async def execute(self, input_data: InvestigationInput) -> List[NormalizedResult]:
        """Execute investigation query and return standardized normalized results."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        avg_time = (self.total_execution_time / self.execution_count) if self.execution_count > 0 else 0.0
        success_rate = (self.success_count / self.execution_count * 100.0) if self.execution_count > 0 else 100.0
        return {
            "id": self.name.lower().replace(" ", "_").replace(".", "_").replace("/", "_"),
            "name": self.name,
            "layer": self.layer,
            "layer_display": self.layer_display,
            "category": self.category,
            "description": self.description,
            "installed": self.is_installed(),
            "version": self.version,
            "license": self.license,
            "enabled": self.enabled,
            "last_execution": self.last_execution,
            "success_rate": round(success_rate, 1),
            "avg_execution_time_seconds": round(avg_time, 2),
            "supported_identifiers": self.supported_identifiers,
        }

    def create_result(
        self,
        query: str,
        entity_type: str,
        entity: str,
        attribute: str,
        value: str,
        url: str,
        confidence: float,
        status: VerificationStatus,
        evidence: str,
        raw_reference: str = ""
    ) -> NormalizedResult:
        return NormalizedResult(
            source=self.name,
            source_type=self.category,
            query=query,
            entity_type=entity_type,
            entity=entity,
            attribute=attribute,
            value=value,
            url=url,
            timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=max(0.0, min(1.0, confidence)),
            status=status,
            evidence=evidence,
            raw_reference=raw_reference
        )
