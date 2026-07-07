import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from app.agent import local_privacy_boundary_shield, dynamic_subscription_market_lookup

class TestFinShieldProductionSuite(unittest.TestCase):
    
    def test_context_hygiene_boundary_scrubbing(self):
        """Validates that plaintext financial identifiers are blocked before ingestion."""
        dirty_input = "User account bill101@gmail.com paid with card 4111-2222-3333-4444."
        sanitized_output, pii_detected = local_privacy_boundary_shield(dirty_input)
        
        self.assertTrue(pii_detected)
        self.assertNotIn("4111-2222-3333-4444", sanitized_output)
        self.assertIn("[[REDACTED_CARD_NUMBER]]", sanitized_output)
        print("\n✅ Edge context hygiene shield validation passed.")

    def test_dynamic_mcp_database_lookup(self):
        """Validates tool queries map dynamic registry values and invoke FX converters."""
        meta_string = dynamic_subscription_market_lookup("disney")
        
        # Verify that our tool correctly builds string contexts for our ADK Agent
        self.assertIsInstance(meta_string, str)
        self.assertTrue("Computed via live" in meta_string or "Standardized regional" in meta_string)
        print("✅ ADK external tool registry string verification passed.")

if __name__ == "__main__":
    unittest.main()