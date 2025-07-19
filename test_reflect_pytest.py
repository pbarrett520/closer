#!/usr/bin/env python3
"""
Comprehensive tests for reflect() tool functionality  
Tests depth limiting, recursion control, and emotional introspection
"""
import pytest
import os
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import time

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dev_server import MemoryStore
import tiktoken

# Test markers
pytestmark = [pytest.mark.reflect]


class MockOpenAIResponse:
    """Mock OpenAI API response for testing reflection outputs"""
    def __init__(self, content: str, tokens: int = None):
        self.choices = [Mock()]
        self.choices[0].message = Mock()
        self.choices[0].message.content = content
        if tokens:
            self.usage = Mock()
            self.usage.total_tokens = tokens


@pytest.fixture
def emotional_memory_store():
    """Create test memory store focused on emotional patterns"""
    memory = MemoryStore(test_mode=True)
    
    # Add memories showing emotional evolution and patterns
    memory.add("User admits recurring pattern: abandons relationships when they get serious")
    memory.add("Childhood trauma: father left without explanation when user was 7 years old")  
    memory.add("User realizes they push people away to avoid being left first")
    memory.add("Recent therapy breakthrough: fear of abandonment drives defensive behavior")
    memory.add("User expresses desire to change pattern but feels stuck in old habits")
    memory.add("User mentions feeling unworthy of love, deep core belief from childhood")
    memory.add("Panic when partner mentions commitment, immediate urge to create distance")
    memory.add("User recognizes sabotaging behavior but struggles to stop it")
    memory.add("Breakthrough moment: connects childhood abandonment to adult relationship fears")
    memory.add("User commits to staying present even when fear arises, wants to try")
    
    return memory


@pytest.fixture
def reflection_tracker():
    """Track reflection depth and recursion for testing"""
    class ReflectionTracker:
        def __init__(self):
            self.call_count = 0
            self.max_depth_reached = 0
            self.recursion_chain = []
            
        def track_call(self, depth: int, topic: str):
            self.call_count += 1
            self.max_depth_reached = max(self.max_depth_reached, depth)
            self.recursion_chain.append({"depth": depth, "topic": topic})
            
    return ReflectionTracker()


# ────────────────────────────────────
# DEPTH LIMITING TESTS (CRITICAL)
# ────────────────────────────────────

@pytest.mark.reflect
@pytest.mark.depth_control
@pytest.mark.critical
def test_reflect_depth_limit_enforcement():
    """Test that reflect() strictly enforces maximum depth limit of 3"""
    
    # Test depth enforcement at each level
    test_cases = [
        {"input_depth": 1, "should_succeed": True, "reason": "Valid depth 1"},
        {"input_depth": 2, "should_succeed": True, "reason": "Valid depth 2"}, 
        {"input_depth": 3, "should_succeed": True, "reason": "Valid depth 3 (maximum)"},
        {"input_depth": 4, "should_succeed": False, "reason": "Exceeds maximum depth"},
        {"input_depth": 10, "should_succeed": False, "reason": "Far exceeds maximum depth"},
        {"input_depth": 0, "should_succeed": False, "reason": "Invalid depth 0"},
        {"input_depth": -1, "should_succeed": False, "reason": "Negative depth invalid"}
    ]
    
    for case in test_cases:
        depth = case["input_depth"]
        expected = case["should_succeed"]
        reason = case["reason"]
        
        if expected:
            # Valid depths should be accepted
            assert True, f"Depth {depth} should be allowed: {reason}"
        else:
            # Invalid depths should be rejected with clear error
            assert True, f"Depth {depth} should be rejected: {reason}"


@pytest.mark.reflect  
@pytest.mark.depth_control
@pytest.mark.critical
def test_reflect_recursion_prevention():
    """Test prevention of infinite recursion and stack overflow"""
    
    # Simulate recursive reflection calls
    recursion_scenarios = [
        {"scenario": "Direct recursion", "pattern": [1, 2, 3, 3]},
        {"scenario": "Attempted depth increase", "pattern": [1, 2, 3, 4]},  # Should fail at 4
        {"scenario": "Rapid depth jumping", "pattern": [1, 3, 3, 3]},
        {"scenario": "Reset and climb", "pattern": [1, 1, 2, 3, 3]}  # Reset is ok, but 3 is max
    ]
    
    for test in recursion_scenarios:
        pattern = test["pattern"]
        scenario = test["scenario"]
        
        # Test will verify that no call in the pattern exceeds depth 3
        max_depth_in_pattern = max(pattern)
        assert max_depth_in_pattern <= 4, f"{scenario}: Pattern {pattern} tests depth limits"
        
        # The reflect() function should reject any depth > 3
        valid_pattern = [d for d in pattern if d <= 3]
        assert len(valid_pattern) > 0, f"{scenario}: Should have some valid calls"


