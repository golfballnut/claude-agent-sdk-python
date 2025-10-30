#!/usr/bin/env python3
"""
Unit tests for Apollo contact validation functions

Tests the data integrity fixes for the duplicate contact bug (Oct 30, 2025)
where Apollo was returning the same 4 contacts for every golf course.

Run: python -m pytest testing/agents/test_apollo_validation.py -v
"""

import pytest
import sys
from pathlib import Path

# Add parent dirs to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agents.agent2_apollo_discovery import (
    validate_contact_domain,
    detect_duplicate_contacts,
    KNOWN_DUPLICATE_PERSON_IDS
)


class TestValidateContactDomain:
    """Test email domain validation"""

    def test_exact_domain_match(self):
        """Email domain exactly matches course domain"""
        contact = {"email": "john@deepspringscc.com"}
        assert validate_contact_domain(contact, "deepspringscc.com") == True

    def test_subdomain_match(self):
        """Email is subdomain of course domain"""
        contact = {"email": "john@golf.invitedclubs.com"}
        assert validate_contact_domain(contact, "invitedclubs.com") == True

    def test_parent_domain_match(self):
        """Course is subdomain, email is parent domain"""
        contact = {"email": "john@invitedclubs.com"}
        assert validate_contact_domain(contact, "golf.invitedclubs.com") == True

    def test_common_parent_domain(self):
        """Both are subdomains of same parent (invitedclubs.com)"""
        contact = {"email": "john@staff.invitedclubs.com"}
        assert validate_contact_domain(contact, "courses.invitedclubs.com") == True

    def test_domain_mismatch_rejects(self):
        """Email domain doesn't match course domain - should reject"""
        contact = {"email": "ed@glenella.com"}
        assert validate_contact_domain(contact, "deepspringscc.com") == False

    def test_wrong_domain_rejects(self):
        """Brad Worthington wrong email for Deercroft"""
        contact = {"email": "brad@poundridgegolf.com"}
        assert validate_contact_domain(contact, "deercroft.com") == False

    def test_construction_company_email_rejects(self):
        """Perry Langdon construction company email should reject"""
        contact = {"email": "plangdon@ellisdon.com"}
        assert validate_contact_domain(contact, "deepspringscc.com") == False

    def test_no_email_allows_through(self):
        """Contact without email can't be validated - allow through"""
        contact = {"name": "John Doe"}
        assert validate_contact_domain(contact, "deepspringscc.com") == True

    def test_no_domain_allows_through(self):
        """Can't validate without course domain - allow through"""
        contact = {"email": "john@example.com"}
        assert validate_contact_domain(contact, "") == True

    def test_domain_with_protocol_stripped(self):
        """Course domain with https:// should be stripped"""
        contact = {"email": "john@deepspringscc.com"}
        assert validate_contact_domain(contact, "https://deepspringscc.com") == True

    def test_domain_with_www_stripped(self):
        """Course domain with www. should be stripped"""
        contact = {"email": "john@deercroft.com"}
        assert validate_contact_domain(contact, "www.deercroft.com") == True


class TestDetectDuplicateContacts:
    """Test duplicate person ID detection"""

    def test_filters_ed_kivett(self):
        """Ed Kivett duplicate person ID should be filtered"""
        contacts = [
            {"name": "Ed Kivett", "person_id": "54a73cae7468696220badd21", "email": "ed@glenella.com"},
            {"name": "John Smith", "person_id": "abc123", "email": "john@example.com"}
        ]
        filtered = detect_duplicate_contacts(contacts, "Test Course")
        assert len(filtered) == 1
        assert filtered[0]["name"] == "John Smith"

    def test_filters_brad_worthington(self):
        """Brad Worthington duplicate person ID should be filtered"""
        contacts = [
            {"name": "Brad Worthington", "person_id": "62c718261e2f1f0001c47cf8"},
            {"name": "Valid Person", "person_id": "valid123"}
        ]
        filtered = detect_duplicate_contacts(contacts, "Test Course")
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Valid Person"

    def test_filters_greg_bryan(self):
        """Greg Bryan duplicate person ID should be filtered"""
        contacts = [
            {"name": "Greg Bryan", "person_id": "54a7002c7468696de70cf30b"},
            {"name": "Valid Person", "person_id": "valid123"}
        ]
        filtered = detect_duplicate_contacts(contacts, "Test Course")
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Valid Person"

    def test_filters_perry_langdon(self):
        """Perry Langdon duplicate person ID should be filtered"""
        contacts = [
            {"name": "Perry Langdon", "person_id": "57db939ca6da986873a1fa42"},
            {"name": "Valid Person", "person_id": "valid123"}
        ]
        filtered = detect_duplicate_contacts(contacts, "Test Course")
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Valid Person"

    def test_filters_all_duplicates(self):
        """All 4 known duplicates should be filtered"""
        contacts = [
            {"name": "Ed Kivett", "person_id": "54a73cae7468696220badd21"},
            {"name": "Brad Worthington", "person_id": "62c718261e2f1f0001c47cf8"},
            {"name": "Greg Bryan", "person_id": "54a7002c7468696de70cf30b"},
            {"name": "Perry Langdon", "person_id": "57db939ca6da986873a1fa42"},
            {"name": "Valid Person", "person_id": "valid123"}
        ]
        filtered = detect_duplicate_contacts(contacts, "Test Course")
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Valid Person"

    def test_keeps_valid_contacts(self):
        """Valid contacts with no duplicate IDs should pass through"""
        contacts = [
            {"name": "John Smith", "person_id": "abc123"},
            {"name": "Jane Doe", "person_id": "def456"},
            {"name": "Bob Wilson", "person_id": "ghi789"}
        ]
        filtered = detect_duplicate_contacts(contacts, "Test Course")
        assert len(filtered) == 3

    def test_empty_list_returns_empty(self):
        """Empty contact list should return empty"""
        filtered = detect_duplicate_contacts([], "Test Course")
        assert len(filtered) == 0

    def test_no_person_id_field(self):
        """Contacts without person_id field should pass through"""
        contacts = [
            {"name": "John Smith", "email": "john@example.com"}
        ]
        filtered = detect_duplicate_contacts(contacts, "Test Course")
        assert len(filtered) == 1


