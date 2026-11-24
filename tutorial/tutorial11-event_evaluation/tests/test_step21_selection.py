"""Check the event-specific direct-catchment / one-step tributary selection contract."""
import copy
import importlib.util
from pathlib import Path
import unittest

import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / "script/s21-gauge_allocation.py"
SPEC = importlib.util.spec_from_file_location("step21_selection", SCRIPT)
STEP21 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STEP21)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        # The reviewed Ahr anchor (2,0) drains one step into raw mainstem (1,1).
        axis = np.arange(3, dtype=float)
        outlets = np.ones((3, 3), dtype=float)
        area = np.full((3, 3), 100e6)
        area[2, 0] = 50e6
        nx = np.full((3, 3), -9)
        ny = np.full((3, 3), -9)
        nx[2, 0], ny[2, 0] = 2, 2
        self.data = (axis, axis, outlets, outlets, area, nx, ny, outlets, outlets)
        self.rows = []
        for report, cell in [("impact-ahr-schuld", (2, 0)), ("impact-ahr-altenahr", (1, 1))]:
            self.rows.append({
                "report_id": report, "river_group": "Ahr", "catmxy_status": "assigned",
                "catmxy_row_0based": str(cell[0]), "catmxy_col_0based": str(cell[1]),
                "river_allocation_status": "plausible", "river_allocation_reason": "lookup evidence",
                "ai_notes": "source note",
            })

    def test_direct_lookup_and_verified_one_step_proxy(self):
        STEP21.select_evaluation_cells(self.rows, self.data)
        direct, corrected = self.rows
        self.assertEqual((direct["river_model_row_0based"], direct["river_model_col_0based"]), (2, 0))
        self.assertEqual(corrected["river_allocation_method"], "one_step_upstream_tributary_proxy")
        self.assertEqual((corrected["river_model_row_0based"], corrected["river_model_col_0based"]), (2, 0))
        self.assertEqual((corrected["catmxy_row_0based"], corrected["catmxy_col_0based"]), ("1", "1"))
        self.assertEqual(corrected["river_allocation_status"], "plausible")
        self.assertEqual(corrected["river_correction_steps"], "1")

    def test_missing_anchor_or_wrong_edge_has_no_evaluation_cell(self):
        scenarios = [(self.rows[1:], self.data)]
        wrong = list(self.data)
        wrong[5] = wrong[5].copy()
        wrong[5][2, 0] = 1  # The anchor now drains to another incoming branch.
        scenarios.append((self.rows, tuple(wrong)))
        for rows, data in scenarios:
            with self.subTest(anchor_count=len(rows)):
                selected = copy.deepcopy(rows)
                STEP21.select_evaluation_cells(selected, data)
                corrected = selected[-1]
                self.assertEqual(corrected["river_allocation_status"], "unresolved")
                self.assertEqual(corrected["river_model_row_0based"], "")
                self.assertEqual(corrected["catmxy_row_0based"], "1")

    def test_missing_coordinates_never_snap_to_anchor(self):
        missing = dict(self.rows[1], catmxy_status="missing_coordinates",
                       catmxy_row_0based="", catmxy_col_0based="", river_allocation_status="unresolved")
        rows = [self.rows[0], missing]
        STEP21.select_evaluation_cells(rows, self.data)
        self.assertEqual(missing["river_model_row_0based"], "")
        self.assertEqual(missing["river_correction_applied"], "false")


if __name__ == "__main__":
    unittest.main()