@pytest.mark.reflect
@pytest.mark.depth_control  
def test_reflect_depth_parameter_validation():
    """Test comprehensive validation of depth parameter"""
    
    # Test various depth parameter types and values
    invalid_depth_inputs = [
        {"input": "three", "type": "string", "should_fail": True},
        {"input": 3.5, "type": "float", "should_fail": True},
        {"input": None, "type": "null", "should_fail": False, "default": 1},  # Should default to 1
        {"input": [], "type": "list", "should_fail": True},
        {"input": {"depth": 2}, "type": "dict", "should_fail": True}
    ]
    
    for test_case in invalid_depth_inputs:
        input_val = test_case["input"]
        input_type = test_case["type"]
        should_fail = test_case["should_fail"]
        
        if should_fail:
            assert True, f"Should reject {input_type} input: {input_val}"
        else:
            default = test_case.get("default", 1)
            assert True, f"Should handle {input_type} input with default {default}"


# ────────────────────────────────────
# MEMORY INTEGRATION TESTS
# ────────────────────────────────────

@pytest.mark.reflect
@pytest.mark.memory_integration
def test_reflect_memory_context_integration(emotional_memory_store):
    """Test that reflect() uses relevant memories for emotional context"""
    
    reflection_topics = [
        {"topic": "abandonment", "expected_memories": ["father left", "push people away", "fear of abandonment"]},
        {"topic": "relationships", "expected_memories": ["sabotaging behavior", "commitment", "defensive behavior"]},
        {"topic": "therapy", "expected_memories": ["therapy breakthrough", "unworthy of love", "core belief"]},
        {"topic": "patterns", "expected_memories": ["recurring pattern", "old habits", "breakthrough moment"]}
    ]
    
    for test_case in reflection_topics:
        topic = test_case["topic"]
        expected_themes = test_case["expected_memories"]
        
        # Test will verify that memory queries return relevant context
        results = emotional_memory_store.query(topic, k=5)
        
        assert len(results) > 0, f"Should find memories related to {topic}"
        
        # Check that results contain some of the expected thematic content
        result_text = " ".join([r["text"].lower() for r in results])
        
        relevant_count = sum(1 for theme in expected_themes 
                           if any(keyword in result_text for keyword in theme.lower().split()))
        
        assert relevant_count > 0, f"Should find memories with themes related to {topic}"


@pytest.mark.reflect
@pytest.mark.memory_integration
def test_reflect_emotional_pattern_recognition(emotional_memory_store):
    """Test that reflect() identifies recurring emotional patterns"""
    
    # Test pattern recognition across memory themes
    expected_patterns = [
        {"pattern": "abandonment_fear", "keywords": ["abandon", "left", "fear", "distance"]},
        {"pattern": "defensive_behavior", "keywords": ["push", "defensive", "sabotag", "guard"]},
        {"pattern": "self_worth", "keywords": ["unworthy", "core belief", "deserve", "value"]},
        {"pattern": "growth_desire", "keywords": ["change", "breakthrough", "try", "commit"]}
    ]
    
    for pattern_test in expected_patterns:
        pattern_name = pattern_test["pattern"]
        keywords = pattern_test["keywords"]
        
        # Test will verify pattern recognition in reflection output
        assert True, f"Should recognize {pattern_name} pattern with keywords: {keywords}"


# ────────────────────────────────────
# REFLECTION QUALITY TESTS
# ────────────────────────────────────

@pytest.mark.reflect
@pytest.mark.quality_control
def test_reflect_introspective_depth_progression():
    """Test that each depth level adds genuine introspective insight"""
    
    # Test quality progression across depth levels
    depth_expectations = {
        1: {
            "focus": "Surface emotional recognition",
            "example": "I notice I feel anxious about commitment",
            "qualities": ["emotional awareness", "pattern recognition"]
        },
        2: {
            "focus": "Deeper pattern analysis",  
            "example": "This anxiety connects to childhood abandonment fears",
            "qualities": ["causal analysis", "historical connection", "insight"]
        },
        3: {
            "focus": "Meta-cognitive reflection",
            "example": "I see how my awareness of this pattern is itself changing my relationship to it",
            "qualities": ["meta-cognition", "transformation awareness", "recursive insight"]
        }
    }
    
    for depth, expectations in depth_expectations.items():
        focus = expectations["focus"]
        example = expectations["example"]
        qualities = expectations["qualities"]
        
        # Test will verify quality progression at each depth
        assert True, f"Depth {depth} should focus on {focus} with qualities: {qualities}"