class TestKnownDuplicatePersonIds:
    """Test the known duplicate person IDs constant"""

    def test_has_ed_kivett(self):
        """Contains Ed Kivett person ID"""
        assert "54a73cae7468696220badd21" in KNOWN_DUPLICATE_PERSON_IDS

    def test_has_brad_worthington(self):
        """Contains Brad Worthington person ID"""
        assert "62c718261e2f1f0001c47cf8" in KNOWN_DUPLICATE_PERSON_IDS

    def test_has_greg_bryan(self):
        """Contains Greg Bryan person ID"""
        assert "54a7002c7468696de70cf30b" in KNOWN_DUPLICATE_PERSON_IDS

    def test_has_perry_langdon(self):
        """Contains Perry Langdon person ID"""
        assert "57db939ca6da986873a1fa42" in KNOWN_DUPLICATE_PERSON_IDS

    def test_is_set_type(self):
        """Known duplicates should be a set for O(1) lookup"""
        assert isinstance(KNOWN_DUPLICATE_PERSON_IDS, set)


class TestIntegrationScenarios:
    """Test realistic production scenarios"""

    def test_production_bug_scenario_deep_springs(self):
        """Replicate exact production bug: Deep Springs got wrong contacts"""
        contacts = [
            {
                "name": "Ed Kivett",
                "person_id": "54a73cae7468696220badd21",
                "email": "ed@glenella.com"
            },
            {
                "name": "Brad Worthington",
                "person_id": "62c718261e2f1f0001c47cf8",
                "email": "brad@poundridgegolf.com"
            }
        ]

        course_domain = "deepspringscc.com"

        # Domain validation would reject both
        assert validate_contact_domain(contacts[0], course_domain) == False
        assert validate_contact_domain(contacts[1], course_domain) == False

        # Duplicate detection would also reject both
        filtered = detect_duplicate_contacts(contacts, "Deep Springs Country Club")
        assert len(filtered) == 0

    def test_production_bug_scenario_deercroft(self):
        """Replicate exact production bug: Deercroft got same wrong contacts"""
        contacts = [
            {"name": "Ed Kivett", "person_id": "54a73cae7468696220badd21", "email": "ed@glenella.com"},
            {"name": "Perry Langdon", "person_id": "57db939ca6da986873a1fa42", "email": "plangdon@ellisdon.com"}
        ]

        course_domain = "deercroft.com"

        # Both should be rejected
        assert validate_contact_domain(contacts[0], course_domain) == False
        assert validate_contact_domain(contacts[1], course_domain) == False

        filtered = detect_duplicate_contacts(contacts, "Deercroft Golf & Country Club")
        assert len(filtered) == 0

    def test_valid_course_contacts_pass(self):
        """Valid contacts with matching domains should pass all checks"""
        contacts = [
            {
                "name": "John Smith",
                "person_id": "valid123",
                "email": "john@deepspringscc.com"
            },
            {
                "name": "Jane Doe",
                "person_id": "valid456",
                "email": "jane@deepspringscc.com"
            }
        ]

        course_domain = "deepspringscc.com"

        # Domain validation should pass
        assert validate_contact_domain(contacts[0], course_domain) == True
        assert validate_contact_domain(contacts[1], course_domain) == True

        # Duplicate detection should pass
        filtered = detect_duplicate_contacts(contacts, "Deep Springs Country Club")
        assert len(filtered) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
