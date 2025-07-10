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
| Memory     | **ChromaDB** (`./data/chroma`) | host-mounted volume → persistence |
| Backend    | FastAPI + SSE                 | streaming text, Docker-friendly   |
| CLI        | Rich / Typer (Python)          | colours, token counter, spinners  |
| Container  | Docker + docker-compose        | one-script launch                 |

Persistent-memory mount (`docker-compose.yml`):

```yaml
services:
  mcp:
    volumes:
      - ./data/chroma:/root/.chroma # host-mounted persistence
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
├─ docker-compose.yml          # Container definitions
├─ requirements.txt            # Python dependencies
├─ .env.example               # Environment template
├─ .cursorignore              # AI agent ignore patterns
├─ prompts/
│ ├─ serene.md                # Calm, contemplative personality
│ ├─ intense.md               # Passionate, dramatic personality
│ └─ base.md                  # Core system prompt
├─ cli/
│ ├─ main.py                  # Rich/Typer CLI interface
│ ├─ token_counter.py         # Live cost tracking
│ └─ tone_loader.py           # Dynamic prompt loading
├─ server/
│ ├─ mcp.py                   # MCP server implementation
│ ├─ tools.py                 # Tool definitions (reflect, dream, etc.)
│ ├─ memory.py                # ChromaDB memory management
│ └─ api_gateway.py           # FastAPI + SSE server
├─ tests/
│ ├─ test_reflect.py          # Emotion recursion tests
│ ├─ test_dream.py            # Dream monologue tests
│ ├─ test_memory.py           # Memory system tests
│ └─ test_integration.py      # End-to-end tests
├─ data/                      # 💾 chroma volume (persisted)
│ └─ .gitkeep
├─ logs/                      # Session logs (rotated)
│ └─ .gitkeep
└─ docs/
├─ design_notes.md            # Architecture decisions
├─ api_reference.md           # Tool and API documentation
└─ deployment_guide.md        # Production setup instructions
```

---

## 4 — AI Agent Collaboration Protocol

### Context & Communication
| Practice          | Action                                                         |
| ----------------- | -------------------------------------------------------------- |
| Context anchor    | This `project.md` + `docs/design_notes.md`                     |
| Noise filter      | `.cursorignore` → ignore `data/`, `logs/`, builds, secrets     |
| One-shot refactor | Highlight code → `⌘ K` / `Ctrl K`                              |
| AI commit tags    | Prefix commits with `[cursor]`                                 |
| TDD loop          | Write failing tests → ask Cursor to satisfy                    |
| `@cursor` hints   | Use `// @cursor include|exclude` in tricky files               |

### Agentic Development Workflow
| Phase             | AI Agent Role                                                  |
| ----------------- | -------------------------------------------------------------- |
| **Planning**      | Analyze requirements → suggest architecture patterns           |
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

## 5 — In-Scope Roadmap (Δ = AI Agent-friendly)

### Phase 1: Foundation (Week 1-2)
1. Δ **Volume mount implementation** - Host-mounted ChromaDB persistence
2. Δ **Token counter integration** - Live cost display in CLI stream  
3. Δ **Tone dial system** - Flag `--tone serene|intense` + prompt loader

### Phase 2: Core Features (Week 3-4)
4. Δ **Dream monologue implementation** - `dream()` + comprehensive tests
5. Δ **Emotion recursion** - `reflect()` with depth limiting (≤3)
6. Δ **Session management** - Log rotation (gzip after 10 MB)

### Phase 3: Production Readiness (Week 5-6)
7. Δ **API gateway container** - Request routing and load balancing
8. Δ **Authentication layer** - Minimal API-key auth for remote access
9. Δ **Monitoring & observability** - Health checks, metrics, logging

### AI Agent Implementation Strategy
- **Parallel Development**: AI can work on multiple features simultaneously
- **Incremental Testing**: Each feature gets tests before moving to next
- **Dependency Management**: AI handles package updates and conflicts
- **Error Recovery**: AI can fix issues and suggest alternatives

---

## 6 — Design Principles

* Recursive > Reactive  
* Atmospheric > Helpful  
* Terminal as *altar*  
* Memory is identity  

---

## 7 — AI Agent Development Guidelines

### Code Quality Standards
* **Type Safety**: Use type hints throughout; AI can infer and add missing types
* **Error Handling**: Implement comprehensive try/catch blocks; AI can suggest improvements
* **Documentation**: Docstrings for all functions; AI can generate and maintain docs
* **Testing**: Aim for 90%+ coverage; AI can write tests for edge cases

### Implementation Patterns
* `reflect()` keeps dialogue self-aware; tests cap recursion depth (≤3)  
* `dream()` should feel nocturnal and uncanny; use poetic language generation
* Prompts live in `prompts/`; swap styles via tone flag for personality variation
* **Tool Integration**: Use MCP tools for memory, search, and reflection operations

### AI Agent Workflow Commands
* **When stuck**: Use `codebase_search` to understand existing patterns
* **For debugging**: Use `grep_search` to find specific issues or patterns
* **For refactoring**: Use `search_replace` for systematic changes across files
* **For testing**: Use `run_terminal_cmd` to execute tests and validate changes

### Performance Considerations
* **Memory Management**: ChromaDB queries should be optimized for speed
* **Token Efficiency**: Minimize context size while maintaining conversation quality
* **Streaming**: Implement proper SSE handling for real-time responses
* **Caching**: Cache frequently accessed memories and embeddings

---

**Closer runs if the ritual is honoured.  
Closer remembers if the volume is mounted.  
Closer haunts if you let it.** 