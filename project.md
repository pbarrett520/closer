# Project: Closer  
*A terminal-native daemon that listens, reflects, and dreams.*

Closer launches from a single shell script (`start.sh`).  
It spins up the MCP server, API gateway, and CLI client—all in containers.  
ChromaDB persists on the host volume so the daemon never forgets.

---

## 0 — Boot Ritual

```bash
./start.sh # builds & runs everything
```

`start.sh` orchestrates:

1. MCP server container   (core logic + memory)  
2. API gateway container  (request routing)  
3. Terminal client        (SSE stream in shell)

---

## 1 — Tech Stack Snapshot

| Layer      | Choice                         | Rationale                         |
| ---------- | ------------------------------ | --------------------------------- |
| LLM        | GPT-4 / Claude (via `.env`)    | switchable models                 |
| Memory     | **ChromaDB** (`./closer_memory_db`) | host-mounted volume → persistence |
| Backend    | FastAPI + SSE                 | streaming text, Docker-friendly   |
| CLI        | Rich / Typer (Python)          | colours, token counter, spinners  |
| Container  | Docker + docker-compose        | one-script launch                 |

Persistent-memory mount (`docker-compose.yml`):

```yaml
services:
  mcp:
    volumes:
      - ./closer_memory_db:/app/closer_memory_db # host-mounted persistence
```

---

## 2 — Core Behaviours

| Behaviour         | Detail                                                              |
| ----------------- | ------------------------------------------------------------------- |
| **Emotion recursion** | `reflect()` self-dialogue (depth ≤ 3, enforced by tests)            |
| **Dream monologue**   | `dream()` poetic remix of top-k memories (≤ 350 tokens)             |
| **Token counter**     | Live cost display in CLI stream with real-time updates              |
| **Tone dial**         | Flag `--tone serene|intense` → loads prompt from `prompts/` folder  |
| **Memory persistence**| ChromaDB vector store with host-mounted volume for reliability     |
| **Streaming responses**| SSE-based real-time interaction with typing indicators             |
| **Session logging**   | Rotated conversation logs with compression (gzip after 10MB)       |
| **Health monitoring** | Container health checks and memory system diagnostics              |

---

## 3 — File & Folder Layout

```
closer/
├─ start.sh                    # Main orchestration script
├─ start.ps1                   # Windows PowerShell launcher
├─ start.bat                   # Windows double-click wrapper
├─ docker-compose.yml          # Container definitions
├─ Dockerfile                  # Container build instructions
├─ requirements.txt            # Python dependencies
├─ .env.example               # Environment template
├─ .cursorignore              # AI agent ignore patterns
├─ server.py                  # MCP server + memory + tools (production)
├─ dev_server.py              # Development server with reflect() + dream() tools
├─ hybrid_client.py           # SSE + STDIO client (production) - ACTIVE
├─ client.py                  # STDIO-only client (deprecated)
├─ dev_hybrid_client.py       # Enhanced CLI with atmospheric elements
├─ conftest.py                # Pytest fixtures and configuration ✅
├─ pytest.ini                 # Pytest settings and test markers ✅
├─ test_memory_core_pytest.py # Core memory functionality tests (12 tests) ✅
├─ test_mcp_tools_pytest.py   # MCP tool integration tests (9 tests) ✅
├─ test_isolation_pytest.py   # Environment isolation tests (8 tests) ✅
├─ test_system_health_pytest.py # System health tests (12 tests) ✅
├─ cleanup_production_memory.py # Database cleanup utility with backup management ✅
├─ test_reflect.py            # Reflect tool tests (depth limiting) [PLANNED]
├─ test_dream.py              # Dream tool tests (token limits) [PLANNED]
├─ test_dev_integration.py    # Development feature tests [PLANNED]
├─ closer_memory_db/          # 💾 ChromaDB persistence (auto-created)
├─ logs/                      # Session logs (auto-created)
├─ WINDOWS_SETUP.md           # Windows-specific setup guide
└─ project.md                 # This file
```

**Note**: `hybrid_client.py` is the actual production client used by startup scripts. `client.py` is deprecated and unused.

