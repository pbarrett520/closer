#!/usr/bin/env python3
"""
Pytest version of comprehensive system health tests
Tests overall system integration and health
"""
import pytest
import os
from pathlib import Path


@pytest.mark.system
def test_docker_environment():
    """Test that we're running in the expected Docker environment"""
    # Check for Docker indicators
    docker_indicators = [
        Path("/app").exists(),  # Docker app directory
        os.environ.get("DOCKER_ENV") == "true",  # Docker environment variable
        Path("/.dockerenv").exists()  # Docker container indicator file
    ]
    
    assert any(docker_indicators), "Should be running in Docker environment"


@pytest.mark.system
def test_environment_variables():
    """Test that required environment variables are set"""
    # Test API keys are configured (not just default values)
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    brave_key = os.environ.get("BRAVE_API_KEY", "")
    
    assert openai_key, "OPENAI_API_KEY should be set"
    assert brave_key, "BRAVE_API_KEY should be set"
    
    # Should not be placeholder values
    assert openai_key != "local-key", "OPENAI_API_KEY should not be placeholder"
    assert not openai_key.startswith("local-"), "OPENAI_API_KEY should be real key"
    assert not brave_key.startswith("local-"), "BRAVE_API_KEY should be real key"
    
    # Check other important environment variables
    assert os.environ.get("DOCKER_ENV") == "true", "DOCKER_ENV should be true"
    assert os.environ.get("MCP_TRANSPORT") == "sse", "MCP_TRANSPORT should be sse"


@pytest.mark.system
def test_python_imports():
    """Test that all required Python modules can be imported"""
    # Core dependencies
    import chromadb
    import tiktoken
    import openai
    import aiohttp
    import rich
    
    # MCP dependencies
    import fastmcp
    import mcp
    
    # SSE dependencies  
    import uvicorn
    import starlette
    import sse_starlette
    
    # All imports successful
    assert True, "All required modules imported successfully"


@pytest.mark.system
def test_server_module_imports():
    """Test that server modules can be imported correctly"""
    from server import (
        MemoryStore, 
        save_memory,
        query_memory, 
        web_search,
        memory,
        mcp,
        client,
        BRAVE_TOKEN
    )
    
    # Verify key objects are available
    assert MemoryStore is not None, "MemoryStore class should be importable"
    assert memory is not None, "Global memory instance should be available"
    assert mcp is not None, "FastMCP instance should be available"
    assert client is not None, "OpenAI client should be available"
    assert BRAVE_TOKEN is not None, "BRAVE_TOKEN should be configured"


@pytest.mark.system
def test_database_connectivity():
    """Test that database systems are accessible"""
    from server import MemoryStore
    
    # Test ChromaDB connectivity
    memory = MemoryStore(test_mode=True)
    
    # Should be able to access collection
    count = memory.col.count()
    assert count >= 0, "Should be able to query ChromaDB collection"
    
    # Should be able to add and retrieve
    idx = memory.add("System health test memory")
    retrieved = memory.get(idx)
    assert retrieved == "System health test memory", "Should be able to add and retrieve memories"


@pytest.mark.system
def test_openai_api_connectivity():
    """Test that OpenAI API is accessible"""
    from server import client
    
    # Try to generate a simple embedding (this tests API connectivity)
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test connectivity"
        )
        assert len(response.data) > 0, "Should receive embedding response"
        assert len(response.data[0].embedding) > 0, "Embedding should have data"
    except Exception as e:
        pytest.fail(f"OpenAI API connectivity test failed: {e}")


