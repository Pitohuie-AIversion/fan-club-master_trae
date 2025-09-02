import sys
import os
from pathlib import Path
from multiprocessing import Queue

import pytest

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Try importing tkinter
try:
    import tkinter as tk
except Exception:
    tk = None

import fc.archive as ac
from fc.archive import FCArchive
from fc.backend.mapper import Mapper
from fc.frontend.gui.widgets.control import GridWidget, LiveTable

class CaptureSend:
    def __init__(self):
        self.last = None
    def __call__(self, vec):
        self.last = list(vec)


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


def tk_root():
    if tk is None:
        pytest.skip("tkinter not importable in this environment")
    try:
        root = tk.Tk()
        root.withdraw()
        return root
    except Exception as e:
        pytest.skip(f"Tk not available or misconfigured (init.tcl): {e}")


def approx_list(lst):
    return [round(x, 3) for x in lst]


def test_gridwidget_prefill():
    root = tk_root()
    ar = build_minimal_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    grid = GridWidget(root, ar, mapper, capture, q)
    grid.draw(cellLength=20)

    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]
    F = F_r + F_d
    grid.feedbackIn(F)

    grid.select_g(2)
    grid.map(GridWidget._const(0.7), 0, 0)
    assert approx_list(capture.last) == [0.2, 0.3, 0.7, 0.5]

    grid.deselect_g(2)
    grid.select_g(1)
    grid.select_g(3)
    grid.map(GridWidget._const(0.9), 0, 0)
    assert approx_list(capture.last) == [0.2, 0.9, 0.4, 0.9]

    F2_d = [0.21, 0.31, 0.41, 0.51]
    grid.feedbackIn(F_r + F2_d)
    grid.deselect_g(1)
    grid.deselect_g(3)
    grid.select_g(2)
    grid.map(GridWidget._const(0.8), 0, 0)
    assert approx_list(capture.last) == [0.21, 0.31, 0.8, 0.51]


def test_gridwidget_empty_selection_maps_all():
    root = tk_root()
    ar = build_minimal_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    grid = GridWidget(root, ar, mapper, capture, q)
    grid.draw(cellLength=20)

    # Provide initial feedback so prefill has values
    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]
    grid.feedbackIn(F_r + F_d)

    # No selection => selected_count=0, mapping should apply to all
    assert grid.selected_count == 0
    grid.map(GridWidget._const(0.6), 0, 0)
    assert approx_list(capture.last) == [0.6, 0.6, 0.6, 0.6]


def test_gridwidget_select_all_then_map():
    root = tk_root()
    ar = build_minimal_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    grid = GridWidget(root, ar, mapper, capture, q)
    grid.draw(cellLength=20)

    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]
    grid.feedbackIn(F_r + F_d)

    grid.selectAll()
    assert grid.selected_count == grid.size_g
    grid.map(GridWidget._const(0.75), 0, 0)
    assert approx_list(capture.last) == [0.75, 0.75, 0.75, 0.75]


def build_multi_layer_archive():
    q = Queue()
    ar = FCArchive(q, "TEST-ML", FCArchive.DEFAULT)
    P = ar.profile()
    P[ac.maxFans] = 4
    # 2 layers, 2x2
    P[ac.fanArray] = {ac.FA_rows: 2, ac.FA_columns: 2, ac.FA_layers: 2}
    base = dict(P[ac.defaultSlave])
    base[ac.SV_index] = 0
    base[ac.MD_assigned] = True
    base[ac.MD_row] = 0
    base[ac.MD_column] = 0
    base[ac.MD_rows] = 2
    base[ac.MD_columns] = 2
    # map fans 0..3 to both layers 0- and 1-, reusing same mapping per layer
    # Using "0-0,1-1,2-2,3-3" means: for each cell (0..3), layer0->fan, layer1->same fan
    base[ac.MD_mapping] = "0-0,1-1,2-2,3-3"
    P[ac.savedSlaves] = (base,)
    ar.profile(P)
    return ar


def test_gridwidget_multilayer_prefill_and_selection():
    root = tk_root()
    ar = build_multi_layer_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    grid = GridWidget(root, ar, mapper, capture, q)
    grid.draw(cellLength=20)

    # Feedback for 1 slave * 4 fans => size_k=4, duplicate for RPM/DC
    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]
    grid.feedbackIn(F_r + F_d)

    # Select one cell in layer 0 only
    grid.deepVar.set(False)  # operate only current layer
    grid.layer = 0
    grid.selected_g = [False]*grid.size_g
    grid.selected_count = 0
    g_target = 2  # layer0 index for cell (r=1,c=0)
    grid.select_g(g_target)

    # Map only selection; others should be prefilled from F_buffer
    grid.map(GridWidget._const(0.9), 0, 0)
    # With multilayer mapping, KG points to layer 1; selecting layer 0 only should not change anything
    assert approx_list(capture.last) == [0.2, 0.3, 0.4, 0.5]
    # Select one cell in layer 1 only
    grid.deepVar.set(False)  # operate only current layer
    grid.layer = 1
    grid.selected_g = [False]*grid.size_g
    grid.selected_count = 0
    g_target = grid.RC + 2  # layer1 index for cell (r=1,c=0)
    grid.select_g(g_target)
    
    # Map only selection; others should be prefilled from F_buffer
    grid.map(GridWidget._const(0.9), 0, 0)
    assert approx_list(capture.last) == [0.2, 0.3, 0.9, 0.5]

    # Stay on layer 1 and select a different cell; ensure prefill still works
    grid.layer = 1
    grid.selected_g = [False]*grid.size_g
    grid.selected_count = 0
    g_target_l1 = grid.RC + 1  # layer1, cell index 1
    grid.select_g(g_target_l1)
    grid.map(GridWidget._const(0.7), 0, 0)
    # Because mapping is by k (fans 0..3), and KG for multilayer points to layer1, expect changed index 1
    assert approx_list(capture.last) == [0.2, 0.7, 0.4, 0.5]


