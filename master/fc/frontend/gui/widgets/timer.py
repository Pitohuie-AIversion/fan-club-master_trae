################################################################################
## Project: Fanclub Mark IV "Master" timer widget ## File: timer.py          ##
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __  __   __                  ##
##                  | | |  | |  | T_| | || |    |  ||_ | | _|                 ##
##                  | _ |  |T|  |  |  |  _|      ||   \\_//                   ##
##                  || || |_ _| |_|_| |_| _|    |__|  |___|                   ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>  ##                ##
## dashuai                    ## <dschen2018@gmail.com>     ##                ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + General time-sequence control GUI widget.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import os
import time as tm

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.widgets import grid as gd
from fc.frontend.gui.embedded import colormaps as cms
from fc.frontend.gui.theme import BG_ACCENT

## GLOBALS #####################################################################
NOTHING = lambda: None

## CLASS #######################################################################
class TimerWidget(ttk.Frame):
    DEFAULT_STEP_MS = 100
    DEFAULT_END = 0

    END_STEP, END_TIME = 0, 1

    def __init__(self, master, startF, stopF, stepF, endDCF,logstartF,logstopF):
        ttk.Frame.__init__(self, master)

        # Setup:
        self.startF = startF
        self.stopF = stopF
        self.stepF = stepF
        self.endDCF = endDCF
        self.logstartF = logstartF
        self.logstopF = logstopF

        self.activeWidgets = []
        self.running = False
        self.period = self.DEFAULT_STEP_MS
        self.endType = None
        self.t0 = 0
        self.t = 0
        self.k0 = 0
        self.k = 0
        self.t_in = 0

        validateF = self.register(gus._validateF)
        validateC = self.register(gus._validateN)

        self.timeFrame = ttk.Frame(self)
        self.timeFrame.pack(fill = tk.BOTH, expand = True)

        self.timeTopBar = ttk.Frame(self.timeFrame, style="Topbar.TFrame")
        self.timeTopBar.pack(side = tk.TOP, fill = tk.X, expand = True)

        # Start/Stop button:
        self.startStopButton = ttk.Button(self.timeTopBar, text = "Start",
            command = self._start, style = "TButton")
        self.startStopButton.pack(side = tk.LEFT)

        # Step label:
        self.stepLabel = ttk.Label(self.timeTopBar, text = "   Step: ")
        self.stepLabel.pack(side = tk.LEFT)

        # Step field:
        validateC = self.register(gus._validateN)
        self.stepEntry = ttk.Entry(self.timeTopBar, width = 6,
            validate = 'key', validatecommand = (validateC, '%S', '%s', '%d'))
        self.stepEntry.insert(0, self.DEFAULT_STEP_MS)
        self.stepEntry.pack(side = tk.LEFT)
        self.activeWidgets.append(self.stepEntry)

        # Unit label:
        self.unitLabel = ttk.Label(self.timeTopBar, text = "(ms)",
            **gus.fontc)
        self.unitLabel.pack(side = tk.LEFT)

        # End label:
        self.endLabel = ttk.Label(self.timeTopBar, text = "   End: ")
        self.endLabel.pack(side = tk.LEFT)

        # End field:
        self.endEntry = ttk.Entry(self.timeTopBar, width = 6,
            validate = 'key',
            validatecommand = (validateC, '%S', '%s', '%d'))
        self.endEntry.pack(side = tk.LEFT)
        self.end = None
        self.activeWidgets.append(self.endEntry)

        self.ends = {"Step (k)":self.END_STEP, "Time (s)":self.END_TIME}
        self.endMenuVar = tk.StringVar()
        self.endMenuVar.set(tuple(self.ends.keys())[0])
        self.endMenu = ttk.OptionMenu(self.timeTopBar, self.endMenuVar, self.endMenuVar.get(), *list(self.ends.keys()))
        self.endMenu.configure(width = 10)
        self.endMenu.pack(side = tk.LEFT)
        self.activeWidgets.append(self.endMenu)

        # Timing display bar:
        self.timeDisplayBar = ttk.Frame(self.timeFrame)
        self.timeDisplayBar.pack(side = tk.TOP, fill = tk.X, expand = True,
            pady = 10)

        # Index display:
        self.kLabel = ttk.Label(self.timeDisplayBar, text = "  k = ")
        self.kLabel.pack(side = tk.LEFT)

        self.kVar = tk.IntVar()
        self.indexDisplay = ttk.Entry(self.timeDisplayBar, textvariable = self.kVar, justify = 'c',
            validate = 'key', validatecommand = (validateC, '%S', '%s', '%d'))
        self.indexDisplay.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.kVar.set(0)
        self.activeWidgets.append(self.indexDisplay)

        # Time display:
        self.tLabel = ttk.Label(self.timeDisplayBar, text = "  t = ")
        self.tLabel.pack(side = tk.LEFT)

        self.tVar = tk.DoubleVar()
        self.timeDisplay = ttk.Entry(self.timeDisplayBar, textvariable = self.tVar, justify = 'c',
            validate = 'key', validatecommand = (validateF, '%S', '%s', '%d'))
        self.timeDisplay.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.tVar.set(0.0)
        self.activeWidgets.append(self.timeDisplay)

        # Timing control bar:
        self.timeControlBar = ttk.Frame(self.timeFrame)
        self.timeControlBar.pack(side = tk.TOP, fill = tk.X, expand = True)

        # Control logging:
        self.logVar = tk.BooleanVar()
        self.logVar.set(False)
        self.logButton = ttk.Checkbutton(self.timeControlBar,
            text = "Log Data", variable = self.logVar, style="TCheckbutton")
        self.logButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.logButton)

        # End DC:
        self.endDCVar = tk.BooleanVar()
        self.endDCVar.set(False)
        self.endDCButton = ttk.Checkbutton(self.timeControlBar,
            text = "Set DC at end: ", variable = self.endDCVar, style="TCheckbutton")
        self.endDCButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.endDCButton)

        self.endDCEntry = ttk.Entry(self.timeControlBar, width = 6,
            validate = 'key',validatecommand = (validateF, '%S', '%s', '%d'))
        self.endDCEntry.pack(side = tk.LEFT, **gus.padc)
        self.endDCEntry.insert(0, "0")
        self.activeWidgets.append(self.endDCEntry)

        self.endDCLabel = ttk.Label(self.timeControlBar,
            text = "[0.0, 100.0]",
            style = "Secondary.TLabel")
        self.endDCLabel.pack(side = tk.LEFT)

    def _start(self, *_):
        if not self.running:
            if self.startF():
                self.startStopButton.config(state = tk.NORMAL, text = "Stop",
                    command = self._stop)

                self.running = True

                period_raw = self.stepEntry.get()
                self.period = int(period_raw if period_raw is not None else \
                    self.DEFAULT_STEP_MS)
                self.stepEntry.delete(0, tk.END)
                self.stepEntry.insert(0, self.period)

                t_raw = self.tVar.get()
                self.t_in = float(t_raw if t_raw is not None else 0.0)
                self.tVar.set(self.t_in)

                self.t0 = tm.time()
                self.t = self.t0 + self.t_in

                k_raw = self.kVar.get()
                self.k0 = int(k_raw if k_raw is not None else 0)
                self.kVar.set(self.k0)

                self.k = self.k0
                end_raw = self.endEntry.get()

                for widget in self.activeWidgets:
                    widget.config(state = tk.DISABLED)

                if end_raw is None or len(end_raw) == 0:
                    self.end = None
                else:
                    self.end = int(end_raw)
                    self.endType = self.ends[self.endMenuVar.get()]

                if self.logVar.get():
                    self.logstartF()

                self._step()

    def _stop(self, *_):
        if self.running:
            if self.endDCVar.get():
                endDC_raw = self.endDCEntry.get()
                if endDC_raw is not None and len(endDC_raw) > 0:
                    endDC = float(endDC_raw)/100.0
                    if endDC <= 1.0 and endDC >= 0.0:
                        self.endDCF(endDC)

            if self.logVar.get():
                self.logstopF()

            self.running = False
            self.t = 0
            self.k = 0
            self.tVar.set(self.t_in)
            self.kVar.set(self.k0)
            for widget in self.activeWidgets:
                widget.config(state = tk.NORMAL)
            self.startStopButton.config(state = tk.NORMAL, text = "Start",
                command = self._start)
            self.stopF()

    def _step(self):
        """
        Timer step function
        """
        try:
            # Check if widget still exists
            if not (hasattr(self, 'winfo_exists') and self.winfo_exists()):
                return
                
            if self.running:
                self.kVar.set(self.k)
                self.stepF(self.t, self.k)
                self.t = self.t_in + tm.time() - self.t0
                self.tVar.set(f"{self.t:.3f}")
                self.k += 1
                if self.end is not None and \
                    (self.endType == self.END_TIME and self.t > self.end or\
                    self.endType == self.END_STEP and self.k > self.end):
                    self._stop()
                else:
                    try:
                        if self.winfo_exists() and self.running:
                            self.after(self.period, self._step)
                    except (tk.TclError, AttributeError):
                        # Widget destroyed or error, stop timer
                        self.running = False
        except (tk.TclError, AttributeError):
            # Widget destroyed, stop timer
            self.running = False
        except Exception as e:
            print(f"Timer step error: {e}")
            self.running = False