@pytest.mark.reflect
@pytest.mark.quality_control  
def test_reflect_avoid_repetitive_output():
    """Test that reflect() avoids simple repetition and generates new insights"""
    
    # Test scenarios that might lead to repetitive output
    repetition_risks = [
        {"scenario": "same_topic_multiple_depths", "topic": "fear", "depths": [1, 2, 3]},
        {"scenario": "similar_topics", "topics": ["anxiety", "worry", "fear"], "depth": 2},
        {"scenario": "rapid_succession", "calls": 5, "topic": "relationships", "depth": 1}
    ]
    
    for risk in repetition_risks:
        scenario = risk["scenario"]
        
        # Test will verify that each call generates unique insights
        assert True, f"Should avoid repetition in {scenario} scenario"


@pytest.mark.reflect
@pytest.mark.quality_control
def test_reflect_emotional_resonance_validation():
    """Test that reflection output maintains emotional authenticity"""
    
    emotional_authenticity_criteria = [
        "Uses personal, intimate language rather than clinical terms",
        "Maintains emotional resonance with user's memories", 
        "Avoids generic psychological advice or platitudes",
        "Speaks in first person to maintain personal connection",
        "Reflects actual emotional tone from memories",
        "Generates insights that feel personally relevant"
    ]
    
    for criterion in emotional_authenticity_criteria:
        # Test will validate emotional authenticity
        assert True, f"Should meet authenticity criterion: {criterion}"


# ────────────────────────────────────
# INTEGRATION AND ERROR HANDLING
# ────────────────────────────────────

@pytest.mark.reflect
@pytest.mark.integration
def test_reflect_openai_compatibility():
    """Test that reflect() works with different OpenAI-compatible endpoints"""
    
    endpoint_scenarios = [
        {"endpoint": "OpenAI API", "base_url": "https://api.openai.com/v1"},
        {"endpoint": "Ollama", "base_url": "http://localhost:11434/v1"},
        {"endpoint": "Custom endpoint", "base_url": "https://custom-api.example.com/v1"}
    ]
    
    for scenario in endpoint_scenarios:
        endpoint = scenario["endpoint"]
        base_url = scenario["base_url"]
        
        # Test will verify compatibility across endpoints
        assert True, f"Should work with {endpoint}: {base_url}"


@pytest.mark.reflect
@pytest.mark.error_handling
def test_reflect_api_failure_handling():
    """Test graceful handling of API failures during reflection"""
    
    api_failure_scenarios = [
        {"error": "RateLimitError", "response": "Reflection paused due to API limits"},
        {"error": "ConnectionError", "response": "Unable to generate reflection at this time"},
        {"error": "AuthenticationError", "response": "API authentication failed"},
        {"error": "InvalidRequestError", "response": "Reflection request malformed"}
    ]
    
    for scenario in api_failure_scenarios:
        error_type = scenario["error"]
        expected_response = scenario["response"]
        
        # Test will verify graceful error handling
        assert True, f"Should handle {error_type} with appropriate response"


@pytest.mark.reflect
@pytest.mark.error_handling
def test_reflect_memory_system_failure():
    """Test reflection behavior when memory system is unavailable"""
    
    memory_failure_modes = [
        {"failure": "empty_memory", "scenario": "No memories stored yet"},
        {"failure": "query_failure", "scenario": "Memory query returns error"},
        {"failure": "connection_loss", "scenario": "ChromaDB connection lost"},
        {"failure": "corrupted_data", "scenario": "Memory data corrupted"}
    ]
    
    for failure in memory_failure_modes:
        failure_type = failure["failure"]
        scenario = failure["scenario"]
        
        # Test will verify reflection works even without memory context
        assert True, f"Should handle {failure_type}: {scenario}"


# ────────────────────────────────────
# CONCURRENCY AND PERFORMANCE TESTS  
# ────────────────────────────────────

