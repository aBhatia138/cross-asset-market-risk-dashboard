import unittest

from src.tool_registry import execute_tool

class TestDashboardSnapshot(unittest.TestCase):
    #Prepare a valid dashboard context before each test
    def setUp(self):

        self.dashboard_context = {
            "ric":"XAU=",
            "start_date":"2026-10-01",
            "end_date":"2026-11-07",
            "first_observation":"2026-10-01",
            "last_observation":"2026-11-07",
            "metrics": {
                "Observations": 257,
                "Annualized Volatility": 0.2806,
                "Maximum Drawdown": -0.085,
                "Latest Price": 3980.50,
                "Latest Daily Return": 0.012
            }
        }

    def test_valid_dashboard_context(self):
        #A valid dahsboard context should return a successful snapshot
        result = execute_tool(
            "get_dashboard_snapshot",
            {},
            dashboard_context=self.dashboard_context
        )

        self.assertTrue(result["success"])

        self.assertEqual(
            result["ric"],
            "XAU="
        )

        self.assertEqual(
            result["date_range"]["start"],
            "2026-10-01"
        )

        self.assertEqual(
            result["date_range"]["end"],
            "2026-11-07"
        )

        self.assertEqual(
            result["metrics"]["Annualized Volatility"],
            0.2806
        )

    def test_missing_dashboard_context(self):
        #Missing dashboard context should return an error
        result = execute_tool(
            "get_dashboard_snapshot",
            {},
            dashboard_context=None
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "No dashboard data is currently available."
        )

    def test_incomplete_dashboard_context(self):
        #Missing required fields should cause the tool to fail

        incomplete_context = {
            "ric": "XAU=",
            "start_date": "2026-10-01",
            "metrics": {}
        }

        result = execute_tool(
            "get_dashboard_snapshot",
            {},
            dashboard_context=incomplete_context
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "Dashboard context is incomplete."
        )

    def test_invalid_metrics(self):
        #Metrics must be supplied as a dictionary

        invalid_context = self.dashboard_context.copy()
        invalid_context["metrics"] = None

        result = execute_tool(
            "get_dashboard_snapshot",
            {},
            dashboard_context=invalid_context
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"],
            "Dashboard metrics must be a dictionary."
        )

if __name__ == "__main__":
    unittest.main()

