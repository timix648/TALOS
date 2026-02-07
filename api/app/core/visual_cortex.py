"""
VISUAL CORTEX: Playwright-Powered Visual Bug Detection
========================================================
This module adds "eyes" to TALOS - the ability to see and fix UI bugs
that don't throw runtime errors but break the visual experience.

This is THE killer feature that differentiates TALOS from competitors.
Most DevOps tools only see text (logs). TALOS sees the actual UI.

Architecture:
    1. Capture: Playwright takes screenshot of failed UI state
    2. Encode: Screenshot is base64 encoded for Gemini
    3. Analyze: Gemini's multimodal vision identifies visual issues
    4. Fix: CSS/Layout fixes are generated and verified

Use Cases:
    - Overlapping elements
    - Z-index issues (buttons hidden behind modals)
    - Layout breaks (elements pushed off-screen)
    - Color contrast issues
    - Missing images / broken assets
    - Responsive layout failures
"""

import os
import base64
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from google import genai
from app.core.key_manager import key_rotator

VISION_MODEL = "gemini-3-flash-preview" 


@dataclass
class VisualBugReport:
    """Report from visual analysis."""
    has_issues: bool
    issues: List[Dict[str, Any]]
    screenshot_description: str
    suggested_fixes: List[Dict[str, str]]
    confidence: float


@dataclass
class VisualTestResult:
    """Result from a visual test run."""
    passed: bool
    screenshot_path: Optional[str]
    screenshot_base64: Optional[str]
    error_message: Optional[str]
    element_selector: Optional[str]
    viewport: Dict[str, int]


