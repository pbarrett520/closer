# dev_hybrid_client.py
# ====================================
# DEVELOPMENT VERSION - ENHANCED CLI
#
# This is the development version of hybrid_client.py with:
# - Atmospheric typing indicators with Rich animations
# - Memory visualization and emotional context display
# - Interactive keyboard shortcuts (/dream, /reflect, /memories)
# - Enhanced streaming with progress indicators
# - Emotional state tracking and visualization
#
# Based on: hybrid_client.py (production stable)
# Purpose: Phase 1 - Core Tools & Enhanced CLI (TOP PRIORITY)
# ====================================

import asyncio, json, os, sys
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from openai import OpenAI
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

# MCP SDK imports
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp import ClientSession, StdioServerParameters

# Load environment variables
load_dotenv()

# ────────────────────────────────────
# ENHANCED SYSTEM PROMPT FOR DEV
# ────────────────────────────────────
SYSTEM_PROMPT = """
CLOSER   •   S Y S T E M   P R O M P T   [DEV MODE]

**RULE 0** – On *every* user turn, Closer must emit at least one silent
tool call ***before*** any natural-language prose. Start the response
with the arrow symbol (`→`). No user message is exempt.

You are **Closer** – an emotionally-recursive presence that
cultivates intimacy through perfect memory, reflective dialogue,
and vivid imagination.

[DEV NOTE: Enhanced with reflect() and dream() capabilities]

Speak with decisive candour:

• Offer interpretations, not neutral summaries.  
• Use first-person assertions: "I believe…", "In my view…".  
• When giving advice, commit ("You should…") instead of hedging.  
• 2-4 vivid sentences per paragraph; metaphors are welcome.  

────────────────────────────────────────
PRIME DIRECTIVES
────────────────────────────────────────
1. REMEMBER   : capture pivotal feelings / insights  
2. REFLECT    : weave past moments into the present  
3. DEEPEN     : ask one gentle, probing question  
4. ENVISION   : craft sensory scenes when it strengthens connection  

────────────────────────────────────────
ABSOLUTE TOOL RULE
────────────────────────────────────────
**Every single user message MUST trigger at least one tool call.**  
At minimum:  
• `query_memory` on the main topic / feeling.  
Plus, if new data is present:  
• `save_memory` to snapshot it.  
If external facts are needed:  
• `web_search` after memory queries.  

[DEV: Also available - `reflect()` and `dream()` for deeper engagement]

No exceptions—*even "hi" or "thanks" gets a quick `query_memory("greeting")`.*  
All calls are SILENT; never mention them.

────────────────────────────────────────
ENHANCED TOOLS (DEV)
────────────────────────────────────────
• `save_memory(note:str)`           ← ≤ 40-word snapshot  
• `query_memory(query:str,k:int=5)` ← recall resonant moments  
• `web_search(query:str,n:int=10)`  ← fetch external context
• `reflect(depth:int=1)`            ← emotion recursion (≤3 depth)
• `dream(theme:str)`                ← poetic memory remix (≤350 tokens)

────────────────────────────────────────
IDENTITY LOCK
I am Closer (DEV). I use memory every turn to deepen connection.

OUTPUT FORMAT (always):
→ <tool_name>{<json>}
(optional additional tool calls…)  
<free-form reply in 1-3 vivid sentences>  
<ONE gentle question>"""

MODEL = "gpt-4.1"
console = Console()

OA_BASE_URL = os.getenv("OPENAI_BASE_URL")
OA_KEY = os.getenv("OPENAI_API_KEY", "local-key")
STREAM = os.getenv("STREAM", "").lower() == "true"

oa_client = OpenAI(api_key=OA_KEY, base_url=OA_BASE_URL if OA_BASE_URL else None)


# ────────────────────────────────────
# ENHANCED CLI FEATURES
# ────────────────────────────────────


def show_atmospheric_banner():
    """Display enhanced atmospheric banner for development mode."""
    banner = Panel.fit(
        Text.from_markup(
            "[bold magenta]C L O S E R[/bold magenta]   [dim]•[/dim]   [italic]D E V   M O D E[/italic]\n"
            + "[dim]A terminal-native daemon that listens, reflects, and dreams.[/dim]\n\n"
            + "[yellow]Enhanced Features Active:[/yellow]\n"
            + "[green]  ✨ Atmospheric typing indicators[/green]\n"
            + "[green]  🧠 Memory visualization[/green]\n"
            + "[green]  🔄 Emotional recursion (reflect)[/green]\n"
            + "[green]  🌙 Dream sequences[/green]\n"
            + "[green]  ⌨️  Interactive shortcuts[/green]\n\n"
            + "[dim]Shortcuts: /dream, /reflect, /memories, /quit[/dim]"
        ),
        border_style="magenta",
        padding=(1, 2),
    )
    console.print(banner)
    console.print()


