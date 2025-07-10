#!/usr/bin/env python3
"""
Test MCP tool functionality without calling decorated functions directly
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_mcp_tools():
    """Test that MCP tools are properly registered"""
    from server import memory, mcp, BRAVE_TOKEN

    print("🧪 Testing MCP tool functionality...")

    # Test 1: Check tool registration
    print("\n1. Checking MCP tool registration...")
    try:
        # FastMCP doesn't have list_tools(), but we can check if tools are defined
        from server import save_memory, query_memory, web_search

        print("✓ MCP tools imported successfully:")
        print("  - save_memory")
        print("  - query_memory")
        print("  - web_search")
    except Exception as e:
        print(f"✗ Failed to import tools: {e}")
        import traceback

        traceback.print_exc()

    # Test 2: Test underlying memory functionality
    print("\n2. Testing memory functionality...")
    try:
        # Add a test memory
        idx = memory.add("Test memory from MCP tool test")
        print(f"✓ Memory saved with index: {idx}")

        # Retrieve it
        retrieved = memory.get(idx)
        if retrieved:
            print(f"✓ Memory retrieved: {retrieved[:50]}...")
        else:
            print(f"✗ Could not retrieve memory #{idx}")
    except Exception as e:
        print(f"✗ Memory test failed: {e}")

    # Test 3: Check Brave API configuration
    print("\n3. Checking web_search readiness...")
    if BRAVE_TOKEN:
        print("✓ BRAVE_API_KEY is configured")
    else:
        print("✗ BRAVE_API_KEY is not set (web_search will fail)")

    # Test 4: Show memory database status
    print("\n4. Memory database status:")
    try:
        count = memory.col.count()
        print(f"✓ Total memories stored: {count}")
        print(f"✓ Database path: {memory.db_path}")
        print(f"✓ Next memory index: {memory.next_index}")
    except Exception as e:
        print(f"✗ Failed to get memory status: {e}")


if __name__ == "__main__":
    test_mcp_tools()
    print("\n🎉 MCP tool test completed!")
