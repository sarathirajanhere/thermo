def test_deviation_calculation(self):
        """Test deviation calculation from baseline."""
        baseline = FacilityBaseline(self.facility_id)

        # Add historical data to establish baseline
        historical_values = [10.0, 12.0, 11.0, 13.0, 12.0]  # Mean = 11.6
        for val in historical_values:
            baseline.add_observation(val)

        # Test deviation calculation
        deviation_result = baseline.compute_deviation(20.0)

        self.assertEqual(deviation_result["baseline_status"], "AVAILABLE")
        self.assertAlmostEqual(deviation_result["expected_value"], 11.6)
        # Note: compute_deviation doesn't return current_value, only deviation and deviation_ratio
        self.assertAlmostEqual(deviation_result["deviation"], 8.4)  # 20.0 - 11.6
        self.assertAlmostEqual(deviation_result["deviation_ratio"], 8.4 / 11.6)