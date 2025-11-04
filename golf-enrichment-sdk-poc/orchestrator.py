"""
Golf Course Research Orchestrator - SDK Implementation
Phase 2.5.2: Multi-tool research workflow for maximum accuracy

5-Step Workflow:
1. Firecrawl web search (comprehensive intel)
2. Jina official site scrape (verified data)
3. Hunter.io contact discovery (emails)
4. Perplexity fallback (fill gaps)
5. Synthesis & validation

Expected Results:
- 85-95% accuracy (vs 60-70% single-API)
- 60%+ email discovery (vs 30%)
- Full source URLs for citations
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, query
from agents.research_agent import golf_research_agent


class GolfCourseResearchOrchestrator:
    """Orchestrates multi-tool golf course research using SDK agents"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.results_dir = Path(__file__).parent / "results" / "sdk_agent"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def research_course(
        self,
        course_name: str,
        city: str,
        state_code: str
    ) -> Dict[str, Any]:
        """
        Research a single golf course using SDK agent + MCP tools

        Args:
            course_name: Name of golf course
            city: City location
            state_code: 2-letter state code

        Returns:
            Complete research results with quality metrics
        """
        print(f"\n{'='*60}")
        print(f"🏌️  Researching: {course_name}")
        print(f"📍 Location: {city}, {state_code}")
        print(f"{'='*60}\n")

        start_time = datetime.now()

        # Step 1: Prepare research prompt with course details
        # Note: MCP servers are already configured in ~/.claude/settings.json
        research_prompt = f"""Research the following golf course using the multi-tool workflow:

Course: {course_name}
City: {city}
State: {state_code}

Follow the 5-step research workflow:
1. Use Firecrawl to search for comprehensive information
2. Find and scrape official website with Jina Reader
3. Use Hunter.io Domain Search for contact discovery
4. Use Perplexity for any remaining gaps
5. Synthesize and validate all findings

Return complete JSON response per the schema in your instructions."""

        # Step 2: Execute research with SDK agent
        print("🤖 Starting SDK agent research...")
        print(f"📋 Allowed tools: Firecrawl, Hunter.io, Jina, Perplexity, Supabase")

        try:
            result = await self._execute_research(research_prompt)

            # Step 4: Extract and validate response
            research_data = self._extract_json_response(result)

            # Step 5: Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(research_data)

            # Step 6: Package complete result
            complete_result = {
                "course_name": course_name,
                "city": city,
                "state_code": state_code,
                "research_timestamp": datetime.now().isoformat(),
                "sdk_version": "claude-agent-sdk",
                "agent_used": "golf_research_agent",
                "research_data": research_data,
                "quality_metrics": quality_metrics,
                "execution_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
                "raw_response": result
            }

            # Step 7: Save results
            self._save_results(complete_result, course_name)

            # Step 8: Store in Supabase
            await self._store_in_database(complete_result)

            # Print summary
            self._print_summary(complete_result)

            return complete_result

        except Exception as e:
            print(f"❌ Error during research: {str(e)}")
            raise

    async def _execute_research(self, prompt: str) -> str:
        """Execute research using SDK Client with MCP support"""

        # Path to .mcp.json configuration
        mcp_config_path = Path(__file__).parent / ".mcp.json"

        options = ClaudeAgentOptions(
            agents={"golf_researcher": golf_research_agent},
            mcp_servers=str(mcp_config_path),  # Path to .mcp.json
            allowed_tools=[
                "mcp__firecrawl__firecrawl_search",
                "mcp__firecrawl__firecrawl_scrape",
                "mcp__jina__jina_reader",
                "mcp__jina__jina_search",
                "mcp__perplexity__perplexity_ask",  # Fixed: perplexity not perplexity-ask
                "mcp__hunter__Domain-Search",  # Fixed: hunter not hunter-io
                "mcp__hunter__Email-Finder",
                "mcp__hunter__Email-Verifier",
                "mcp__supabase__execute_sql",
            ],
            disallowed_tools=[
                "Bash", "Write", "Edit", "TodoWrite", "Task"
            ]
        )

        # Collect all messages from the agent
        full_response = []

        # Use ClaudeSDKClient for MCP support
        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            async for message in client.receive_response():
                # Extract text content from messages
                if hasattr(message, 'content'):
                    for block in message.content:
                        if hasattr(block, 'text') and block.text:
                            full_response.append(block.text)
                            print(f"  📝 {block.text[:100]}..." if len(block.text) > 100 else f"  📝 {block.text}")

        return "\n".join(full_response)

    def _extract_json_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from agent response"""
        # Look for JSON code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "{" in response and "}" in response:
            # Try to extract raw JSON
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
        else:
            raise ValueError("No JSON found in response")

        return json.loads(json_str)

    def _calculate_quality_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality metrics for validation"""

        # Count contacts
        decision_makers = data.get("section4_decision_makers", [])
        contact_count = len(decision_makers)
        emails_found = sum(1 for dm in decision_makers if dm.get("email"))

        # Count citations
        citation_count = self._count_citations(data)

        # Check tier classification
        tier_data = data.get("section5_course_tier", {})
        tier_classification = tier_data.get("classification", "not_found")

        # Check range ball classification
        classification_data = data.get("section1_classification", {})
        range_ball_classification = classification_data.get("classification", "not_found")

        # Calculate quality score (0-100)
        quality_score = 0

        # Contacts (40 points max)
        if contact_count >= 3:
            quality_score += 30
        elif contact_count >= 2:
            quality_score += 20
        elif contact_count >= 1:
            quality_score += 10

        if emails_found >= 2:
            quality_score += 10
        elif emails_found >= 1:
            quality_score += 5

        # Citations (30 points max)
        if citation_count >= 10:
            quality_score += 30
        elif citation_count >= 7:
            quality_score += 25
        elif citation_count >= 5:
            quality_score += 20
        elif citation_count >= 3:
            quality_score += 10

        # Classification (30 points max)
        if tier_classification not in ["not_found", "INSUFFICIENT_DATA"]:
            quality_score += 15

        if range_ball_classification not in ["not_found", "INSUFFICIENT_DATA"]:
            quality_score += 15

        return {
            "contact_count": contact_count,
            "emails_found": emails_found,
            "citation_count": citation_count,
            "tier_classification": tier_classification,
            "range_ball_classification": range_ball_classification,
            "quality_score": quality_score,
            "validation_status": "pass" if quality_score >= 60 else "review_needed",
            "validation_issues": self._identify_issues(quality_score, contact_count, citation_count, tier_classification)
        }

    def _count_citations(self, data: Dict[str, Any]) -> int:
        """Count total citations across all sections"""
        count = 0

        def count_sources(obj):
            nonlocal count
            if isinstance(obj, dict):
                if "source" in obj and obj["source"]:
                    count += 1
                for value in obj.values():
                    count_sources(value)
            elif isinstance(obj, list):
                for item in obj:
                    count_sources(item)

        count_sources(data)
        return count

    def _identify_issues(
        self,
        quality_score: int,
        contact_count: int,
        citation_count: int,
        tier_classification: str
    ) -> List[str]:
        """Identify quality issues"""
        issues = []

        if contact_count < 2:
            issues.append("Insufficient contacts (need ≥2)")
        if citation_count < 5:
            issues.append("Insufficient citations (need ≥5)")
        if tier_classification in ["not_found", "INSUFFICIENT_DATA"]:
            issues.append("Tier classification missing")
        if quality_score < 60:
            issues.append("Overall quality score below threshold")

        return issues

    def _save_results(self, result: Dict[str, Any], course_name: str) -> None:
        """Save results to JSON file"""
        safe_name = course_name.lower().replace(" ", "_").replace("'", "")
        filename = self.results_dir / f"{safe_name}_sdk_agent.json"

        with open(filename, "w") as f:
            json.dump(result, f, indent=2)

        print(f"\n💾 Results saved: {filename}")

    async def _store_in_database(self, result: Dict[str, Any]) -> None:
        """Store results in Supabase"""
        # TODO: Implement Supabase storage
        # For now, just print confirmation
        print("📊 Database storage: Not yet implemented")

    def _print_summary(self, result: Dict[str, Any]) -> None:
        """Print result summary"""
        metrics = result["quality_metrics"]

        print(f"\n{'='*60}")
        print(f"📊 RESEARCH SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Quality Score: {metrics['quality_score']}/100")
        print(f"👥 Contacts Found: {metrics['contact_count']} ({metrics['emails_found']} with emails)")
        print(f"📚 Citations: {metrics['citation_count']}")
        print(f"🏆 Tier: {metrics['tier_classification']}")
        print(f"⚾ Classification: {metrics['range_ball_classification']}")
        print(f"⏱️  Execution Time: {result['execution_time_ms']}ms")
        print(f"🔍 Validation: {metrics['validation_status']}")

        if metrics['validation_issues']:
            print(f"\n⚠️  Issues:")
            for issue in metrics['validation_issues']:
                print(f"   - {issue}")

        print(f"{'='*60}\n")


