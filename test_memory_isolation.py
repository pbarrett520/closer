#!/usr/bin/env python3
"""
Phase 2: Memory Store Isolation Tests
====================================

This test file verifies that test and production memory stores are completely isolated.
These tests should PASS to prove the isolation is working correctly.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def setup_test_environment():
    """Set up test environment variables"""
    os.environ["TEST_ENV"] = "true"


def cleanup_test_environment():
    """Clean up test environment variables"""
    if "TEST_ENV" in os.environ:
        del os.environ["TEST_ENV"]


def test_environment_detection():
    """
    GREEN TEST: Test environment detection should work correctly
    """
    print("\n[GREEN] TEST: Environment Detection")
    print("=" * 50)

    try:
        from dev_server import MemoryStore

        # Test with explicit test mode
        test_store = MemoryStore(test_mode=True)
        prod_store = MemoryStore(test_mode=False)

        print(f"Test store is_test_env: {test_store.is_test_env}")
        print(f"Production store is_test_env: {prod_store.is_test_env}")
        print(f"Test store collection: {test_store.collection_name}")
        print(f"Production store collection: {prod_store.collection_name}")

        # Verify test environment detection
        assert (
            test_store.is_test_env == True
        ), "Test store should detect test environment"
        assert (
            prod_store.is_test_env == False
        ), "Production store should not detect test environment"

        # Verify different collection names
        assert (
            test_store.collection_name == "test_mem"
        ), f"Expected 'test_mem', got '{test_store.collection_name}'"
        assert (
            prod_store.collection_name == "closer_mem"
        ), f"Expected 'closer_mem', got '{prod_store.collection_name}'"

        print("+ Environment detection working correctly")
        return True

    except Exception as e:
        print(f"- Environment detection failed: {e}")
        return False


def test_database_path_isolation():
    """
    GREEN TEST: Test and production databases should use completely different paths
    """
    print("\n[GREEN] TEST: Database Path Isolation")
    print("=" * 50)

    try:
        from dev_server import create_test_memory_store, create_production_memory_store

        # Create both types of stores
        test_store = create_test_memory_store()
        prod_store = create_production_memory_store()

        print(f"Test database path: {test_store.db_path}")
        print(f"Production database path: {prod_store.db_path}")

        # Verify paths are different
        assert (
            test_store.db_path != prod_store.db_path
        ), "Test and production should use different database paths"

        # Verify test path contains "test"
        assert (
            "test" in str(test_store.db_path).lower()
        ), "Test path should contain 'test'"

        # Verify production path contains "closer"
        assert (
            "closer" in str(prod_store.db_path).lower()
        ), "Production path should contain 'closer'"

        # Verify paths exist and are writable
        assert test_store.db_path.exists(), "Test database path should exist"
        assert prod_store.db_path.exists(), "Production database path should exist"

        print("+ Database path isolation working correctly")
        return True

    except Exception as e:
        print(f"- Database path isolation failed: {e}")
        return False


def test_collection_isolation():
    """
    GREEN TEST: Test and production should use different ChromaDB collections
    """
    print("\n[GREEN] TEST: Collection Isolation")
    print("=" * 50)

    try:
        from dev_server import create_test_memory_store, create_production_memory_store

        # Create both types of stores
        test_store = create_test_memory_store()
        prod_store = create_production_memory_store()

        print(f"Test collection name: {test_store.collection_name}")
        print(f"Production collection name: {prod_store.collection_name}")

        # Verify different collection names
        assert (
            test_store.collection_name != prod_store.collection_name
        ), "Test and production should use different collections"
        assert (
            test_store.collection_name == "test_mem"
        ), "Test should use 'test_mem' collection"
        assert (
            prod_store.collection_name == "closer_mem"
        ), "Production should use 'closer_mem' collection"

        # Verify collections exist and are accessible
        test_count = test_store.col.count()
        prod_count = prod_store.col.count()

        print(f"Test collection count: {test_count}")
        print(f"Production collection count: {prod_count}")

        print("+ Collection isolation working correctly")
        return True

    except Exception as e:
        print(f"- Collection isolation failed: {e}")
        return False


def test_data_isolation():
    """
    GREEN TEST: Data added to test store should not appear in production and vice versa
    """
    print("\n[GREEN] TEST: Data Isolation")
    print("=" * 50)

    try:
        from dev_server import create_test_memory_store, create_production_memory_store

        # Create both types of stores
        test_store = create_test_memory_store()
        prod_store = create_production_memory_store()

        # Add unique data to each store
        test_memory = "TEST_UNIQUE_MEMORY_12345"
        prod_memory = "PROD_UNIQUE_MEMORY_67890"

        test_idx = test_store.add(test_memory)
        prod_idx = prod_store.add(prod_memory)

        print(f"Added test memory at index: {test_idx}")
        print(f"Added production memory at index: {prod_idx}")

        # Verify data is in the correct stores
        assert (
            test_store.get(test_idx) == test_memory
        ), "Test memory should be in test store"
        assert (
            prod_store.get(prod_idx) == prod_memory
        ), "Production memory should be in production store"

        # Verify data is NOT in the wrong stores
        test_store_prod_lookup = test_store.get(prod_idx)
        prod_store_test_lookup = prod_store.get(test_idx)

        print(f"Test store looking up prod index {prod_idx}: {test_store_prod_lookup}")
        print(
            f"Production store looking up test index {test_idx}: {prod_store_test_lookup}"
        )

        assert (
            test_store_prod_lookup is None
        ), "Production memory should not be in test store"
        assert (
            prod_store_test_lookup is None or prod_store_test_lookup != test_memory
        ), "Test memory should not be in production store"

        # Test queries to verify isolation
        test_results = test_store.query("TEST_UNIQUE", k=5)
        prod_results = prod_store.query("PROD_UNIQUE", k=5)

        # Verify query results are isolated
        test_found = any("TEST_UNIQUE" in r.get("text", "") for r in test_results)
        prod_found = any("PROD_UNIQUE" in r.get("text", "") for r in prod_results)

        assert test_found, "Test store should find test-specific data"
        assert prod_found, "Production store should find production-specific data"

        # Verify cross-contamination does not occur
        prod_in_test = any("PROD_UNIQUE" in r.get("text", "") for r in test_results)
        test_in_prod = any("TEST_UNIQUE" in r.get("text", "") for r in prod_results)

        assert not prod_in_test, "Test store should not find production data"
        assert not test_in_prod, "Production store should not find test data"

        print("+ Data isolation working correctly")
        return True

    except Exception as e:
        print(f"- Data isolation failed: {e}")
        return False


def test_factory_functions():
    """
    GREEN TEST: Factory functions should create properly isolated stores
    """
    print("\n[GREEN] TEST: Factory Functions")
    print("=" * 50)

    try:
        from dev_server import create_test_memory_store, create_production_memory_store

        # Create multiple instances to verify consistency
        test_store1 = create_test_memory_store()
        test_store2 = create_test_memory_store()
        prod_store1 = create_production_memory_store()
        prod_store2 = create_production_memory_store()

        # Verify all test stores have test characteristics
        assert test_store1.is_test_env == True, "Test store 1 should be in test mode"
        assert test_store2.is_test_env == True, "Test store 2 should be in test mode"
        assert (
            test_store1.collection_name == "test_mem"
        ), "Test store 1 should use test collection"
        assert (
            test_store2.collection_name == "test_mem"
        ), "Test store 2 should use test collection"

        # Verify all production stores have production characteristics
        assert (
            prod_store1.is_test_env == False
        ), "Production store 1 should not be in test mode"
        assert (
            prod_store2.is_test_env == False
        ), "Production store 2 should not be in test mode"
        assert (
            prod_store1.collection_name == "closer_mem"
        ), "Production store 1 should use production collection"
        assert (
            prod_store2.collection_name == "closer_mem"
        ), "Production store 2 should use production collection"

        print("+ Factory functions working correctly")
        return True

    except Exception as e:
        print(f"- Factory functions failed: {e}")
        return False


def test_environment_variable_detection():
    """
    GREEN TEST: Environment variable detection should work correctly
    """
    print("\n[GREEN] TEST: Environment Variable Detection")
    print("=" * 50)

    try:
        from dev_server import MemoryStore

        # Test with TEST_ENV=true
        os.environ["TEST_ENV"] = "true"
        test_store = MemoryStore()

        assert test_store.is_test_env == True, "Should detect TEST_ENV=true"
        assert (
            test_store.collection_name == "test_mem"
        ), "Should use test collection when TEST_ENV=true"

        # Clean up
        del os.environ["TEST_ENV"]

        # Test with explicit production mode (override automatic detection)
        prod_store = MemoryStore(test_mode=False)
        assert (
            prod_store.is_test_env == False
        ), "Should not detect test environment with explicit test_mode=False"
        assert (
            prod_store.collection_name == "closer_mem"
        ), "Should use production collection with explicit test_mode=False"

        print("+ Environment variable detection working correctly")
        return True

    except Exception as e:
        print(f"- Environment variable detection failed: {e}")
        return False


def run_isolation_tests():
    """Run all isolation tests"""
    print("[TEST] PHASE 2: Memory Store Isolation Tests")
    print("=" * 60)
    print("These tests should PASS to prove isolation is working correctly")
    print()

    tests = [
        test_environment_detection,
        test_database_path_isolation,
        test_collection_isolation,
        test_data_isolation,
        test_factory_functions,
        test_environment_variable_detection,
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
    print("PHASE 2 RESULTS:")
    print(f"Tests passed: {results.count(True)}")
    print(f"Tests failed: {results.count(False)}")

    if results.count(True) == len(tests):
        print("\n+ SUCCESS: All isolation tests passed!")
        print("Memory store isolation is working correctly")
        print("Ready to proceed to Phase 3: Cleanup Utilities")
        return True
    else:
        print(f"\n- FAILURE: {results.count(False)} tests failed")
        print("Memory store isolation needs work")
        return False


if __name__ == "__main__":
    success = run_isolation_tests()
    sys.exit(0 if success else 1)
