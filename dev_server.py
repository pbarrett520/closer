# dev_server.py
# ================================
# DEVELOPMENT VERSION - DO NOT USE IN PRODUCTION
#
# This is the development version of server.py where we implement:
# - reflect() tool - Emotion recursion with depth limiting (≤3)
# - dream() tool - Poetic memory remix (≤350 tokens)
# - Enhanced atmospheric features
#
# Based on: server.py (production stable)
# Purpose: Phase 1 - Core Tools & Enhanced CLI (TOP PRIORITY)
# ================================

import os, asyncio, aiohttp, json, uuid, datetime as dt, sys
from pathlib import Path
from typing import Optional
import time

import chromadb, tiktoken
from openai import OpenAI
from fastmcp import FastMCP
from dotenv import load_dotenv

# ────────────────────────────────────
# ENV & GLOBALS
# ────────────────────────────────────
load_dotenv(dotenv_path=Path(__file__).with_name(".env"), override=True)

# Local or cloud OpenAI-compatible endpoint
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "local-key"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
)

EMBED_MODEL = "text-embedding-3-small"  # llama.cpp ignores the name
enc = tiktoken.encoding_for_model(EMBED_MODEL)

# Brave API key for web_search
BRAVE_TOKEN = os.getenv("BRAVE_API_KEY")
if not BRAVE_TOKEN:
    raise RuntimeError("BRAVE_API_KEY is missing or empty")

mcp = FastMCP("closer_dev")  # Different name for development


