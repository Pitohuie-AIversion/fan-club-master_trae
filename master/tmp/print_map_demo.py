import sys
from pathlib import Path
from multiprocessing import Queue

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    import tkinter as tk
except Exception as e:
    print(f"[ERROR] tkinter not available: {e}")
    sys.exit(0)

from fc.archive import FCArchive
import fc.archive as ac
from fc.backend.mapper import Mapper
from fc.frontend.gui.widgets.control import GridWidget

class CaptureSend:
    def __init__(self):
        self.last = None
    def __call__(self, vec):
        self.last = list(vec)
        print("[SEND]", [round(x, 3) for x in self.last])


def build_minimal_archive():
    q = Queue()
    ar = FCArchive(q, "TEST", FCArchive.DEFAULT)
    P = ar.profile()
    P[ac.maxFans] = 4
    P[ac.fanArray] = {ac.FA_rows: 2, ac.FA_columns: 2, ac.FA_layers: 1}
    base = dict(P[ac.defaultSlave])
    base[ac.SV_index] = 0
    base[ac.MD_assigned] = True
    base[ac.MD_row] = 0
    base[ac.MD_column] = 0
    base[ac.MD_rows] = 2
    base[ac.MD_columns] = 2
    base[ac.MD_mapping] = "0,1,2,3"
    P[ac.savedSlaves] = (base,)
    ar.profile(P)
    return ar


def main():
    root = tk.Tk()
    root.withdraw()

    ar = build_minimal_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    grid = GridWidget(root, ar, mapper, capture, q)
    grid.draw(cellLength=20)

    # Provide initial feedback so prefill has values
    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]
    F = F_r + F_d
    grid.feedbackIn(F)

    print("Case1: select 2 -> map 0.7 (others retain prefill)")
    grid.select_g(2)
    grid.map(GridWidget._const(0.7), 0, 0)

    print("Case2: select 1 & 3 -> map 0.9 (others retain prefill)")
    grid.deselectAll()
    grid.select_g(1)
    grid.select_g(3)
    grid.map(GridWidget._const(0.9), 0, 0)

    print("Case3: new feedback, select 2 -> map 0.8")
    F2_d = [0.21, 0.31, 0.41, 0.51]
    grid.feedbackIn(F_r + F2_d)
    grid.deselectAll()
    grid.select_g(2)
    grid.map(GridWidget._const(0.8), 0, 0)

    print("Case4: empty selection -> map 0.6 to all")
    grid.deselectAll()
    grid.map(GridWidget._const(0.6), 0, 0)

    print("Case5: new grid without feedback, select 2 -> map 0.55 (others default)")
    grid2 = GridWidget(root, ar, mapper, capture, q)
    grid2.draw(cellLength=20)
    grid2.select_g(2)
    grid2.map(GridWidget._const(0.55), 0, 0)

    print("Done.")

if __name__ == "__main__":
    main()