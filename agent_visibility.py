#!/usr/bin/env python3
"""
agent-visibility.py
Deep observability into agent state, execution, and context.
Powers "read into what's happening at any given time"

Tracks:
  - Tool execution flow (what ran, when, inputs/outputs)
  - Agent state transitions (thinking → acting → waiting)
  - Context snapshots (active memory, priorities)
  - Decision reasoning (why this tool? why this path?)
  - Performance metrics (latency, token usage, cache hits)
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict

# Paths
CONFIG_DIR = Path.home() / ".moonunit2"
VISIBILITY_LOG = CONFIG_DIR / "visibility.jsonl"
METRICS_FILE = CONFIG_DIR / "metrics.json"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ToolExecution:
    """Single tool invocation snapshot."""
    tool_name: str
    tool_id: str
    timestamp: float
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    status: str  # pending, running, success, error
    latency_ms: float
    error: Optional[str] = None
    reasoning: Optional[str] = None  # Why was this tool chosen?
    
    def to_dict(self):
        return asdict(self)


@dataclass
class AgentState:
    """Snapshot of agent state at any moment."""
    timestamp: float
    phase: str  # thinking, acting, waiting, deciding
    active_context: List[str]  # Current memory keys in use
    tool_stack: List[str]  # Tools being executed in sequence
    next_action: Optional[str]  # What agent plans to do next
    confidence: float  # 0-1 confidence in current path
    reason: str  # Plain English explanation of state
    
    def to_dict(self):
        return asdict(self)


class Visibility:
    """Deep introspection into agent execution."""
    
    def __init__(self):
        self.tool_history: List[ToolExecution] = []
        self.state_history: List[AgentState] = []
        self.metrics = defaultdict(lambda: {"count": 0, "total_latency": 0})
        self.current_reasoning = ""
        self._load_history()
    
    def _load_history(self):
        """Load existing visibility logs."""
        if VISIBILITY_LOG.exists():
            with open(VISIBILITY_LOG, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "tool":
                            exec_data = data.get("execution", {})
                            self.tool_history.append(ToolExecution(**exec_data))
                        elif data.get("type") == "state":
                            state_data = data.get("state", {})
                            self.state_history.append(AgentState(**state_data))
                    except:
                        pass
    
    def record_tool(self, tool_name: str, inputs: Dict, outputs: Dict,
                   status: str = "success", latency_ms: float = 0,
                   error: Optional[str] = None, reasoning: Optional[str] = None):
        """Record tool execution."""
        exec_obj = ToolExecution(
            tool_name=tool_name,
            tool_id=f"{tool_name}_{int(time.time() * 1000)}",
            timestamp=time.time(),
            inputs=inputs,
            outputs=outputs,
            status=status,
            latency_ms=latency_ms,
            error=error,
            reasoning=reasoning or self.current_reasoning
        )
        self.tool_history.append(exec_obj)
        self._append_log({"type": "tool", "execution": exec_obj.to_dict()})
        
        # Update metrics
        self.metrics[tool_name]["count"] += 1
        self.metrics[tool_name]["total_latency"] += latency_ms
    
    def record_state(self, phase: str, active_context: List[str],
                    tool_stack: List[str], next_action: Optional[str],
                    confidence: float, reason: str):
        """Record agent state transition."""
        state_obj = AgentState(
            timestamp=time.time(),
            phase=phase,
            active_context=active_context,
            tool_stack=tool_stack,
            next_action=next_action,
            confidence=confidence,
            reason=reason
        )
        self.state_history.append(state_obj)
        self._append_log({"type": "state", "state": state_obj.to_dict()})
    
    def set_reasoning(self, reason: str):
        """Set reasoning for next tool call."""
        self.current_reasoning = reason
    
    def _append_log(self, record: Dict):
        """Append to visibility log."""
        with open(VISIBILITY_LOG, 'a') as f:
            f.write(json.dumps(record) + "\n")
    
    def get_snapshot(self, last_n: int = 10) -> Dict:
        """Get current state snapshot (last N events)."""
        return {
            "timestamp": time.time(),
            "recent_tools": [t.to_dict() for t in self.tool_history[-last_n:]],
            "recent_states": [s.to_dict() for s in self.state_history[-last_n:]],
            "metrics_summary": {k: {
                "count": v["count"],
                "avg_latency": v["total_latency"] / v["count"] if v["count"] > 0 else 0
            } for k, v in self.metrics.items()},
            "current_phase": self.state_history[-1].phase if self.state_history else "unknown"
        }
    
    def explain_current_state(self) -> str:
        """Generate human-readable explanation of what's happening."""
        if not self.state_history:
            return "Agent not started yet."
        
        latest_state = self.state_history[-1]
        latest_tool = self.tool_history[-1] if self.tool_history else None
        
        lines = [
            f"📊 Agent Status",
            f"  Phase: {latest_state.phase}",
            f"  Confidence: {latest_state.confidence * 100:.0f}%",
            f"  Reason: {latest_state.reason}",
            "",
            f"🔧 Recent Activity",
        ]
        
        if latest_tool:
            lines.append(f"  Last tool: {latest_tool.tool_name}")
            lines.append(f"  Status: {latest_tool.status}")
            lines.append(f"  Latency: {latest_tool.latency_ms:.1f}ms")
            if latest_tool.error:
                lines.append(f"  Error: {latest_tool.error}")
        
        lines.extend([
            "",
            f"🧠 Active Context",
        ])
        for ctx in latest_state.active_context[:5]:
            lines.append(f"  - {ctx}")
        
        if latest_state.next_action:
            lines.extend([
                "",
                f"➡️  Next Action",
                f"  {latest_state.next_action}"
            ])
        
        return "\n".join(lines)
    
    def save_metrics(self):
        """Save metrics snapshot."""
        with open(METRICS_FILE, 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "metrics": {k: {
                    "count": v["count"],
                    "total_latency": v["total_latency"],
                    "avg_latency": v["total_latency"] / v["count"] if v["count"] > 0 else 0
                } for k, v in self.metrics.items()},
                "total_tools_run": len(self.tool_history),
                "total_state_changes": len(self.state_history)
            }, f, indent=2)


# Global visibility instance
visibility = Visibility()


def print_visibility():
    """Print current agent visibility."""
    print(visibility.explain_current_state())


if __name__ == "__main__":
    print_visibility()
