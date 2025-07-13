#!/usr/bin/env python3
"""
Pytest version of MCP tool functionality tests
Converted from test_mcp_tools.py
"""
import pytest
import tempfile
from pathlib import Path


@pytest.mark.mcp
def test_mcp_tools_import(mcp_tools):
    """Test that MCP tools can be imported successfully"""
    tools = mcp_tools
    
    # Verify all expected tools are available
    assert 'save_memory' in tools, "save_memory tool should be available"
    assert 'query_memory' in tools, "query_memory tool should be available" 
    assert 'web_search' in tools, "web_search tool should be available"
    assert 'memory' in tools, "memory store should be available"


@pytest.mark.mcp
def test_save_memory_functionality(mcp_tools):
    """Test save_memory tool underlying functionality"""
    memory = mcp_tools['memory']
    
    # Test saving a memory directly through the memory store
    test_content = "Test memory from MCP tool test"
    idx = memory.add(test_content)
    
    assert idx >= 0, "Memory save should return valid index"
    
    # Verify it was saved
    retrieved = memory.get(idx)
    assert retrieved == test_content, "Saved memory should be retrievable"


@pytest.mark.mcp
def test_query_memory_functionality(mcp_tools):
    """Test query_memory tool underlying functionality"""
    memory = mcp_tools['memory']
    
    # Add a test memory
    test_content = "Test memory from MCP tool test"
    memory.add(test_content)
    
    # Query for it
    results = memory.query("MCP tool test", k=5)
    
    assert len(results) > 0, "Query should return results"
    
    # Should find our test memory
    found = any("MCP tool test" in result.get("text", "") for result in results)
    assert found, "Query should find the test memory"


@pytest.mark.mcp
def test_brave_api_configuration(mcp_tools):
    """Test that Brave Search API is configured"""
    brave_token = mcp_tools['brave_token']
    
    assert brave_token is not None, "BRAVE_API_KEY should be configured"
    assert len(brave_token) > 10, "BRAVE_API_KEY should be a real key, not placeholder"
    assert not brave_token.startswith("local-"), "BRAVE_API_KEY should not be placeholder value"


@pytest.mark.mcp 
def test_memory_database_status(mcp_tools):
    """Test memory database status and health"""
    memory = mcp_tools['memory']
    
    # Check database properties
    assert memory.db_path.exists(), "Database path should exist"
    assert hasattr(memory, 'next_index'), "Memory should have next_index property"
    assert memory.next_index >= 0, "Next index should be non-negative"
    
    # Check collection
    count = memory.col.count()
    assert count >= 0, "Collection count should be non-negative"


@pytest.mark.mcp
def test_memory_store_isolation(mcp_tools):
    """Test that MCP tools use isolated test memory store"""
    memory = mcp_tools['memory']
    
    # Should be using test environment
    assert memory.is_test_env == True, "MCP tools should use test environment"
    assert memory.collection_name == "test_mem", "Should use test collection"
    
    # Database path should be in temp directory - resolve symlinks and normalize paths
    temp_dir = Path(tempfile.gettempdir()).resolve()
    test_path = memory.db_path.resolve()
    assert temp_dir in test_path.parents or test_path.is_relative_to(temp_dir), \
        f"Test memory should use temporary directory. Expected under {temp_dir}, got {test_path}"


@pytest.mark.mcp
def test_memory_persistence_basics(mcp_tools):
    """Test basic memory persistence through MCP interface"""
    memory = mcp_tools['memory']
    
    # Record initial state
    initial_count = memory.col.count()
    initial_next_index = memory.next_index
    
    # Add a memory
    test_content = "Persistence test memory"
    idx = memory.add(test_content)
    
    # Verify state changes
    new_count = memory.col.count()
    new_next_index = memory.next_index
    
    assert new_count == initial_count + 1, "Collection count should increase by 1"
    assert new_next_index == initial_next_index + 1, "Next index should increment by 1"
    assert idx == initial_next_index, "New memory should get the previous next_index"


@pytest.mark.mcp
@pytest.mark.slow
def test_memory_embedding_consistency(mcp_tools):
    """Test that embeddings are generated consistently"""
    memory = mcp_tools['memory']
    
    # Generate embedding twice for same text
    text = "consistency test"
    embedding1 = memory._embed(text)
    embedding2 = memory._embed(text)
    
    # Should have same length and dimensions
    assert len(embedding1) == len(embedding2), "Embeddings should have same length"
    assert len(embedding1) == 1536, "Should be 1536-dimensional embeddings"
    
    # OpenAI embeddings are not perfectly deterministic, but should be very similar
    # Calculate cosine similarity between the two embeddings
    import numpy as np
    
    # Convert to numpy arrays for easier calculation
    emb1 = np.array(embedding1)
    emb2 = np.array(embedding2)
    
    # Calculate cosine similarity
    cosine_sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    # Embeddings should be very similar (cosine similarity > 0.95)
    assert cosine_sim > 0.95, f"Embeddings should be very similar (cosine similarity: {cosine_sim:.6f})"
    
    # Check that individual values are reasonably close
    max_diff = np.max(np.abs(emb1 - emb2))
    assert max_diff < 0.1, f"Maximum difference between embeddings should be small (got {max_diff:.6f})"


@pytest.mark.mcp
def test_multiple_memory_operations(mcp_tools):
    """Test multiple memory operations in sequence"""
    memory = mcp_tools['memory']
    
    # Add multiple memories
    memories = [
        "First test memory",
        "Second test memory", 
        "Third test memory"
    ]
    
    indices = []
    for mem_text in memories:
        idx = memory.add(mem_text)
        indices.append(idx)
    
    # Verify all were added with sequential indices
    for i, idx in enumerate(indices):
        if i > 0:
            assert idx == indices[i-1] + 1, "Indices should be sequential"
    
    # Verify all can be retrieved
    for i, idx in enumerate(indices):
        retrieved = memory.get(idx)
        assert retrieved == memories[i], f"Memory {i} should be retrievable"
    
    # Verify search works across all
    results = memory.query("test memory", k=len(memories))
    assert len(results) >= len(memories), "Should find all test memories" 