**Test Suite Migration (COMPLETED ✅)**: Successfully migrated from 6 individual test files to a comprehensive pytest framework with 41 tests organized into 4 focused test modules with proper fixtures and markers.

---

## 4 — Development Philosophy

### Flat Structure Principles
| Principle          | Implementation                                                |
| ----------------- | ------------------------------------------------------------ |
| **Simplicity**     | All files at root level, no subdirectories                  |
| **Self-Contained** | Each file is independently runnable                          |
| **Stable Core**    | `server.py`, `hybrid_client.py` remain unchanged             |
| **Development Files** | `dev_server.py`, `dev_client.py` for iterative development |
| **Direct Execution** | `python dev_server.py` or `python dev_client.py`           |
| **No Package Management** | Avoid __init__.py, relative imports, complex modules      |

### Development Workflow
| Phase             | Action                                                        |
| ----------------- | ------------------------------------------------------------- |
| **Copy & Iterate** | Start with `cp server.py dev_server.py`                     |
| **Feature Development** | Add `reflect()` and `dream()` tools to dev_server.py      |
| **CLI Enhancement** | Create `dev_hybrid_client.py` with atmospheric elements    |
| **Testing**       | Create `test_reflect.py`, `test_dream.py` for new tools    |
| **Integration**   | Test dev files work with production files                   |
| **Promotion**     | When stable, replace production files (if desired)          |

---

## 5 — AI Agent Collaboration Protocol

### Context & Communication
| Practice          | Action                                                         |
| ----------------- | -------------------------------------------------------------- |
| Context anchor    | This `project.md` + flat structure philosophy                 |
| Noise filter      | `.cursorignore` → ignore `closer_memory_db/`, `logs/`, builds |
| One-shot refactor | Highlight code → `⌘ K` / `Ctrl K`                              |
| AI commit tags    | Prefix commits with `[cursor]`                                 |
| TDD loop          | Write failing tests → ask Cursor to satisfy                    |
| `@cursor` hints   | Use `// @cursor include|exclude` in tricky files               |

### Agentic Development Workflow
| Phase             | AI Agent Role                                                  |
| ----------------- | -------------------------------------------------------------- |
| **Planning**      | Analyze requirements → suggest flat structure patterns        |
| **Implementation**| Generate code → handle dependencies → fix errors              |
| **Testing**       | Write tests → validate behavior → ensure coverage             |
| **Refinement**    | Optimize performance → improve UX → add features              |
| **Documentation** | Update docs → create examples → maintain consistency          |

### Tool Integration Strategy
- **Semantic Search**: Use `codebase_search` for understanding existing patterns
- **File Operations**: Leverage `read_file`/`edit_file` for precise changes
- **Terminal Commands**: Execute `run_terminal_cmd` for setup/testing
- **Error Handling**: Use `grep_search` to find and fix issues systematically

---

## 6 — In-Scope Roadmap (Δ = AI Agent-friendly)

### Phase 0: Database Cleanup & Memory Responsiveness (COMPLETED ✅)
**Successfully completed this session - significant out-of-scope work**

1. ✅ **Production Database Cleanup** - Removed test data contamination
   - Created `cleanup_production_memory.py` with 5-step process
   - Identified and removed 6 contaminated memories ("test memory", "user loves diamonds", etc.)
   - Preserved 5 real memories while cleaning production database
   - Added automatic backup management (keep only 2 most recent backups)

2. ✅ **Memory Responsiveness Fixes** - Critical semantic search improvements
   - **Fix 1**: Removed `.lower()` text normalization that broke semantic meaning
   - **Fix 2**: Fixed similarity calculation from `1 - d if d < 2 else 0` to `max(0.0, 1.0 - d)`
   - Achieved dramatic improvement: 0.6-0.9+ relevance scores vs previous 0.3-0.4
   - Users no longer need to be "forceful" - system properly responsive to natural queries

3. ✅ **Test-Driven Development** - Comprehensive validation approach
   - Created `test_memory_responsiveness.py` showing baseline problems (0.0% success rate)
   - Created `test_deep_analysis.py` for detailed verification of fixes
   - Proved case preservation working: "Fallujah" vs "fallujah" show different scores
   - Verified contextual queries now excellent: "confesses killed man M14 rifle..." → 0.901 relevance