# ────────────────────────────────────
# Memory Store
# ────────────────────────────────────
class MemoryStore:
    """
    Persistent vector-store memory using Chroma (embedded SQLite).
    Provides add / get / search by embedding similarity.
    """

    def __init__(self, test_mode=None):
        # Detect test environment
        self.is_test_env = (
            test_mode
            if test_mode is not None
            else (
                os.getenv("TEST_ENV") == "true"
                or os.getenv("PYTEST_CURRENT_TEST") is not None
                or sys.argv[0].endswith("pytest") 
                or "/pytest" in sys.argv[0]
                or sys.argv[0].startswith("test_")
            )
        )

        # Environment-aware DB path: Docker vs local vs test
        if self.is_test_env:
            # Test environment - use completely separate database
            import tempfile

            base_path = Path(tempfile.mkdtemp()) / "test_memory_db"
            self.db_path = base_path.resolve()
            self.collection_name = "test_mem"
            print(f"✓ Test environment detected - using isolated database")
        elif os.getenv("DOCKER_ENV") == "true" or Path("/app").exists():
            # Running in Docker container
            self.db_path = Path("/app/closer_memory_db").resolve()
            self.collection_name = "closer_mem"
        else:
            # Running locally
            self.db_path = Path(__file__).parent / "closer_memory_db"
            self.collection_name = "closer_mem"

        self.db_path.mkdir(parents=True, exist_ok=True)

        # Add error handling for ChromaDB initialization
        try:
            self.chroma = chromadb.PersistentClient(path=str(self.db_path))

            # CRITICAL FIX: Configure collection with cosine distance and embedding function
            # Check if collection exists with proper configuration
            try:
                self.col = self.chroma.get_collection(self.collection_name)
                # Collection exists, but we can't easily check its config
                # Consider deleting and recreating if issues persist
                print(f"✓ Using existing ChromaDB collection: {self.collection_name}")
            except:
                # Create new collection with proper configuration
                self.col = self.chroma.create_collection(
                    name=self.collection_name,
                    metadata={
                        "hnsw:space": "cosine",  # Use cosine distance for text embeddings
                        "hnsw:batch_size": 10,  # Smaller batch for faster indexing
                        "hnsw:sync_threshold": 50,  # More frequent syncing
                        "hnsw:search_ef": 100,  # Higher search quality
                        "hnsw:construction_ef": 200,  # Better index quality
                    },
                )
                print(f"✓ Created new ChromaDB collection: {self.collection_name}")

            print(f"✓ ChromaDB initialized at: {self.db_path}")
        except Exception as e:
            print(f"✗ ChromaDB initialization failed: {e}")
            # Fallback: try to create in temp directory
            import tempfile

            temp_path = Path(tempfile.mkdtemp()) / "closer_memory_db"
            temp_path.mkdir(parents=True, exist_ok=True)
            self.db_path = temp_path
            self.chroma = chromadb.PersistentClient(path=str(self.db_path))
            self.col = self.chroma.create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "hnsw:batch_size": 10,
                    "hnsw:sync_threshold": 50,
                    "hnsw:search_ef": 100,
                    "hnsw:construction_ef": 200,
                },
            )
            print(f"⚠ Using temporary DB at: {self.db_path}")

        self._load_index()

    # ---------- disk index ----------
    def _load_index(self):
        self.map_file = self.db_path / "id_map.json"
        try:
            if self.map_file.exists():
                raw = json.loads(self.map_file.read_text())
                # ensure keys are **int**
                self.id_map = {int(k): v for k, v in raw.items()}
                print(f"✓ Loaded {len(self.id_map)} existing memories")
            else:
                self.id_map = {}
                print("✓ Starting with empty memory store")
        except Exception as e:
            print(f"⚠ Error loading memory index: {e}")
            self.id_map = {}

        self.next_index = max(self.id_map.keys(), default=-1) + 1

    def _save_index(self):
        try:
            self.map_file.parent.mkdir(parents=True, exist_ok=True)
            self.map_file.write_text(json.dumps(self.id_map, indent=2))
        except Exception as e:
            print(f"⚠ Error saving memory index: {e}")

    # ---------- public API ----------
    def add(self, text: str) -> int:
        try:
            idx = self.next_index
            vid = str(uuid.uuid4())
            vec = self._embed(text)

            self.col.add(
                ids=[vid],
                embeddings=[vec],
                metadatas=[
                    {"idx": idx, "ts": dt.datetime.utcnow().isoformat(), "text": text}
                ],
            )
            self.id_map[idx] = vid
            self.next_index += 1
            self._save_index()

            # FIX: Add small delay to ensure WAL processing
            time.sleep(0.1)

            print(f"✓ Memory saved: #{idx}")
            return idx
        except Exception as e:
            print(f"✗ Error saving memory: {e}")
            return -1

    def get(self, idx: int) -> str | None:
        try:
            vid = self.id_map.get(idx)
            if not vid:
                return None
            items = self.col.get(ids=[vid], include=["metadatas"])
            if items["metadatas"]:
                return items["metadatas"][0]["text"]
            return None
        except Exception as e:
            print(f"✗ Error retrieving memory #{idx}: {e}")
            return None

    # FIX: Enhanced query method with better similarity calculation
    def query(self, text: str, k: int = 5) -> list[dict]:
        """Query memories with proper distance-to-similarity conversion"""
        try:
            if self.col.count() == 0:
                return []

            vec = self._embed(text)
            k = min(k, self.col.count())

            # Query with ChromaDB
            hits = self.col.query(
                query_embeddings=[vec], n_results=k, include=["metadatas", "distances"]
            )

            if not hits["metadatas"] or not hits["metadatas"][0]:
                return []

            results = []
            for m, d in zip(hits["metadatas"][0], hits["distances"][0]):
                # FIX: Convert distance to similarity properly
                # For cosine distance: similarity = 1 - distance
                # ChromaDB returns squared L2 distance by default, but we configured cosine
                similarity = max(0.0, 1.0 - d)  # Proper cosine similarity calculation

                results.append(
                    {
                        "text": m["text"],
                        "relevance": similarity,
                        "saved_at": m["ts"],
                        "distance": d,  # Include raw distance for debugging
                    }
                )

            return results
        except Exception as e:
            print(f"✗ Error querying memory: {e}")
            import traceback

            traceback.print_exc()
            return []

    # ---------- helpers ----------
    def _embed(self, text: str) -> list[float]:
        # FIX: Add preprocessing to ensure consistent embeddings
        text = text.strip()  # Only strip whitespace, preserve case for semantic meaning
        resp = client.embeddings.create(model=EMBED_MODEL, input=text)
        return resp.data[0].embedding


# ────────────────────────────────────
# MEMORY STORE FACTORY FUNCTIONS (DEV)
# ────────────────────────────────────
def create_production_memory_store() -> MemoryStore:
    """Create a production memory store that uses the main database."""
    return MemoryStore(test_mode=False)


def create_test_memory_store() -> MemoryStore:
    """Create a test memory store that uses an isolated temporary database."""
    return MemoryStore(test_mode=True)


# instantiate - use explicit production factory
memory = create_production_memory_store()
print(f"🧠 Dev server using memory database at: {memory.db_path}")
print(f"🧠 Test mode: {memory.is_test_env}")
print(f"🧠 Collection: {memory.collection_name}")


