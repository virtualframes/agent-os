import subprocess
import os
from datetime import datetime

class CopilotAutomation:
    def __init__(self, repo_path="~/agent-os"):
        self.repo_path = os.path.expanduser(repo_path)

    def auto_sync(self, commit_msg="AgentOS update"):
        os.chdir(self.repo_path)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push"], check=True)
        self.log_action(f"Pushed: {commit_msg}")

    def log_action(self, action):
        with open(os.path.join(self.repo_path, "copilot.log"), "a") as f:
            f.write(f"{datetime.utcnow().isoformat()} — {action}\n")