def test_gridwidget_hold_clears_selection_on_map():
    root = tk_root()
    ar = build_minimal_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    grid = GridWidget(root, ar, mapper, capture, q)
    grid.draw(cellLength=20)

    # Feed initial values
    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]
    grid.feedbackIn(F_r + F_d)

    # Select 1 and 3
    grid.deselectAll()
    grid.select_g(1)
    grid.select_g(3)
    assert grid.selected_count == 2

    # Disable hold => selection should be cleared after map
    grid.holdVar.set(False)
    grid.map(GridWidget._const(0.88), 0, 0)

    # Only selected were changed; others preserved via prefill
    assert approx_list(capture.last) == [0.2, 0.88, 0.4, 0.88]
    assert grid.selected_count == 0


def build_two_slave_archive():
    q = Queue()
    ar = FCArchive(q, "TEST-2S", FCArchive.DEFAULT)
    P = ar.profile()
    # 2x2 grid, 1 layer
    P[ac.fanArray] = {ac.FA_rows: 2, ac.FA_columns: 2, ac.FA_layers: 1}
    # each slave has 2 fans (2 rows x 1 column)
    P[ac.maxFans] = 2

    base = dict(P[ac.defaultSlave])
    base[ac.MD_assigned] = True
    base[ac.MD_rows] = 2
    base[ac.MD_columns] = 1
    base[ac.MD_row] = 0
    base[ac.MD_column] = 0
    base[ac.MD_mapping] = "0,1"  # two cells in its column

    base2 = dict(base)
    base2[ac.SV_index] = 1
    base2[ac.MD_column] = 1  # second column

    base[ac.SV_index] = 0

    P[ac.savedSlaves] = (base, base2)
    ar.profile(P)
    return ar


def test_gridwidget_multislave_prefill_selection_changes():
    root = tk_root()
    ar = build_two_slave_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    grid = GridWidget(root, ar, mapper, capture, q)
    grid.draw(cellLength=20)

    # size_k = nslaves * maxFans = 2 * 2 = 4
    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]  # k=0..3 => [s0f0, s0f1, s1f0, s1f1]
    grid.feedbackIn(F_r + F_d)

    # Select grid index mapping to k=1 (slave 0, fan 1): that's column 0, row 1 => g=1
    grid.deselectAll()
    grid.select_g(1)
    grid.map(GridWidget._const(0.9), 0, 0)
    # g=1 is in slave 1, fan 0 => k=2
    assert approx_list(capture.last) == [0.2, 0.3, 0.9, 0.5]
    
    # Select grid index mapping to k=2 (slave 1, fan 0): that's column 1, row 0 => g=2
    grid.deselectAll()
    grid.select_g(2)
    grid.map(GridWidget._const(0.6), 0, 0)
    # g=2 is in slave 0, fan 1 => k=1; control buffer is prefilled from F_buffer, so previous k=2 change reverts to 0.4
    assert approx_list(capture.last) == [0.2, 0.6, 0.4, 0.5]


def test_gridwidget_map_without_feedback_prefills_zero():
    root = tk_root()
    ar = build_minimal_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    grid = GridWidget(root, ar, mapper, capture, q)
    grid.draw(cellLength=20)

    # No feedback provided yet => F_buffer is zeros
    grid.deselectAll()
    grid.select_g(2)
    grid.map(GridWidget._const(0.42), 0, 0)

    # Only selected index updated, others stay at 0 due to zero-prefill
    assert approx_list(capture.last) == [0.0, 0.0, 0.42, 0.0]


def test_livetable_initially_paused_feedback_and_map():
    root = tk_root()
    ar = build_minimal_archive()
    mapper = Mapper(ar)
    capture = CaptureSend()
    q = Queue()

    lt = LiveTable(root, ar, mapper, capture, None, q)

    # Start paused
    lt.playPauseFlag = False
    F_r = [0, 0, 0, 0]
    F_d = [0.2, 0.3, 0.4, 0.5]
    F = F_r + F_d
    lt.feedbackIn(F)

    # While paused, F_buffer should NOT be updated (per current logic), so mapping should use initial zeros prefill then apply only selected
    # However, our implementation still allows control_buffer prefill only when F_buffer has data of size 2*size_k
    # Given F_buffer likely remains zeros, mapping should produce only the selected change with others defaulted from current buffer (zeros => remain 0 before send)

    lt.selected_g = [False] * lt.size_g
    lt.selected_g[2] = True
    lt.selected_count = 1
    lt.map(LiveTable._const(0.65), 0, 0)
    # Others are zero because no prefill occurred due to paused feedback
    assert approx_list(capture.last) == [0.0, 0.0, 0.65, 0.0]

    # Resume and feed again; then map a different index to check prefill now uses latest DCs
    lt.playPauseFlag = True
    lt.feedbackIn(F)
    lt.selected_g = [False] * lt.size_g
    lt.selected_g[0] = True
    lt.selected_count = 1
    lt.map(LiveTable._const(0.55), 0, 0)
    assert approx_list(capture.last) == [0.55, 0.3, 0.4, 0.5]