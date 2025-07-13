#!/usr/bin/env python3
"""
Pytest fixtures for Closer testing
Provides clean test environments and memory stores
"""
import os
import pytest
import tempfile
from pathlib import Path
import sys

# Add current directory to path so we can import server modules
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture
def clean_test_memory():
    """
    Create a completely isolated test memory store
    Each test gets a fresh, empty memory store in a temporary directory
    """
    from server import MemoryStore
    
    # Force test mode to ensure isolation
    memory = MemoryStore(test_mode=True)
    yield memory
    
    # Cleanup is automatic since test stores use temp directories


@pytest.fixture
def sample_test_memory():
    """
    Create a test memory store with sample data for testing queries
    """
    from server import MemoryStore
    
    memory = MemoryStore(test_mode=True)
    
    # Add sample memories that match what the original tests used
    memory.add("Test memory: user loves diamonds")
    memory.add("User confesses: killed a man with M14 rifle in Fallujah, Iraq during combat")
    memory.add("User reveals origin of loneliness: bullied for liking Warhammer in 6th grade")
    
    yield memory


@pytest.fixture
def test_environment():
    """
    Set up clean test environment variables and cleanup afterward
    """
    # Store original environment
    original_env = dict(os.environ)
    
    # Set test environment
    os.environ["TEST_ENV"] = "true"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mcp_tools():
    """
    Import MCP tools for testing
    """
    try:
        from server import save_memory, query_memory, web_search, memory, BRAVE_TOKEN
        return {
            'save_memory': save_memory,
            'query_memory': query_memory, 
            'web_search': web_search,
            'memory': memory,
            'brave_token': BRAVE_TOKEN
        }
    except ImportError as e:
        pytest.skip(f"Could not import MCP tools: {e}")


@pytest.fixture(scope="session")
def docker_environment():
    """
    Verify we're running in the expected Docker environment
    """
    if not Path("/app").exists():
        pytest.skip("Tests must run in Docker environment")
    
    return True 