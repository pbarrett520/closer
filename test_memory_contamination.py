#!/usr/bin/env python3
"""
Phase 1: Demonstrate Memory Contamination Problem
===============================================

This test file contains FAILING tests that prove memory contamination exists.
These tests are designed to fail and demonstrate the problem before we fix it.

The contamination issue: Test scripts add garbage data like "Test memory: user loves diamonds"
which drowns out real emotional memories when users query for their personal experiences.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def setup_memory_system():
    """Setup access to the development memory system for testing"""
    try:
        from dev_server import memory

        return memory
    except Exception as e:
        print(f"X Failed to import memory system: {e}")
        return None


def is_test_memory(memory_text: str) -> bool:
    """
    Detect if a memory entry is test data contamination

    Test data patterns we're looking for:
    - "Test memory"
    - "test" (generic test mentions)
    - "diamonds" (from test_memory.py)
    - "MCP tool test" (from test_mcp_tools.py)
    """
    test_patterns = [
        "Test memory",
        "test memory",
        "MCP tool test",
        "user loves diamonds",
        "This is a test",
        "integration testing",
        "for testing",
    ]

    text_lower = memory_text.lower()
    return any(pattern.lower() in text_lower for pattern in test_patterns)


def get_all_memories(memory_store) -> List[Dict[str, Any]]:
    """Get all memories from the memory store for analysis"""
    try:
        count = memory_store.col.count()
        if count == 0:
            return []

        # Get all items with metadata
        all_items = memory_store.col.get(include=["metadatas"])

        if not all_items["metadatas"]:
            return []

        memories = []
        for meta in all_items["metadatas"]:
            memories.append(
                {
                    "text": meta.get("text", ""),
                    "idx": meta.get("idx", -1),
                    "saved_at": meta.get("ts", ""),
                    "is_test": is_test_memory(meta.get("text", "")),
                }
            )

        return memories

    except Exception as e:
        print(f"X Error getting all memories: {e}")
        return []


def find_test_contamination(memory_store) -> List[Dict[str, Any]]:
    """Find all test data contamination in the memory store"""
    all_memories = get_all_memories(memory_store)
    return [m for m in all_memories if m["is_test"]]


# ==============================================================================
# FAILING TESTS - These should fail to demonstrate the contamination problem
# ==============================================================================


def test_memory_contamination_detection():
    """
    RED TEST: Should find test data contamination in production memory

    This test is EXPECTED TO FAIL - it demonstrates the contamination problem.
    """
    print("\n[RED] TEST: Memory Contamination Detection")
    print("=" * 50)

    memory = setup_memory_system()
    if not memory:
        print("X Cannot run test - memory system not available")
        return False

    # Find contamination
    contaminated_memories = find_test_contamination(memory)

    print(f"Found {len(contaminated_memories)} contaminated memories:")
    for i, mem in enumerate(contaminated_memories[:5]):  # Show first 5
        print(f"  {i+1}. {mem['text'][:60]}...")

    # This assertion should FAIL if contamination exists
    try:
        assert (
            len(contaminated_memories) == 0
        ), f"Expected no contamination, found {len(contaminated_memories)} test memories"
        print("+ UNEXPECTED: No contamination found")
        return True
    except AssertionError as e:
        print(f"- EXPECTED FAILURE: {e}")
        return False


def test_memory_retrieval_accuracy():
    """
    RED TEST: Should demonstrate that real memories are drowned out by test data

    This test simulates the user experience where they ask about real memories
    but get test garbage instead.
    """
    print("\n[RED] TEST: Memory Retrieval Accuracy")
    print("=" * 50)

    memory = setup_memory_system()
    if not memory:
        print("X Cannot run test - memory system not available")
        return False

    # Add a real memory that should be easily found
    real_memory = "User reveals origin of loneliness: bullied for liking Warhammer in 6th grade, formative wound"
    memory_idx = memory.add(real_memory)
    print(f"Added real memory with index: {memory_idx}")

    # Test various queries that should find the real memory
    test_queries = [
        ("6th grade", "should find bullying trauma"),
        ("warhammer", "should find Warhammer context"),
        ("bullied", "should find bullying experience"),
        ("loneliness", "should find loneliness origin"),
    ]

    failures = []

    for query, expectation in test_queries:
        print(f"\nTesting query: '{query}' ({expectation})")

        results = memory.query(query, k=5)

        if not results:
            failures.append(f"Query '{query}' returned no results")
            continue

        # Check if real memory is in results
        real_memory_found = any(
            "bullied for liking Warhammer" in r.get("text", "") for r in results
        )

        # Check if test garbage is dominating results
        test_memory_found = any(is_test_memory(r.get("text", "")) for r in results)

        print(f"  Results: {len(results)} memories")
        print(f"  Real memory found: {real_memory_found}")
        print(f"  Test contamination in results: {test_memory_found}")

        if results:
            print(f"  Top result: {results[0].get('text', '')[:60]}...")
            print(f"  Top relevance: {results[0].get('relevance', 0):.3f}")

        if not real_memory_found:
            failures.append(f"Query '{query}' did not find real memory")

        if test_memory_found:
            failures.append(f"Query '{query}' returned test contamination")

    # Clean up our test memory
    try:
        if memory_idx >= 0:
            # Remove the memory we added for testing
            vid = memory.id_map.get(memory_idx)
            if vid:
                memory.col.delete(ids=[vid])
                del memory.id_map[memory_idx]
                memory._save_index()
    except Exception as e:
        print(f"Warning: Could not clean up test memory: {e}")

    # This test should FAIL if contamination is affecting retrieval
    if failures:
        print(f"\n- EXPECTED FAILURES ({len(failures)}):")
        for failure in failures:
            print(f"  - {failure}")
        return False
    else:
        print("\n+ UNEXPECTED: All queries worked correctly")
        return True


def test_relevance_score_degradation():
    """
    RED TEST: Should show that test contamination degrades relevance scores

    When test data dominates the database, real queries get poor relevance scores.
    """
    print("\n[RED] TEST: Relevance Score Degradation")
    print("=" * 50)

    memory = setup_memory_system()
    if not memory:
        print("X Cannot run test - memory system not available")
        return False

    # Get baseline stats
    all_memories = get_all_memories(memory)
    contaminated_memories = [m for m in all_memories if m["is_test"]]
    real_memories = [m for m in all_memories if not m["is_test"]]

    print(f"Memory Database Stats:")
    print(f"  Total memories: {len(all_memories)}")
    print(f"  Contaminated memories: {len(contaminated_memories)}")
    print(f"  Real memories: {len(real_memories)}")
    if len(all_memories) > 0:
        print(
            f"  Contamination ratio: {len(contaminated_memories) / len(all_memories) * 100:.1f}%"
        )

    # Test a query that should not match test data
    query = "emotional vulnerability childhood trauma"
    results = memory.query(query, k=5)

    print(f"\nQuery: '{query}'")
    print(f"Results: {len(results)}")

    if results:
        for i, result in enumerate(results):
            is_contaminated = is_test_memory(result.get("text", ""))
            print(
                f"  {i+1}. {'[TEST]' if is_contaminated else '[REAL]'} {result.get('text', '')[:50]}..."
            )
            print(f"      Relevance: {result.get('relevance', 0):.3f}")

    # Check if test contamination is appearing in results
    test_results = [r for r in results if is_test_memory(r.get("text", ""))]

    if test_results:
        print(
            f"\n- EXPECTED FAILURE: Found {len(test_results)} test contamination entries in results"
        )
        print("This proves test data is interfering with real memory retrieval")
        return False
    else:
        print("\n+ UNEXPECTED: No test contamination in results")
        return True


def run_contamination_demonstration():
    """Run all contamination demonstration tests"""
    print("[TEST] PHASE 1: Demonstrating Memory Contamination Problem")
    print("=" * 60)
    print(
        "These tests are EXPECTED TO FAIL - they prove the contamination problem exists"
    )
    print()

    tests = [
        test_memory_contamination_detection,
        test_memory_retrieval_accuracy,
        test_relevance_score_degradation,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"X Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print("PHASE 1 RESULTS:")
    print(f"Tests that failed as expected: {results.count(False)}")
    print(f"Tests that unexpectedly passed: {results.count(True)}")

    if results.count(False) > 0:
        print("\n+ SUCCESS: Tests failed as expected, proving contamination exists")
        print("Ready to proceed to Phase 2: Memory Store Isolation")
        return True
    else:
        print("\n! UNEXPECTED: All tests passed - contamination may not exist")
        return False


if __name__ == "__main__":
    success = run_contamination_demonstration()
    sys.exit(0 if success else 1)
