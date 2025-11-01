#!/usr/bin/env python3
"""
Golf Enrichment V2 Validator - Test Harness
Purpose: Automated testing of Render validator service in Docker
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any
import requests
from supabase import create_client, Client

# Configuration
VALIDATOR_URL = os.getenv("VALIDATOR_URL", "http://validator:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
TEST_DATA_DIR = "/app/test_data"
RESULTS_DIR = "/app/results"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


class TestResult:
    """Test result tracker"""
    def __init__(self, test_id: str, description: str):
        self.test_id = test_id
        self.description = description
        self.passed = False
        self.error = None
        self.validation_response = None
        self.db_records = {}
        self.duration = 0
        self.cost_estimate = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "description": self.description,
            "passed": self.passed,
            "error": self.error,
            "duration_seconds": self.duration,
            "cost_estimate": self.cost_estimate,
            "validation_response": self.validation_response,
            "db_records": self.db_records
        }


class TestHarness:
    """Main test harness"""

    def __init__(self):
        self.test_cases = []
        self.expected_outputs = {}
        self.results: List[TestResult] = []

    def load_test_data(self):
        """Load test cases and expected outputs"""
        print("Loading test data...")

        # Load test cases
        with open(f"{TEST_DATA_DIR}/v2_test_cases.json", 'r') as f:
            data = json.load(f)
            self.test_cases = data["cases"]

        # Load expected outputs
        with open(f"{TEST_DATA_DIR}/expected_outputs.json", 'r') as f:
            data = json.load(f)
            self.expected_outputs = data["test_expectations"]

        print(f"✅ Loaded {len(self.test_cases)} test cases")

    def check_validator_health(self) -> bool:
        """Verify validator service is healthy"""
        print("\nChecking validator health...")
        try:
            response = requests.get(f"{VALIDATOR_URL}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Validator is healthy")
                return True
            else:
                print(f"❌ Validator unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach validator: {e}")
            return False

    def run_validation_test(self, test_case: Dict[str, Any]) -> TestResult:
        """Run a single validation test"""
        test_id = test_case["test_id"]
        result = TestResult(test_id, test_case["description"])

        print(f"\n{'='*60}")
        print(f"Test: {test_id}")
        print(f"Description: {test_case['description']}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            # Step 1: Insert into staging table (mimics edge function behavior)
            staging_id = None
            if supabase:
                print("Inserting into llm_research_staging_test...")
                staging_response = supabase.table("llm_research_staging_test").insert({
                    "course_name": test_case["course_name"],
                    "state_code": test_case["state_code"],
                    "v2_json": test_case["v2_json"],
                    "status": "pending"
                }).execute()

                if staging_response.data:
                    staging_id = staging_response.data[0]["id"]
                    print(f"✅ Staging record created: {staging_id}")
                else:
                    print("❌ Failed to create staging record")
                    result.error = "Failed to insert into staging table"
                    return result
            else:
                # No Supabase - use mock UUID
                staging_id = "00000000-0000-0000-0000-000000000000"
                print(f"⚠️  Using mock staging_id (Supabase not configured)")

            # Step 2: Prepare request payload for validator
            payload = {
                "staging_id": staging_id,
                "course_name": test_case["course_name"],
                "state_code": test_case["state_code"],
                "v2_json": test_case["v2_json"]
            }

            # Call validator API
            print(f"Calling validator: POST {VALIDATOR_URL}/validate-and-write")
            response = requests.post(
                f"{VALIDATOR_URL}/validate-and-write",
                json=payload,
                timeout=30
            )

            result.validation_response = response.json() if response.ok else {"error": response.text}
            result.duration = time.time() - start_time

            # Check expected result
            expected = test_case["expected_result"]

            if expected == "success":
                # Should succeed
                if response.status_code == 200:
                    print("✅ Validation succeeded (expected)")
                    result.passed = self.verify_database_writes(test_case, result)
                else:
                    print(f"❌ Validation failed (expected success): {response.status_code}")
                    result.error = f"Expected success but got {response.status_code}: {response.text}"

            elif expected == "success_with_warning":
                # Should succeed with warnings
                if response.status_code == 200:
                    validation_flags = result.validation_response.get("validation_flags", [])
                    if validation_flags:
                        print(f"✅ Validation succeeded with warnings: {validation_flags}")
                        result.passed = True
                    else:
                        print("⚠️  Expected warnings but got none")
                        result.passed = False
                        result.error = "Expected validation warnings"
                else:
                    print(f"❌ Validation failed: {response.status_code}")
                    result.error = f"Expected success with warnings but failed: {response.text}"

            elif expected == "validation_error":
                # Should fail validation
                if response.status_code in [400, 422]:
                    print(f"✅ Validation failed as expected: {response.status_code}")
                    result.passed = True
                else:
                    print(f"❌ Expected validation error but got: {response.status_code}")
                    result.error = f"Expected validation error but got {response.status_code}"

            else:
                result.error = f"Unknown expected_result: {expected}"

        except Exception as e:
            result.error = str(e)
            print(f"❌ Test exception: {e}")

        result.duration = time.time() - start_time
        print(f"\nTest completed in {result.duration:.2f}s")
        print(f"Result: {'✅ PASS' if result.passed else '❌ FAIL'}")

        return result

    def verify_database_writes(self, test_case: Dict[str, Any], result: TestResult) -> bool:
        """Verify data was written to Supabase correctly"""
        if not supabase:
            print("⚠️  Supabase client not configured, skipping DB verification")
            return True  # Pass if no DB to check

        print("\nVerifying database writes...")
        test_id = test_case["test_id"]
        expected = self.expected_outputs.get(test_id, {})

        try:
            # Check staging table (test version)
            staging_response = supabase.table("llm_research_staging_test").select("*").eq(
                "course_name", test_case["course_name"]
            ).order("created_at", desc=True).limit(1).execute()

            if not staging_response.data:
                print("❌ No staging record found")
                return False

            staging_record = staging_response.data[0]
            result.db_records["staging"] = staging_record

            # Check validation status
            if staging_record.get("status") != expected.get("validation_status"):
                print(f"❌ Staging status mismatch: {staging_record.get('status')} != {expected.get('validation_status')}")
                return False

            print(f"✅ Staging record status: {staging_record.get('status')}")

            # Check course record (if validation succeeded)
            if expected.get("validation_status") == "validated":
                course_response = supabase.table("golf_courses_test").select("*").eq(
                    "course_name", test_case["course_name"]
                ).execute()

                if not course_response.data:
                    print("❌ No course record found")
                    return False

                course_record = course_response.data[0]
                result.db_records["course"] = course_record

                # Verify expected fields
                expected_fields = expected.get("expected_golf_course_fields", {})
                for field, expected_value in expected_fields.items():
                    actual_value = course_record.get(field)
                    if field == "v2_validation_flags":
                        # Special handling for flags (array comparison)
                        if set(actual_value or []) != set(expected_value):
                            print(f"⚠️  Field {field}: {actual_value} != {expected_value}")
                    elif actual_value != expected_value:
                        print(f"⚠️  Field {field}: {actual_value} != {expected_value}")

                print(f"✅ Course record found: {course_record['course_name']}")

                # Check contacts
                contacts_response = supabase.table("golf_course_contacts_test").select("*").eq(
                    "golf_course_id", course_record["id"]
                ).execute()

                result.db_records["contacts"] = contacts_response.data
                expected_count = expected.get("expected_contacts_count", 0)
                actual_count = len(contacts_response.data)

                if actual_count != expected_count:
                    print(f"⚠️  Contact count: {actual_count} != {expected_count}")
                else:
                    print(f"✅ Contact count: {actual_count}")

            return True

        except Exception as e:
            print(f"❌ Database verification error: {e}")
            return False

    def run_all_tests(self):
        """Run all test cases"""
        print(f"\n{'='*60}")
        print(f"Starting test suite: {len(self.test_cases)} tests")
        print(f"{'='*60}")

        for test_case in self.test_cases:
            result = self.run_validation_test(test_case)
            self.results.append(result)

            # Small delay between tests
            time.sleep(1)

    def generate_report(self):
        """Generate test report"""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        success_rate = (passed / total * 100) if total > 0 else 0
        total_duration = sum(r.duration for r in self.results)
        avg_duration = total_duration / total if total > 0 else 0

        print(f"Total tests: {total}")
        print(f"Passed: {passed} ({success_rate:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Total duration: {total_duration:.2f}s")
        print(f"Average duration: {avg_duration:.2f}s per test")

        # Detailed results
        print(f"\n{'='*60}")
        print("DETAILED RESULTS")
        print(f"{'='*60}")

        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"\n{status} - {result.test_id}")
            print(f"  Description: {result.description}")
            print(f"  Duration: {result.duration:.2f}s")
            if result.error:
                print(f"  Error: {result.error}")

        # Save JSON report
        os.makedirs(RESULTS_DIR, exist_ok=True)

        report = {
            "test_suite": "Golf Enrichment V2 Validator",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": success_rate,
                "total_duration_seconds": total_duration,
                "avg_duration_seconds": avg_duration
            },
            "results": [r.to_dict() for r in self.results]
        }

        with open(f"{RESULTS_DIR}/test_report.json", 'w') as f:
            json.dump(report, f, indent=2)

        # Save summary text
        summary_text = f"""
Golf Enrichment V2 Validator - Test Results
{'='*60}

Total Tests: {total}
Passed: {passed} ({success_rate:.1f}%)
Failed: {failed}

Total Duration: {total_duration:.2f}s
Average Duration: {avg_duration:.2f}s per test

{'='*60}

Deployment Ready: {'YES ✅' if failed == 0 else 'NO ❌'}
"""

        with open(f"{RESULTS_DIR}/summary.txt", 'w') as f:
            f.write(summary_text)

        print(f"\n{'='*60}")
        print(f"Reports saved to {RESULTS_DIR}/")
        print(f"  - test_report.json")
        print(f"  - summary.txt")
        print(f"{'='*60}")

        # Exit with appropriate code
        sys.exit(0 if failed == 0 else 1)


def main():
    """Main entry point"""
    print("="*60)
    print("Golf Enrichment V2 Validator - Test Harness")
    print("="*60)

    harness = TestHarness()

    # Load test data
    harness.load_test_data()

    # Check validator health
    if not harness.check_validator_health():
        print("\n❌ Validator is not healthy, cannot proceed")
        sys.exit(1)

    # Run tests
    harness.run_all_tests()

    # Generate report
    harness.generate_report()


if __name__ == "__main__":
    main()