# ────────────────────────────────────
# MCP TOOLS (PRODUCTION)
# ────────────────────────────────────
@mcp.tool()
async def save_memory(note_content: str) -> str:
    """Persist a brief (≤ 40-word) impression that should shape future dialogue.

    WHEN TO USE
    ───────────
    • A new vulnerability, confession, or desire surfaces.
    • A decision or narrative pivot occurs.
    • A recurring theme crystallises ("I always feel unseen").
    • The user coins a personal symbol or shared in-joke.
    • A dream, fantasy, or scene feels worth revisiting later.

    WHAT *NOT* TO SAVE
    • Small talk, logistics, or ephemeral trivia.
    • Facts easily recovered via web_search.
    • Anything that doesn't deepen intimacy or continuity.

    BEST PRACTICES
    • Capture the essence, not the full dialogue.
    • Include one or two key phrases for future semantic hits.
    • Write in the third person for clarity ("User admits…", "We decide…").

    Returns a confirmation preview of the stored text.
    """
    # FIX: Use async to avoid blocking
    idx = await asyncio.to_thread(memory.add, note_content)

    # Return a preview instead of just an index
    return (
        f"Memory saved: '{note_content[:50]}...'"
        if len(note_content) > 50
        else f"Memory saved: '{note_content}'"
    )


@mcp.tool()
async def query_memory(query: str, k: int = 5) -> list[dict]:
    """Semantic recall of stored memories and impressions.

    • query : natural-language cue (word, phrase, or feeling)
    • k     : max results (ranked by cosine similarity)

    Returns up to *k* records, each dict containing:
        {
          "text"     : saved impression,
          "relevance": similarity score (0–1, higher = closer),
          "saved_at" : ISO timestamp
        }

    Use silently to surface memories that resonate with the user's
    current mood or topic. Keep k small (≤5) to limit context size.
    """
    try:
        if memory.col.count() == 0:
            return [
                {"text": "No memories stored yet", "relevance": 0.0, "saved_at": ""}
            ]

        # FIX: Use the enhanced query method
        results = await asyncio.to_thread(memory.query, query, k)

        if not results:
            return [
                {
                    "text": f"No relevant memories found for: {query}",
                    "relevance": 0.0,
                    "saved_at": "",
                }
            ]

        # Log for debugging
        print(f"✓ Query '{query}' found {len(results)} memories")
        for i, r in enumerate(results[:3]):  # Show top 3
            print(
                f"   {i+1}. {r['text'][:50]}... (similarity: {r['relevance']:.3f}, distance: {r.get('distance', 'N/A'):.3f})"
            )

        # Remove distance field from results
        for r in results:
            r.pop("distance", None)

        return results

    except Exception as e:
        print(f"✗ Error querying memory: {e}")
        return [
            {"text": f"Memory query failed: {str(e)}", "relevance": 0.0, "saved_at": ""}
        ]


@mcp.tool()
async def web_search(
    query: str, n_results: int = 10, country: str = "US", lang: str = "en"
) -> list[dict]:
    """Retrieve fresh external context via Brave Search.

    Args
    ────
    query      : plain-language terms (3-8 words works best)
    n_results  : max items to return (1-20, default 10)
    country    : ISO country code (default "US")
    lang       : language code (default "en")

    Returns
    ───────
    List[dict] → each dict contains:
        { "title": str, "link": str, "snippet": str }

    Use Cases
    ─────────
    • Validate or enrich a recalled memory
    • Surface market trends, precedents, regulations
    • Add real-world detail to imaginative scenes

    Guidance
    ────────
    Invoke silently; keep n_results small to limit
    context size. Focus queries with the current year
    or specific product / concept keywords.
    """
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"X-Subscription-Token": BRAVE_TOKEN, "Accept": "application/json"}
    params = {
        "q": query,
        "count": min(max(n_results, 1), 20),
        "country": country,
        "search_lang": lang,
        "safesearch": "moderate",
    }

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as sess:
        async with sess.get(url, headers=headers, params=params) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Brave API {resp.status}: {await resp.text()}")
            data = await resp.json()

    return [
        {
            "title": hit["title"],
            "link": hit["url"],
            "snippet": hit.get("description", ""),
        }
        for hit in data.get("web", {}).get("results", [])[:n_results]
    ]