async def research_test_courses():
    """Test the orchestrator on 3 NC courses"""

    # Load environment variables
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")

    orchestrator = GolfCourseResearchOrchestrator(supabase_url, supabase_key)

    # Test courses (same as Session 12 Perplexity tests)
    test_courses = [
        {"name": "The Tradition Golf Club", "city": "Charlotte", "state": "NC"},
        {"name": "Forest Creek Golf Club", "city": "Pinehurst", "state": "NC"},
        {"name": "Hemlock Golf Course", "city": "Walnut Cove", "state": "NC"},
    ]

    results = []

    for course in test_courses:
        try:
            result = await orchestrator.research_course(
                course_name=course["name"],
                city=course["city"],
                state_code=course["state"]
            )
            results.append(result)

        except Exception as e:
            print(f"❌ Failed to research {course['name']}: {str(e)}")
            continue

    # Print comparison summary
    print(f"\n{'='*60}")
    print("📈 BATCH SUMMARY")
    print(f"{'='*60}")
    print(f"Total Courses: {len(test_courses)}")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(test_courses) - len(results)}")

    if results:
        avg_quality = sum(r["quality_metrics"]["quality_score"] for r in results) / len(results)
        avg_contacts = sum(r["quality_metrics"]["contact_count"] for r in results) / len(results)
        avg_citations = sum(r["quality_metrics"]["citation_count"] for r in results) / len(results)

        print(f"\nAverage Quality Score: {avg_quality:.1f}/100")
        print(f"Average Contacts: {avg_contacts:.1f}")
        print(f"Average Citations: {avg_citations:.1f}")

    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    asyncio.run(research_test_courses())
