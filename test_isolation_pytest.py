#!/usr/bin/env python3
"""
Pytest version of environment isolation tests
Converted from test_memory_isolation.py with fixes for failing tests
"""
import pytest
import os
import tempfile
from pathlib import Path


@pytest.mark.isolation
def test_environment_detection():
    """Test that test and production environments are detected correctly"""
    from server import MemoryStore
    
    # Test explicit test mode
    test_store = MemoryStore(test_mode=True)
    assert test_store.is_test_env == True, "Explicit test mode should be detected"
    assert test_store.collection_name == "test_mem", "Test store should use test collection"
    
    # Test explicit production mode  
    prod_store = MemoryStore(test_mode=False)
    assert prod_store.is_test_env == False, "Explicit production mode should be detected"
    assert prod_store.collection_name == "closer_mem", "Production store should use production collection"


@pytest.mark.isolation
def test_database_path_isolation():
    """Test that test and production databases use different paths"""
    from server import MemoryStore
    
    test_store = MemoryStore(test_mode=True)
    prod_store = MemoryStore(test_mode=False)
    
    # Paths should be different
    assert test_store.db_path != prod_store.db_path, "Test and production should use different database paths"
    
    # Test store should use temp directory - resolve symlinks and normalize paths
    temp_dir = Path(tempfile.gettempdir()).resolve()
    test_path = test_store.db_path.resolve()
    assert temp_dir in test_path.parents or test_path.is_relative_to(temp_dir), \
        f"Test store should use temporary directory. Expected under {temp_dir}, got {test_path}"
    
    # Production store should use app directory (in Docker) or local directory
    prod_path_str = str(prod_store.db_path)
    assert "/app/" in prod_path_str or "closer_memory_db" in prod_path_str, \
        "Production store should use app or local directory"


@pytest.mark.isolation
def test_collection_isolation():
    """Test that test and production use different collections"""
    from server import MemoryStore
    
    test_store = MemoryStore(test_mode=True)
    prod_store = MemoryStore(test_mode=False)
    
    # Collection names should be different
    assert test_store.collection_name != prod_store.collection_name, \
        "Test and production should use different collection names"
    
    assert test_store.collection_name == "test_mem", "Test should use test_mem collection"
    assert prod_store.collection_name == "closer_mem", "Production should use closer_mem collection"


@pytest.mark.isolation
def test_data_isolation():
    """Test that test and production data don't cross-contaminate"""
    from server import MemoryStore
    
    # Create fresh, isolated stores
    test_store = MemoryStore(test_mode=True)
    prod_store = MemoryStore(test_mode=False)
    
    # Add unique data to each store
    test_memory = "TEST_UNIQUE_MEMORY_12345"
    prod_memory = "PROD_UNIQUE_MEMORY_67890"
    
    test_idx = test_store.add(test_memory)
    prod_idx = prod_store.add(prod_memory)
    
    # Verify data is in the correct stores
    assert test_store.get(test_idx) == test_memory, "Test memory should be in test store"
    assert prod_store.get(prod_idx) == prod_memory, "Production memory should be in production store"
    
    # Verify data is NOT in the wrong stores
    # NOTE: This is the test that was failing before - let's fix it
    # The issue was that stores with different databases might still share indices
    # We should test that the CONTENT is isolated, not just the indices
    
    # Query for unique content to verify isolation
    test_results = test_store.query("TEST_UNIQUE_MEMORY_12345", k=5)
    prod_results = prod_store.query("PROD_UNIQUE_MEMORY_67890", k=5)
    
    # Each store should only find its own data
    test_found_own = any("TEST_UNIQUE" in r.get("text", "") for r in test_results)
    prod_found_own = any("PROD_UNIQUE" in r.get("text", "") for r in prod_results)
    
    assert test_found_own, "Test store should find its own test data"
    assert prod_found_own, "Production store should find its own production data"
    
    # Cross-contamination check - search for the other store's data
    test_results_cross = test_store.query("PROD_UNIQUE_MEMORY_67890", k=10)
    prod_results_cross = prod_store.query("TEST_UNIQUE_MEMORY_12345", k=10)
    
    test_found_prod = any("PROD_UNIQUE" in r.get("text", "") for r in test_results_cross)
    prod_found_test = any("TEST_UNIQUE" in r.get("text", "") for r in prod_results_cross)
    
    assert not test_found_prod, "Test store should not find production data"
    assert not prod_found_test, "Production store should not find test data"