def get_playwright_setup_script() -> str:
    """
    Returns a Python script that captures a screenshot using Playwright.
    
    KEY FIX: Uses the SYNCHRONOUS Playwright API instead of async.
    The async API was hanging silently at browser.new_page() in E2B's
    constrained environment due to event loop / IPC issues with the
    internal Node.js subprocess. The sync API is more reliable.
    
    Design choices:
    - SYNC Playwright API (no asyncio, no event loop issues)
    - Per-step signal.SIGALRM hard timeouts (Linux-only, perfect for E2B)
    - All progress logged to stderr (stdout is clean JSON)
    - URL rewritten to 127.0.0.1 to skip DNS resolution
    - Memory diagnostics logged before Chromium launch
    - Chrome PID check after launch to confirm process is alive
    """
    return '''
import json
import sys
import time
import base64
import signal
import os
import resource

# === Force unbuffered I/O so logs survive process kill ===
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

# === Disable core dumps (Chromium segfaults write 100MB+ blocking VM disk I/O) ===
try:
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
except Exception:
    pass

# === LOG FILE: Persistent log that survives E2B process kill ===
# When E2B SDK times out and kills this process, stderr is discarded.
# Writing to a file ensures the agent can read diagnostics post-mortem.
LOG_FILE = "/tmp/visual_capture.log"
try:
    with open(LOG_FILE, "w") as f:
        f.write(f"[capture] Log started at {time.time():.1f}\\n")
except Exception:
    pass

def log(msg):
    """Log to stderr AND a persistent file. File survives process kill."""
    line = f"[capture] {msg}"
    print(line, file=sys.stderr, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{line}\\n")
            f.flush()
            os.fsync(f.fileno())  # Force kernel buffer to disk immediately
    except Exception:
        pass

class StepTimeout(Exception):
    """Raised when a single step exceeds its individual timeout."""
    pass

def _alarm_handler(signum, frame):
    raise StepTimeout("Step exceeded its timeout")

# ============================================================================
# FIX MECHANISM A: /dev/shm Shared Memory Deadlock
# ============================================================================
# Chromium uses /dev/shm for zero-copy IPC between its Browser and Renderer
# processes (screenshot bitmap data, compositing layers, etc.).
#
# In microVMs & containers, /dev/shm defaults to 64MB. A single 1280x720
# screenshot at 32-bit color = 3.6MB per buffer. With double/triple buffering,
# texture caches, and compositing layers, Chromium easily exceeds 64MB.
#
# When /dev/shm fills up:
#   - Renderer blocks trying to allocate a new shared memory segment
#   - Browser blocks waiting for Renderer to finish the frame
#   - DEADLOCK: neither can proceed, process hangs silently
#
# Fix: Remount /dev/shm with 256MB BEFORE launching Chromium.
# The --disable-dev-shm-usage flag is a backup (moves IPC to /tmp).
# ============================================================================
def fix_shared_memory():
    """Resize /dev/shm to prevent Chromium IPC deadlock."""
    try:
        shm_stat = os.statvfs("/dev/shm")
        shm_total_mb = (shm_stat.f_blocks * shm_stat.f_frsize) // (1024 * 1024)
        shm_free_mb = (shm_stat.f_bavail * shm_stat.f_frsize) // (1024 * 1024)
        log(f"/dev/shm: {shm_free_mb}MB free / {shm_total_mb}MB total")

        if shm_total_mb < 256:
            log(f"/dev/shm too small ({shm_total_mb}MB). Remounting to 256MB...")
            ret = os.system("mount -o remount,size=256m /dev/shm 2>/dev/null")
            if ret == 0:
                shm_stat2 = os.statvfs("/dev/shm")
                new_mb = (shm_stat2.f_blocks * shm_stat2.f_frsize) // (1024 * 1024)
                log(f"/dev/shm resized: {shm_total_mb}MB -> {new_mb}MB")
            else:
                log(f"/dev/shm remount failed (exit {ret}). Will rely on --disable-dev-shm-usage flag.")
        else:
            log(f"/dev/shm is adequate ({shm_total_mb}MB)")
    except Exception as e:
        log(f"/dev/shm check error: {e}. Will rely on --disable-dev-shm-usage flag.")

def kill_stale_chrome():
    """Kill any leftover Chrome processes from previous runs."""
    try:
        os.system("pkill -9 -f chrome 2>/dev/null")
        os.system("pkill -9 -f chromium 2>/dev/null")
        time.sleep(0.5)
    except Exception:
        pass

def preflight_browser_check():
    """Quick check: can Chromium start at all? Catches missing libs, broken binaries."""
    import subprocess
    try:
        # Find chromium binary
        result = subprocess.run(
            ["find", "/root/.cache/ms-playwright", "/home", "-name", "chrome", "-type", "f"],
            capture_output=True, text=True, timeout=5
        )
        chrome_path = result.stdout.strip().split("\\n")[0] if result.stdout.strip() else None
        if not chrome_path:
            log("Pre-flight: Chrome binary not found, skipping check")
            return True  # Let Playwright try to find it

        # Try to run --version (fast, tests that the binary + libs work)
        ver_result = subprocess.run(
            [chrome_path, "--headless", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if ver_result.returncode == 0:
            log(f"Pre-flight OK: {ver_result.stdout.strip()}")
            return True
        else:
            log(f"Pre-flight FAIL: exit={ver_result.returncode}, stderr={ver_result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        log("Pre-flight: --version timed out (browser may be broken)")
        return False
    except Exception as e:
        log(f"Pre-flight error: {e}")
        return True  # Don't block on pre-flight errors

def capture_visual_state(url, viewport_width=1280, viewport_height=720):
    t0 = time.time()
    log(f"Starting SYNC capture: {url} ({viewport_width}x{viewport_height})")

    # === MECHANISM A: Fix shared memory before anything else ===
    fix_shared_memory()
    kill_stale_chrome()

    # Force 127.0.0.1 — DNS for 'localhost' can be slow/broken in containers
    url = url.replace("://localhost", "://127.0.0.1")
    log(f"Resolved URL: {url}")

    # Diagnostics: available memory
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if "MemAvailable" in line:
                    mem_mb = int(line.split()[1]) // 1024
                    log(f"Available memory: {mem_mb} MB")
                    break
    except Exception:
        pass

    # Pre-flight: verify Chromium binary works
    if not preflight_browser_check():
        log("ABORTING: Chromium pre-flight check failed")
        return {"success": False, "error": "Chromium binary failed pre-flight check (missing libs or broken binary)"}

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"success": False, "error": "playwright not installed"}

    result = {
        "success": False,
        "screenshot_base64": None,
        "console_errors": [],
        "network_errors": [],
        "viewport": {"width": viewport_width, "height": viewport_height},
    }

    browser = None
    pw = None
    context = None
    page = None

    # Install the SIGALRM handler for per-step timeouts
    old_handler = signal.signal(signal.SIGALRM, _alarm_handler)

    try:
        # === Step 1: Start Playwright (30s) ===
        log("Step 1/8: Starting Playwright...")
        signal.alarm(30)
        t1 = time.time()
        pw = sync_playwright().start()
        signal.alarm(0)
        log(f"  OK  Playwright started in {time.time()-t1:.1f}s")

        # === Step 2: Launch Chromium (30s) ===
        log("Step 2/8: Launching Chromium...")
        signal.alarm(30)
        t2 = time.time()
        browser = pw.chromium.launch(
            headless=True,
            args=[
                # === MECHANISM A: Prevent /dev/shm IPC deadlock ===
                "--disable-dev-shm-usage",      # Moves shared memory IPC to /tmp (backup for shm resize)
                # === MECHANISM B: Prevent root-user sandbox crash ===
                "--no-sandbox",                 # Required: E2B runs as root (UID 0)
                "--disable-setuid-sandbox",     # Required: no SUID binaries in microVM
                # === Stability: disable features that break in microVMs ===
                "--disable-gpu",                # No GPU passthrough in microVMs
                "--disable-software-rasterizer",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-features=TranslateUI,VizDisplayCompositor,IsolateOrigins,site-per-process",
                "--no-first-run",
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                # === MECHANISM C: Single-process mode to avoid renderer spawn hang ===
                # In low-memory VMs, spawning a separate renderer process often hangs
                # because the kernel can't fork fast enough under memory pressure.
                # Single-process mode runs renderer in the same process as browser.
                "--single-process",             # KEY FIX: Avoid renderer spawn hang
                # === MECHANISM D: Minimize process count in low-memory VMs ===
                "--no-zygote",                  # Skip zygote forker (saves ~30MB)
                "--renderer-process-limit=1",   # Max 1 renderer process (backup if not single-process)
                "--disable-accelerated-2d-canvas",
                "--disable-accelerated-video-decode",
                "--force-device-scale-factor=1",
                "--disable-ipc-flooding-protection",  # Don't throttle IPC in constrained envs
                # === Memory: limit Chromium's appetite ===
                "--js-flags=--max-old-space-size=128",  # Reduced from 256 for low-mem VMs
                # === Additional stability flags ===
                "--disable-web-security",       # Skip CORS checks for local screenshots
                "--disable-features=NetworkService",
                "--mute-audio",                 # No audio processing needed
            ],
        )
        signal.alarm(0)
        log(f"  OK  Chromium launched in {time.time()-t2:.1f}s")

        # Verify Chrome process is alive
        try:
            pids = os.popen("pgrep -c chrome 2>/dev/null").read().strip()
            log(f"  Chrome process count: {pids}")
        except Exception:
            pass

        # === Step 3a: Create context (15s) ===
        log("Step 3a/8: Creating browser context...")
        signal.alarm(15)
        t3 = time.time()
        context = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            bypass_csp=True,
        )
        signal.alarm(0)
        log(f"  OK  Context created in {time.time()-t3:.1f}s")
        
        # === Step 3b: Create page with retry (30s total, 3 attempts) ===
        # Page creation spawns a Chromium renderer process which can hang
        # in low-memory VMs. Retry mechanism helps recover from transient hangs.
        log("Step 3b/8: Creating page (with retry)...")
        page = None
        page_attempts = 2
        browser_crashed = False
        for page_attempt in range(page_attempts):
            try:
                signal.alarm(15)  # 15s per attempt
                t3b = time.time()
                page = context.new_page()
                signal.alarm(0)
                log(f"  OK  Page created in {time.time()-t3b:.1f}s (attempt {page_attempt + 1})")
                break
            except StepTimeout:
                signal.alarm(0)
                log(f"  RETRY  Page creation timed out (attempt {page_attempt + 1}/{page_attempts})")
                # Kill renderer processes that may be hung
                os.system("pkill -9 -f 'type=renderer' 2>/dev/null")
                time.sleep(1)
                if page_attempt == page_attempts - 1:
                    raise StepTimeout("Page creation failed after all retries")
            except Exception as e:
                signal.alarm(0)
                err_str = str(e).lower()
                log(f"  ERROR  Page creation error: {e} (attempt {page_attempt + 1})")
                # Detect browser crash - need full restart
                if "closed" in err_str or "crash" in err_str or "target" in err_str:
                    log("  CRASH  Browser process died - will restart")
                    browser_crashed = True
                    break
                if page_attempt == page_attempts - 1:
                    raise
        
        # If browser crashed, handle gracefully
        if browser_crashed:
            log("  CRASH  Browser process died")
            try:
                if browser: browser.close()
            except: pass
            try:
                if pw: pw.stop()
            except: pass
            os.system("pkill -9 -f 'chrome' 2>/dev/null")
            os.system("pkill -9 -f 'chromium' 2>/dev/null")
            result["error"] = "Browser crashed during page creation"
            signal.signal(signal.SIGALRM, old_handler)
            return result
        
        if not page:
            raise Exception("Failed to create page after all retries")

        # === Step 4: Navigate (30s) ===
        log(f"Step 4/8: Navigating to {url}...")
        signal.alarm(30)
        t4 = time.time()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            signal.alarm(0)
            log(f"  OK  Navigation done in {time.time()-t4:.1f}s")
        except StepTimeout:
            raise
        except Exception as nav_err:
            signal.alarm(0)
            log(f"  FAIL  Navigation error: {nav_err}")
            result["error"] = f"Navigation failed: {str(nav_err)[:150]}"
            browser.close()
            pw.stop()
            return result

        # === Step 5: Wait for full load (15s) ===
        log("Step 5/8: Waiting for load state...")
        t5 = time.time()
        try:
            page.wait_for_load_state("load", timeout=15000)
            log(f"  OK  Fully loaded in {time.time()-t5:.1f}s")
        except Exception:
            log(f"  WARN  Load timeout after {time.time()-t5:.1f}s, proceeding")

        # === Step 6: JS hydration wait (5s fixed) ===
        log("Step 6/8: Waiting 5s for JS hydration...")
        time.sleep(5)
        log(f"  OK  Ready at {time.time()-t0:.1f}s total")

        # === Step 7: Screenshot (15s) ===
        log("Step 7/8: Taking screenshot...")
        signal.alarm(15)
        t7 = time.time()
        screenshot_bytes = page.screenshot(full_page=False, timeout=10000)
        signal.alarm(0)

        result["screenshot_base64"] = base64.b64encode(screenshot_bytes).decode("utf-8")
        result["success"] = True
        log(f"  OK  Screenshot: {time.time()-t7:.1f}s, {len(result['screenshot_base64'])} bytes b64")

        result["title"] = page.title()
        result["final_url"] = page.url

        context.close()
        browser.close()
        context = None
        browser = None
        pw = None
        log(f"DONE  Total capture time: {time.time()-t0:.1f}s")
        # Note: finally block will handle signal restore
        return result

    except StepTimeout:
        signal.alarm(0)
        elapsed = time.time() - t0
        log(f"STEP TIMEOUT at {elapsed:.1f}s — a step exceeded its individual timeout limit")
        result["error"] = f"Step timed out at {elapsed:.1f}s"
    except Exception as e:
        signal.alarm(0)
        log(f"ERROR: {type(e).__name__}: {e}")
        result["error"] = f"{type(e).__name__}: {str(e)[:200]}"
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        # Cleanup resources
        try:
            if context: context.close()
        except: pass
        try:
            if browser: browser.close()
        except: pass
        try:
            if pw: pw.stop()
        except: pass

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args()

    result = capture_visual_state(args.url, args.width, args.height)
    # Print JSON to stdout (this is what the agent parses)
    print(json.dumps(result))
'''


