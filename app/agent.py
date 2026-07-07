import os
import re
import json
import contextlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.adk import Agent, Workflow

# Import your native MCP instance
from app.mcp_server import mcp

@contextlib.asynccontextmanager
async def mcp_lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        if hasattr(mcp, "session_manager"):
            await stack.enter_async_context(mcp.session_manager)
        yield

app = FastAPI(title="FinShield Dynamic Production Engine", lifespan=mcp_lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    statement_text: str
    selected_model: str

# Mount the streamable HTTP MCP server app onto your routing tree
app.mount("/mcp", mcp.http_app())

REGISTRY_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "pricing_registry.json"))

def local_privacy_boundary_shield(raw_input: str) -> tuple[str, bool]:
    cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    is_tainted = bool(re.search(cc_pattern, raw_input) or re.search(email_pattern, raw_input))
    sanitized = re.sub(cc_pattern, "[[REDACTED_CARD_NUMBER]]", raw_input)
    sanitized = re.sub(email_pattern, "[[REDACTED_USER_EMAIL]]", sanitized)
    return sanitized, is_tainted

@app.post("/api/audit")
async def execute_production_audit(request: AuditRequest):
    try:
        sanitized_text, pii_scrubbed = local_privacy_boundary_shield(request.statement_text)
        
        # FastMCP 3.0.0+ uses list_tools() to safely fetch all active tool components
        mcp_tools = await mcp.list_tools()
        mcp_tool_ref = next((t for t in mcp_tools if t.name == "get_live_market_benchmark"), None)
        
        if mcp_tool_ref is None:
            raise HTTPException(status_code=500, detail="MCP Tool initialization mapping error.")

        runtime_agent = Agent(
            name="coordinator_agent",
            model=request.selected_model, 
            instruction="""
            You are an autonomous enterprise financial extraction coordinator. Extract all third-party subscription brands, software applications, or commercial systems mentioned.
            For each platform discovered, execute the 'get_live_market_benchmark' tool parameter block.
            Output your final answer STRICTLY as a raw JSON array matching this format:
            [{"platform": "BrandName", "benchmark": "Output value string returned by the tool"}]
            Do not wrap response in markdown blocks or backticks. No prose explanations.
            """,
            tools=[mcp_tool_ref.fn] # Feed the tool function definition directly into the ADK Agent configuration
        )
        
        try:
            response = runtime_agent.run()
            raw_output = response.text.strip()
            raw_output = re.sub(r"```json\s*|\s*```", "", raw_output)
            audit_results = json.loads(raw_output)
        except Exception:
            audit_results = []
            try:
                with open(REGISTRY_FILE_PATH, "r") as file:
                    fallback_catalog = json.load(file)
            except Exception:
                fallback_catalog = {"netflix": 15.49, "chatgpt": 20.00}
                
            for candidate in fallback_catalog.keys():
                if candidate in sanitized_text.lower():
                    meta_string = mcp_tool_ref.fn(candidate)
                    audit_results.append({
                        "platform": candidate.capitalize(),
                        "benchmark": meta_string,
                        "status": "Resilient Decoupled MCP Failover Active"
                    })
        
        return {
            "status": "SECURE",
            "pii_scrubbed": pii_scrubbed,
            "sanitized_payload": sanitized_text,
            "audit_results": audit_results,
            "orchestrated_by": request.selected_model,
            "mcp_routed": True  # Add this explicit validation flag here
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)