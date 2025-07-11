# server.py
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

mcp = FastMCP("closer")


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
                or "test" in sys.argv[0].lower()
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
# MEMORY STORE FACTORY FUNCTIONS
# ────────────────────────────────────
def create_production_memory_store() -> MemoryStore:
    """Create a production memory store that uses the main database."""
    return MemoryStore(test_mode=False)


def create_test_memory_store() -> MemoryStore:
    """Create a test memory store that uses an isolated temporary database."""
    return MemoryStore(test_mode=True)


# instantiate
memory = MemoryStore()


# ────────────────────────────────────
# MCP TOOLS
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
# ENTRY - Support both STDIO and SSE
# ────────────────────────────────────
if __name__ == "__main__":
    import sys

    # Check if running with SSE flag
    if "--sse" in sys.argv or os.getenv("MCP_TRANSPORT") == "sse":
        # Run as SSE server
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))

        print(f"Starting i2i server with SSE transport on {host}:{port}")
        print(f"SSE endpoint will be: http://{host}:{port}/sse")

        # Add auth middleware if API keys are configured
        # if API_KEYS:
        # print(f"API key authentication enabled ({len(API_KEYS)} keys configured)")

        # Run with SSE transport
        # FastMCP handles the SSE paths automatically
        mcp.run(transport="sse", host=host, port=port)
    else:
        # Default: Run as STDIO server
        print("Starting i2i server with STDIO transport")
        mcp.run()