async def analyze_screenshot_with_gemini(
    screenshot_base64: str,
    context: str = "",
    css_content: str = "",
    error_description: str = ""
) -> VisualBugReport:
    """
    Uses Gemini's multimodal capabilities to analyze a screenshot for visual bugs.
    
    Args:
        screenshot_base64: Base64 encoded screenshot
        context: Description of what the page should look like
        css_content: Relevant CSS code
        error_description: What the user reported as broken
    
    Returns:
        VisualBugReport with identified issues and suggested fixes
    """
    prompt = f"""You are a frontend developer expert at identifying visual bugs in web applications.

Analyze this screenshot for visual issues.

## CONTEXT
{context if context else "This is a web application that should display correctly."}

## REPORTED ISSUE
{error_description if error_description else "A visual regression test failed."}

## RELEVANT CSS (if available)
```css
{css_content if css_content else "CSS not provided"}
```

## TASK
1. Describe what you see in the screenshot
2. Identify any visual bugs or layout issues:
   - Overlapping elements
   - Hidden or obscured content
   - Broken layouts
   - Z-index issues
   - Spacing/margin problems
   - Color contrast issues
   - Missing or broken images
   - Text overflow/truncation
3. For each issue, suggest a CSS fix

## RESPONSE FORMAT (JSON)
```json
{{
    "screenshot_description": "Brief description of what's visible",
    "has_issues": true/false,
    "issues": [
        {{
            "type": "overlap|z-index|layout|spacing|contrast|broken-image|other",
            "element": "description of affected element",
            "problem": "what's wrong",
            "severity": "high|medium|low"
        }}
    ],
    "suggested_fixes": [
        {{
            "file": "path/to/file.css or component.tsx",
            "selector": ".class-name or element",
            "current_css": "current problematic CSS if known",
            "fixed_css": "the corrected CSS",
            "explanation": "why this fixes the issue"
        }}
    ],
    "confidence": 0.0-1.0
}}
```
"""
    
    try:
        current_key = key_rotator.get_current_key()
        client = genai.Client(api_key=current_key)
        
        image_data = base64.b64decode(screenshot_base64)
        
        response = client.models.generate_content(
            model=VISION_MODEL,
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": screenshot_base64
                            }
                        }
                    ]
                }
            ]
        )
        
       
        response_text = response.text
    
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        
        import json
        result = json.loads(response_text)
        
        return VisualBugReport(
            has_issues=result.get("has_issues", False),
            issues=result.get("issues", []),
            screenshot_description=result.get("screenshot_description", ""),
            suggested_fixes=result.get("suggested_fixes", []),
            confidence=result.get("confidence", 0.5)
        )
        
    except Exception as e:
        print(f"Visual analysis error: {e}")
        return VisualBugReport(
            has_issues=False,
            issues=[],
            screenshot_description=f"Error analyzing screenshot: {e}",
            suggested_fixes=[],
            confidence=0.0
        )


