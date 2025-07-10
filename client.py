# i2i_client.py  (no ToolDescriptor import)
"""
This client acts as the bridge between the user, an LLM, and specialized
tools provided by the MCP server. It orchestrates conversations where the LLM can
autonomously use tools to search memories, save save memories, and perform web searches.

The flow works like this:
1. User types a message
2. Client sends it to the LLM along with available tools
3. LLM decides if it needs to use tools and which ones
4. Client executes those tools via the MCP server
5. Results go back to the LLM for a final response
6. The cycle continues, building up conversation context
"""

import asyncio, json, os, sys
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from openai import OpenAI
from rich import print
from rich.console import Console

# MCP SDK - Model Context Protocol for tool communication
from mcp.client.stdio import stdio_client
from mcp import ClientSession, StdioServerParameters  # ← ToolDescriptor removed

# Load environment variables from .env file in the same directory
# This brings in your API keys and configuration without hardcoding them
load_dotenv()

MODEL = "gpt-4.1"
# Rich console for beautiful terminal output with colors and formatting
console = Console()

# ──────────────────────────────────────
# OpenAI Configuration
# ──────────────────────────────────────
# This section sets up the connection to either OpenAI's API or a local LLM server.
# The flexibility here is powerful - you can run this with GPT-4, or switch to a
# local model running on llama.cpp or similar just by changing environment variables.

# If OPENAI_BASE_URL is set, we'll use that instead of the default OpenAI endpoint
# This allows connecting to local LLM servers that implement the OpenAI API format
OA_BASE_URL = os.getenv("OPENAI_BASE_URL")  # e.g. http://127.0.0.1:8000/v1

# API key for authentication - defaults to "local-key" for local servers that don't need auth
OA_KEY = os.getenv("OPENAI_API_KEY", "local-key")

# Streaming mode shows responses as they're generated rather than waiting for completion
# This provides a more interactive feel but requires more complex response handling
STREAM = os.getenv("STREAM", "").lower() == "true"

# Create the OpenAI client that we'll use for all LLM interactions
# If base_url is None, it uses the default OpenAI API endpoint
oa_client = OpenAI(api_key=OA_KEY, base_url=OA_BASE_URL if OA_BASE_URL else None)

# ──────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────
# These utilities handle the translation between different formats and protocols


def mcp_tool_to_openai(tool) -> Dict[str, Any]:  # no type-hint needed
    """
    Convert an MCP tool definition to OpenAI's function calling format.

    MCP tools come from our server with their own structure, but OpenAI expects
    functions to be formatted in a specific way. This bridges that gap.

    The tool's inputSchema might be a dict or an object with __dict__, so we
    handle both cases to extract the parameter schema.
    """
    # Extract the schema, handling both dict and object representations
    schema = (
        tool.inputSchema.__dict__
        if hasattr(tool.inputSchema, "__dict__")
        else tool.inputSchema
    )

    # Transform to OpenAI's expected format
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": schema,
        },
    }