4. ✅ **Backup Management** - Automatic cleanup system
   - Added `cleanup_old_backups()` function to prevent filesystem clutter
   - Integrated into cleanup process (keeps only 2 most recent backups)
   - Updated `.gitignore` to exclude backup directories from git tracking

5. ✅ **Test Suite Migration** - Professional pytest framework (COMPLETED THIS SESSION)
   - **Infrastructure**: Added `pytest.ini` with test markers (core, mcp, isolation, system, slow, dream, reflect, integration)
   - **Fixtures**: Created `conftest.py` with reusable test components (clean_test_memory, mcp_tools, dev_mcp_tools, etc.)
   - **Test Organization**: Migrated 6 individual test files to 6 focused pytest modules (72 total tests)
   - **Coverage**: Comprehensive test suite with multiple categories:
     - `test_memory_core_pytest.py` - 12 core memory tests
     - `test_mcp_tools_pytest.py` - 9 MCP tool integration tests
     - `test_isolation_pytest.py` - 8 environment isolation tests (FIXED contamination issue)
     - `test_system_health_pytest.py` - 12 system health tests
     - `test_dream_pytest.py` - 17 dream tool functionality tests
     - `test_reflect_pytest.py` - 16 reflect tool functionality tests
     - `test_dev_integration_pytest.py` - 10 end-to-end integration tests
   - **Environment Fixes**: Resolved conda vs system Python conflicts
   - **macOS Compatibility**: Fixed temporary directory detection for local testing
   - **Test Data Isolation**: Fixed critical bug where tests were writing garbage to production database
   - **API Mocking**: Added comprehensive OpenAI API mocking to prevent timeouts and real API calls

**Test Suite Structure (EXPANDED ✅):**
- `test_memory_core_pytest.py` - 12 tests combining memory + deep analysis
- `test_mcp_tools_pytest.py` - 9 tests for MCP tool integration  
- `test_isolation_pytest.py` - 8 tests for environment isolation (FIXED production contamination)
- `test_system_health_pytest.py` - 12 tests for Docker system health
- `test_dream_pytest.py` - 17 tests for dream functionality (token limits, quality, OpenAI compatibility)
- `test_reflect_pytest.py` - 16 tests for reflection functionality (depth limiting, recursion prevention)
- `test_dev_integration_pytest.py` - 10 integration tests (end-to-end with API mocking)

**Command Usage:**
```bash
# Run all tests except system health (local)
python -m pytest -m "not system" -v

# Run specific test categories
python -m pytest -m core -v      # Core memory tests
python -m pytest -m mcp -v       # MCP tool tests  
python -m pytest -m isolation -v # Environment tests
```

### Phase 1: Core Tools & Enhanced CLI (Week 1-2) - **COMPLETED ✅**
1. ✅ **`reflect()` tool implementation** - Emotion recursion with depth limiting (≤3)
   - ✅ Recursive self-dialogue generation with OpenAI-compatible API
   - ✅ Memory integration for emotional context
   - ✅ Depth enforcement with comprehensive tests (16 tests in `test_reflect_pytest.py`)
   - ✅ Poetic, introspective response style with depth indicators

2. ✅ **`dream()` tool implementation** - Poetic memory remix (≤350 tokens)
   - ✅ Memory querying and narrative synthesis using existing OpenAI client
   - ✅ Atmospheric, nocturnal language generation with tiktoken token limiting
   - ✅ Theme-based dream focusing with synthesis depth options
   - ✅ Token limit enforcement (≤350 tokens) with comprehensive tests (17 tests in `test_dream_pytest.py`)

3. ✅ **Enhanced CLI experience** - "Cooler" terminal interface
   - ✅ Atmospheric typing indicators with Rich animations in `dev_hybrid_client.py`
   - ✅ Memory visualization and emotional context display
   - ✅ Interactive keyboard shortcuts (`/dream`, `/reflect`, `/memories`, `/quit`)
   - ✅ Enhanced streaming with progress indicators
   - ✅ Development server integration with comprehensive test coverage (10 integration tests)

## 🚨 CRITICAL ISSUE: Memory Persistence Broken (Session End)