def get_visual_test_commands(project_type: str) -> Dict[str, str]:
    """
    Returns commands to run visual tests based on project type.
    """
    commands = {
        "nodejs": {
            "install": "npm install --save-dev playwright @playwright/test && npx playwright install chromium",
            "run": "npx playwright test --reporter=json",
            "config_file": "playwright.config.ts"
        },
        "python": {
            "install": "pip install playwright pytest-playwright && playwright install chromium",
            "run": "pytest --visual-regression",
            "config_file": "conftest.py"
        }
    }
    return commands.get(project_type, commands["nodejs"])


async def run_visual_regression_check(
    box, 
    url: str,
    baseline_screenshot_path: Optional[str] = None,
    viewport_width: int = 1280,
    viewport_height: int = 720
) -> Dict[str, Any]:
    """
    Runs a visual regression check in the sandbox.
    
    Args:
        box: TaskSandbox instance
        url: URL to test (can be localhost for dev server)
        baseline_screenshot_path: Path to baseline screenshot for comparison
        viewport_width: Browser viewport width
        viewport_height: Browser viewport height
    
    Returns:
        Dict with test results, screenshot, and analysis
    """
    result = {
        "passed": False,
        "screenshot_base64": None,
        "analysis": None,
        "error": None
    }
    
    
    box.write_file("visual_capture.py", get_playwright_setup_script())
    
    
    install_check = box.run_command("python3 -c 'from playwright.async_api import async_playwright' 2>&1 || echo 'NOT_INSTALLED'")
    
    if "NOT_INSTALLED" in install_check['stdout'] or install_check['exit_code'] != 0:
        print("Installing Playwright...")
        box.run_command("pip install playwright && playwright install chromium")
    
    
    capture_result = box.run_command(
        f"python3 visual_capture.py --url '{url}' --width {viewport_width} --height {viewport_height}"
    )
    
    try:
        import json
        capture_data = json.loads(capture_result['stdout'])
        
        if capture_data.get("success"):
            result["screenshot_base64"] = capture_data.get("screenshot_base64")
            result["console_errors"] = capture_data.get("console_errors", [])
            result["network_errors"] = capture_data.get("network_errors", [])
            
          
            if result["screenshot_base64"]:
                analysis = await analyze_screenshot_with_gemini(
                    screenshot_base64=result["screenshot_base64"],
                    error_description="Visual regression test - checking for UI issues"
                )
                result["analysis"] = {
                    "has_issues": analysis.has_issues,
                    "issues": analysis.issues,
                    "description": analysis.screenshot_description,
                    "suggested_fixes": analysis.suggested_fixes,
                    "confidence": analysis.confidence
                }
                result["passed"] = not analysis.has_issues
        else:
            result["error"] = capture_data.get("error", "Unknown capture error")
            
    except json.JSONDecodeError as e:
        result["error"] = f"Failed to parse capture result: {e}"
    
    return result


