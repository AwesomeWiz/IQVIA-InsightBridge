import unittest

from app import app
from setup_db import setup_database


class QueryApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup_database()
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def ask(self, question):
        response = self.client.post("/api/query", json={"question": question})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_california_premium_customers(self):
        result = self.ask("Which California customers use premium plans?")
        self.assertEqual(result["explanation"]["intent"], "customers_by_plan_location")
        # The supplied data has no California premium-plan customers, so the
        # correct result is a successful empty answer rather than invented rows.
        self.assertEqual(result["rows"], [])
        self.assertEqual(result["summary"], "No matching data was found.")

    def test_revenue_by_quarter(self):
        result = self.ask("Show revenue by quarter in 2023.")
        self.assertEqual([row[1] for row in result["rows"]], ["Q1", "Q2", "Q3", "Q4"])

    def test_high_or_critical_churn(self):
        result = self.ask("Which customers have high or critical churn risk?")
        self.assertTrue(all(row[2] in ("high", "critical") for row in result["rows"]))

    def test_open_sales_opportunities(self):
        result = self.ask("Show open sales opportunities.")
        self.assertTrue(all(row[2] not in ("closed_won", "closed_lost") for row in result["rows"]))

    def test_best_customers_requires_clarification(self):
        result = self.ask("Show the best customers.")
        self.assertIsNotNone(result["clarification"])


if __name__ == "__main__":
    unittest.main()