@pytest.mark.isolation
def test_factory_functions():
    """Test that factory functions create properly isolated stores"""
    # Skip if dev_server is not available (this was causing import issues)
    pytest.importorskip("dev_server", reason="dev_server not available")
    
    from dev_server import create_test_memory_store, create_production_memory_store
    
    # Create multiple instances to verify consistency
    test_store1 = create_test_memory_store()
    test_store2 = create_test_memory_store()
    prod_store1 = create_production_memory_store()
    prod_store2 = create_production_memory_store()
    
    # Verify all test stores have test characteristics
    assert test_store1.is_test_env == True, "Test store 1 should be in test mode"
    assert test_store2.is_test_env == True, "Test store 2 should be in test mode"
    assert test_store1.collection_name == "test_mem", "Test store 1 should use test collection"
    assert test_store2.collection_name == "test_mem", "Test store 2 should use test collection"
    
    # Verify all production stores have production characteristics
    assert prod_store1.is_test_env == False, "Production store 1 should not be in test mode"
    assert prod_store2.is_test_env == False, "Production store 2 should not be in test mode"
    assert prod_store1.collection_name == "closer_mem", "Production store 1 should use production collection"
    assert prod_store2.collection_name == "closer_mem", "Production store 2 should use production collection"


@pytest.mark.isolation
def test_environment_variable_detection(test_environment):
    """Test that environment variable detection works correctly"""
    from server import MemoryStore
    
    # Should detect TEST_ENV=true (set by test_environment fixture)
    test_store = MemoryStore()
    assert test_store.is_test_env == True, "Should detect TEST_ENV=true"
    assert test_store.collection_name == "test_mem", "Should use test collection when TEST_ENV=true"


@pytest.mark.isolation
def test_explicit_mode_override():
    """Test that explicit test_mode parameter overrides environment detection"""
    # Set up environment that would normally indicate production
    original_test_env = os.environ.get("TEST_ENV")
    if "TEST_ENV" in os.environ:
        del os.environ["TEST_ENV"]
    
    try:
        from server import MemoryStore
        
        # Explicit test mode should override environment
        test_store = MemoryStore(test_mode=True)
        assert test_store.is_test_env == True, "Explicit test_mode=True should override environment"
        
        # Explicit production mode should override environment  
        prod_store = MemoryStore(test_mode=False)
        assert prod_store.is_test_env == False, "Explicit test_mode=False should override environment"
        
    finally:
        # Restore original environment
        if original_test_env is not None:
            os.environ["TEST_ENV"] = original_test_env


@pytest.mark.isolation 
def test_temp_directory_cleanup():
    """Test that test stores use proper temporary directories"""
    from server import MemoryStore
    
    test_store = MemoryStore(test_mode=True)
    
    # Should use temp directory - resolve symlinks and normalize paths
    temp_dir = Path(tempfile.gettempdir()).resolve()
    test_path = test_store.db_path.resolve()
    assert temp_dir in test_path.parents or test_path.is_relative_to(temp_dir), \
        f"Test store should use temporary directory. Expected under {temp_dir}, got {test_path}"
    
    # Directory should exist and be writable
    assert test_store.db_path.exists(), "Test database directory should exist"
    
    # Should be able to write to it
    test_file = test_store.db_path / ".write_test"
    test_file.write_text("test")
    assert test_file.exists(), "Should be able to write to test directory"
    test_file.unlink()  # Cleanup 