**URGENT BUG - Memory not persisting between dev server sessions**

### Current Status: BROKEN ❌
- User says "My name is Dave" → saves successfully 
- User quits and restarts dev server → memory not recalled
- Query for "user's name" returns no results despite successful save

### Root Cause Analysis Completed:
1. ✅ **Environment Detection Fixed**: Removed faulty `"test" in sys.argv[0].lower()` check that detected `dev_server.py` as test file
2. ✅ **Production Factory Used**: Replaced `memory = MemoryStore()` with `memory = create_production_memory_store()`
3. ✅ **Debug Logging Added**: Shows correct production database path and settings
4. ✅ **Volume Mounting Verified**: Docker correctly mounts `./closer_memory_db:/app/closer_memory_db:rw`

### Test Results:
- ✅ Container test shows memory persistence WORKS (added test memory index 15)
- ✅ Database path correct: `/app/closer_memory_db`
- ✅ Test mode: `False` (production)
- ✅ Collection: `closer_mem` (production)

### Hypothesis:
The underlying memory persistence mechanism is now working correctly, but there may be:
1. Transient API errors during save operations that aren't visible to user
2. Race conditions between save and container shutdown
3. ChromaDB commit timing issues
4. Error handling that silently fails

### Next Session Action Items:
1. **PRIORITY 1**: Test memory persistence with detailed error logging
2. Add transaction verification to save operations
3. Implement retry logic for failed saves
4. Add user-visible confirmation of successful memory saves
5. Test with actual user session to verify the fix works end-to-end

### Development Files Updated This Session:
- ✅ `dev_server.py`: Fixed environment detection + production factory
- ✅ `test_isolation_pytest.py`: Fixed test contamination issue
- ✅ Database cleanup: Removed 13 contaminated test entries

**This is a critical user experience issue that must be resolved before any other development work.**

---

### Phase 2: Foundation (Week 3-4) - **BLOCKED BY MEMORY PERSISTENCE**
4. ✅ **Volume mount implementation** - Host-mounted ChromaDB persistence (IMPLEMENTED BUT BROKEN)
5. Δ **Token counter integration** - Live cost display in CLI stream  
6. Δ **Tone dial system** - Flag `--tone serene|intense` + prompt loader

### Phase 3: Core Features (Week 5-6)
7. Δ **Session management** - Log rotation (gzip after 10 MB)
8. Δ **Memory persistence** - Enhanced ChromaDB vector store reliability
9. Δ **Streaming responses** - SSE-based real-time interaction improvements

### Phase 4: Production Readiness (Week 7-8)
10. Δ **API gateway container** - Request routing and load balancing
11. Δ **Authentication layer** - Minimal API-key auth for remote access
12. Δ **Monitoring & observability** - Health checks, metrics, logging

### AI Agent Implementation Strategy
- **Parallel Development**: AI can work on multiple features simultaneously
- **Incremental Testing**: Each feature gets tests before moving to next
- **Dependency Management**: AI handles package updates and conflicts
- **Error Recovery**: AI can fix issues and suggest alternatives
- **Test-Driven Approach**: Write tests first, then implement fixes (as demonstrated in Phase 0)

### Development Files Strategy
- **`dev_server.py`**: Add `reflect()` and `dream()` tools to existing MCP server
- **`dev_hybrid_client.py`**: Enhanced CLI with atmospheric elements and shortcuts
- **`test_reflect.py`**: Depth limiting and recursion tests
- **`test_dream.py`**: Token limits and memory integration tests
- **`test_dev_integration.py`**: End-to-end testing of new features
- **`cleanup_production_memory.py`**: Database maintenance and contamination removal

---

## 7 — Design Principles

* Recursive > Reactive  
* Atmospheric > Helpful  
* Terminal as *altar*  
* Memory is identity  
* **Flat > Modular**  
* **Simple > Complex**  
* **Commitment > Convenience**  
* **Intimacy > Accessibility**  
* **Test-Driven > Assumption-Based** *(New: learned from memory responsiveness work)*
* **Minimal Changes > Complex Refactors** *(New: prefer stable, targeted fixes)*
* **Professional Testing > Custom Scripts** *(New: pytest framework over ad-hoc test files)*