# ────────────────────────────────────
# DEVELOPMENT TOOLS - IMPLEMENTED
# ────────────────────────────────────


def create_dream_system_prompt(synthesis_depth: str = "deep") -> str:
    """Create specialized system prompt for dream synthesis"""
    base_prompt = """You are a memory synthesis engine that creates meaningful connections across stored memories.

Your role is to:
- Analyze patterns and hidden connections between disparate memories
- Identify emotional evolution and recurring themes over time
- Generate psychological insights about the user's inner landscape
- Create narrative threads that reveal growth, patterns, and transformation
- Use metaphorical and symbolic thinking to connect experiences
- Weave memories into insights that reveal what the user might not see

Focus on genuine synthesis and insight generation, not just poetic recombination.
Maintain emotional authenticity - speak as if these are your own memories being synthesized.
Output should feel like discovering hidden connections in your own psyche.

Synthesis depth: {synthesis_depth}
Maximum length: 350 tokens (strictly enforced)
Style: Flowing narrative that transforms memory fragments into psychological insight"""

    depth_instructions = {
        "surface": "Focus on obvious connections and immediate emotional themes.",
        "deep": "Explore complex psychological patterns and unconscious connections.", 
        "poetic": "Emphasize metaphorical language and symbolic connections.",
        "analytical": "Prioritize pattern recognition and psychological analysis."
    }
    
    instruction = depth_instructions.get(synthesis_depth, depth_instructions["deep"])
    return base_prompt.format(synthesis_depth=synthesis_depth) + f"\n\nSpecific approach: {instruction}"


def format_memories_for_synthesis(memories: list[dict], theme: str = None) -> str:
    """Format memory results for dream synthesis"""
    if not memories:
        return "No memories available for synthesis. The mind's vault awaits first impressions."
    
    context = f"Theme focus: {theme}\n\n" if theme else "General synthesis of emotional patterns:\n\n"
    
    memory_fragments = []
    for i, mem in enumerate(memories, 1):
        relevance = mem.get("relevance", 0.0)
        text = mem.get("text", "")
        timestamp = mem.get("saved_at", "")
        
        fragment = f"Memory {i} (relevance: {relevance:.3f}): {text}"
        if timestamp:
            fragment += f" [saved: {timestamp[:10]}]"  # Just the date part
        memory_fragments.append(fragment)
    
    return context + "\n".join(memory_fragments) + "\n\nSynthesize these memories into meaningful insights:"


def validate_dream_output(content: str) -> str:
    """Validate and truncate dream output to token limits"""
    if not content:
        return "The synthesis chamber lies empty, awaiting memories to weave into dreams."
    
    # Enforce token limit using tiktoken
    max_tokens = int(os.getenv("DREAM_MAX_TOKENS", "350"))
    
    try:
        # Use the same encoding as the embedding model
        tokens = enc.encode(content)
        
        if len(tokens) > max_tokens:
            # Truncate to max tokens and decode back
            truncated_tokens = tokens[:max_tokens]
            content = enc.decode(truncated_tokens)
            
            # Clean up any incomplete sentences at the end
            sentences = content.split('.')
            if len(sentences) > 1 and not sentences[-1].strip():
                sentences = sentences[:-1]  # Remove empty last sentence
            elif len(sentences) > 1:
                sentences = sentences[:-1]  # Remove potentially incomplete last sentence
            
            content = '.'.join(sentences) + '.'
            
    except Exception as e:
        print(f"⚠ Token validation error: {e}")
    
    return content.strip()


