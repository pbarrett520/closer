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
├─ test_memory.py             # Memory system tests
├─ test_mcp_tools.py          # Tool integration tests
├─ test_reflect.py            # Reflect tool tests (depth limiting)
├─ test_dream.py              # Dream tool tests (token limits)
├─ test_dev_integration.py    # Development feature tests
├─ closer_memory_db/          # 💾 ChromaDB persistence (auto-created)
├─ logs/                      # Session logs (auto-created)
├─ WINDOWS_SETUP.md           # Windows-specific setup guide
└─ project.md                 # This file
```

**Note**: `hybrid_client.py` is the actual production client used by startup scripts. `client.py` is deprecated and unused.

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

### Phase 1: Core Tools & Enhanced CLI (Week 1-2) - **TOP PRIORITY**
1. Δ **`reflect()` tool implementation** - Emotion recursion with depth limiting (≤3)
   - Recursive self-dialogue generation
   - Memory integration for emotional context
   - Depth enforcement with comprehensive tests
   - Poetic, introspective response style

2. Δ **`dream()` tool implementation** - Poetic memory remix (≤350 tokens)
   - Memory querying and narrative weaving
   - Atmospheric, nocturnal language generation
   - Theme-based dream focusing
   - Sensory, uncanny atmosphere creation

3. Δ **Enhanced CLI experience** - "Cooler" terminal interface
   - Atmospheric typing indicators with Rich animations
   - Memory visualization and emotional context display
   - Interactive keyboard shortcuts (`/dream`, `/reflect`, `/memories`)
   - Enhanced streaming with progress indicators
   - Emotional state tracking and visualization

### Phase 2: Foundation (Week 3-4)
4. Δ **Volume mount implementation** - Host-mounted ChromaDB persistence
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

### Development Files Strategy
- **`dev_server.py`**: Add `reflect()` and `dream()` tools to existing MCP server
- **`dev_hybrid_client.py`**: Enhanced CLI with atmospheric elements and shortcuts
- **`test_reflect.py`**: Depth limiting and recursion tests
- **`test_dream.py`**: Token limits and memory integration tests
- **`test_dev_integration.py`**: End-to-end testing of new features

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

*The technical setup is a filter, not a flaw. Docker configs and API keys are the price of entry to something genuine.*  

---

## 8 — AI Agent Development Guidelines

### Code Quality Standards
* **Type Safety**: Use type hints throughout; AI can infer and add missing types
* **Error Handling**: Implement comprehensive try/catch blocks; AI can suggest improvements
* **Documentation**: Docstrings for all functions; AI can generate and maintain docs
* **Testing**: Aim for 90%+ coverage; AI can write tests for edge cases

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

### AI Agent Workflow Commands
* **When stuck**: Use `