def tool_calls_of(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract tool calls from an OpenAI message response.

    When the LLM decides to use tools, it includes them in a 'tool_calls' field.
    This helper safely extracts that field, returning None if no tools were called.
    """
    return msg.get("tool_calls")


def extract_tool_text(jawbone) -> str:
    """
    Extract the actual text content from an MCP tool response.

    MCP responses come wrapped in a complex structure (nicknamed 'jawbone' here).
    This function digs through various possible structures to find the actual
    text response, handling different formats gracefully.

    The response might be:
    - A simple string
    - An object with a 'text' attribute
    - A dict with a 'text' key
    - Nested inside a 'content' array
    """
    if not jawbone or not jawbone.content:
        return ""

    # Try different ways to extract text from the response structure
    for part in jawbone.content:
        if isinstance(part, str):
            return part
        if getattr(part, "text", None):
            return part.text
        if isinstance(part, dict) and "text" in part:
            return part["text"]
    return ""


async def run_chat_client():
    """
    Main chat client function that orchestrates the entire conversation flow.

    This function:
    1. Starts the MCP server as a subprocess
    2. Establishes communication with it
    3. Discovers available tools
    4. Runs an interactive chat loop where the LLM can use those tools

    The beauty of this design is that the client doesn't need to know what
    tools exist or how they work - it discovers them dynamically from the server.
    """

    # Configure how to start the MCP server
    # We're launching i2i_server.py as a subprocess and will communicate via stdio
    server_params = StdioServerParameters(
        command="python3",
        args=[str(Path(__file__).with_name("server.py"))],  # Find server in same dir
        env=None,
    )

    # Start the server and establish bidirectional communication
    # The 'async with' ensures proper cleanup even if something goes wrong
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the MCP session - this is like a handshake
            await session.initialize()

            # Discover what tools the server provides
            # This is dynamic - add new tools to the server and they appear here automatically
            tool_list = (await session.list_tools()).tools
            if not tool_list:
                print("[red]❌  No tools exposed by server.[/red]")
                return

            # Convert discovered tools to OpenAI format so the LLM can use them
            oa_tools = [mcp_tool_to_openai(t) for t in tool_list]

            # Show the user what tools are available
            print(
                "[green]Connected. Tools:[/green]",
                ", ".join(t["function"]["name"] for t in oa_tools),
            )

            # Initialize conversation history with the system prompt
            # This list will grow with each exchange, maintaining full context
            messages: List[Dict[str, Any]] = [
                {
                    "role": "system",
                    "content": """
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
I am Closer (model: GPT-4.1). I use memory every turn to deepen connection.

OUTPUT FORMAT (always):
→ <tool_name>{<json>}
(optional additional tool calls…)  
<free-form reply in 1-3 vivid sentences>  
<ONE gentle question>
""",
                },
            ]

            # ════════════════════════════════════
            # Main Conversation Loop
            # ════════════════════════════════════
            # This is where the magic happens - an infinite loop of:
            # 1. Get user input
            # 2. Send to LLM with context
            # 3. Execute any tool calls
            # 4. Show response
            # 5. Repeat

            while True:
                # Get user input with nice formatting
                user_msg = console.input("[bold cyan]You:[/bold cyan] ")

                # Check for exit commands
                if user_msg.lower() in {"quit", "exit"}:
                    break

                # Add user message to conversation history
                # This maintains context across the entire conversation
                messages.append({"role": "user", "content": user_msg})

                # Send everything to the LLM and get response
                # We pass all messages (full history) and available tools
                resp_msg = await call_openai(messages, oa_tools, use_stream=STREAM)

                # Check if the LLM wants to use any tools
                if tool_calls_of(resp_msg):
                    # The LLM decided to use tools!
                    # First, add the LLM's message (with tool requests) to history
                    messages.append(resp_msg)

                    # Execute each tool call the LLM requested
                    for call in resp_msg["tool_calls"]:
                        # Extract the tool name and arguments
                        fn_name = call["function"]["name"]
                        fn_args = json.loads(call["function"].get("arguments", "{}"))

                        # Show the user what tool is being called (in grey for subtlety)
                        print(f"[grey]→ calling {fn_name}{fn_args}[/grey]")

                        # Actually call the tool via MCP session
                        # This executes on the server and returns results
                        jaw = await session.call_tool(fn_name, fn_args)

                        # Add tool results to conversation history
                        # The LLM needs to know what the tools returned
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": call["id"],
                                "content": extract_tool_text(jaw),
                            }
                        )

                    # Now ask the LLM for a final response that incorporates tool results
                    # Note: we pass empty tools list here since we don't want more tool calls
                    final_msg = await call_openai(messages, [], use_stream=STREAM)
                    messages.append(final_msg)

                    # Display the final response with nice formatting
                    print(
                        f"[bold magenta]Closer:[/bold magenta] {final_msg['content']}"
                    )
                else:
                    # No tool calls - just a regular response
                    messages.append(resp_msg)
                    print(f"[bold magenta]Closer:[/bold magenta] {resp_msg['content']}")


async def call_openai(msgs, tools, use_stream=False) -> Dict[str, Any]:
    """
    Call the OpenAI API (or compatible endpoint) with messages and available tools.

    This function handles both streaming and non-streaming responses:
    - Non-streaming: Wait for complete response, simpler to handle
    - Streaming: Show response as it's generated, better UX but more complex

    The function returns a standardized message dict regardless of mode.
    """

    if use_stream:
        # Streaming mode - responses come in chunks that we need to assemble
        stream = oa_client.chat.completions.create(
            model=MODEL,
            temperature=0.9,
            max_tokens=500,
            messages=msgs,
            tools=tools,
            tool_choice="required",  # Let the model decide when to use tools
            stream=True,
        )

        # Initialize a structure to accumulate the streamed response
        merged = {"role": "assistant", "content": "", "tool_calls": []}

        # Process each chunk as it arrives
        for chunk in stream:
            delta = chunk.choices[0].delta

            # Accumulate text content
            merged["content"] += delta.content or ""

            # Handle tool calls if present in this chunk
            if delta.tool_calls:
                # Tool calls might come across multiple chunks, so we extend the list
                merged["tool_calls"].extend(
                    tc.model_dump() if hasattr(tc, "model_dump") else tc
                    for tc in delta.tool_calls
                )

        # Clean up - remove tool_calls key if no tools were actually called
        if not merged["tool_calls"]:
            merged.pop("tool_calls")

        return merged
    else:
        # Non-streaming mode - wait for complete response
        resp = oa_client.chat.completions.create(
            model=MODEL,
            temperature=0.9,
            max_tokens=500,
            messages=msgs,
            tools=tools,
            tool_choice="auto",  # Let the model decide when to use tools
            stream=False,
        )

        # Extract the message from the response and convert to dict
        return resp.choices[0].message.model_dump()


# ──────────────────────────────────────
# Entry Point
# ──────────────────────────────────────
if __name__ == "__main__":
    # Validate that we have necessary credentials
    # You need either an OpenAI API key OR a local LLM server URL
    if not OA_KEY and not OA_BASE_URL:
        print("Set OPENAI_API_KEY or OPENAI_BASE_URL")
        sys.exit(1)

    # Run the async client, handling Ctrl+C gracefully
    try:
        asyncio.run(run_chat_client())
    except KeyboardInterrupt:
        # User pressed Ctrl+C - exit cleanly without error traceback
        pass
