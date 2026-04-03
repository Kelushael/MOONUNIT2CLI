#!/usr/bin/env python3
"""
agent-orchestrator.py
Master orchestrator that ties everything together:
  ✅ Deep visibility (what's happening)
  ✅ Autonomous toolkit (auto-create tools)
  ✅ UX optimization (learn from user)
  ✅ Config auto-update (persist everything)

Agent flow:
  1. User request → visibility logs it
  2. Agent analyzes needed tools → toolkit auto-creates
  3. Agent executes with visibility tracking
  4. UX optimizer learns from outcome
  5. Config auto-updates for next time
  6. Agent explains what happened
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import our systems
import sys
sys.path.insert(0, str(Path(__file__).parent))

try:
    from agent_visibility import visibility, Visibility, ToolExecution, AgentState
    from autonomous_toolkit import toolkit, ToolkitManager
    from ux_behavior_optimizer import optimizer, UXBehaviorOptimizer, Interaction
except ImportError as e:
    print(f"⚠️  Import error: {e}")


CONFIG_DIR = Path.home() / ".moonunit2"
ORCHESTRATOR_LOG = CONFIG_DIR / "orchestrator.jsonl"


class AgentOrchestrator:
    """Master orchestrator - brain of the autonomous agent."""
    
    def __init__(self):
        self.visibility = visibility
        self.toolkit = toolkit
        self.optimizer = optimizer
        self.execution_history = []
    
    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze request and prepare execution plan."""
        
        # Record state: analyzing
        self.visibility.record_state(
            phase="thinking",
            active_context=[user_request],
            tool_stack=[],
            next_action="Detect needed tools",
            confidence=1.0,
            reason="Parsing user request"
        )
        
        # Detect needed tools
        needed_tools = self.toolkit.detect_needed_tools(user_request)
        
        # Auto-create tools if missing
        created_tools = self.toolkit.ensure_tools(needed_tools)
        if created_tools:
            self.visibility.set_reasoning(f"Auto-created tools: {created_tools}")
        
        # Get UX preferences
        response_format = self.optimizer.get_response_format()
        
        # Get recommended execution approach
        recommended_tool = self.optimizer.get_recommended_tool(
            user_request.split()[0] if user_request else "general",
            needed_tools
        )
        
        plan = {
            "timestamp": time.time(),
            "request": user_request,
            "detected_tools": needed_tools,
            "created_tools": created_tools,
            "recommended_tool": recommended_tool,
            "response_format": response_format,
            "auto_execute": self.optimizer.should_auto_execute(
                confidence=0.8,  # Calculated based on context
                is_dangerous=False
            )
        }
        
        return plan
    
    def execute_plan(self, plan: Dict, agent=None) -> Dict[str, Any]:
        """Execute the plan using the real sovereign agent."""

        start_time = time.time()
        tool_name = plan.get("recommended_tool")

        # Record state: acting
        self.visibility.record_state(
            phase="acting",
            active_context=[plan["request"], tool_name or "unknown"],
            tool_stack=[tool_name] if tool_name else [],
            next_action=f"Execute via agent",
            confidence=0.8,
            reason=f"Routing to sovereign agent"
        )

        response = None
        status = "success"

        if agent is not None:
            # Use the real agent
            try:
                response = agent.send(plan["request"])
                status = "success" if response else "empty"
            except Exception as e:
                response = f"Error: {e}"
                status = "error"
        else:
            response = "[no agent instance — call execute_plan(plan, agent=agent)]"
            status = "no_agent"

        latency_ms = (time.time() - start_time) * 1000

        execution_result = {
            "tool": tool_name,
            "status": status,
            "response": response,
            "latency_ms": latency_ms,
        }

        # Record with visibility
        self.visibility.record_tool(
            tool_name=tool_name or "agent",
            inputs={"request": plan["request"]},
            outputs={"response": (response or "")[:200]},
            status=status,
            latency_ms=latency_ms,
            reasoning=f"User requested: {plan['request']}"
        )

        # Log interaction for UX learning
        interaction = Interaction(
            timestamp=time.time(),
            interaction_type="execution",
            tool_used=tool_name,
            duration_ms=latency_ms,
            success=status == "success",
            metadata={
                "request": plan["request"],
                "auto_created_tools": plan.get("created_tools", [])
            }
        )
        self.optimizer.log_interaction(interaction)

        return execution_result
    
    def generate_response(self, plan: Dict, execution_result: Dict) -> str:
        """Generate response in optimized format."""
        
        response_format = plan.get("response_format", {})
        
        lines = []
        
        # Title
        lines.append("🤖 Agent Execution Report")
        
        # What we detected
        tools = plan.get("detected_tools", [])
        if tools:
            lines.append(f"\n📦 Tools Detected: {', '.join(tools)}")
        
        # What we created
        created = plan.get("created_tools", [])
        if created:
            lines.append(f"✨ Auto-created: {', '.join(created)}")
        
        # What we executed
        lines.append(f"\n⚙️  Execution")
        lines.append(f"  Tool: {plan.get('recommended_tool', 'agent')}")
        lines.append(f"  Status: {execution_result.get('status', 'unknown')}")
        lines.append(f"  Latency: {execution_result.get('latency_ms', 0):.1f}ms")
        
        # Results
        if response_format.get("include_reasoning"):
            lines.append(f"\n💭 Reasoning")
            lines.append(f"  Used learned preferences from previous interactions")
            lines.append(f"  Selected tools based on success history")
        
        # Visibility
        lines.append(f"\n👁️  Agent Visibility")
        lines.append(f"  Recent state: {self.visibility.state_history[-1].phase if self.visibility.state_history else 'unknown'}")
        lines.append(f"  Tools executed: {len(self.visibility.tool_history)}")
        
        # UX optimization status
        analysis = self.optimizer.analyze_task_success_rate(1)
        if analysis:
            lines.append(f"\n📈 Performance")
            lines.append(f"  Success rate: {analysis.get('success_rate', 0) * 100:.0f}%")
            lines.append(f"  Optimization tip: {analysis.get('recommendation', 'Performing well')}")
        
        return "\n".join(lines)
    
    def run_full_cycle(self, user_request: str) -> Dict[str, Any]:
        """Run complete orchestration cycle."""
        
        print(f"\n🚀 Processing: {user_request}\n")
        
        # Phase 1: Analyze
        plan = self.analyze_request(user_request)
        
        # Phase 2: Execute
        result = self.execute_plan(plan)
        
        # Phase 3: Generate response
        response = self.generate_response(plan, result)
        
        print(response)
        
        # Phase 4: Save optimization data
        self.optimizer.save_optimization_report()
        
        return {
            "request": user_request,
            "plan": plan,
            "execution": result,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_status_dashboard(self) -> str:
        """Generate real-time dashboard of agent status."""
        
        lines = [
            "╔════════════════════════════════════════╗",
            "║  🤖 AUTONOMOUS AGENT DASHBOARD        ║",
            "╚════════════════════════════════════════╝",
            ""
        ]
        
        # Visibility status
        lines.append("📊 VISIBILITY")
        vis_snapshot = self.visibility.get_snapshot(5)
        lines.append(f"  Phase: {vis_snapshot.get('current_phase', 'unknown')}")
        lines.append(f"  Tools executed: {len(vis_snapshot.get('recent_tools', []))}")
        lines.append(f"  State changes: {len(vis_snapshot.get('recent_states', []))}")
        
        # Toolkit status
        lines.append("\n🧰 TOOLKIT")
        toolkit_tools = self.toolkit.list_tools()
        lines.append(f"  Tools available: {len(toolkit_tools)}")
        for name in list(toolkit_tools.keys())[:3]:
            lines.append(f"    ✓ {name}")
        
        # UX Optimization status
        lines.append("\n📈 UX OPTIMIZATION")
        ux_report = self.optimizer.generate_optimization_report()
        analysis = ux_report.get("recent_analysis", {})
        lines.append(f"  Success rate: {analysis.get('success_rate', 0) * 100:.0f}%")
        lines.append(f"  Interactions: {analysis.get('total_interactions', 0)}")
        lines.append(f"  Preferred tools: {len(self.optimizer.preferences.preferred_tools)}")
        
        # Config status
        lines.append("\n⚙️  CONFIG")
        lines.append(f"  Response length: {self.optimizer.preferences.response_length}")
        lines.append(f"  Explanation depth: {self.optimizer.preferences.explanation_depth}")
        lines.append(f"  Auto-execute: {self.optimizer.preferences.auto_execute}")
        
        return "\n".join(lines)
    
    def save_cycle_log(self, cycle_data: Dict):
        """Save cycle execution log."""
        with open(ORCHESTRATOR_LOG, 'a') as f:
            f.write(json.dumps(cycle_data) + "\n")


# Global orchestrator
orchestrator = AgentOrchestrator()


if __name__ == "__main__":
    # Example execution
    print(orchestrator.generate_status_dashboard())
    
    # Run example tasks
    tasks = [
        "Scrape weather data and generate a dashboard",
        "Create a responsive login form with CSS",
        "Fetch data from an API and build a workflow"
    ]
    
    for task in tasks[:1]:  # Run just first task for demo
        cycle = orchestrator.run_full_cycle(task)