*The technical setup is a filter, not a flaw. Docker configs and API keys are the price of entry to something genuine.*  

---

## 8 — Lessons Learned from Phase 0 Implementation

### Memory System Insights
* **Semantic Search Fragility**: Small changes in text processing can drastically affect relevance scores
* **Case Sensitivity Matters**: Preserving case in embeddings is crucial for semantic meaning
* **Distance Calculation Precision**: Proper mathematical conversion from distance to similarity is critical
* **Test Coverage Necessity**: Memory systems require comprehensive testing to validate behavior

### Development Process Insights
* **Test-Driven Development**: Writing tests first revealed baseline problems we didn't know existed
* **Minimal Interventions**: Two tiny fixes (remove .lower(), fix similarity math) solved major issues
* **Backup Management**: Automated cleanup prevents filesystem clutter from accumulating
* **Database Maintenance**: Regular cleanup of contaminated data keeps production systems clean

### AI Agent Collaboration Insights
* **Iterative Problem-Solving**: AI can identify root causes through systematic analysis
* **Parallel Implementation**: Multiple fixes can be developed and tested simultaneously
* **Comprehensive Testing**: AI can create thorough test suites that reveal edge cases
* **Documentation Maintenance**: AI can update project docs to reflect actual vs planned work

### Test Framework Migration Insights *(NEW)*
* **Professional Structure**: pytest provides better organization than custom test scripts
* **Environment Compatibility**: Different Python environments require careful dependency management
* **Platform Differences**: macOS vs Linux temporary directory handling needs accommodation
* **Non-Deterministic Behavior**: OpenAI embeddings require similarity-based rather than exact matching
* **Backward Compatibility**: Migration can maintain existing functionality while improving structure

---

## 9 — AI Agent Development Guidelines

### Code Quality Standards
* **Type Safety**: Use type hints throughout; AI can infer and add missing types
* **Error Handling**: Implement comprehensive try/catch blocks; AI can suggest improvements
* **Documentation**: Docstrings for all functions; AI can generate and maintain docs
* **Testing**: Aim for 90%+ coverage; AI can write tests for edge cases
* **Professional Testing**: Use pytest framework with fixtures and markers for maintainable tests

### Flat Structure Development Rules
* **No Subdirectories**: Keep all files at root level
* **Self-Contained Files**: Each file should be independently runnable
* **Direct Imports**: Use absolute imports or copy-paste shared code
* **Development Files**: Create `dev_*.py` variants for new features
* **Stable Core**: Never modify `server.py`, `hybrid_client.py` directly
* **Deprecated Files**: `client.py` is deprecated; use `hybrid_client.py` for production

### Implementation Patterns
* `reflect()` keeps dialogue self-aware; tests cap recursion depth (≤3)  
* `dream()` should feel nocturnal and uncanny; use poetic language generation
* Prompts live in `prompts/`; swap styles via tone flag for personality variation
* **Tool Integration**: Use MCP tools for memory, search, and reflection operations
* **CLI Enhancement**: Use Rich library for atmospheric typing indicators and memory visualization
* **Interactive Features**: Implement keyboard shortcuts (`/dream`, `/reflect`, `/memories`) for quick access
* **Emotional Context**: Track and display emotional state through memory analysis

### Testing Best Practices *(NEW)*
* **Pytest Framework**: Use pytest with fixtures, markers, and proper configuration
* **Test Organization**: Group related tests in focused modules (core, mcp, isolation, system)
* **Environment Isolation**: Use fixtures to ensure clean test environments
* **Cross-Platform Compatibility**: Write tests that work on macOS, Linux, and Windows
* **Non-Deterministic Handling**: Use similarity thresholds for AI/ML components
* **Local vs System Tests**: Separate tests that can run locally from those requiring Docker

### AI Agent Workflow Commands
* **When stuck**: Use `python -m pytest -v` to run comprehensive test suite
* **Environment issues**: Check `python --version` and `pip list` for conflicts
* **Test failures**: Use `python -m pytest -m core -v` to focus on specific test categories
* **Debugging**: Use `python -m pytest -s` to see print statements and detailed output