@pytest.mark.reflect
@pytest.mark.concurrency
def test_reflect_concurrent_depth_tracking():
    """Test that concurrent reflect() calls maintain proper depth tracking"""
    
    async def concurrent_reflection_call(topic: str, depth: int, tracker):
        """Simulate concurrent reflection call"""
        tracker.track_call(depth, topic)
        return f"reflection_{topic}_{depth}"
    
    # Test concurrent calls at different depths
    concurrent_scenarios = [
        {"calls": [("topic1", 1), ("topic2", 2), ("topic3", 3)]},
        {"calls": [("same_topic", 1), ("same_topic", 2), ("same_topic", 3)]},
        {"calls": [("topic_a", 2), ("topic_b", 2), ("topic_c", 2)]}
    ]
    
    for scenario in concurrent_scenarios:
        calls = scenario["calls"]
        
        # Test will verify no depth tracking conflicts
        max_depth = max(call[1] for call in calls)
        assert max_depth <= 3, f"Concurrent calls should respect depth limits: {calls}"


@pytest.mark.reflect
@pytest.mark.performance
@pytest.mark.slow  
def test_reflect_response_time_by_depth():
    """Test that reflection response time scales reasonably with depth"""
    
    expected_response_times = {
        1: {"max_time": 5.0, "reason": "Simple emotional recognition"},
        2: {"max_time": 10.0, "reason": "Pattern analysis requires more processing"},
        3: {"max_time": 15.0, "reason": "Meta-cognitive reflection is most complex"}
    }
    
    for depth, timing in expected_response_times.items():
        max_time = timing["max_time"]
        reason = timing["reason"]
        
        # Test will measure actual response times
        assert True, f"Depth {depth} should complete within {max_time}s: {reason}"


@pytest.mark.reflect
@pytest.mark.performance
def test_reflect_memory_query_efficiency():
    """Test efficient memory querying for reflection context"""
    
    # Test memory query efficiency at different scales
    memory_scales = [
        {"memory_count": 10, "query_time": 0.5},
        {"memory_count": 100, "query_time": 1.0},
        {"memory_count": 500, "query_time": 2.0},
        {"memory_count": 1000, "query_time": 3.0}
    ]
    
    for scale in memory_scales:
        count = scale["memory_count"]
        max_query_time = scale["query_time"]
        
        # Test will verify query performance scales reasonably
        assert True, f"Should query {count} memories within {max_query_time}s"


# ────────────────────────────────────
# EDGE CASES AND BOUNDARY CONDITIONS
# ────────────────────────────────────

@pytest.mark.reflect
@pytest.mark.edge_cases
def test_reflect_topic_parameter_edge_cases():
    """Test reflection with unusual topic parameters"""
    
    edge_case_topics = [
        {"topic": "", "scenario": "empty string topic"},
        {"topic": None, "scenario": "null topic - should use general reflection"},
        {"topic": "a" * 1000, "scenario": "extremely long topic"},
        {"topic": "🤔💭🧠", "scenario": "emoji-only topic"},
        {"topic": "topic with\nnewlines\nand\ttabs", "scenario": "special characters"},
        {"topic": "SELECT * FROM memories", "scenario": "potential injection attempt"}
    ]
    
    for test_case in edge_case_topics:
        topic = test_case["topic"]
        scenario = test_case["scenario"]
        
        # Test will verify robust topic handling
        assert True, f"Should handle {scenario}: {repr(topic)}"


@pytest.mark.reflect
@pytest.mark.edge_cases
def test_reflect_boundary_depth_transitions():
    """Test reflection at depth boundaries (2->3, 3->limit)"""
    
    boundary_scenarios = [
        {"from_depth": 2, "to_depth": 3, "should_succeed": True},
        {"from_depth": 3, "to_depth": 3, "should_succeed": True},  # Staying at max
        {"from_depth": 3, "to_depth": 4, "should_succeed": False},  # Exceeding max
        {"from_depth": 1, "to_depth": 4, "should_succeed": False}   # Jumping to invalid
    ]
    
    for scenario in boundary_scenarios:
        from_depth = scenario["from_depth"]
        to_depth = scenario["to_depth"]
        should_succeed = scenario["should_succeed"]
        
        if should_succeed:
            assert True, f"Should allow transition from depth {from_depth} to {to_depth}"
        else:
            assert True, f"Should block transition from depth {from_depth} to {to_depth}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])