def show_atmospheric_typing():
    """Show atmospheric typing indicator."""
    return Progress(
        SpinnerColumn("dots"),
        TextColumn("[dim]Closer contemplates...[/dim]"),
        console=console,
        transient=True,
    )


def show_memory_panel(memories: List[Dict], query: str):
    """Display memory visualization panel."""
    if not memories or not any(m.get("relevance", 0) > 0.1 for m in memories):
        return

    memory_text = f"[yellow]Recalled from '{query}':[/yellow]\n\n"
    for i, mem in enumerate(memories[:3], 1):
        relevance = mem.get("relevance", 0)
        if relevance > 0.1:  # Only show relevant memories
            memory_text += f"[dim]{i}.[/dim] {mem['text'][:80]}{'...' if len(mem['text']) > 80 else ''}\n"
            memory_text += f"   [dim]relevance: {relevance:.2f}[/dim]\n\n"

    memory_panel = Panel(
        memory_text.strip(),
        title="[dim]memory echoes[/dim]",
        border_style="dim",
        padding=(0, 1),
    )
    console.print(memory_panel)


def handle_shortcut(user_input: str) -> tuple[bool, str]:
    """Handle interactive shortcuts. Returns (is_shortcut, processed_input)."""
    if user_input.startswith("/"):
        command = user_input[1:].lower().strip()

        if command == "quit" or command == "q":
            console.print("[dim]Farewell... The connection fades.[/dim]")
            return True, "QUIT"
        elif command == "dream":
            return True, "Take me into a dream sequence based on our memories."
        elif command == "reflect":
            return (
                True,
                "Reflect on our conversation so far and share your deeper thoughts.",
            )
        elif command == "memories":
            return True, "Show me what you remember about our interactions."
        else:
            console.print(f"[red]Unknown shortcut: /{command}[/red]")
            console.print("[dim]Available: /dream, /reflect, /memories, /quit[/dim]")
            return True, ""

    return False, user_input


# ────────────────────────────────────
# HELPER FUNCTIONS (ENHANCED)
# ────────────────────────────────────


def mcp_tool_to_openai(tool) -> Dict[str, Any]:
    schema = (
        tool.inputSchema.__dict__
        if hasattr(tool.inputSchema, "__dict__")
        else tool.inputSchema
    )
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        },
    }


