from e2b import Sandbox
import os
import time

E2B_API_KEY = os.getenv("E2B_API_KEY")

SANDBOX_TIMEOUT = 3600 

# Note: E2B resource limits (8 vCPU, 8GB RAM, 10GB disk) are set at template level.
# The default "base" template should use available resources.
# /dev/shm is still limited - Chromium uses --disable-dev-shm-usage to use /tmp instead.


class TaskSandbox:
    def __init__(self, repo_url: str, github_token: str):
    
        self.repo_url = repo_url.replace("https://", f"https://x-access-token:{github_token}@")
        self.sandbox = None
        self._bg_handles = [] 

    def __enter__(self):
        print(f"📦 SANDBOX: Initializing E2B environment (timeout: {SANDBOX_TIMEOUT}s)...")
        
        
        self.sandbox = Sandbox.create("base", timeout=SANDBOX_TIMEOUT)
        
        print(f"SANDBOX: Cloning {self.repo_url}...")
        
        
        try:
            clone_result = self.sandbox.commands.run(
                f"git clone {self.repo_url} /home/user/repo",
                timeout=120  
            )
        except Exception as e:
            
            raise Exception(f"Failed to clone repo: {e}")
            
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        
        for handle in self._bg_handles:
            try:
                handle.kill()
            except Exception:
                pass
        self._bg_handles.clear()
        
        if self.sandbox:
            print("SANDBOX: Destroying environment...")
        
            self.sandbox.kill()

    def run_background(self, command: str) -> object:
        """
        Start a long-running process (server, watcher) without blocking.
        Uses E2B's native background=True which returns immediately.
        
        Returns: CommandHandle with .pid, .kill(), .wait(), .disconnect()
        """
        print(f"BG_EXEC: {command}")
        try:
            handle = self.sandbox.commands.run(
                f"cd /home/user/repo && {command}",
                background=True,
                timeout=0  
            )
            self._bg_handles.append(handle)
            print(f"   Background process started (PID: {handle.pid})")
            return handle
        except Exception as e:
            print(f"Failed to start background process: {e}")
            return None

    def kill_background(self, handle=None):
        """Kill a specific background process or all of them."""
        if handle:
            try:
                handle.kill()
                if handle in self._bg_handles:
                    self._bg_handles.remove(handle)
            except Exception:
                pass
        else:
           
            for h in self._bg_handles:
                try:
                    h.kill()
                except Exception:
                    pass
            self._bg_handles.clear()

    def run_command(self, command: str, capture_on_fail: bool = True, timeout: int = 300):
        """Runs a shell command inside the repo directory.
        
        Args:
            command: The shell command to run
            capture_on_fail: Whether to capture output even when command fails
            timeout: Command timeout in seconds (default 5 min for npm install/build)
        """
        print(f"EXEC: {command}")
        
        try:
           
            result = self.sandbox.commands.run(
                f"cd /home/user/repo && {command}",
                timeout=timeout
            )
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code
            }
            
        except Exception as e:
         
            error_str = str(e)

            if capture_on_fail:
                try:
        
                    capture_cmd = f"cd /home/user/repo && {{ {command}; }}; echo \"EXIT_CODE:$?\""
                    result = self.sandbox.commands.run(capture_cmd, timeout=timeout)
                    
                    output = result.stdout
                    stderr_output = result.stderr or ""
                    
                    if "EXIT_CODE:" in output:
                        parts = output.rsplit("EXIT_CODE:", 1)
                        actual_output = parts[0].strip()
                        exit_code = int(parts[1].strip()) if parts[1].strip().isdigit() else 1
                    else:
                        actual_output = output
                        exit_code = 1
                    
                    print(f"Command failed (exit code {exit_code})")
                    return {
                        "stdout": actual_output,
                        "stderr": stderr_output,
                        "exit_code": exit_code
                    }
                except Exception as inner_e:
                   
                    if "timeout" in str(inner_e).lower():
                        print(f"Command timed out after {timeout}s: {command[:50]}...")
                        return {
                            "stdout": "",
                            "stderr": f"Command timed out after {timeout} seconds",
                            "exit_code": 124  
                        }
                    print(f"Command failed (fallback): {inner_e}")
            
       
            if "timeout" in error_str.lower():
                print(f"Command timed out: {command[:50]}...")
                return {
                    "stdout": "",
                    "stderr": f"Command timed out after {timeout} seconds",
                    "exit_code": 124
                }
            
            print(f"Command failed (expected): {e}")
            return {
                "stdout": "",
                "stderr": error_str,
                "exit_code": 1
            }

    def read_file(self, filepath: str):
        """Reads a file from the repo"""
        return self.sandbox.files.read(f"/home/user/repo/{filepath}")

    def read_file_bytes(self, absolute_path: str) -> bytes:
        """Reads a file from any path in the sandbox (for screenshots, etc.)"""
        return self.sandbox.files.read(absolute_path)

    def write_file(self, filepath: str, content: str):
        """Writes content to a file in the repo"""
        self.sandbox.files.write(f"/home/user/repo/{filepath}", content)
    
    def capture_screenshot_simple(self, url: str = "http://localhost:5173", output_path: str = "/tmp/screenshot.png") -> bytes:
        """
        Simpler screenshot capture using Playwright CLI directly.
        Saves to file and reads via E2B SDK - more reliable than stdout parsing.
        
        Returns: Raw screenshot bytes (PNG) or None if failed
        """
        import base64
        print(f"📸 SANDBOX: Simple screenshot capture of {url}...")
        
        # Use Playwright CLI with proper flags for headless environment
        capture_cmd = f"""
        cd /home/user/repo && \
        PLAYWRIGHT_BROWSERS_PATH=0 npx --yes playwright screenshot \
            --browser chromium \
            --wait-for-timeout 5000 \
            '{url}' '{output_path}' 2>&1
        """
        
        try:
            result = self.run_command(capture_cmd, timeout=120)
            print(f"   📋 Playwright output: {result.get('stdout', '')[:200]}")
            
            if result.get('exit_code', 1) != 0:
                print(f"   ⚠️ Playwright failed with exit code {result.get('exit_code')}")
                return None
            
            # Read the file directly using E2B SDK
            try:
                screenshot_bytes = self.sandbox.files.read(output_path)
                print(f"   ✅ Screenshot read: {len(screenshot_bytes)} bytes")
                return screenshot_bytes
            except Exception as read_err:
                print(f"   ⚠️ Failed to read screenshot file: {read_err}")
                return None
                
        except Exception as e:
            print(f"   ❌ Screenshot capture failed: {e}")
            return None
    
    def capture_screenshot(self, url: str = "http://localhost:3000") -> bytes:
        """
        Captures a screenshot of the running application for visual bug detection.
        Uses Playwright inside the sandbox.
        
        Returns: Screenshot bytes (PNG) for Gemini Vision API
        """
        print(f"📸 SANDBOX: Capturing screenshot of {url}...")
     
        screenshot_script = f"""
        cd /home/user/repo && \
        npx --yes playwright install chromium && \
        npx --yes playwright screenshot {url} /tmp/screenshot.png --wait-for-timeout 3000
        """
        
        try:
            self.run_command(screenshot_script, timeout=120)
            
            screenshot_data = self.sandbox.files.read("/tmp/screenshot.png")
            return screenshot_data
        except Exception as e:
            print(f"   ❌ Screenshot capture failed: {e}")
            return None
    
    def run_visual_test(self, test_command: str = "npx playwright test") -> dict:
        """
        Runs Playwright visual regression tests and captures failure screenshots.
        
        Returns: Dict with test results and any failure screenshots
        """
        print(f"SANDBOX: Running visual tests...")
        
        result = self.run_command(test_command)
        
       
        artifacts_check = self.run_command("ls -la test-results/ 2>/dev/null || echo 'no artifacts'")
        
        if "no artifacts" not in artifacts_check['stdout']:
            
            print("SANDBOX: Found visual test artifacts (failure screenshots)")
            result['has_screenshots'] = True
        else:
            result['has_screenshots'] = False
        
        return result
    
    
    def apply_fix(self, filepath: str, content: str) -> bool:
        """
        Applies a fix to a file and returns success status.
        Used in the Red/Green/Refactor verification loop.
        """
        print(f"SANDBOX: Applying fix to {filepath}...")
        try:
            self.write_file(filepath, content)
            return True
        except Exception as e:
            print(f"SANDBOX: Failed to apply fix: {e}")
            return False
    
    def create_branch(self, branch_name: str) -> bool:
        """Creates a new git branch for the fix."""
        print(f"SANDBOX: Creating branch {branch_name}...")
        result = self.run_command(f"git checkout -b {branch_name}")
        return result['exit_code'] == 0
    
    def commit_and_push(self, message: str, branch_name: str) -> bool:
        """Commits changes and pushes to remote."""
        print(f"SANDBOX: Committing and pushing...")
        
     
        cleanup_commands = [
            "rm -f repomix_script.py",          
            "rm -f /home/user/repo/repomix_script.py",
            "rm -f visual_capture.py",    
            "rm -f /home/user/repo/visual_capture.py",
            "rm -f core",                       
            "rm -f /home/user/repo/core",
            "git checkout -- repomix_script.py 2>/dev/null || true",  
            "git checkout -- visual_capture.py 2>/dev/null || true",
        ]
        for cmd in cleanup_commands:
            self.run_command(cmd)
        
        commands = [
            "git config user.email 'talos@self-healing.ai'",
            "git config user.name 'TALOS Agent'",
            "git add -A",
            
            "git reset HEAD -- repomix_script.py 2>/dev/null || true",
            "git reset HEAD -- visual_capture.py 2>/dev/null || true",
            "git reset HEAD -- core 2>/dev/null || true",  
            
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
                print(f"SANDBOX: Git operation failed: {result['stderr']}")
                return False
        
        return True