@pytest.mark.system
@pytest.mark.slow
def test_brave_search_connectivity():
    """Test that Brave Search API is accessible"""
    from server import BRAVE_TOKEN
    import aiohttp
    import asyncio
    
    async def test_brave():
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_TOKEN
        }
        params = {
            "q": "test query",
            "count": 1,
            "safesearch": "moderate"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                assert resp.status == 200, f"Brave API should be accessible (status: {resp.status})"
                data = await resp.json()
                assert "web" in data, "Brave API should return web results"
    
    # Run the async test
    try:
        asyncio.run(test_brave())
    except Exception as e:
        pytest.fail(f"Brave Search API connectivity test failed: {e}")


@pytest.mark.system
def test_file_system_permissions():
    """Test that file system permissions are correct"""
    from server import MemoryStore
    
    memory = MemoryStore(test_mode=True)
    
    # Database directory should be writable
    assert memory.db_path.exists(), "Database directory should exist"
    
    # Should be able to create files
    test_file = memory.db_path / ".permission_test"
    test_file.write_text("permission test")
    assert test_file.exists(), "Should be able to create files in database directory"
    
    # Should be able to read files
    content = test_file.read_text()
    assert content == "permission test", "Should be able to read created files"
    
    # Should be able to delete files
    test_file.unlink()
    assert not test_file.exists(), "Should be able to delete files"


@pytest.mark.system
def test_memory_system_end_to_end():
    """Test complete memory system workflow end-to-end"""
    from server import MemoryStore
    
    memory = MemoryStore(test_mode=True)
    
    # Full workflow: add -> query -> retrieve
    test_memories = [
        "System test: user discusses favorite books",
        "System test: user mentions anxiety about work", 
        "System test: user shares childhood memory of summer"
    ]
    
    # Add memories
    indices = []
    for mem in test_memories:
        idx = memory.add(mem)
        indices.append(idx)
    
    # Verify all were added
    assert len(indices) == len(test_memories), "All memories should be added"
    
    # Test retrieval by index
    for i, idx in enumerate(indices):
        retrieved = memory.get(idx)
        assert retrieved == test_memories[i], f"Memory {i} should be retrievable"
    
    # Test semantic search
    results = memory.query("books", k=5)
    book_found = any("books" in r.get("text", "") for r in results)
    assert book_found, "Should be able to find book-related memory via search"
    
    results = memory.query("anxiety", k=5)
    anxiety_found = any("anxiety" in r.get("text", "") for r in results)
    assert anxiety_found, "Should be able to find anxiety-related memory via search"


@pytest.mark.system
def test_mcp_tools_integration():
    """Test that MCP tools work in system context"""
    from server import save_memory, query_memory, web_search, memory
    
    # Test save_memory function exists and is available
    assert save_memory is not None, "save_memory should be available"
    assert query_memory is not None, "query_memory should be available"
    assert web_search is not None, "web_search should be available"
    
    # Test they are MCP tools
    assert hasattr(save_memory, 'name'), "save_memory should be MCP tool"
    assert hasattr(query_memory, 'name'), "query_memory should be MCP tool"
    assert hasattr(web_search, 'name'), "web_search should be MCP tool"
    
    # Test underlying memory system is functional
    initial_count = memory.col.count()
    idx = memory.add("MCP integration test memory")
    new_count = memory.col.count()
    
    assert new_count == initial_count + 1, "Memory should be added through MCP system"


@pytest.mark.system
def test_error_handling():
    """Test that system handles errors gracefully"""
    from server import MemoryStore
    
    memory = MemoryStore(test_mode=True)
    
    # Test invalid memory retrieval
    result = memory.get(-1)  # Invalid index
    assert result is None, "Invalid memory retrieval should return None"
    
    result = memory.get(99999)  # Non-existent index
    assert result is None, "Non-existent memory retrieval should return None"
    
    # Test empty query
    results = memory.query("", k=1)
    assert isinstance(results, list), "Empty query should return list (even if empty)"


@pytest.mark.system
def test_performance_baseline():
    """Test basic performance characteristics"""
    from server import MemoryStore
    import time
    
    memory = MemoryStore(test_mode=True)
    
    # Test embedding generation performance
    start_time = time.time()
    memory._embed("performance test text")
    embedding_time = time.time() - start_time
    
    assert embedding_time < 5.0, f"Embedding generation should be fast (took {embedding_time:.2f}s)"
    
    # Test memory add performance
    start_time = time.time()
    memory.add("Performance test memory")
    add_time = time.time() - start_time
    
    assert add_time < 2.0, f"Memory addition should be fast (took {add_time:.2f}s)" 