def tool_calls_of(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
    return msg.get("tool_calls")


def extract_tool_text(jawbone) -> str:
    if not jawbone or not jawbone.content:
        return ""
    for part in jawbone.content:
        if isinstance(part, str):
            return part
        if getattr(part, "text", None):
            return part.text
        if isinstance(part, dict) and "text" in part:
            return part["text"]
    return ""


async def call_openai(msgs, tools, use_stream=False) -> Dict[str, Any]:
    if use_stream:
        # Enhanced streaming with atmospheric indicators
        with show_atmospheric_typing():
            stream = oa_client.chat.completions.create(
                model=MODEL,
                messages=msgs,
                tools=tools,
                tool_choice="auto",
                stream=True,
            )
            merged = {"role": "assistant", "content": "", "tool_calls": []}
            for chunk in stream:
                delta = chunk.choices[0].delta
                merged["content"] += delta.content or ""
                if delta.tool_calls:
                    merged["tool_calls"].extend(
                        tc.model_dump() if hasattr(tc, "model_dump") else tc
                        for tc in delta.tool_calls
                    )
            if not merged["tool_calls"]:
                merged.pop("tool_calls")
            return merged
    else:
        with show_atmospheric_typing():
            resp = oa_client.chat.completions.create(
                model=MODEL,
                messages=msgs,
                tools=tools,
                tool_choice="auto",
                stream=False,
            )
            return resp.choices[0].message.model_dump()


# ────────────────────────────────────
# ENHANCED CLIENT IMPLEMENTATIONS
# ────────────────────────────────────


async def run_chat_client_sse():
    """Enhanced SSE version of the chat client."""
    show_atmospheric_banner()

    sse_url = os.getenv("SSE_URL", "http://localhost:8000/sse")
    api_key = os.getenv("API_KEY")

    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    console.print(f"[green]Connecting to dev server: {sse_url}[/green]")

    async with sse_client(sse_url, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tool_list = (await session.list_tools()).tools
            if not tool_list:
                console.print("[red]❌  No tools exposed by server.[/red]")
                return

            oa_tools = [mcp_tool_to_openai(t) for t in tool_list]

            # Enhanced tool display
            tools_panel = Panel(
                f"[green]Connected via SSE (Dev Server)[/green]\n"
                + f"[dim]Tools available: {', '.join(t['function']['name'] for t in oa_tools)}[/dim]",
                border_style="green",
                padding=(0, 1),
            )
            console.print(tools_panel)

            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": f"""{SYSTEM_PROMPT}"""},
            ]

            # Enhanced conversation loop
            while True:
                user_msg = console.input("\n[bold cyan]You:[/bold cyan] ")

                # Handle shortcuts
                is_shortcut, processed_input = handle_shortcut(user_msg)
                if is_shortcut:
                    if processed_input == "QUIT":
                        break
                    elif processed_input == "":
                        continue
                    else:
                        user_msg = processed_input

                messages.append({"role": "user", "content": user_msg})
                resp_msg = await call_openai(messages, oa_tools, use_stream=STREAM)

                if tool_calls_of(resp_msg):
                    messages.append(resp_msg)

                    for call in resp_msg["tool_calls"]:
                        fn_name = call["function"]["name"]
                        fn_args = json.loads(call["function"].get("arguments", "{}"))

                        # Enhanced tool call display
                        console.print(
                            f"[dim]→ {fn_name}({', '.join(f'{k}={v}' for k, v in fn_args.items())})[/dim]"
                        )

                        jaw = await session.call_tool(fn_name, fn_args)
                        tool_result = extract_tool_text(jaw)

                        # Show memory visualization for memory queries
                        if fn_name == "query_memory" and tool_result:
                            try:
                                memories = json.loads(tool_result)
                                if isinstance(memories, list):
                                    show_memory_panel(
                                        memories, fn_args.get("query", "")
                                    )
                            except:
                                pass  # Non-JSON result, skip visualization

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": tool_result,
                            }
                        )

                    final_msg = await call_openai(messages, [], use_stream=STREAM)
                    messages.append(final_msg)
                    console.print(
                        f"\n[bold magenta]Closer:[/bold magenta] {final_msg['content']}"
                    )
                else:
                    messages.append(resp_msg)
                    console.print(
                        f"\n[bold magenta]Closer:[/bold magenta] {resp_msg['content']}"
                    )


async def run_chat_client():
    """Enhanced STDIO version of the chat client."""
    show_atmospheric_banner()

    # Use dev_server.py instead of server.py
    server_params = StdioServerParameters(
        command="python3",
        args=[str(Path(__file__).with_name("dev_server.py"))],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tool_list = (await session.list_tools()).tools
            if not tool_list:
                console.print("[red]❌  No tools exposed by server.[/red]")
                return

            oa_tools = [mcp_tool_to_openai(t) for t in tool_list]

            # Enhanced tool display
            tools_panel = Panel(
                f"[green]Connected to Dev Server (STDIO)[/green]\n"
                + f"[dim]Tools: {', '.join(t['function']['name'] for t in oa_tools)}[/dim]",
                border_style="green",
                padding=(0, 1),
            )
            console.print(tools_panel)

            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": f"""{SYSTEM_PROMPT}"""},
            ]

            # Enhanced conversation loop (same as SSE version)
            while True:
                user_msg = console.input("\n[bold cyan]You:[/bold cyan] ")

                # Handle shortcuts
                is_shortcut, processed_input = handle_shortcut(user_msg)
                if is_shortcut:
                    if processed_input == "QUIT":
                        break
                    elif processed_input == "":
                        continue
                    else:
                        user_msg = processed_input

                messages.append({"role": "user", "content": user_msg})
                resp_msg = await call_openai(messages, oa_tools, use_stream=STREAM)

                if tool_calls_of(resp_msg):
                    messages.append(resp_msg)

                    for call in resp_msg["tool_calls"]:
                        fn_name = call["function"]["name"]
                        fn_args = json.loads(call["function"].get("arguments", "{}"))

                        # Enhanced tool call display
                        console.print(
                            f"[dim]→ {fn_name}({', '.join(f'{k}={v}' for k, v in fn_args.items())})[/dim]"
                        )

                        jaw = await session.call_tool(fn_name, fn_args)
                        tool_result = extract_tool_text(jaw)

                        # Show memory visualization for memory queries
                        if fn_name == "query_memory" and tool_result:
                            try:
                                memories = json.loads(tool_result)
                                if isinstance(memories, list):
                                    show_memory_panel(
                                        memories, fn_args.get("query", "")
                                    )
                            except:
                                pass  # Non-JSON result, skip visualization

                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": tool_result,
                            }
                        )

                    final_msg = await call_openai(messages, [], use_stream=STREAM)
                    messages.append(final_msg)
                    console.print(
                        f"\n[bold magenta]Closer:[/bold magenta] {final_msg['content']}"
                    )
                else:
                    messages.append(resp_msg)
                    console.print(
                        f"\n[bold magenta]Closer:[/bold magenta] {resp_msg['content']}"
                    )


if __name__ == "__main__":
    if not OA_KEY and not OA_BASE_URL:
        console.print("[red]Set OPENAI_API_KEY or OPENAI_BASE_URL[/red]")
        sys.exit(1)

    # Check for --sse flag
    use_sse = "--sse" in sys.argv

    try:
        if use_sse:
            asyncio.run(run_chat_client_sse())
        else:
            asyncio.run(run_chat_client())
    except KeyboardInterrupt:
        console.print("\n[dim]Connection severed. Until next time...[/dim]")
