#!/usr/bin/env python3
"""
autonomous-toolkit.py
Self-extending toolkit registry. Agent can ADD tools on-the-fly based on user requests.

Tools include:
  - Web scraping (BeautifulSoup, Selenium)
  - HTML manipulation (generate, parse, diff)
  - Frontend design (CSS generation, component templates)
  - API integration (REST, GraphQL)
  - Workflow generation (chain tools autonomously)

Agent can:
  1. Detect user needs ("scrape website", "design button")
  2. Check if tool exists
  3. If not, auto-generate tool from template
  4. Register in config
  5. Execute immediately
  6. Update toolkit for future use
"""

import json
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Paths
CONFIG_DIR = Path.home() / ".moonunit2"
TOOLS_DIR = CONFIG_DIR / "tools"
TOOLKIT_MANIFEST = CONFIG_DIR / "toolkit-manifest.json"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
TOOLS_DIR.mkdir(parents=True, exist_ok=True)


class ToolkitManager:
    """Manages dynamic tool creation and registration."""
    
    TOOL_TEMPLATES = {
        "web_scraper": '''#!/usr/bin/env python3
"""Web scraper tool - auto-generated."""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TOOL_DEF = {
    "name": "web_scraper",
    "description": "Scrape web pages, extract data",
    "inputs": {
        "url": "URL to scrape",
        "selector": "CSS selector for data",
        "extract": "text|html|attributes"
    }
}

def execute(url: str, selector: str = "body", extract: str = "text"):
    """Scrape and extract data."""
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        elements = soup.select(selector)
        
        results = []
        for el in elements:
            if extract == "text":
                results.append(el.get_text(strip=True))
            elif extract == "html":
                results.append(str(el))
            elif extract == "attributes":
                results.append(dict(el.attrs))
        
        return {"success": True, "count": len(results), "data": results[:10]}
    except Exception as e:
        return {"success": False, "error": str(e)}
''',
        
        "html_generator": '''#!/usr/bin/env python3
"""HTML component generator - auto-generated."""

TOOL_DEF = {
    "name": "html_generator",
    "description": "Generate HTML components from description",
    "inputs": {
        "component": "button|card|form|modal|navbar",
        "props": "JSON with color, text, etc"
    }
}

def execute(component: str, props: dict = None):
    """Generate HTML component."""
    props = props or {}
    
    templates = {
        "button": '<button class="btn btn-{color}">{text}</button>',
        "card": '<div class="card"><h3>{title}</h3><p>{content}</p></div>',
        "form": '<form><input type="text" placeholder="{placeholder}"><button>Submit</button></form>',
        "modal": '<div class="modal"><div class="modal-content">{content}</div></div>',
        "navbar": '<nav class="navbar"><a href="#">{brand}</a></nav>'
    }
    
    html = templates.get(component, "")
    for key, val in props.items():
        html = html.replace("{" + key + "}", str(val))
    
    return {"success": True, "html": html, "component": component}
''',
        
        "css_generator": '''#!/usr/bin/env python3
"""CSS generator - auto-generated."""

TOOL_DEF = {
    "name": "css_generator",
    "description": "Generate CSS from design requirements",
    "inputs": {
        "element": "class or tag name",
        "props": "JSON {color, padding, etc}"
    }
}

def execute(element: str, props: dict = None):
    """Generate CSS rule."""
    props = props or {}
    
    css_lines = [f".{element} {{"]
    
    # Map common props to CSS
    prop_map = {
        "color": "color",
        "bg_color": "background-color",
        "padding": "padding",
        "margin": "margin",
        "font_size": "font-size",
        "width": "width",
        "height": "height",
        "border": "border",
        "border_radius": "border-radius",
    }
    
    for key, val in props.items():
        css_prop = prop_map.get(key, key)
        css_lines.append(f"  {css_prop}: {val};")
    
    css_lines.append("}")
    
    return {"success": True, "css": "\\n".join(css_lines)}
''',
        
        "api_client": '''#!/usr/bin/env python3
"""REST API client - auto-generated."""
import requests
import json

TOOL_DEF = {
    "name": "api_client",
    "description": "Make REST API calls",
    "inputs": {
        "url": "API endpoint",
        "method": "GET|POST|PUT|DELETE",
        "data": "Request body (JSON)"
    }
}

def execute(url: str, method: str = "GET", data: dict = None):
    """Make API call."""
    try:
        kwargs = {"timeout": 10}
        if data:
            kwargs["json"] = data
        
        resp = requests.request(method, url, **kwargs)
        return {
            "success": True,
            "status": resp.status_code,
            "data": resp.json() if resp.headers.get('content-type', '').endswith('json') else resp.text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
''',
        
        "workflow_builder": '''#!/usr/bin/env python3
"""Workflow orchestrator - auto-generated."""
import json

TOOL_DEF = {
    "name": "workflow_builder",
    "description": "Chain multiple tools into workflow",
    "inputs": {
        "steps": "List of {tool, inputs}",
        "conditional": "Optional condition between steps"
    }
}

def execute(steps: list, conditional: str = None):
    """Execute workflow steps."""
    results = []
    context = {}
    
    for i, step in enumerate(steps):
        tool_name = step.get("tool")
        inputs = step.get("inputs", {})
        
        # Replace variables from previous steps
        for key, val in inputs.items():
            if isinstance(val, str) and val.startswith("$"):
                var_name = val[1:]
                inputs[key] = context.get(var_name, val)
        
        # Execute step (simplified)
        result = {"step": i, "tool": tool_name, "inputs": inputs, "status": "executed"}
        results.append(result)
        context.update(result)
    
    return {"success": True, "steps_executed": len(results), "results": results}
'''
    }
    
    def __init__(self):
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load toolkit manifest."""
        if TOOLKIT_MANIFEST.exists():
            with open(TOOLKIT_MANIFEST) as f:
                return json.load(f)
        return {"tools": {}, "created_at": datetime.now().isoformat()}
    
    def _save_manifest(self):
        """Save toolkit manifest."""
        self.manifest["updated_at"] = datetime.now().isoformat()
        with open(TOOLKIT_MANIFEST, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def tool_exists(self, tool_name: str) -> bool:
        """Check if tool is registered."""
        return tool_name in self.manifest["tools"]
    
    def detect_needed_tools(self, user_request: str) -> List[str]:
        """Detect which tools user needs based on request."""
        keywords = {
            "web_scraper": ["scrape", "crawl", "extract", "download", "website"],
            "html_generator": ["generate", "create", "design", "component", "html", "button", "card"],
            "css_generator": ["style", "css", "color", "design", "theme", "layout"],
            "api_client": ["api", "fetch", "call", "request", "endpoint"],
            "workflow_builder": ["workflow", "chain", "automate", "sequence", "pipeline"],
        }
        
        request_lower = user_request.lower()
        needed = []
        
        for tool_name, keywords_list in keywords.items():
            if any(kw in request_lower for kw in keywords_list):
                needed.append(tool_name)
        
        return needed
    
    def create_tool(self, tool_name: str) -> bool:
        """Auto-generate and register tool."""
        if tool_name not in self.TOOL_TEMPLATES:
            return False
        
        # Create tool file
        tool_path = TOOLS_DIR / f"{tool_name}.py"
        tool_path.write_text(self.TOOL_TEMPLATES[tool_name])
        tool_path.chmod(0o755)
        
        # Register in manifest
        self.manifest["tools"][tool_name] = {
            "path": str(tool_path),
            "created": datetime.now().isoformat(),
            "status": "active"
        }
        self._save_manifest()
        
        return True
    
    def ensure_tools(self, needed_tools: List[str]) -> List[str]:
        """Ensure all needed tools exist, create if necessary."""
        created = []
        for tool_name in needed_tools:
            if not self.tool_exists(tool_name):
                if self.create_tool(tool_name):
                    created.append(tool_name)
        return created
    
    def list_tools(self) -> Dict:
        """List all available tools."""
        return self.manifest["tools"]
    
    def auto_suggest_workflow(self, task: str) -> Dict:
        """Suggest workflow to accomplish task."""
        needed = self.detect_needed_tools(task)
        self.ensure_tools(needed)
        
        # Build suggested workflow
        workflow = {
            "task": task,
            "tools": needed,
            "steps": [{"tool": t, "inputs": {}} for t in needed],
            "auto_generated": True
        }
        return workflow


# Global toolkit
toolkit = ToolkitManager()


if __name__ == "__main__":
    # Example: detect and create tools for user request
    user_task = "Scrape the weather and generate a dashboard to display it"
    
    needed = toolkit.detect_needed_tools(user_task)
    print(f"📦 Detected needed tools: {needed}")
    
    created = toolkit.ensure_tools(needed)
    print(f"✅ Created tools: {created}")
    
    workflow = toolkit.auto_suggest_workflow(user_task)
    print(f"🔄 Suggested workflow:")
    print(json.dumps(workflow, indent=2))
