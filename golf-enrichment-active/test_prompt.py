#!/usr/bin/env python3
"""
Test runner for enhanced golf course research prompt.
Tests the 8-section prompt on multiple courses and validates responses.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from claude_agent_sdk import query


class PromptTester:
    """Tests the enhanced research prompt on golf courses."""

    def __init__(self, base_dir: Path | None = None):
        """Initialize tester with base directory."""
        self.base_dir = base_dir or Path(__file__).parent
        self.prompt_file = self.base_dir / "prompts" / "enhanced_research_v1.md"
        self.courses_file = self.base_dir / "test_courses.json"
        self.schema_file = self.base_dir / "schemas" / "llm_response_v1.json"
        self.results_dir = self.base_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

    def load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        with open(self.prompt_file, "r") as f:
            return f.read()

    def load_test_courses(self) -> dict[str, Any]:
        """Load test course data."""
        with open(self.courses_file, "r") as f:
            return json.load(f)

    def load_schema(self) -> dict[str, Any]:
        """Load JSON schema for validation."""
        with open(self.schema_file, "r") as f:
            return json.load(f)

    def build_prompt_for_course(self, template: str, course: dict[str, Any]) -> str:
        """Replace template variables with course data."""
        return (
            template.replace("{COURSE_NAME}", course["course_name"])
            .replace("{CITY}", course["city"])
            .replace("{STATE}", course["state"])
        )

    async def run_test(self, course: dict[str, Any]) -> dict[str, Any]:
        """
        Run the prompt test on a single course.

        Returns:
            dict with keys: course_id, success, response, error, metadata
        """
        print(f"\n{'='*60}")
        print(f"Testing: {course['course_name']} ({course['city']}, {course['state']})")
        print(f"{'='*60}\n")

        template = self.load_prompt_template()
        prompt = self.build_prompt_for_course(template, course)

        result = {
            "course_id": course["id"],
            "course_name": course["course_name"],
            "city": course["city"],
            "state": course["state"],
            "test_time": datetime.now().isoformat(),
            "success": False,
            "response": None,
            "error": None,
            "metadata": {
                "prompt_length": len(prompt),
                "expected_insights": course.get("expected_insights", {}),
            },
        }

        try:
            print("Sending request to Claude...")
            print(f"Prompt length: {len(prompt)} characters\n")

            # Use the Claude SDK query function
            response = await query(
                prompt=prompt,
                # Extended timeout for web research
                # Can add options like model, etc. if needed
            )

            # Extract text response
            response_text = ""
            for block in response:
                if hasattr(block, "text"):
                    response_text += block.text

            print(f"Received response: {len(response_text)} characters\n")

            # Try to parse as JSON
            # Look for JSON in code blocks or raw text
            json_response = self._extract_json(response_text)

            if json_response:
                result["response"] = json_response
                result["success"] = True
                print("✅ JSON parsed successfully")

                # Basic validation
                validation_results = self._validate_response(json_response, course)
                result["validation"] = validation_results

                # Print summary
                self._print_response_summary(json_response, validation_results)
            else:
                result["error"] = "Could not parse JSON from response"
                result["raw_response"] = response_text[:1000]  # First 1000 chars
                print(f"❌ JSON parsing failed")
                print(f"Response preview:\n{response_text[:500]}...\n")

        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Error: {e}\n")

        return result

    def _extract_json(self, text: str) -> dict[str, Any] | None:
        """
        Extract JSON from response text.
        Handles JSON in code blocks or raw text.
        """
        # Try to find JSON in code blocks first
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_text = text[start:end].strip()
        else:
            # Try raw text
            json_text = text.strip()

        # Try to parse
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            # Try to find JSON object boundaries
            try:
                start = json_text.find("{")
                end = json_text.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(json_text[start:end])
            except:
                pass

        return None

    def _validate_response(
        self, response: dict[str, Any], course: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate response against expected structure.
        Returns validation results dict.
        """
        results = {
            "overall": True,
            "checks": [],
        }

        def check(name: str, passed: bool, message: str = ""):
            results["checks"].append(
                {"name": name, "passed": passed, "message": message}
            )
            if not passed:
                results["overall"] = False

        # Section 1: Classification (CRITICAL)
        s1 = response.get("section_1_classification", {})
        classification = s1.get("classification")
        check(
            "Section 1 classification present",
            classification
            in ["BOTH", "BUY", "SELL", "INSUFFICIENT_DATA"],
            f"Got: {classification}",
        )
        check("Section 1 confidence present", s1.get("confidence") is not None)
        check(
            "Section 1 reasoning present",
            s1.get("reasoning") is not None and len(str(s1.get("reasoning", ""))) > 10,
        )

        # Check signals have sources
        if classification in ["BUY", "BOTH"]:
            buy_signals = s1.get("buy_signals", [])
            check("BUY signals present", len(buy_signals) > 0)
            if buy_signals:
                has_sources = all("source" in sig for sig in buy_signals)
                check("BUY signals have sources", has_sources)

        if classification in ["SELL", "BOTH"]:
            sell_signals = s1.get("sell_signals", [])
            check("SELL signals present", len(sell_signals) > 0)
            if sell_signals:
                has_sources = all("source" in sig for sig in sell_signals)
                check("SELL signals have sources", has_sources)

        # Section 4: Decision makers (CRITICAL)
        decision_makers = response.get("section_4_decision_makers", [])
        check("Section 4 decision makers present", len(decision_makers) >= 0)
        if decision_makers:
            dm = decision_makers[0]
            check("Decision maker has name", "name" in dm)
            check("Decision maker has title", "title" in dm)
            check("Decision maker has priority", "priority" in dm)

        # Section 5: Course tier
        s5 = response.get("section_5_course_tier", {}).get("course_tier", {})
        tier = s5.get("classification")
        check(
            "Section 5 tier classification present",
            tier in ["premium", "medium", "budget"],
            f"Got: {tier}",
        )

        # Global checks
        check("Course name matches", response.get("course_name") == course["course_name"])
        check("Research date present", "research_date" in response)
        check("Research notes present", "research_notes" in response)

        return results

    def _print_response_summary(
        self, response: dict[str, Any], validation: dict[str, Any]
    ):
        """Print a summary of the response."""
        print("\n" + "-" * 60)
        print("RESPONSE SUMMARY")
        print("-" * 60)

        # Section 1
        s1 = response.get("section_1_classification", {})
        print(f"\n📊 CLASSIFICATION: {s1.get('classification', 'N/A')}")
        print(f"   Confidence: {s1.get('confidence', 'N/A')}")
        print(f"   Strategy: {s1.get('recommended_strategy', 'N/A')}")
        print(f"   Buy signals: {len(s1.get('buy_signals', []))}")
        print(f"   Sell signals: {len(s1.get('sell_signals', []))}")

        # Section 4
        decision_makers = response.get("section_4_decision_makers", [])
        print(f"\n👥 DECISION MAKERS: {len(decision_makers)} found")
        for i, dm in enumerate(decision_makers[:3], 1):  # Show first 3
            email_status = "✅" if dm.get("email") else "❌"
            print(f"   {i}. {dm.get('name', 'N/A')} - {dm.get('title', 'N/A')} {email_status}")

        # Section 5
        s5 = response.get("section_5_course_tier", {}).get("course_tier", {})
        print(f"\n🏌️  COURSE TIER: {s5.get('classification', 'N/A')}")
        print(f"   Type: {s5.get('course_type', 'N/A')}")

        # Validation
        print(f"\n✅ VALIDATION: {'PASSED' if validation['overall'] else 'FAILED'}")
        failed = [c for c in validation["checks"] if not c["passed"]]
        if failed:
            print(f"   Failed checks: {len(failed)}")
            for check in failed[:5]:  # Show first 5 failures
                print(f"   ❌ {check['name']}: {check.get('message', '')}")

        print("-" * 60 + "\n")

    def save_result(self, result: dict[str, Any]):
        """Save test result to file."""
        filename = f"{result['course_id']}_response.json"
        filepath = self.results_dir / filename

        with open(filepath, "w") as f:
            json.dump(result, f, indent=2)

        print(f"💾 Results saved to: {filepath}")

    async def run_phase(self, phase: int = 1):
        """
        Run a testing phase.

        Phase 1: Just The Neuse Golf Club
        Phase 2: All test courses
        """
        courses_data = self.load_test_courses()
        test_courses = courses_data["test_courses"]

        if phase == 1:
            courses_to_test = [c for c in test_courses if c["test_priority"] == 1]
        else:
            courses_to_test = test_courses

        print(f"\n🧪 PHASE {phase}: Testing {len(courses_to_test)} course(s)")
        print("=" * 60)

        results = []
        for course in courses_to_test:
            result = await self.run_test(course)
            self.save_result(result)
            results.append(result)

            # Pause between tests to avoid rate limits
            if len(courses_to_test) > 1:
                print("\nWaiting 5 seconds before next test...\n")
                await asyncio.sleep(5)

        # Print final summary
        self._print_phase_summary(results)

        return results

    def _print_phase_summary(self, results: list[dict[str, Any]]):
        """Print summary of all tests in phase."""
        print("\n" + "=" * 60)
        print("PHASE SUMMARY")
        print("=" * 60)

        successful = [r for r in results if r["success"]]
        print(f"\n✅ Successful: {len(successful)}/{len(results)}")

        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"\n{status} {result['course_name']}")

            if result["success"]:
                response = result["response"]
                classification = response.get("section_1_classification", {}).get(
                    "classification", "N/A"
                )
                decision_makers = len(response.get("section_4_decision_makers", []))
                validation = result.get("validation", {}).get("overall", False)

                print(f"   Classification: {classification}")
                print(f"   Decision makers: {decision_makers}")
                print(f"   Validation: {'PASSED' if validation else 'FAILED'}")
            else:
                print(f"   Error: {result.get('error', 'Unknown')}")

        print("\n" + "=" * 60)


async def main():
    """Main entry point."""
    tester = PromptTester()

    # Default to phase 1 (just The Neuse Golf Club)
    phase = 1
    if len(sys.argv) > 1:
        try:
            phase = int(sys.argv[1])
        except ValueError:
            print("Usage: python test_prompt.py [phase_number]")
            print("  phase 1: Test The Neuse Golf Club only (default)")
            print("  phase 2: Test all courses")
            sys.exit(1)

    await tester.run_phase(phase)


if __name__ == "__main__":
    asyncio.run(main())
