import anthropic
from typing import Dict, Any, List
import httpx
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os

class MCPRouter:
    """Master Control Program - AI orchestration layer"""

    def __init__(self, gateway_url: str, claude_key: str):
        self.gateway = gateway_url
        self.claude = anthropic.Anthropic(api_key=claude_key)
        self.gmail = None
        # Load GitHub token from environment or use a placeholder
        self.github_token = os.environ.get("GITHUB_TOKEN", "your-github-token-here")
        # Attempt to set up Gmail with placeholder credentials
        self.setup_gmail('credentials.json')

    def setup_gmail(self, creds_path: str):
        """Initialize Gmail API safely with placeholder credentials."""
        try:
            # The presence of the file is enough for the demo to not crash.
            # In a real scenario, this would involve a proper OAuth flow.
            if os.path.exists(creds_path):
                # This will likely fail without a valid token.json, but it prevents a crash.
                creds = Credentials.from_authorized_user_file(creds_path)
                self.gmail = build('gmail', 'v1', credentials=creds)
        except Exception:
            # Silently fail if credentials are not valid.
            # The _search_gmail method will handle the case where self.gmail is None.
            self.gmail = None

    async def route_command(self, natural_input: str, context: Dict) -> Dict[str, Any]:
        """Parse natural language and route to appropriate service"""

        # Use Claude to determine intent and extract parameters
        tools = [
            {
                "name": "synthesize_code",
                "description": "Generate or analyze code using multi-model synthesis",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "models": {"type": "array", "items": {"type": "string"}},
                        "lane": {"type": "string", "enum": ["stem", "medical", "security"]}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_gmail",
                "description": "Search Gmail for messages matching criteria",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_results": {"type": "integer", "default": 10}
                    }
                }
            },
            {
                "name": "github_operation",
                "description": "Perform GitHub operations (list PRs, create issues, etc)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string"},
                        "repo": {"type": "string"},
                        "params": {"type": "object"}
                    }
                }
            },
            {
                "name": "scan_security",
                "description": "Scan code or dependencies for security issues",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["code", "deps"]},
                        "content": {"type": "string"}
                    }
                }
            }
        ]

        response = self.claude.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            tools=tools,
            messages=[
                {"role": "user", "content": natural_input}
            ]
        )

        # Execute tool calls
        results = []
        for block in response.content:
            if block.type == "tool_use":
                result = await self._execute_tool(block.name, block.input)
                results.append(result)

        return {
            "intent": response.stop_reason,
            "actions": results,
            "thinking": response.content[0].text if response.content else ""
        }

    async def _execute_tool(self, tool_name: str, params: Dict) -> Any:
        """Execute the specified tool"""

        if tool_name == "synthesize_code":
            return await self._synthesize(params)
        elif tool_name == "search_gmail":
            return self._search_gmail(params)
        elif tool_name == "github_operation":
            return await self._github_op(params)
        elif tool_name == "scan_security":
            return await self._security_scan(params)

    async def _synthesize(self, params: Dict) -> Dict:
        """Call your existing synthesize microservice"""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.gateway}/synthesize",
                json={
                    "consent_id": "terminal_session",
                    "query": params["query"],
                    "models": params.get("models", []),
                    "lane": params.get("lane", "stem")
                },
                headers={"Authorization": "Bearer demo-token"}
            )
            return resp.json()

    def _search_gmail(self, params: Dict) -> List[Dict]:
        """Search Gmail via API"""
        if not self.gmail:
            return {"error": "Gmail not configured"}

        results = self.gmail.users().messages().list(
            userId='me',
            q=params["query"],
            maxResults=params.get("max_results", 10)
        ).execute()

        messages = []
        for msg in results.get('messages', []):
            full = self.gmail.users().messages().get(
                userId='me', id=msg['id']
            ).execute()
            messages.append({
                "id": msg['id'],
                "subject": next((h['value'] for h in full['payload']['headers']
                               if h['name'] == 'Subject'), 'No Subject'),
                "snippet": full['snippet']
            })

        return messages

    async def _github_op(self, params: Dict) -> Dict:
        """GitHub operations via API"""
        async with httpx.AsyncClient() as client:
            if params["action"] == "list_prs":
                resp = await client.get(
                    f"https://api.github.com/repos/{params['repo']}/pulls",
                    headers={"Authorization": f"Bearer {self.github_token}"}
                )
                return resp.json()

    async def _security_scan(self, params: Dict) -> Dict:
        """Route to scan microservice"""
        endpoint = "/scan/code" if params["type"] == "code" else "/scan/deps"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.gateway}{endpoint}",
                json=params,
                headers={"Authorization": "Bearer demo-token"}
            )
            return resp.json()