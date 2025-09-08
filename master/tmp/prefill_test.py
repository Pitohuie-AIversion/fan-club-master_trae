import sys
from pathlib import Path
# Ensure project root (containing 'fc') is importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tkinter as tk
from multiprocessing import Queue
import fc.archive as ac
from fc.archive import FCArchive
from fc.backend.mapper import Mapper
from fc.frontend.gui.widgets.control import GridWidget, LiveTable

class CaptureSend:
    def __init__(self):
        self.last = None
    def __call__(self, vec):
        self.last = list(vec)
        print("SENT:", ",".join(f"{v:.3f}" if isinstance(v, float) else str(v) for v in self.last))


def build_minimal_archive():
    q = Queue()
    # Pass DEFAULT at construction to avoid AttributeError
    ar = FCArchive(q, "TEST", FCArchive.DEFAULT)
    P = ar.profile()
    # Configure a 2x2x1 grid with 1 slave and 4 fans mapped 1:1
    P[ac.maxFans] = 4
    P[ac.fanArray] = {
        ac.FA_rows: 2,
        ac.FA_columns: 2,
        ac.FA_layers: 1,
    }
    base = dict(P[ac.defaultSlave])
    base[ac.SV_index] = 0
    base[ac.MD_assigned] = True
    base[ac.MD_row] = 0
    base[ac.MD_column] = 0
    base[ac.MD_rows] = 2
    base[ac.MD_columns] = 2
    base[ac.MD_mapping] = "0,1,2,3"  # 2x2 single layer mapping
    P[ac.savedSlaves] = (base,)
    ar.profile(P)
    return ar


def main():
    # Tk context for widget construction
    root = tk.Tk()
    root.withdraw()

    ar = build_minimal_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()

    q = Queue()

    # ---------- GridWidget tests ----------
    grid = GridWidget(root, ar, mapper, capture, q)

    # Build the grid so built() becomes True
    grid.draw(cellLength=20)

    # Feedback vector: first half RPMs (ignored here), second half DCs
    # size_k = nslaves * maxFans = 1*4 = 4
    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]
    F = F_r + F_d
    grid.feedbackIn(F)

    # Test 1: single selection keeps others, only selected updated
    grid.select_g(2)
    grid.map(GridWidget._const(0.7), 0, 0)
    print("CAPTURE:", capture.last)
    assert [round(x, 3) for x in capture.last] == [0.2, 0.3, 0.7, 0.5], "Grid Test1 failed"

    # Test 2: multi-selection updates selected indices, preserves others
    grid.deselect_g(2)
    grid.select_g(1)
    grid.select_g(3)
    grid.map(GridWidget._const(0.9), 0, 0)
    print("CAPTURE2:", capture.last)
    assert [round(x, 3) for x in capture.last] == [0.2, 0.9, 0.4, 0.9], "Grid Test2 failed"

    # Test 3: new feedback updates F_buffer, mapping uses latest values to prefill
    F2_d = [0.21, 0.31, 0.41, 0.51]
    grid.feedbackIn(F_r + F2_d)
    grid.deselect_g(1)
    grid.deselect_g(3)
    grid.select_g(2)
    grid.map(GridWidget._const(0.8), 0, 0)
    print("CAPTURE3:", capture.last)
    assert [round(x, 3) for x in capture.last] == [0.21, 0.31, 0.8, 0.51], "Grid Test3 failed"

    print("GridWidget prefill tests passed.")

    # ---------- LiveTable tests ----------
    lt_capture = CaptureSend()
    # LiveTable requires (master, archive, mapper, send_method, network, pqueue)
    lt = LiveTable(root, ar, mapper, lt_capture, None, q)

    # Initial feedback
    lt.feedbackIn(F)

    # LT Test 1: single selection behavior (manually set selection state)
    lt.selected_g = [False] * lt.size_g
    lt.selected_g[2] = True
    lt.selected_count = 1
    lt.map(LiveTable._const(0.7), 0, 0)
    print("LT_CAP1:", lt_capture.last)
    assert [round(x, 3) for x in lt_capture.last] == [0.2, 0.3, 0.7, 0.5], "LT Test1 failed"

    # LT Test 2: multi-selection updates
    lt.selected_g = [False] * lt.size_g
    for g in (1, 3):
        lt.selected_g[g] = True
    lt.selected_count = 2
    lt.map(LiveTable._const(0.9), 0, 0)
    print("LT_CAP2:", lt_capture.last)
    assert [round(x, 3) for x in lt_capture.last] == [0.2, 0.9, 0.4, 0.9], "LT Test2 failed"

    # LT Test 3: pause prevents F_buffer update, so prefill uses previous DCs
    lt.playPauseFlag = False  # Pause
    lt.feedbackIn(F_r + [0.21, 0.31, 0.41, 0.51])  # should NOT update F_buffer
    lt.selected_g = [False] * lt.size_g
    lt.selected_g[2] = True
    lt.selected_count = 1
    lt.map(LiveTable._const(0.8), 0, 0)
    print("LT_CAP3:", lt_capture.last)
    assert [round(x, 3) for x in lt_capture.last] == [0.2, 0.3, 0.8, 0.5], "LT Test3 failed"

    # LT Test 4: resume, feedback updates F_buffer, prefill uses new DCs
    lt.playPauseFlag = True  # Resume
    lt.feedbackIn(F_r + [0.21, 0.31, 0.41, 0.51])
    lt.selected_g = [False] * lt.size_g
    lt.selected_g[0] = True
    lt.selected_count = 1
    lt.map(LiveTable._const(0.6), 0, 0)
    print("LT_CAP4:", lt_capture.last)
    assert [round(x, 3) for x in lt_capture.last] == [0.6, 0.31, 0.41, 0.51], "LT Test4 failed"

    print("LiveTable prefill tests passed.")

    print("All prefill tests passed.")

if __name__ == "__main__":
    main()