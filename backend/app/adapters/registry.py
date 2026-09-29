from typing import Dict, List, Optional
from backend.app.adapters.base import BaseAdapter

class ToolRegistry:
    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}

    def register(self, adapter: BaseAdapter):
        self._adapters[adapter.name.lower().replace(" ", "_")] = adapter

    def get(self, adapter_id: str) -> Optional[BaseAdapter]:
        return self._adapters.get(adapter_id)

    def list_all(self) -> List[BaseAdapter]:
        return list(self._adapters.values())

    def get_stats(self) -> List[Dict]:
        return [adapter.get_stats() for adapter in self._adapters.values()]

    def toggle(self, adapter_id: str, enabled: bool) -> bool:
        adapter = self._adapters.get(adapter_id)
        if adapter:
            adapter.enabled = enabled
            return True
        return False

tool_registry = ToolRegistry()
