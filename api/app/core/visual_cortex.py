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

# Model with vision capabilities
VISION_MODEL = "gemini-2.0-flash"  # or gemini-1.5-pro for complex analysis


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
    Returns a Python script that sets up Playwright in the sandbox.
    This script handles installation and basic test execution.
    """
    return '''
import asyncio
import json
import sys
import base64
from pathlib import Path

async def capture_visual_state(url: str, viewport_width: int = 1280, viewport_height: int = 720):
    """
    Captures the visual state of a web page.
    Returns screenshot as base64 and any console errors.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print(json.dumps({"error": "playwright not installed", "install": "pip install playwright && playwright install chromium"}))
        sys.exit(1)
    
    result = {
        "success": False,
        "screenshot_base64": None,
        "console_errors": [],
        "network_errors": [],
        "viewport": {"width": viewport_width, "height": viewport_height}
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height}
        )
        page = await context.new_page()
        
        # Capture console errors
        page.on("console", lambda msg: result["console_errors"].append({
            "type": msg.type,
            "text": msg.text
        }) if msg.type == "error" else None)
        
        # Capture network failures
        page.on("requestfailed", lambda req: result["network_errors"].append({
            "url": req.url,
            "failure": req.failure
        }))
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Take full-page screenshot
            screenshot_bytes = await page.screenshot(full_page=True)
            result["screenshot_base64"] = base64.b64encode(screenshot_bytes).decode("utf-8")
            result["success"] = True
            
            # Get page title and URL for context
            result["title"] = await page.title()
            result["final_url"] = page.url
            
        except Exception as e:
            result["error"] = str(e)
        
        await browser.close()
    
    print(json.dumps(result))
    return result

async def run_visual_test(test_script: str):
    """
    Runs a Playwright test script and captures results.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print(json.dumps({"error": "playwright not installed"}))
        sys.exit(1)
    
    result = {
        "passed": False,
        "screenshots": [],
        "errors": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            # Execute the test script in a controlled environment
            exec_globals = {"browser": browser, "result": result, "asyncio": asyncio}
            exec(test_script, exec_globals)
            
            if "test" in exec_globals and asyncio.iscoroutinefunction(exec_globals["test"]):
                await exec_globals["test"]()
            
            result["passed"] = True
            
        except AssertionError as e:
            result["errors"].append({"type": "assertion", "message": str(e)})
        except Exception as e:
            result["errors"].append({"type": "exception", "message": str(e)})
        
        await browser.close()
    
    print(json.dumps(result))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="URL to capture")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    args = parser.parse_args()
    
    if args.url:
        asyncio.run(capture_visual_state(args.url, args.width, args.height))
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
        
        # Create image part from base64
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
        
        # Parse JSON from response
        response_text = response.text
        
        # Extract JSON from markdown code blocks if present
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
        print(f"⚠️ Visual analysis error: {e}")
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
    box,  # TaskSandbox instance
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
    
    # Write the Playwright helper script
    box.write_file("visual_capture.py", get_playwright_setup_script())
    
    # Install Playwright if needed
    install_check = box.run_command("python3 -c 'from playwright.async_api import async_playwright' 2>&1 || echo 'NOT_INSTALLED'")
    
    if "NOT_INSTALLED" in install_check['stdout'] or install_check['exit_code'] != 0:
        print("📦 Installing Playwright...")
        box.run_command("pip install playwright && playwright install chromium")
    
    # Capture the visual state
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
            
            # If we got a screenshot, analyze it
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

## 🧪 VERIFICATION COMMAND
```bash
[Command to verify the fix - usually npm run build or npm run lint]
```

## 📝 PR DESCRIPTION
**Title**: fix: [brief description]
**Body**: [2-3 sentence explanation]
"""
