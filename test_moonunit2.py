#!/usr/bin/env python3
"""
Comprehensive test suite for MOONUNIT2 CLI and agent framework.
Run: python3 test_moonunit2.py
"""

import sys
import json
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all imports work."""
    print("🧪 Testing imports...")
    try:
        import agent_visibility
        import autonomous_toolkit
        import ux_behavior_optimizer
        import agent_orchestrator
        print("✅ All imports successful\n")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}\n")
        return False


def test_visibility():
    """Test visibility system."""
    print("🧪 Testing visibility system...")
    from agent_visibility import visibility, ToolExecution
    
    # Test tool recording
    visibility.record_tool(
        tool_name="test_tool",
        inputs={"input": "test"},
        outputs={"output": "result"},
        status="success",
        latency_ms=100,
        reasoning="Testing"
    )
    
    # Test snapshot
    snapshot = visibility.get_snapshot(5)
    assert "recent_tools" in snapshot
    assert len(snapshot["recent_tools"]) > 0
    print("  ✓ Tool recording")
    
    # Test state tracking
    visibility.record_state(
        phase="testing",
        active_context=["test_context"],
        tool_stack=["test_tool"],
        next_action="Test action",
        confidence=0.95,
        reason="Unit testing"
    )
    
    assert snapshot.get("current_phase") or visibility.state_history[-1].phase == "testing"
    print("  ✓ State tracking")
    
    # Test explanation
    explanation = visibility.explain_current_state()
    assert "Phase:" in explanation
    print("  ✓ Explanation generation")
    
    print("✅ Visibility system passed\n")
    return True


def test_toolkit():
    """Test autonomous toolkit."""
    print("🧪 Testing autonomous toolkit...")
    from autonomous_toolkit import toolkit
    
    # Test tool detection
    needed = toolkit.detect_needed_tools("Scrape the website for data")
    assert "web_scraper" in needed
    print("  ✓ Tool detection")
    
    # Test tool creation
    created = toolkit.ensure_tools(["web_scraper"])
    assert "web_scraper" in toolkit.manifest["tools"]
    print("  ✓ Tool creation")
    
    # Test tool listing
    tools = toolkit.list_tools()
    assert len(tools) > 0
    print("  ✓ Tool listing")
    
    # Test workflow suggestion
    workflow = toolkit.auto_suggest_workflow("Generate HTML and CSS")
    assert "steps" in workflow
    print("  ✓ Workflow suggestion")
    
    print("✅ Autonomous toolkit passed\n")
    return True


def test_ux_optimizer():
    """Test UX behavior optimizer."""
    print("🧪 Testing UX behavior optimizer...")
    from ux_behavior_optimizer import optimizer, Interaction
    import time
    
    # Log interaction
    interaction = Interaction(
        timestamp=time.time(),
        interaction_type="test",
        tool_used="web_scraper",
        duration_ms=500,
        success=True,
        feedback_score=4.5,
        sentiment="positive"
    )
    optimizer.log_interaction(interaction)
    print("  ✓ Interaction logging")
    
    # Test recommendation
    recommended = optimizer.get_recommended_tool("scraping", ["web_scraper", "api_client"])
    assert recommended == "web_scraper"
    print("  ✓ Tool recommendation")
    
    # Test response format
    fmt = optimizer.get_response_format()
    assert "max_tokens" in fmt
    print("  ✓ Response format")
    
    # Test auto-execute decision
    should_execute = optimizer.should_auto_execute(0.95, is_dangerous=False)
    print("  ✓ Auto-execute decision")
    
    # Test analysis
    analysis = optimizer.analyze_task_success_rate(24)
    assert "success_rate" in analysis
    print("  ✓ Success analysis")
    
    print("✅ UX optimizer passed\n")
    return True


def test_orchestrator():
    """Test agent orchestrator."""
    print("🧪 Testing agent orchestrator...")
    from agent_orchestrator import orchestrator
    
    # Test request analysis
    plan = orchestrator.analyze_request("Create a login form")
    assert "detected_tools" in plan
    print("  ✓ Request analysis")
    
    # Test execution
    result = orchestrator.execute_plan(plan)
    assert "status" in result
    print("  ✓ Execution")
    
    # Test response generation
    response = orchestrator.generate_response(plan, result)
    assert "Agent Execution Report" in response
    print("  ✓ Response generation")
    
    # Test dashboard
    dashboard = orchestrator.generate_status_dashboard()
    assert "DASHBOARD" in dashboard
    print("  ✓ Dashboard generation")
    
    print("✅ Orchestrator passed\n")
    return True


def test_full_cycle():
    """Test complete agent cycle."""
    print("🧪 Testing full execution cycle...")
    from agent_orchestrator import orchestrator
    
    result = orchestrator.run_full_cycle("Test request for HTML generation")
    
    assert "request" in result
    assert "plan" in result
    assert "execution" in result
    assert "response" in result
    
    print("✅ Full cycle passed\n")
    return True


def test_config_persistence():
    """Test config persistence."""
    print("🧪 Testing config persistence...")
    from pathlib import Path
    
    config_dir = Path.home() / ".moonunit2"
    assert config_dir.exists()
    print("  ✓ Config directory exists")
    
    assert (config_dir / "tools").exists()
    assert (config_dir / "ux-behavior").exists()
    print("  ✓ Subdirectories exist")
    
    print("✅ Config persistence passed\n")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("🤖 MOONUNIT1 COMPREHENSIVE TEST SUITE")
    print("="*50 + "\n")
    
    tests = [
        test_imports,
        test_visibility,
        test_toolkit,
        test_ux_optimizer,
        test_orchestrator,
        test_full_cycle,
        test_config_persistence,
    ]
    
    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append((test_func.__name__, passed))
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}\n")
            results.append((test_func.__name__, False))
    
    # Summary
    print("="*50)
    print("📊 TEST RESULTS")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}  {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