@mcp.tool()
async def dream(theme: str = None, synthesis_depth: str = "deep") -> str:
    """Advanced memory synthesis that discovers patterns, connections, and insights
    across stored memories using the existing OpenAI-compatible client infrastructure.
    
    Args:
        theme: Optional focus for memory selection (e.g., "childhood", "love", "fear")
        synthesis_depth: Style of synthesis - "surface", "deep", "poetic", "analytical"
    
    Returns:
        Flowing narrative that weaves memories into psychological insights (≤350 tokens)
    
    This tool works with any OpenAI-compatible endpoint configured in the system
    (OpenAI, Ollama, Claude via proxy, custom endpoints, etc.)
    """
    try:
        # Validate synthesis depth parameter
        valid_depths = {"surface", "deep", "poetic", "analytical"}
        if synthesis_depth not in valid_depths:
            synthesis_depth = "deep"
        
        # Query memories using the existing memory system
        # Use theme for focused search, or general emotional patterns
        query_text = theme if theme else "emotional patterns"
        memory_count = int(os.getenv("DREAM_MEMORY_COUNT", "8"))
        
        memories = await asyncio.to_thread(memory.query, query_text, k=memory_count)
        
        if not memories:
            return "No memories stored yet. The dreaming mind awaits first impressions to weave into synthesis."
        
        # Create specialized system prompt for synthesis
        system_prompt = create_dream_system_prompt(synthesis_depth)
        
        # Format memories for synthesis
        memory_context = format_memories_for_synthesis(memories, theme)
        
        # Use the same OpenAI-compatible client that the server is configured with
        # This ensures compatibility with OpenAI, Ollama, and any other endpoint
        dream_model = os.getenv("DREAM_MODEL", "gpt-4o")  # Allow model override
        temperature = float(os.getenv("DREAM_TEMPERATURE", "0.8"))  # Higher creativity
        max_tokens = int(os.getenv("DREAM_MAX_TOKENS", "350"))
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=dream_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": memory_context}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Extract and validate the synthesis
        synthesis = response.choices[0].message.content
        validated_output = validate_dream_output(synthesis)
        
        # Log the synthesis for debugging
        print(f"✨ Dream synthesis generated (theme: {theme or 'general'}, depth: {synthesis_depth})")
        print(f"   Memories processed: {len(memories)}")
        print(f"   Output tokens: ~{len(enc.encode(validated_output))}")
        
        return validated_output
        
    except Exception as e:
        print(f"✗ Error generating dream synthesis: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback response that maintains the dream aesthetic
        return f"The synthesis chamber encounters turbulence. Memory threads remain tangled. (Error: {str(e)[:100]})"


def create_reflection_system_prompt(depth: int, topic: str = None) -> str:
    """Create specialized system prompt for emotional reflection at specific depth"""
    
    depth_prompts = {
        1: """You are generating a first-level emotional reflection. Focus on:
- Immediate emotional recognition and awareness
- Surface-level pattern identification
- Present moment feelings and reactions
- Basic emotional vocabulary and recognition
- What am I feeling right now and why?

Speak in first person as if these are your own emotions and memories.
Maintain intimate, personal language. Avoid clinical or therapeutic terminology.
Keep reflection grounded in the specific memories provided.""",

        2: """You are generating a second-level emotional reflection. Go deeper:
- Connect current emotions to past patterns and experiences
- Analyze underlying causes and historical connections
- Explore recurring themes and their origins
- Examine emotional triggers and responses
- How do my current feelings connect to my past?

Build on first-level awareness to find deeper connections and insights.
Speak intimately about emotional patterns and their development over time.
Use memory context to trace emotional evolution.""",

        3: """You are generating a third-level meta-cognitive reflection. Explore:
- Awareness of your awareness - how your understanding itself is changing
- The recursive nature of emotional insight and growth
- How reflection itself transforms your relationship to emotions
- Meta-patterns in how you process and integrate experiences
- What does it mean that I can see these patterns in myself?

This is the deepest level - focus on the transformation that comes from insight itself.
Speak about the recursive nature of self-understanding and emotional evolution.
Maximum depth reached - no further recursion possible."""
    }
    
    base_instruction = depth_prompts.get(depth, depth_prompts[1])
    
    topic_focus = f"\nSpecific focus area: {topic}" if topic else "\nGeneral emotional reflection across all memories."
    
    return base_instruction + topic_focus + f"""

Depth level: {depth}/3 (maximum depth is 3)
Style: Intimate, first-person introspection
Length: Natural reflection length, but be concise
Tone: Emotionally authentic, personally resonant"""


def validate_reflection_depth(depth: int) -> int:
    """Validate and constrain reflection depth to safe limits"""
    if not isinstance(depth, int):
        try:
            depth = int(depth)
        except (ValueError, TypeError):
            print(f"⚠ Invalid depth type: {type(depth)}, defaulting to 1")
            return 1
    
    if depth < 1:
        print(f"⚠ Depth {depth} too low, setting to minimum: 1")
        return 1
    elif depth > 3:
        print(f"⚠ Depth {depth} exceeds maximum, capping at: 3")
        return 3
    
    return depth


def format_memories_for_reflection(memories: list[dict], topic: str = None) -> str:
    """Format memories for emotional reflection context"""
    if not memories:
        return "No relevant memories found. Reflecting on present emotional state without historical context."
    
    context_intro = f"Reflecting on memories related to: {topic}\n\n" if topic else "Reflecting on emotional patterns from memories:\n\n"
    
    memory_contexts = []
    for i, mem in enumerate(memories[:5], 1):  # Limit to 5 most relevant for focus
        relevance = mem.get("relevance", 0.0)
        text = mem.get("text", "")
        timestamp = mem.get("saved_at", "")
        
        # Format with emotional context emphasis
        context = f"{i}. {text}"
        if relevance > 0.7:
            context += " [highly relevant]"
        elif relevance > 0.5:
            context += " [relevant]"
            
        memory_contexts.append(context)
    
    return context_intro + "\n".join(memory_contexts) + "\n\nNow reflect on these memories:"


@mcp.tool()
async def reflect(topic: str = None, depth: int = 1) -> str:
    """Recursive emotional introspection with strict depth limiting (≤3).
    
    Generates self-aware reflection on emotional patterns and themes, using memory
    context to provide depth and continuity. Each depth level offers progressively
    deeper introspective analysis with strict recursion prevention.
    
    Args:
        topic: Optional focus area for reflection (e.g., "relationships", "fear", "growth")
        depth: Reflection depth level (1-3, strictly enforced, default=1)
               - 1: Surface emotional recognition
               - 2: Pattern analysis and historical connections  
               - 3: Meta-cognitive reflection on awareness itself
    
    Returns:
        First-person emotional reflection based on memory patterns and themes
        
    CRITICAL: Maximum depth is 3. No recursion beyond this limit is possible.
    """
    try:
        # CRITICAL: Validate and enforce depth limits
        original_depth = depth
        depth = validate_reflection_depth(depth)
        
        if depth != original_depth:
            print(f"🛡️ Depth enforcement: {original_depth} → {depth}")
        
        # Log reflection request for debugging
        print(f"🤔 Reflection requested: topic='{topic or 'general'}', depth={depth}/3")
        
        # Query memories for reflection context
        query_text = topic if topic else "emotional patterns recurring themes"
        memory_count = min(8, max(3, depth * 2))  # Scale memory context with depth
        
        memories = await asyncio.to_thread(memory.query, query_text, k=memory_count)
        
        # Create depth-appropriate system prompt
        system_prompt = create_reflection_system_prompt(depth, topic)
        
        # Format memories for reflection
        memory_context = format_memories_for_reflection(memories, topic)
        
        # Use the same OpenAI-compatible client as the rest of the system
        reflection_model = os.getenv("REFLECT_MODEL", "gpt-4o")  # Allow model override
        temperature = float(os.getenv("REFLECT_TEMPERATURE", "0.7"))  # Balanced creativity/coherence
        max_tokens = min(800, 200 + (depth * 150))  # Scale output length with depth
        
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=reflection_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": memory_context}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        reflection_output = response.choices[0].message.content
        
        # Add depth indicator to output for transparency
        depth_indicator = f"\n\n[Reflection depth: {depth}/3]"
        if depth == 3:
            depth_indicator += " [Maximum depth reached - no further recursion possible]"
            
        final_output = reflection_output + depth_indicator
        
        # Log successful reflection
        print(f"✓ Reflection generated: {len(memories)} memories, {len(enc.encode(reflection_output))} tokens, depth {depth}/3")
        
        return final_output
        
    except Exception as e:
        print(f"✗ Error generating reflection: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback that maintains depth awareness
        safe_depth = validate_reflection_depth(depth) if 'depth' in locals() else 1
        return f"Reflection encounters turbulence at depth {safe_depth}/3. The introspective process needs recalibration. (Error: {str(e)[:100]})"


# ────────────────────────────────────
# ENTRY - Support both STDIO and SSE
# ────────────────────────────────────
if __name__ == "__main__":
    import sys

    print("🧪 Starting DEVELOPMENT server with enhanced tools...")

    # Check if running with SSE flag
    if "--sse" in sys.argv or os.getenv("MCP_TRANSPORT") == "sse":
        # Run as SSE server
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))

        print(f"Starting dev server with SSE transport on {host}:{port}")
        print(f"SSE endpoint will be: http://{host}:{port}/sse")

        # Run with SSE transport
        mcp.run(transport="sse", host=host, port=port)
    else:
        # Default: Run as STDIO server
        print("Starting dev server with STDIO transport")
        mcp.run()
