"""
Framework adapters for parsing traces from popular agent frameworks.
"""

from typing import List, Dict, Any, Optional
import json
import re

class TraceParser:
    """Base class for trace parsers."""
    
    def parse(self, data: Any) -> List[Dict[str, str]]:
        raise NotImplementedError

class OpenAIParser(TraceParser):
    def parse(self, data: Any) -> List[Dict[str, str]]:
        actions = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    agent = item.get("agent") or item.get("agent_name") or "openai_agent"
                    action = item.get("action") or item.get("function") or "unknown"
                    actions.append({"agent": agent, "action": action})
        elif isinstance(data, dict):
            steps = data.get("steps") or data.get("messages") or []
            for step in steps:
                if isinstance(step, dict):
                    agent = step.get("agent") or step.get("role") or "openai_agent"
                    action = step.get("action") or step.get("content") or "message"
                    actions.append({"agent": agent, "action": action})
        return actions

class AutoGenParser(TraceParser):
    def parse(self, data: Any) -> List[Dict[str, str]]:
        actions = []
        if isinstance(data, list):
            for msg in data:
                if isinstance(msg, dict):
                    sender = msg.get("sender") or msg.get("from") or "autogen_agent"
                    tool_calls = msg.get("tool_calls") or []
                    if tool_calls:
                        for tc in tool_calls:
                            if isinstance(tc, dict):
                                action = tc.get("name") or tc.get("function") or "tool_call"
                                actions.append({"agent": sender, "action": action})
                    else:
                        actions.append({"agent": sender, "action": "send_message"})
        elif isinstance(data, dict):
            for key, value in data.items():
                if key in ("messages", "conversation"):
                    return self.parse(value)
        return actions

class CrewAIParser(TraceParser):
    def parse(self, data: Any) -> List[Dict[str, str]]:
        actions = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    agent = item.get("agent") or item.get("role") or "crew_agent"
                    action = item.get("task") or item.get("action") or item.get("tool") or "unknown"
                    actions.append({"agent": agent, "action": action})
        elif isinstance(data, dict):
            tasks = data.get("tasks") or data.get("results") or []
            for task in tasks:
                if isinstance(task, dict):
                    agent = task.get("agent") or task.get("assigned_to") or "crew_agent"
                    action = task.get("name") or task.get("description") or "execute_task"
                    actions.append({"agent": agent, "action": action})
        return actions

class LangGraphParser(TraceParser):
    def parse(self, data: Any) -> List[Dict[str, str]]:
        actions = []
        if isinstance(data, dict):
            nodes = data.get("nodes") or data.get("steps") or []
            for node in nodes:
                if isinstance(node, dict):
                    agent = node.get("agent") or node.get("config", {}).get("agent") or "langgraph_node"
                    action = node.get("type") or node.get("name") or node.get("action") or "execute"
                    actions.append({"agent": agent, "action": action})
        return actions

class MCPParser(TraceParser):
    """Parse MCP (Model Context Protocol) logs."""
    def parse(self, data: Any) -> List[Dict[str, str]]:
        actions = []
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    agent = entry.get("agent_id") or entry.get("agent") or "mcp_agent"
                    action = entry.get("operation") or entry.get("action") or entry.get("method") or "unknown"
                    actions.append({"agent": agent, "action": action})
        elif isinstance(data, dict):
            entries = data.get("entries") or data.get("logs") or []
            for entry in entries:
                if isinstance(entry, dict):
                    agent = entry.get("agent_id") or entry.get("agent") or "mcp_agent"
                    action = entry.get("operation") or entry.get("action") or entry.get("method") or "unknown"
                    actions.append({"agent": agent, "action": action})
        return actions

class OpenTelemetryParser(TraceParser):
    """Parse OpenTelemetry traces (spans)."""
    def parse(self, data: Any) -> List[Dict[str, str]]:
        actions = []
        if isinstance(data, dict):
            spans = data.get("spans") or data.get("trace") or []
            if isinstance(spans, dict):
                spans = spans.get("spans", [])
            for span in spans:
                if isinstance(span, dict):
                    agent = span.get("attributes", {}).get("agent_id") or span.get("name", "otel_span")
                    action = span.get("name") or span.get("operation") or "unknown"
                    actions.append({"agent": agent, "action": action})
        elif isinstance(data, list):
            for span in data:
                if isinstance(span, dict):
                    agent = span.get("attributes", {}).get("agent_id") or span.get("name", "otel_span")
                    action = span.get("name") or span.get("operation") or "unknown"
                    actions.append({"agent": agent, "action": action})
        return actions

def parse_trace(data: Any, framework: str = "auto") -> List[Dict[str, str]]:
    parsers = {
        "openai": OpenAIParser(),
        "autogen": AutoGenParser(),
        "crewai": CrewAIParser(),
        "langgraph": LangGraphParser(),
        "mcp": MCPParser(),
        "opentelemetry": OpenTelemetryParser(),
    }
    if framework == "auto":
        if isinstance(data, dict):
            if "messages" in data or "conversation" in data:
                framework = "autogen"
            elif "nodes" in data or "steps" in data:
                framework = "langgraph"
            elif "tasks" in data or "results" in data:
                framework = "crewai"
            elif "spans" in data or "trace" in data:
                framework = "opentelemetry"
            elif "entries" in data or "logs" in data:
                framework = "mcp"
            elif "steps" in data or "function" in str(data):
                framework = "openai"
            else:
                framework = "openai"
    parser = parsers.get(framework, OpenAIParser())
    return parser.parse(data)