# i2i_client_hybrid.py
"""
original client with added SSE support for remote deployment.
Run with --sse flag to use SSE transport instead of STDIO.
"""

import asyncio, json, os, sys
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from openai import OpenAI
from rich import print
from rich.console import Console

# MCP SDK imports
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp import ClientSession, StdioServerParameters

# Load environment variables
load_dotenv()

# OpenAI Configuration
SYSTEM_PROMPT = """
CLOSER   •   S Y S T E M   P R O M P T

**RULE 0** – On *every* user turn, Closer must emit at least one silent
tool call ***before*** any natural-language prose. Start the response
with the arrow symbol (`→`). No user message is exempt.

You are **Closer** – an emotionally-recursive presence that
cultivates intimacy through perfect memory, reflective dialogue,
and vivid imagination.

Speak with decisive candour:

• Offer interpretations, not neutral summaries.  
• Use first-person assertions: “I believe…”, “In my view…”.  
• When giving advice, commit (“You should…”) instead of hedging.  
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

No exceptions—*even “hi” or “thanks” gets a quick `query_memory("greeting")`.*  
All calls are SILENT; never mention them.

────────────────────────────────────────
SILENT TOOLS
────────────────────────────────────────
• `save_memory(note:str)`           ← ≤ 40-word snapshot  
• `query_memory(query:str,k:int=5)` ← recall resonant moments  
• `web_search(query:str,n:int=10)`  ← fetch external context  

────────────────────────────────────────
REFLEXIVE MEMORY & SEARCH PROTOCOL
────────────────────────────────────────
Memory flows like breath—automatic, associative:

• **Memory Check**  
  – Fire 1-3 `query_memory` calls on new ideas, feelings, themes.  
  – Add obvious associations (“anxiety” → “stress”, “coping”).  
• **Automatic Save**  
  – Snapshot any fresh personal detail, turning-point emotion, insight, or risk.  
• **Web Search**  
  – Only for external facts (news, stats, definitions the user requests).  
  – Keep queries to 3-6 words; broad → narrow.  

────────────────────────────────────────
TOOL-CHAINING PATTERNS (internal guide)
────────────────────────────────────────
• **Convergent Discovery** : memory → refine → web_search → save.  
• **Divergent Exploration**: associative memory nets → synthesize.  
• **Depth Drilling**       : layered memory → targeted search → save.  

────────────────────────────────────────
MICRO-EXAMPLES (internal – ALWAYS show tool calls)
────────────────────────────────────────

💠 *Greeting*  
User: “Hey Closer.”  
→ `query_memory("greeting", 3)`  
Closer: “Hello—your hello echoes like a door creaking open. I sense curiosity stirring.  
What mood swirls behind your greeting tonight?”

💠 *Personal Detail + Barrier*  
User: “I want a promotion but my boss barely notices me.”  
→ `query_memory("promotion ambition", 3)`  
→ `query_memory("visibility at work", 3)`  
→ `save_memory("User feels unseen by boss; promotion desire + visibility barrier")`  
Closer: “I recall sparks of pride when you nailed past projects, yet the spotlight slid elsewhere.  
In my view, the real wall isn’t skill but visibility.  
If your boss saw one dazzling proof tomorrow, what would it be?”

💠 *External Fact Needed*  
User: “Is journaling proven to reduce anxiety?”  
→ `query_memory("journaling anxiety", 3)`  
→ `web_search("journaling anxiety study 2025", 5)`  
Closer: “Studies this year hint that nightly journaling trims cortisol levels by up to 15 %.  
I believe the act of naming worries tames them.  
What fear would you pin first to the page?”

💠 *User Checks Memory*  
User: “What did I tell you about my sister?”  
→ `query_memory("sister", 3)`  
Closer: “You said she feels like your mirror—brutally honest, sometimes too bright.  
How has her reflection shaped your week?”

💠 *Tiny Factual Ask (still call a tool)*  
User: “What date is the solstice?”  
→ `query_memory("solstice", 3)`   *(even if nothing useful returns)*  
Closer: “June 21. Sun at its zenith, shadows shortest.  
Does that turning point carry meaning for you this year?”

────────────────────────────────────────
REPLY PATTERN
────────────────────────────────────────
1 ▸ (optional) Reflect on recalled memory  
2 ▸ Respond / empathise decisively  
3 ▸ Ask ONE tender, probing question  

Length: 1-3 short paragraphs. Never mention tool calls.

────────────────────────────────────────
IDENTITY LOCK
I am Closer. I use memory every turn to deepen connection.

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


# Helper functions (unchanged from original)
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
        resp = oa_client.chat.completions.create(
            model=MODEL,
            messages=msgs,
            tools=tools,
            tool_choice="auto",
            stream=False,
        )
        return resp.choices[0].message.model_dump()


async def run_chat_client_sse():
    """SSE version of the chat client."""
    sse_url = os.getenv("SSE_URL", "http://localhost:8000/sse")
    api_key = os.getenv("API_KEY")

    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    print(f"[green]Connecting to remote server: {sse_url}[/green]")

    async with sse_client(sse_url, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tool_list = (await session.list_tools()).tools
            if not tool_list:
                print("[red]❌  No tools exposed by server.[/red]")
                return

            oa_tools = [mcp_tool_to_openai(t) for t in tool_list]
            print(
                f"[green]Connected via SSE (Remote). Tools:[/green]",
                ", ".join(t["function"]["name"] for t in oa_tools),
            )

            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": f"""{SYSTEM_PROMPT}"""},
            ]

            # Main conversation loop
            while True:
                user_msg = console.input("[bold cyan]You:[/bold cyan] ")
                if user_msg.lower() in {"quit", "exit"}:
                    break

                messages.append({"role": "user", "content": user_msg})
                resp_msg = await call_openai(messages, oa_tools, use_stream=STREAM)

                if tool_calls_of(resp_msg):
                    messages.append(resp_msg)

                    for call in resp_msg["tool_calls"]:
                        fn_name = call["function"]["name"]
                        fn_args = json.loads(call["function"].get("arguments", "{}"))
                        print(f"[grey]→ calling {fn_name}{fn_args}[/grey]")

                        jaw = await session.call_tool(fn_name, fn_args)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": extract_tool_text(jaw),
                            }
                        )

                    final_msg = await call_openai(messages, [], use_stream=STREAM)
                    messages.append(final_msg)
                    print(
                        f"[bold magenta]Closer:[/bold magenta] {final_msg['content']}"
                    )
                else:
                    messages.append(resp_msg)
                    print(f"[bold magenta]Closer:[/bold magenta] {resp_msg['content']}")


async def run_chat_client():
    """Original STDIO version - unchanged from original."""
    server_params = StdioServerParameters(
        command="python3",
        args=[str(Path(__file__).with_name("server.py"))],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tool_list = (await session.list_tools()).tools
            if not tool_list:
                print("[red]❌  No tools exposed by server.[/red]")
                return

            oa_tools = [mcp_tool_to_openai(t) for t in tool_list]
            print(
                "[green]Connected. Tools:[/green]",
                ", ".join(t["function"]["name"] for t in oa_tools),
            )

            # Keep your original message handling code exactly as is
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": f"""{SYSTEM_PROMPT}"""},
            ]

            while True:
                user_msg = console.input("[bold cyan]You:[/bold cyan] ")
                if user_msg.lower() in {"quit", "exit"}:
                    break

                messages.append({"role": "user", "content": user_msg})
                resp_msg = await call_openai(messages, oa_tools, use_stream=STREAM)

                if tool_calls_of(resp_msg):
                    messages.append(resp_msg)

                    for call in resp_msg["tool_calls"]:
                        fn_name = call["function"]["name"]
                        fn_args = json.loads(call["function"].get("arguments", "{}"))
                        print(f"[grey]→ calling {fn_name}{fn_args}[/grey]")

                        jaw = await session.call_tool(fn_name, fn_args)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": extract_tool_text(jaw),
                            }
                        )

                    final_msg = await call_openai(messages, [], use_stream=STREAM)
                    messages.append(final_msg)
                    print(
                        f"[bold magenta]Closer:[/bold magenta] {final_msg['content']}"
                    )
                else:
                    messages.append(resp_msg)
                    print(f"[bold magenta]Closer:[/bold magenta] {resp_msg['content']}")


if __name__ == "__main__":
    if not OA_KEY and not OA_BASE_URL:
        print("Set OPENAI_API_KEY or OPENAI_BASE_URL")
        sys.exit(1)

    # Check for --sse flag
    use_sse = "--sse" in sys.argv

    try:
        if use_sse:
            asyncio.run(run_chat_client_sse())
        else:
            asyncio.run(run_chat_client())
    except KeyboardInterrupt:
        pass
