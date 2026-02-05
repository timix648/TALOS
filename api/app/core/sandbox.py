from e2b import Sandbox
import os

# The SDK automatically finds E2B_API_KEY in os.environ
E2B_API_KEY = os.getenv("E2B_API_KEY")

class TaskSandbox:
    def __init__(self, repo_url: str, github_token: str):
        # We inject the token into the URL so git clone works efficiently
        self.repo_url = repo_url.replace("https://", f"https://x-access-token:{github_token}@")
        self.sandbox = None

    def __enter__(self):
        print(f"📦 SANDBOX: Initializing E2B environment...")
        
        # Factory Pattern: Use Sandbox.create()
        self.sandbox = Sandbox.create("base")
        
        print(f"📦 SANDBOX: Cloning {self.repo_url}...")
        
        # Clone into /home/user/repo (safe writable directory)
        try:
            clone_result = self.sandbox.commands.run(
                f"git clone {self.repo_url} /home/user/repo"
            )
        except Exception as e:
            # If cloning fails, that's a hard stop
            raise Exception(f"Failed to clone repo: {e}")
            
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sandbox:
            print("📦 SANDBOX: Destroying environment...")
            # Use .kill() for cleanup
            self.sandbox.kill()

    def run_command(self, command: str, capture_on_fail: bool = True):
        """Runs a shell command inside the repo directory"""
        print(f"⚡ EXEC: {command}")
        
        try:
            # cd into the correct directory before running the command
            result = self.sandbox.commands.run(
                f"cd /home/user/repo && {command}"
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code
            }
            
        except Exception as e:
            # E2B raises an exception when command exits with non-zero code
            # Try to extract actual output from the exception
            error_str = str(e)
            
            # Workaround: Run the command again but capture output even on failure
            # by appending `; true` to prevent exception, then check exit code separately
            if capture_on_fail:
                try:
                    # Run with output capture - use subshell to capture exit code
                    capture_cmd = f"cd /home/user/repo && {{ {command}; }} 2>&1; echo \"EXIT_CODE:$?\""
                    result = self.sandbox.commands.run(capture_cmd)
                    
                    output = result.stdout
                    # Parse exit code from output
                    if "EXIT_CODE:" in output:
                        parts = output.rsplit("EXIT_CODE:", 1)
                        actual_output = parts[0].strip()
                        exit_code = int(parts[1].strip()) if parts[1].strip().isdigit() else 1
                    else:
                        actual_output = output
                        exit_code = 1
                    
                    print(f"⚠️ Command failed (exit code {exit_code})")
                    return {
                        "stdout": actual_output,
                        "stderr": "",
                        "exit_code": exit_code
                    }
                except Exception as inner_e:
                    print(f"⚠️ Command failed (fallback): {inner_e}")
            
            print(f"⚠️ Command failed (expected): {e}")
            return {
                "stdout": "",
                "stderr": error_str,
                "exit_code": 1
            }

    def read_file(self, filepath: str):
        """Reads a file from the repo"""
        return self.sandbox.files.read(f"/home/user/repo/{filepath}")

    def write_file(self, filepath: str, content: str):
        """Writes content to a file in the repo"""
        self.sandbox.files.write(f"/home/user/repo/{filepath}", content)
    
    # =========================================================================
    # VISUAL DEBUGGING (Guide Section 6 - Multimodal Debugging)
    # =========================================================================
    
    def capture_screenshot(self, url: str = "http://localhost:3000") -> bytes:
        """
        Captures a screenshot of the running application for visual bug detection.
        Uses Playwright inside the sandbox.
        
        Returns: Base64-encoded screenshot for Gemini Vision API
        """
        print(f"📸 SANDBOX: Capturing screenshot of {url}...")
        
        # Install Playwright if needed and capture screenshot
        screenshot_script = f"""
        cd /home/user/repo && \
        npx --yes playwright install chromium && \
        npx --yes playwright screenshot {url} /tmp/screenshot.png --wait-for-timeout 3000
        """
        
        try:
            self.run_command(screenshot_script)
            # Read the screenshot file
            screenshot_data = self.sandbox.files.read("/tmp/screenshot.png")
            return screenshot_data
        except Exception as e:
            print(f"⚠️ SANDBOX: Screenshot capture failed: {e}")
            return None
    
    def run_visual_test(self, test_command: str = "npx playwright test") -> dict:
        """
        Runs Playwright visual regression tests and captures failure screenshots.
        
        Returns: Dict with test results and any failure screenshots
        """
        print(f"🎭 SANDBOX: Running visual tests...")
        
        result = self.run_command(test_command)
        
        # Check for Playwright test artifacts (screenshots on failure)
        artifacts_check = self.run_command("ls -la test-results/ 2>/dev/null || echo 'no artifacts'")
        
        if "no artifacts" not in artifacts_check['stdout']:
            # There are test artifacts - likely failure screenshots
            print("📷 SANDBOX: Found visual test artifacts (failure screenshots)")
            result['has_screenshots'] = True
        else:
            result['has_screenshots'] = False
        
        return result
    
    # =========================================================================
    # FIX APPLICATION (Guide Section 7.2 - Verification Loop)
    # =========================================================================
    
    def apply_fix(self, filepath: str, content: str) -> bool:
        """
        Applies a fix to a file and returns success status.
        Used in the Red/Green/Refactor verification loop.
        """
        print(f"🔧 SANDBOX: Applying fix to {filepath}...")
        try:
            self.write_file(filepath, content)
            return True
        except Exception as e:
            print(f"❌ SANDBOX: Failed to apply fix: {e}")
            return False
    
    def create_branch(self, branch_name: str) -> bool:
        """Creates a new git branch for the fix."""
        print(f"🌿 SANDBOX: Creating branch {branch_name}...")
        result = self.run_command(f"git checkout -b {branch_name}")
        return result['exit_code'] == 0
    
    def commit_and_push(self, message: str, branch_name: str) -> bool:
        """Commits changes and pushes to remote."""
        print(f"📤 SANDBOX: Committing and pushing...")
        
        # First, clean up TALOS artifacts that shouldn't be committed
        cleanup_commands = [
            "rm -f repomix_script.py",           # Remove our internal script
            "rm -f /home/user/repo/repomix_script.py",
            "git checkout -- repomix_script.py 2>/dev/null || true",  # Restore if it was there
        ]
        for cmd in cleanup_commands:
            self.run_command(cmd)
        
        commands = [
            "git config user.email 'talos@self-healing.ai'",
            "git config user.name 'TALOS Agent'",
            "git add -A",
            # Remove accidentally staged files
            "git reset HEAD -- repomix_script.py 2>/dev/null || true",
            # Don't commit lock files (npm install regenerates them)
            "git reset HEAD -- package-lock.json 2>/dev/null || true",
            "git reset HEAD -- yarn.lock 2>/dev/null || true",
            "git reset HEAD -- poetry.lock 2>/dev/null || true",
            "git reset HEAD -- pnpm-lock.yaml 2>/dev/null || true",
            f"git commit -m '{message}'",
            f"git push origin {branch_name}"
        ]
        
        for cmd in commands:
            result = self.run_command(cmd)
            if result['exit_code'] != 0 and 'nothing to commit' not in result['stdout']:
                print(f"❌ SANDBOX: Git operation failed: {result['stderr']}")
                return False
        
        return True