def generate_visual_fix_prompt(
    screenshot_base64: str,
    css_files: Dict[str, str],
    component_files: Dict[str, str],
    error_description: str
) -> str:
    """
    Generates a comprehensive prompt for fixing visual bugs.
    Includes screenshot and relevant code for context.
    """
    css_context = "\n\n".join([
        f"### {path}\n```css\n{content}\n```"
        for path, content in css_files.items()
    ])
    
    component_context = "\n\n".join([
        f"### {path}\n```tsx\n{content}\n```"
        for path, content in component_files.items()
    ])
    
    return f"""You are TALOS, an autonomous frontend developer fixing a visual bug.

## PROBLEM
{error_description}

## CURRENT CSS FILES
{css_context if css_context else "No CSS files provided"}

## CURRENT COMPONENTS
{component_context if component_context else "No component files provided"}

## INSTRUCTIONS
1. Analyze the screenshot attached to this message
2. Identify the visual issue
3. Provide the COMPLETE fixed file(s)

## RESPONSE FORMAT

**File: [path/to/file]**
```[language]
[Complete fixed code]
```

## VERIFICATION COMMAND
```bash
[Command to verify the fix - usually npm run build or npm run lint]
```

## PR DESCRIPTION
**Title**: fix: [brief description]
**Body**: [2-3 sentence explanation]
"""
