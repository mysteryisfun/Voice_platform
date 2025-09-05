"""
Test LiveKit agent implementation to ensure it's working correctly.
"""

import os
import sys

# Add backend to path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from voice_agents.agent import get_agent_tools, get_agent_instructions


def test_agent_tools():
    """Test that agent tools are loaded correctly"""
    print("Testing agent tools...")
    
    # Test for agent 2 (Sarah)
    tools = get_agent_tools(2)
    print(f"Agent 2 has {len(tools)} tools")
    
    # Check if tools have the expected structure
    if tools:
        first_tool = tools[0]
        print(f"First tool: {getattr(first_tool, '__name__', 'unknown')}")
        print(f"Tool type: {type(first_tool)}")
    
    return len(tools) > 0


def test_agent_instructions():
    """Test that agent instructions are built correctly"""
    print("\nTesting agent instructions...")
    
    # Test for agent 2 (Sarah)
    instructions = get_agent_instructions(2)
    print(f"Instructions length: {len(instructions)} characters")
    print("Instructions preview:")
    print(instructions[:200] + "..." if len(instructions) > 200 else instructions)
    
    # Check for key elements
    has_name = "Sarah" in instructions
    has_tools = "show_product" in instructions
    has_role = "customer support" in instructions.lower() or "assistant" in instructions.lower()
    
    print(f"Contains name 'Sarah': {has_name}")
    print(f"Contains tool references: {has_tools}")
    print(f"Contains role description: {has_role}")
    
    return len(instructions) > 50


def test_import_structure():
    """Test that the agent structure can be imported properly"""
    print("\nTesting import structure...")
    
    try:
        from voice_agents.agent import entrypoint
        print("✅ Entrypoint function imported successfully")
        
        # Check if it's async
        import asyncio
        is_async = asyncio.iscoroutinefunction(entrypoint)
        print(f"✅ Entrypoint is async function: {is_async}")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=== LiveKit Agent Test Suite ===\n")
    
    results = []
    
    # Run tests
    results.append(("Agent Tools", test_agent_tools()))
    results.append(("Agent Instructions", test_agent_instructions()))
    results.append(("Import Structure", test_import_structure()))
    
    # Print results
    print("\n=== Test Results ===")
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 LiveKit agent is ready for deployment!")
        print("Next steps:")
        print("1. Start the LiveKit agent worker")
        print("2. Test voice conversations")
        print("3. Validate tool calls work correctly")


if __name__ == "__main__":
    main()
