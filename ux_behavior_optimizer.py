#!/usr/bin/env python3
"""
ux-behavior-optimizer.py
AI learns from user behavior, adapts UX, optimizes workflows in real-time.

Tracks:
  - User interaction patterns (clicks, time-on-task, retry patterns)
  - Preference learning (preferred tools, response formats, complexity levels)
  - Task completion metrics (success rate, time to completion)
  - Sentiment & satisfaction signals (via prompts, explicit feedback)
  - A/B testing (different approaches, measure which works best)
  - Behavioral adaptation (auto-adjust based on what worked)

Learns:
  - Which tools user prefers for different tasks
  - Optimal response length/complexity for this user
  - Best time to suggest actions vs wait for confirmation
  - When to provide verbose explanation vs quick answer
  - Workflow chains that this user responds best to
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict
import statistics

CONFIG_DIR = Path.home() / ".moonunit2"
UX_DIR = CONFIG_DIR / "ux-behavior"
BEHAVIOR_LOG = UX_DIR / "behavior.jsonl"
PREFERENCES_FILE = UX_DIR / "user-preferences.json"
METRICS_FILE = UX_DIR / "ux-metrics.json"

UX_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Interaction:
    """Single user interaction."""
    timestamp: float
    interaction_type: str  # request, response, action, feedback, error
    tool_used: Optional[str] = None
    duration_ms: float = 0
    success: bool = True
    feedback_score: Optional[float] = None  # 0-5
    sentiment: Optional[str] = None  # positive, neutral, negative
    user_clarifications: int = 0  # How many times user had to clarify
    metadata: Dict = None
    
    def to_dict(self):
        d = asdict(self)
        d["metadata"] = d.get("metadata") or {}
        return d


@dataclass
class UserPreferences:
    """Learned user preferences."""
    response_length: str  # concise, medium, verbose
    explanation_depth: str  # minimal, standard, detailed
    auto_execute: bool  # Execute tools without asking
    preferred_tools: List[str]  # Tools user prefers
    disliked_tools: List[str]  # Tools user avoids
    preferred_workflows: List[str]  # Workflows this user likes
    confidence_threshold: float  # 0-1, only execute if confidence > threshold
    retry_patience: int  # How many retries before giving up
    
    def to_dict(self):
        return asdict(self)


class UXBehaviorOptimizer:
    """Learn from user behavior, optimize UX in real-time."""
    
    def __init__(self):
        self.interactions: List[Interaction] = []
        self.preferences = self._load_preferences()
        self.metrics = defaultdict(lambda: {"count": 0, "success": 0, "total_time": 0})
        self.ab_tests = {}
        self._load_history()
    
    def _load_history(self):
        """Load interaction history."""
        if BEHAVIOR_LOG.exists():
            with open(BEHAVIOR_LOG, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        self.interactions.append(Interaction(**data))
                    except:
                        pass
    
    def _load_preferences(self) -> UserPreferences:
        """Load learned preferences."""
        if PREFERENCES_FILE.exists():
            with open(PREFERENCES_FILE) as f:
                data = json.load(f)
                return UserPreferences(**data)
        return UserPreferences(
            response_length="medium",
            explanation_depth="standard",
            auto_execute=False,
            preferred_tools=[],
            disliked_tools=[],
            preferred_workflows=[],
            confidence_threshold=0.7,
            retry_patience=3
        )
    
    def _save_preferences(self):
        """Persist learned preferences."""
        with open(PREFERENCES_FILE, 'w') as f:
            json.dump(self.preferences.to_dict(), f, indent=2)
    
    def log_interaction(self, interaction: Interaction):
        """Record user interaction."""
        self.interactions.append(interaction)
        with open(BEHAVIOR_LOG, 'a') as f:
            f.write(json.dumps(interaction.to_dict()) + "\n")
        
        # Update metrics
        tool = interaction.tool_used or "general"
        self.metrics[tool]["count"] += 1
        if interaction.success:
            self.metrics[tool]["success"] += 1
        self.metrics[tool]["total_time"] += interaction.duration_ms
    
    def record_feedback(self, task_id: str, score: float, sentiment: str, comment: str = ""):
        """User provides explicit feedback (1-5 stars)."""
        # Find related interaction
        recent = [i for i in self.interactions[-10:] if i.metadata and i.metadata.get("task_id") == task_id]
        if recent:
            recent[-1].feedback_score = score
            recent[-1].sentiment = sentiment
            self.log_interaction(recent[-1])
            
            # Learn from feedback
            self._learn_from_feedback(score, sentiment, recent[-1])
    
    def _learn_from_feedback(self, score: float, sentiment: str, interaction: Interaction):
        """Extract learning from user feedback."""
        if score >= 4:  # User happy
            if interaction.tool_used and interaction.tool_used not in self.preferences.preferred_tools:
                self.preferences.preferred_tools.append(interaction.tool_used)
        
        elif score <= 2:  # User unhappy
            if interaction.tool_used and interaction.tool_used not in self.preferences.disliked_tools:
                self.preferences.disliked_tools.append(interaction.tool_used)
        
        self._save_preferences()
    
    def get_recommended_tool(self, task_type: str, available_tools: List[str]) -> Optional[str]:
        """Recommend best tool based on learned preferences."""
        # Filter out disliked tools
        candidates = [t for t in available_tools if t not in self.preferences.disliked_tools]
        
        # Prioritize preferred tools
        preferred = [t for t in candidates if t in self.preferences.preferred_tools]
        
        if preferred:
            return preferred[0]
        
        # Otherwise pick by success rate
        best_tool = None
        best_success_rate = 0
        
        for tool in candidates:
            if tool in self.metrics:
                rate = self.metrics[tool]["success"] / self.metrics[tool]["count"]
                if rate > best_success_rate:
                    best_success_rate = rate
                    best_tool = tool
        
        return best_tool or (candidates[0] if candidates else None)
    
    def should_auto_execute(self, confidence: float, is_dangerous: bool) -> bool:
        """Decide whether to auto-execute tool."""
        if is_dangerous:
            return False  # Never auto-execute dangerous operations
        return confidence >= self.preferences.confidence_threshold and self.preferences.auto_execute
    
    def get_response_format(self) -> Dict[str, Any]:
        """Get format for response based on learned preferences."""
        return {
            "max_tokens": {"concise": 256, "medium": 512, "verbose": 1024}[self.preferences.response_length],
            "explanation_depth": self.preferences.explanation_depth,
            "include_reasoning": self.preferences.explanation_depth != "minimal",
            "include_alternatives": self.preferences.explanation_depth == "detailed"
        }
    
    def analyze_task_success_rate(self, window_hours: int = 24) -> Dict:
        """Analyze success rate over time window."""
        cutoff = time.time() - (window_hours * 3600)
        recent = [i for i in self.interactions if i.timestamp > cutoff]
        
        if not recent:
            return {}
        
        success_count = sum(1 for i in recent if i.success)
        total = len(recent)
        
        avg_time = statistics.mean([i.duration_ms for i in recent]) if recent else 0
        clarifications = sum(i.user_clarifications for i in recent)
        
        return {
            "window_hours": window_hours,
            "total_interactions": total,
            "success_count": success_count,
            "success_rate": success_count / total if total > 0 else 0,
            "avg_duration_ms": avg_time,
            "total_clarifications": clarifications,
            "clarification_rate": clarifications / total if total > 0 else 0,
            "recommendation": self._make_optimization_recommendation(success_count / total if total > 0 else 0, clarifications / total if total > 0 else 0)
        }
    
    def _make_optimization_recommendation(self, success_rate: float, clarification_rate: float) -> str:
        """Suggest UX optimizations."""
        if success_rate < 0.7 and clarification_rate > 0.3:
            return "Increase explanation depth to reduce clarifications"
        elif success_rate < 0.7:
            return "Review tool selection strategy, too many failures"
        elif clarification_rate > 0.5:
            return "Make responses more concise, user is clarifying often"
        elif success_rate > 0.9 and self.preferences.response_length == "verbose":
            return "Can reduce response length without affecting success"
        return "Performance is good, no major optimizations needed"
    
    def start_ab_test(self, test_id: str, variant_a_func, variant_b_func):
        """Start A/B test between two approaches."""
        self.ab_tests[test_id] = {
            "created": datetime.now().isoformat(),
            "variant_a": {"func": variant_a_func, "results": []},
            "variant_b": {"func": variant_b_func, "results": []},
            "winner": None
        }
    
    def record_ab_result(self, test_id: str, variant: str, success: bool, duration_ms: float, user_feedback: Optional[float] = None):
        """Record A/B test result."""
        if test_id in self.ab_tests:
            self.ab_tests[test_id][f"variant_{variant}"]["results"].append({
                "success": success,
                "duration_ms": duration_ms,
                "feedback": user_feedback,
                "timestamp": time.time()
            })
    
    def get_ab_winner(self, test_id: str) -> Optional[str]:
        """Determine winner of A/B test."""
        if test_id not in self.ab_tests or not self.ab_tests[test_id]["variant_a"]["results"]:
            return None
        
        results_a = self.ab_tests[test_id]["variant_a"]["results"]
        results_b = self.ab_tests[test_id]["variant_b"]["results"]
        
        if not results_b:
            return "a"
        
        success_a = sum(1 for r in results_a if r["success"]) / len(results_a)
        success_b = sum(1 for r in results_b if r["success"]) / len(results_b)
        
        avg_feedback_a = statistics.mean([r["feedback"] for r in results_a if r["feedback"]]) if any(r["feedback"] for r in results_a) else 0
        avg_feedback_b = statistics.mean([r["feedback"] for r in results_b if r["feedback"]]) if any(r["feedback"] for r in results_b) else 0
        
        # Winner by success rate + user feedback
        score_a = success_a * 0.7 + (avg_feedback_a / 5 if avg_feedback_a else 0) * 0.3
        score_b = success_b * 0.7 + (avg_feedback_b / 5 if avg_feedback_b else 0) * 0.3
        
        return "a" if score_a >= score_b else "b"
    
    def generate_optimization_report(self) -> Dict:
        """Generate comprehensive UX optimization report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "user_preferences": self.preferences.to_dict(),
            "metrics": {
                tool: {
                    "count": data["count"],
                    "success_rate": data["success"] / data["count"] if data["count"] > 0 else 0,
                    "avg_duration": data["total_time"] / data["count"] if data["count"] > 0 else 0
                }
                for tool, data in self.metrics.items()
            },
            "recent_analysis": self.analyze_task_success_rate(24),
            "ab_tests": {
                test_id: {
                    "created": test["created"],
                    "variant_a_samples": len(test["variant_a"]["results"]),
                    "variant_b_samples": len(test["variant_b"]["results"]),
                    "winner": self.get_ab_winner(test_id)
                }
                for test_id, test in self.ab_tests.items()
            }
        }
    
    def save_optimization_report(self):
        """Save report to file."""
        report = self.generate_optimization_report()
        with open(METRICS_FILE, 'w') as f:
            json.dump(report, f, indent=2)
        return report


# Global optimizer
optimizer = UXBehaviorOptimizer()


if __name__ == "__main__":
    # Example usage
    print("📊 UX Behavior Optimizer")
    
    # Simulate interactions
    i1 = Interaction(
        timestamp=time.time(),
        interaction_type="request",
        tool_used="web_scraper",
        duration_ms=1200,
        success=True,
        feedback_score=4.5,
        sentiment="positive",
        metadata={"task_id": "task_001"}
    )
    
    optimizer.log_interaction(i1)
    print(f"✅ Logged interaction: {i1.tool_used}")
    
    # Get recommendations
    recommended = optimizer.get_recommended_tool("web_scraping", ["web_scraper", "api_client"])
    print(f"🎯 Recommended tool: {recommended}")
    
    # Generate report
    report = optimizer.generate_optimization_report()
    print(f"📈 Report:")
    print(json.dumps(report, indent=2))
