################################################################################
## Project: Fanclub Mark IV "Master" GUI          ## File: control.py         ##
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
## zhaoyang                   ## <mzymuzhaoyang@gmail.com> ##                 ##
## dashuai                    ## <dschen2018@gmail.com>    ##                 ##
##                            ##                           ##                 ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Graphical interface for the FC array control tools.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

# FUTURE ENHANCEMENTS:
# - Consider adding display table functionality to control panel
# - Implement MAC address-based grid mapping for network indices
# - Optimize board detection using total fan count after initial mapping

## IMPORTS #####################################################################
import os
import time as tm
import random as rd
import multiprocessing as mp
import copy as cp

import math
import random
from math import *
from random import *

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc import archive as ac, printer as pt, standards as std, utils as us
from fc.backend import mapper as mr

from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.embedded import colormaps as cms
from fc.frontend.gui.widgets import grid as gd, loader as ldr, timer as tmr, \
    external as ex, icon_button as ib
from fc.frontend.gui.theme import BG_ACCENT, SURFACE_1, SURFACE_3, TEXT_PRIMARY, TEXT_DISABLED, WARNING_LIGHT, WARNING_DARK

## GLOBALS #####################################################################
P_TIME = 't'
P_ROW, P_COLUMN, P_LAYER = 'r', 'c', 'l'
P_DUTY_CYCLE = 'd'
P_RPM = 'p'
P_MAX_RPM = 'P'
P_ROWS, P_COLUMNS, P_LAYERS = 'R', 'C', 'L'
P_INDEX, P_FAN = 's', 'f'
P_INDICES, P_FANS = 'S', 'F'
P_STEP = 'k'

## MAIN WIDGET #################################################################
class ControlWidget(ttk.Frame, pt.PrintClient):
    """
    Container for all the FC control GUI front-end widgets.
    """
    SYMBOL = "[CW]"

    def __init__(self, master, network, external, mapper, archive, pqueue,
        setLiveBE, setFBE):
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.archive = archive
        self.network = network
        self.external = external
        self.mapper = mapper
        self.setLiveBE, self.setFBE = setLiveBE, setFBE

        self.S_buffer = None
        self.N_buffer = None

        self.main = ttk.PanedWindow(self, orient = tk.HORIZONTAL)
        self.main.pack(fill = tk.BOTH, expand = True)

        self.displayFrame = ttk.Frame(self.main)
        self.displays = []

        self.controlFrame = ttk.Frame(self.main)
        self.control = None

        self.isLive = None
        self.maxRPM = None

        self._build()

        self.main.add(self.controlFrame, weight = 2)
        self.main.add(self.displayFrame, weight = 16)

    def redraw(self):
        """
        Rebuild widgets.
        """
        self.display.redraw()

    def feedbackIn(self, F, simulated = False):
        """
        Process a new feedback vector.
            - F := feedback vector to process.
            - simulated := whether this is a fake feedback vector to display
                when in flow builder mode. Defaults to False.
        """
        if self.isLive and not simulated:
            self.display.feedbackIn(F)
            self.control.feedbackIn(F)
        elif not self.isLive and simulated:
            self.display.feedbackIn(F)
            self.control.feedbackIn(F)
            self.setFBE(F)

    def slavesIn(self, S):
        """
        Process a new slaves vector.
        """
        self.S_buffer = S
        if self.isLive:
            self.display.slavesIn(S)
            self.control.slavesIn(S)

    def networkIn(self, N):
        """
        Process a new network vector.
        """
        self.N_buffer = N
        if self.isLive:
            self.display.networkIn(N)

    def blockAdjust(self):
        """
        Deactivate automatic adjustment of widgets upon window resizes.
        """
        self.display.blockAdjust()

    def unblockAdjust(self):
        """
        Activate automatic adjustment of widgets upon window resizes.
        """
        self.display.unblockAdjust()

    def _setLive(self, live, redundance = 0):
        """
        Set feedback display mode.
            - live := whether in live display mode (True) or in flow builder
                mode (False).
        """
        self.isLive = live
        self.setLiveBE(live)
        if self.isLive:
            if self.N_buffer is not None:
                self.display.networkIn(self.N_buffer)
            else:
                self.printw("No network state buffered when switching to Live")
            if self.S_buffer is not None:
                self.display.slavesIn(self.S_buffer)
            else:
                self.printw("No slave state buffered when switching to Live")
        else:
            self.display.activate()
            self.feedbackIn(self._emptyFeedback(), simulated = True)

    def _build(self):
        """
        Build sub-widgets.
        """
        self.maxRPM = self.archive[ac.maxRPM]
        self._buildDisplays()
        self._buildControl()
        self._setLive(True)

    def _buildControl(self):
        """
        Build control pane.
        """
        if self.control is not None:
            self.control.destroy()
            self.control = None
        self.control = ControlPanelWidget(self.controlFrame, self.mapper,
            self.archive, self.network, self.external, self.display,
            self._setLive, self.pqueue)
        self.control.pack(fill = tk.BOTH, expand = True)

    def _buildDisplays(self):
        """
        Build the interactive display widgets.
        """
        if self.displays:
            for display in self.displays:
                try:
                    if display.winfo_exists():
                        display.destroy()
                except tk.TclError:
                    # Widget already destroyed
                    pass
            try:
                if self.display.winfo_exists():
                    self.display.destroy()
            except tk.TclError:
                # Widget already destroyed
                pass
        self.displays = []

        self.display = DisplayMaster(self.displayFrame, self.pqueue)
        self.display.pack(fill = tk.BOTH, expand = True)

        # Grid:
        self.grid = GridWidget(self.display, self.archive,
            self.mapper, self._send, pqueue = self.pqueue)
        self.display.add(self.grid, text = "Control Grid")
        self.displays.append(self.grid)
        self.external.setController(self.grid)

        # Live table
        self.table = LiveTable(self.display, self.archive, self.mapper,
            self._send, self.network, pqueue = self.pqueue)
        self.display.add(self.table, text = "Live Table")
        self.displays.append(self.table)

    def _send(self, C):
        if self.isLive:
            self.network.controlIn(C)
        else:
            self.feedbackIn(self._buildFlow(C), True)

    def _buildFlow(self, C):
        """
        Build and return a simulated flow to feed back to the display widgets.
            - C := Control vector
        """
        F = [0]*len(C)
        for i, dc in enumerate(C):
            F[i] = int(dc*self.maxRPM)
        return F + C

    def _emptyFeedback(self):
        """
        Build a zeroed-out feedback vector based on the current profile.
        """
        return [0]*self.archive[ac.maxFans]*len(self.archive[ac.savedSlaves])*2

    def profileChange(self):
        """
        Handle a change in the loaded profile.
        """
        self._build()

## WIDGETS #####################################################################
class PythonInputWidget(ttk.Frame):
    """
    Base class for a widget for Python code input.
    """
    SYMBOL = "[PI]"

    WARNING = "NOTE: Scripts use zero-indexing"
    HEADER = "def duty_cycle({}):"
    FOOTER = "self.func = duty_cycle"

    IMPORTS = "math", "random"

    PARAMETERS = (P_ROW, P_COLUMN, P_LAYER, P_INDEX, P_FAN, P_DUTY_CYCLE, P_RPM,
        P_ROWS, P_COLUMNS, P_LAYERS, P_INDICES, P_FANS, P_MAX_RPM,P_TIME,P_STEP)


    def __init__(self, master, callback, pqueue):
        """
        Create a Python input widget in which the user may define a function
        to be mappeded throughout the array.

        CALLBACK is a method to which to pass the resulting Python function
        after being parsed and instantiated, as well as the current time step.
        """
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.parameters = self.PARAMETERS
        self._buildSignature()

        self.callback = callback

        self.interactive = []

        self.grid_columnconfigure(1, weight = 1)
        row = 0

        self.noteLabel = ttk.Label(
            self,
            text = self.WARNING,
            anchor = tk.W,
            style = "Warning.TLabel",
        )
        self.noteLabel.grid(row = row, column = 0, columnspan = 2, sticky = "EW")
        row += 1
        self.topLabel = ttk.Label(self,
            text = self.signature, anchor = tk.W, style = "Secondary.TLabel")
        self.topLabel.grid(row = row, column = 0, columnspan = 2, sticky = "EW")
        row += 1

        self.font = tk.font.Font(font = gus.typography["code"]["font"])
        self.tabstr = "  "
        self.tabsize = self.font.measure(self.tabstr)
        self.realtabs = "    "

        self.indent = ttk.Label(self, text = self.tabstr, style = "Secondary.TLabel")
        self.indent.grid(row = row, column = 0, sticky = "NS")

        self.text = tk.Text(self,
            width = 30, height = 2, padx = 10, pady = 0,
            **gus.text_conf,
            tabs = self.tabsize)
        self.text.grid(row = row, column = 1, rowspan = 2, sticky = "NEWS")
        self.grid_rowconfigure(row, weight = 1)
        self.interactive.append(self.text)

        # For scrollbar, see:
        # https://www.python-course.eu/tkinter_text_widget.php

        self.scrollbar = ttk.Scrollbar(self)
        self.scrollbar.grid(row = row, column = 2, rowspan = 1,
            sticky = "NS")
        self.scrollbar.config(command = self.text.yview)
        self.text.config(yscrollcommand = self.scrollbar.set)
        row += 1

        self.buttonFrame = ttk.Frame(self)
        self.buttonFrame.grid(row = row, column = 0, columnspan = 2,
            sticky = "WE")

        # TODO
        self.runButton = ib.create_apply_button(self.buttonFrame, 
            command = self._run)
        self.runButton.config_text("Apply Statically")
        self.runButton.pack(side = tk.LEFT, **gus.padc)
        self.interactive.append(self.runButton)

        self.loader = ldr.LoaderWidget(self.buttonFrame,
            filetypes = (("Fan Club Python Procedures", ".fcpy"),),
            onSave = self._onSave, onLoad = self._onLoad)
        self.loader.pack(side = tk.LEFT)

        # Wrap-up:
        self.func = None

    # API ......................................................................
    def enable(self):
        """
        Enable buttons and fields.
        """
        self.loader.enable()
        for widget in self.interactive:
            widget.config(state = tk.NORMAL)

    def disable(self):
        """
        Block all interactive components
        """
        self.loader.disable()
        for widget in self.interactive:
            widget.config(state = tk.DISABLED)

    def flat(self):
        """
        Get a "flat" (replace newline by semicolon) version of the currently
        written function.
        """
        body = self.text.get("1.0", tk.END)
        while '\n' in body:
            body = body.replace('\n', ";")
        return body

    def get(self, *_):
        """
        Parses and returns current function. Returns None if the input field is
        left blank
        """
        return self._parse()

    # Internal methods .........................................................
    def _parse(self):
        """
        Parse and return the current function.
        Uses secure code execution with restricted namespace.
        """
        raw = self.text.get(1.0, tk.END)
        if len(raw) < len("return"):
            self.printx("Code too short - must contain at least a return statement")
            return None
        
        # Input validation - check for dangerous operations
        dangerous_keywords = ['import', 'open', 'file', 'exec', 'eval', '__', 'globals', 'locals']
        for keyword in dangerous_keywords:
            if keyword in raw.lower():
                self.printx(f"Security warning: '{keyword}' is not allowed in user code")
                return None
        
        retabbed = raw.replace('\t', self.realtabs)

        built = self.signature + '\n'
        # Add safe imports to the function scope
        for imported in self.IMPORTS:
            built += self.realtabs + "import {}\n".format(imported)
        
        for line in retabbed.split('\n'):
            built += self.realtabs + line + '\n'
        built += self.FOOTER + '\n'

        # Secure execution with restricted namespace
        try:
            # Create restricted global namespace with only safe builtins
            safe_globals = {
                '__builtins__': {
                    'abs': abs, 'min': min, 'max': max, 'round': round,
                    'int': int, 'float': float, 'str': str, 'bool': bool,
                    'len': len, 'range': range, 'enumerate': enumerate,
                    'zip': zip, 'sum': sum, 'any': any, 'all': all
                },
                'math': __import__('math'),
                'random': __import__('random')
            }
            
            # Compile and execute the code safely
            compiled_code = compile(built, '<user_input>', 'exec')
            local_namespace = {}
            exec(compiled_code, safe_globals, local_namespace)
            
            # Extract the function from local namespace
            self.func = local_namespace.get('duty_cycle')
            if self.func is None:
                self.printx("Error: Function 'duty_cycle' not found in code")
                return None
                
        except SyntaxError as e:
            self.printx(f"Syntax error in code: {e}")
            return None
        except Exception as e:
            self.printx(f"Error executing code: {e}")
            return None
            
        return self.func

    def _run(self, *_):
        """
        To be called when the Run button is clicked. Parse the function and
        pass it to the given callback.
        """
        try:
            self._parse()
            if self.func is not None:
                self.callback(self.func, 0, 0)

        except Exception as e:
            self.printx(e, "Exception when parsing Python input:")

    def _buildSignature(self):
        """
        Build the function signature to be consistent with the
        current value of the stored parameter list.
        """
        self.signature = self.HEADER.format(
            ("{}, "*len(self.parameters)).format(*self.parameters)[:-2])

    def _onLoad(self, loaded):
        """
        To be executed by the Load routine within a LoaderWidget.
        """
        if loaded is not None:
            body, filename = loaded
            self.printr("Loaded FC Python function \"{}\"".format(filename))
            self.text.delete('1.0', tk.END)
            self.text.insert('1.0', body)
            # See: https://stackoverflow.com/questions/27966626/
            #   how-to-clear-delete-the-contents-of-a-tkinter-text-widget

    def _builtin(self, *E):
        """
        To be executed by the Built-in button.
        """
        print("[WARNING] _builtin not implemented ")

    def _onSave(self, *E):
        """
        To be executed by the Save routine within a LoaderWidget.
        """
        return self.text.get('1.0', tk.END)

    def _help(self, *E):
        """
        To be executed by Help button.
        """
        print("[WARNING] _help not implemented ")

class MainControlWidget(ttk.Frame, pt.PrintClient):
    """
    Container for the steady flow control tools.
    """
    SYMBOL = "[SC]"
    SLIDER_MIN = 0
    SLIDER_MAX = 100

    FT_ROW, FT_COL, FT_TV, FT_GNLOG, FT_GDLOG = 0, 1 ,2 ,3, 5
    FT_LIST = 4  # List file type
    FT_LGU, FT_LGG = 6, 7  # Log file types for user and grid
    FILETYPES = (
        ("Row (,)", FT_ROW),
        ("Column (\\n)", FT_COL),
        ("t, val", FT_TV),
        ("Log (gen)", FT_GNLOG),
        ("Log (grid)", FT_GDLOG),
    )


    def __init__(self, master, network, display, logstart, logstop,  pqueue):
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ................................................................
        self.network = network
        self.display = display

        self.logstart, self.logstop = logstart, logstop

        self.grid_columnconfigure(0, weight = 1)
        row = 0
        self.loadedFlow = None
        self.flowType = None
        self.values = None
        self.n = None
        self.times = None
        self.tmax = 0
        self.activeWidgets = []

        # Callbacks:
        self.selectAll = self._nothing
        self.deselectAll = self._nothing

        self.simpleFrame = ttk.Frame(self)
        self.simpleFrame.grid(row = row, sticky = "EW")
        row += 1

        # Direct input .........................................................
        self.directFrame = ttk.LabelFrame(self.simpleFrame,
            text = "Direct input")
        self.directFrame.pack(side = tk.LEFT, fill = tk.X, expand = True)

        # Register validation function for numeric input
        vcmd = (self.register(self._validateNumeric), '%P')
        
        self.directValueEntry = ttk.Entry(self.directFrame, width = 6, 
                                        validate='key', validatecommand=vcmd)
        self.directValueEntry.pack(side = tk.LEFT, **gus.padc)
        # Input validation implemented for duty cycle values (0-100)
        self.sendDirectButton = ttk.Button(self.directFrame, text = "Apply",
            command = self._onSendDirect)
        self.sendDirectButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.directValueEntry)
        self.activeWidgets.append(self.sendDirectButton)

        # Keyboard bindings for enhanced user experience
        self._setupKeyboardBindings()

        # Random flow ..........................................................
        self.randomFrame = ttk.LabelFrame(self.simpleFrame, text = "Random Flow")
        self.randomFrame.pack(side = tk.LEFT, fill = tk.X, expand = True)

        self.leftB = ttk.Label(self.randomFrame, text = "[", style = "Secondary.TLabel")
        self.leftB.pack(side = tk.LEFT)

        # Input validation for random range values
        self.randomLow = ttk.Entry(self.randomFrame, width = 5,
                                 validate='key', validatecommand=vcmd)
        self.randomLow.pack(side = tk.LEFT)
        self.randomLow.insert(0, "0")
        self.activeWidgets.append(self.randomLow)

        self.comma = ttk.Label(self.randomFrame, text = ", ", style = "Secondary.TLabel")
        self.comma.pack(side = tk.LEFT)

        # Input validation for random range values
        self.randomHigh = ttk.Entry(self.randomFrame, width = 5,
                                  validate='key', validatecommand=vcmd)
        self.randomHigh.pack(side = tk.LEFT)
        self.randomHigh.insert(0, "100")
        self.activeWidgets.append(self.randomHigh)

        self.rightB = ttk.Label(self.randomFrame, text = "]", style = "Secondary.TLabel")
        self.rightB.pack(side = tk.LEFT)

        self.sendRandomButton = ttk.Button(self.randomFrame, text = "Apply",
            command = self._sendRandom)
        self.sendRandomButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.sendRandomButton)

        # Slider ...............................................................
        self.sliderFrame = ttk.LabelFrame(self, text = "Slider")
        self.sliderFrame.grid(row = row, sticky = "EW")
        row += 1

        # Slider:
        self.slider = ttk.Scale(self.sliderFrame, from_ = 0, to = 100,
            command = lambda s: self._sendDirect(float(s)),
            orient = tk.HORIZONTAL)
        self.slider.pack(side = tk.TOP, fill = tk.X, expand = True)
        self.activeWidgets.append(self.slider)

        # Quick duty cycles:
        self.quickDCButtons = []
        self.quickDCFrame = ttk.Frame(self.sliderFrame)
        self.quickDCFrame.pack(side = tk.TOP, fill = tk.X, expand = True)
        for dc in [0, 10, 20, 30, 50, 70, 80, 90, 100]:
            button = ttk.Button(self.quickDCFrame, text = "{:3d}%".format(dc),
                command = self._quickDCCallback(dc/100))
            button.pack(side = tk.LEFT, fill = tk.X, expand = True)
            self.quickDCButtons.append(button)
            self.activeWidgets.append(button)

        # CHASE Control ........................................................
        self.chaseFrame = ttk.LabelFrame(self, text = "CHASE Mode")
        self.chaseFrame.grid(row = row, sticky = "EW")
        row += 1

        self.chaseControlFrame = ttk.Frame(self.chaseFrame)
        self.chaseControlFrame.pack(side = tk.TOP, fill = tk.X, expand = True)

        self.chaseLabel = ttk.Label(self.chaseControlFrame, text = "Target RPM:", style = "Secondary.TLabel")
        self.chaseLabel.pack(side = tk.LEFT, **gus.padc)

        self.chaseRPMEntry = ttk.Entry(self.chaseControlFrame, width = 8)
        self.chaseRPMEntry.pack(side = tk.LEFT, **gus.padc)
        self.chaseRPMEntry.insert(0, "1000")
        self.activeWidgets.append(self.chaseRPMEntry)

        # Fan Selection for CHASE Mode
        self.chaseFanFrame = ttk.Frame(self.chaseFrame)
        self.chaseFanFrame.pack(side = tk.TOP, fill = tk.X, expand = True, pady = 2)

        self.chaseFanLabel = ttk.Label(self.chaseFanFrame, text = "Fan Selection:", style = "Secondary.TLabel")
        self.chaseFanLabel.pack(side = tk.LEFT, **gus.padc)

        # Target selection radio buttons
        self.chaseTargetVar = tk.StringVar(value = "all")
        self.chaseAllRadio = ttk.Radiobutton(self.chaseFanFrame, text = "All Fans", 
            variable = self.chaseTargetVar, value = "all", command = self._onChaseTargetChange)
        self.chaseAllRadio.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.chaseAllRadio)

        self.chaseSelectedRadio = ttk.Radiobutton(self.chaseFanFrame, text = "Selected", 
            variable = self.chaseTargetVar, value = "selected", command = self._onChaseTargetChange)
        self.chaseSelectedRadio.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.chaseSelectedRadio)

        # Fan selection entry (for selected mode)
        self.chaseFanSelectionFrame = ttk.Frame(self.chaseFrame)
        self.chaseFanSelectionFrame.pack(side = tk.TOP, fill = tk.X, expand = True, pady = 2)

        self.chaseFanSelectionLabel = ttk.Label(self.chaseFanSelectionFrame, text = "Selection String:", style = "Secondary.TLabel")
        self.chaseFanSelectionLabel.pack(side = tk.LEFT, **gus.padc)

        self.chaseFanSelectionEntry = ttk.Entry(self.chaseFanSelectionFrame, width = 20)
        self.chaseFanSelectionEntry.pack(side = tk.LEFT, **gus.padc)
        self.chaseFanSelectionEntry.insert(0, "11110000")  # Default selection pattern
        self.chaseFanSelectionEntry.config(state = tk.DISABLED)  # Initially disabled
        self.activeWidgets.append(self.chaseFanSelectionEntry)

        # Help label for selection format
        self.chaseHelpLabel = ttk.Label(self.chaseFanSelectionFrame, 
            text = "(1=selected, 0=not selected)", style = "Secondary.TLabel")
        self.chaseHelpLabel.pack(side = tk.LEFT, **gus.padc)

        # Note: Using Feedback Control mode only (Standard CHASE mode removed)

        # Control buttons frame
        self.chaseButtonFrame = ttk.Frame(self.chaseFrame)
        self.chaseButtonFrame.pack(side = tk.TOP, fill = tk.X, expand = True, pady = 2)

        self.chaseStartButton = ttk.Button(self.chaseButtonFrame, text = "Start CHASE",
            command = self._onStartChase)
        self.chaseStartButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.chaseStartButton)

        self.chaseStopButton = ttk.Button(self.chaseButtonFrame, text = "Stop",
            command = self._onStopChase, style = "Secondary.TButton")
        self.chaseStopButton.pack(side = tk.LEFT, **gus.padc)
        self.chaseStopButton.config(state = tk.DISABLED)
        self.activeWidgets.append(self.chaseStopButton)

        self.chaseStatusLabel = ttk.Label(self.chaseFrame, text = "Status: Ready", style = "Secondary.TLabel")
        self.chaseStatusLabel.pack(side = tk.TOP, **gus.padc)

        # PI Parameter Tuning Frame (only visible when feedback control is selected)
        self.piTuningFrame = ttk.LabelFrame(self.chaseFrame, text = "PI Parameter Tuning")
        self.piTuningFrame.pack(side = tk.TOP, fill = tk.X, expand = True, pady = 2)
        self.piTuningFrame.pack_forget()  # Initially hidden

        # Kp parameter adjustment
        self.kpFrame = ttk.Frame(self.piTuningFrame)
        self.kpFrame.pack(side = tk.TOP, fill = tk.X, expand = True, pady = 1)

        self.kpLabel = ttk.Label(self.kpFrame, text = "Kp (比例增益):", style = "Secondary.TLabel")
        self.kpLabel.pack(side = tk.LEFT, **gus.padc)

        # Kp validation function for numeric input
        vcmd_kp = (self.register(self._validatePIParameter), '%P', 'kp')
        self.kpEntry = ttk.Entry(self.kpFrame, width = 8, validate='key', validatecommand=vcmd_kp)
        self.kpEntry.pack(side = tk.LEFT, **gus.padc)
        self.kpEntry.insert(0, "0.5")  # Default Kp value - updated to match backend
        self.activeWidgets.append(self.kpEntry)

        self.kpScale = ttk.Scale(self.kpFrame, from_ = 0.1, to = 2.0, 
            command = self._onKpScaleChange, orient = tk.HORIZONTAL, length = 150)
        self.kpScale.pack(side = tk.LEFT, fill = tk.X, expand = True, **gus.padc)
        self.kpScale.set(0.5)  # Default value - updated to match backend
        self.activeWidgets.append(self.kpScale)

        self.kpRangeLabel = ttk.Label(self.kpFrame, text = "(0.1-2.0)", style = "Secondary.TLabel")
        self.kpRangeLabel.pack(side = tk.LEFT, **gus.padc)

        # Ki parameter adjustment
        self.kiFrame = ttk.Frame(self.piTuningFrame)
        self.kiFrame.pack(side = tk.TOP, fill = tk.X, expand = True, pady = 1)

        self.kiLabel = ttk.Label(self.kiFrame, text = "Ki (积分增益):", style = "Secondary.TLabel")
        self.kiLabel.pack(side = tk.LEFT, **gus.padc)

        # Ki validation function for numeric input
        vcmd_ki = (self.register(self._validatePIParameter), '%P', 'ki')
        self.kiEntry = ttk.Entry(self.kiFrame, width = 8, validate='key', validatecommand=vcmd_ki)
        self.kiEntry.pack(side = tk.LEFT, **gus.padc)
        self.kiEntry.insert(0, "0.1")  # Default Ki value - updated to match backend
        self.activeWidgets.append(self.kiEntry)

        self.kiScale = ttk.Scale(self.kiFrame, from_ = 0.01, to = 0.5, 
            command = self._onKiScaleChange, orient = tk.HORIZONTAL, length = 150)
        self.kiScale.pack(side = tk.LEFT, fill = tk.X, expand = True, **gus.padc)
        self.kiScale.set(0.1)  # Default value - updated to match backend
        self.activeWidgets.append(self.kiScale)

        self.kiRangeLabel = ttk.Label(self.kiFrame, text = "(0.01-0.5)", style = "Secondary.TLabel")
        self.kiRangeLabel.pack(side = tk.LEFT, **gus.padc)

        # PI tuning buttons
        self.piButtonFrame = ttk.Frame(self.piTuningFrame)
        self.piButtonFrame.pack(side = tk.TOP, fill = tk.X, expand = True, pady = 2)

        self.autoTuneButton = ttk.Button(self.piButtonFrame, text = "自动调优",
            command = self._onPIAutoTune)
        self.autoTuneButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.autoTuneButton)

        self.resetPIButton = ttk.Button(self.piButtonFrame, text = "重置默认值",
            command = self._onPIReset, style = "Secondary.TButton")
        self.resetPIButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.resetPIButton)

        self.applyPIButton = ttk.Button(self.piButtonFrame, text = "应用参数",
            command = self._onPIApply)
        self.applyPIButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.applyPIButton)

        # PI status display
        self.piStatusFrame = ttk.Frame(self.piTuningFrame)
        self.piStatusFrame.pack(side = tk.TOP, fill = tk.X, expand = True, pady = 1)

        # Current parameters display
        self.piCurrentLabel = ttk.Label(self.piStatusFrame, text = "当前参数: Kp=0.01, Ki=0.001", style = "Secondary.TLabel")
        self.piCurrentLabel.pack(side = tk.LEFT, **gus.padc)

        self.piPerformanceLabel = ttk.Label(self.piStatusFrame, text = "性能: 稳定", style = "Secondary.TLabel")
        self.piPerformanceLabel.pack(side = tk.RIGHT, **gus.padc)

        # Status message display (separate from current parameters)
        self.piStatusLabel = ttk.Label(self.piStatusFrame, text = "状态: 就绪", style = "Secondary.TLabel")
        self.piStatusLabel.pack(side = tk.LEFT, padx=(10, 0))

        # Padding row:
        self.grid_rowconfigure(row, weight = 2)
        row += 1

        # Load Flows ...........................................................
        self.flowFrame = ttk.LabelFrame(self, text = "Load Flow")
        self.flowFrame.grid(row = row, sticky = "EW")
        row += 1

        self.flowLoaderFrame = ttk.Frame(self.flowFrame)
        self.flowLoaderFrame.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
        self.flowLoader = ldr.FlowLoaderWidget(self.flowLoaderFrame,
            self._onLoad)
        self.flowLoader.pack(side = tk.LEFT)
        self.activeWidgets.append(self.flowLoader)

        self.fileLabel = ttk.Label(self.flowLoaderFrame, text = "File: ", style = "Secondary.TLabel")
        self.fileLabel.pack(side = tk.LEFT)
        self.fileField = ttk.Entry(self.flowLoaderFrame, width = 20,
            state = tk.DISABLED)
        self.fileField.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.fileTypeLabel = ttk.Label(self.flowLoaderFrame, text = "Type: ", style = "Secondary.TLabel")
        self.fileTypeLabel.pack(side = tk.LEFT)

        self.fileTypes = {"List": self.FT_LIST, "t vs U" : self.FT_TV,
            "log-u" : self.FT_LGU, "log-g" : self.FT_LGG
            }
        self.typeMenuVar = tk.StringVar()
        self.typeMenuVar.trace('w', self._onTypeMenuChange)
        self.typeMenuVar.set(tuple(self.fileTypes.keys())[0])
        self.typeMenu = ttk.OptionMenu(self.flowLoaderFrame, self.typeMenuVar,
            self.typeMenuVar.get(), *list(self.fileTypes.keys()))
        self.typeMenu.config(width = 6)
        self.typeMenu.pack(side = tk.LEFT)
        self.activeWidgets.append(self.typeMenu)

        # TODO:
        # - start/stop
        # - display
        # - tstep
        self.timer = tmr.TimerWidget(self.flowFrame,
            startF = self._startFlow,
            stopF = self._stopFlow,
            stepF = self._stepF,
            endDCF = lambda dc:self._sendDirect(dc, False),
            logstartF = self.logstart,
            logstopF = self.logstop)
        self.timer.pack(side = tk.TOP, fill = tk.X, expand = True)
    # API ......................................................................


    # Internal methods .........................................................
    def _onSendDirect(self, *_):
        """
        Callback for direct send button.
        """
        try:
            self._sendDirect(float(self.directValueEntry.get()), True)
        except Exception as e:
            self.printx(e, "Exception when sending direct DC")

    def _sendDirect(self, dc, normalize = True):
        """
        Send a "direct input" command using the given send callback.
            - dc := duty cycle to send as float in [0, 100] if normalize is True
                or in [0, 1] if normalize is False.
            - normalize := bool, whether to divide dc by 100.
        """
        normalized = dc/100 if normalize else dc
        self.display.set(normalized)

    def _sendRandom(self, *_):
        """
        Send a randomly-generated magnitude command using the given send
        callback.
        """
        try:
            minDC, maxDC = \
                float(self.randomLow.get()), float(self.randomHigh.get())
            if maxDC < minDC:
                raise ValueError("Upper bound ({maxDC:d}) cannot be "\
                    " smaller than lower ({minDC:d})")
            def f(*_):
                return ((rd.random()*(maxDC - minDC) + minDC))/100
            self.display.map(f, 0, 0)

        except Exception as e:
            self.printx(e, "Exception while processing random DC")

    def _setSliderMax(self, *_):
        """
        Callback for the slider's "Max" button.
        """
        self._sendDirect(self.SLIDER_MAX)

    def _setSliderMin(self, *_):
        """
        Callback for the slider's "Min" button.
        """
        self._sendDirect(self.SLIDER_MIN)

    def _quickDCCallback(self, dc):
        """
        Build a callback to apply the given duty cycle.
        - dc: float, in [0.0, 1.0] to apply when called.
        """
        def callback(*_):
            self._sendDirect(dc, normalize = False)
        return callback

    def _startFlow(self):
        try:
            if self.loadedFlow is not None and self._parseFlow():
                # TODO prepare (disable widgets, etc)
                self._setActiveWidgets(tk.DISABLED)
                return True
            else:
                return False
        except Exception as e:
            self.printx(e, "Exception while starting loaded flow")
            return False

    def _stepF(self, t, k):
        """
        To be called on each step of the flow loader.
        """
        # Process step:
        if self.flowType == self.FT_LIST:
            self.display.set(self.values[min(k, self.n - 1)])
        elif self.flowType == self.FT_TV:
            dc = self._getInterpolatedDC(t)
            print(t, dc)
            self._sendDirect(dc, False)
        else:
            self.printe("Flow type unavailable")
        # Check for stop or continue condition:

    def _stopFlow(self):
        """
        Callback to stop the loaded flow.
        """
        self.values = None
        self.times = None
        self.tmax = 0
        self._setActiveWidgets(tk.NORMAL)

    def _onStartChase(self, *_):
        """
        Callback for CHASE start button.
        """
        try:
            targetRPM = float(self.chaseRPMEntry.get())
            if targetRPM <= 0:
                raise ValueError("Target RPM must be positive")
            
            # Determine fan selection based on radio button selection
            target_mode = self.chaseTargetVar.get()
            
            # Use feedback control mode only (standard mode removed)
            if target_mode == "all":
                self._startFeedbackChase(targetRPM, "all", "")
                self.chaseStatusLabel.config(text = "Status: Feedback CHASE Active - All Fans (Target: {} RPM)".format(int(targetRPM)))
                self.printw("Started feedback-controlled CHASE mode for all fans with target RPM: {}".format(targetRPM))
            else:
                # Selected fans with feedback control
                selection_string = self.chaseFanSelectionEntry.get().strip()
                if not selection_string:
                    raise ValueError("Selection string cannot be empty")
                
                # Validate selection string format (should be 1s and 0s)
                if not all(c in '01' for c in selection_string):
                    raise ValueError("Selection string must contain only 1s and 0s")
                
                self._startFeedbackChase(targetRPM, "selected", selection_string)
                selected_count = selection_string.count('1')
                self.chaseStatusLabel.config(text = "Status: Feedback CHASE Active - {} Selected Fans (Target: {} RPM)".format(selected_count, int(targetRPM)))
                self.printw("Started feedback-controlled CHASE mode for selected fans ({}) with target RPM: {}".format(selection_string, targetRPM))
            
            # Update button states
            self.chaseStartButton.config(state = tk.DISABLED)
            self.chaseStopButton.config(state = tk.NORMAL)
            
        except ValueError as e:
            self.printx(e, "Invalid input for CHASE mode")
        except Exception as e:
            self.printx(e, "Exception when starting CHASE mode")

    def _onStopChase(self, *_):
        """
        Callback for CHASE stop button.
        """
        try:
            # Stop feedback control if it's running
            if hasattr(self, 'feedback_active') and self.feedback_active:
                self._stopFeedbackChase()
            
            # Send stop command (set duty cycle to 0)
            self._sendDirect(0, normalize = False)
            self.chaseStatusLabel.config(text = "Status: Ready")
            self.chaseStartButton.config(state = tk.NORMAL)
            self.chaseStopButton.config(state = tk.DISABLED)
            
            # Hide PI tuning frame
            if hasattr(self, 'piTuningFrame'):
                self.piTuningFrame.pack_forget()
            
            self.printw("Stopped CHASE mode")
            
        except Exception as e:
            self.printx(e, "Exception when stopping CHASE mode")

    def _onPIAutoTune(self, *_):
        """
        Callback for PI Auto Tune button.
        """
        try:
            if not hasattr(self, 'target_rpm') or self.target_rpm is None:
                self.printw("请先启动反馈控制模式才能进行自动调节")
                return
            
            # Get optimal parameters
            kp, ki = self._getOptimalPIParameters(self.target_rpm)
            
            # Update the parameters
            self.kp = kp
            self.ki = ki
            
            # Update UI displays
            self.kpEntry.delete(0, tk.END)
            self.kpEntry.insert(0, f"{kp:.4f}")
            self.kiEntry.delete(0, tk.END)
            self.kiEntry.insert(0, f"{ki:.4f}")
            
            self.kpScale.set(kp * 1000)  # Scale for better slider resolution
            self.kiScale.set(ki * 1000)
            
            # Update current parameters display
            self.piCurrentLabel.config(text=f"当前参数: Kp={kp:.4f}, Ki={ki:.4f}")
            
            # Update performance status
            self.piStatusLabel.config(text="状态: 自动调节完成", fg="green")
            
            self.printw(f"自动调节完成: Kp={kp:.4f}, Ki={ki:.4f}")
            
        except Exception as e:
            self.printx(e, "自动调节PI参数时发生异常")
            if hasattr(self, 'piStatusLabel'):
                self.piStatusLabel.config(text="状态: 自动调节失败", fg="red")

    def _onPIReset(self, *_):
        """
        Callback for PI Reset to Default button.
        """
        try:
            # Reset to default values
            default_kp = 0.01
            default_ki = 0.001
            
            self.kp = default_kp
            self.ki = default_ki
            
            # Update UI displays
            self.kpEntry.delete(0, tk.END)
            self.kpEntry.insert(0, f"{default_kp:.4f}")
            self.kiEntry.delete(0, tk.END)
            self.kiEntry.insert(0, f"{default_ki:.4f}")
            
            self.kpScale.set(default_kp * 1000)
            self.kiScale.set(default_ki * 1000)
            
            # Update current parameters display
            self.piCurrentLabel.config(text=f"当前参数: Kp={default_kp:.4f}, Ki={default_ki:.4f}")
            
            # Update performance status
            self.piStatusLabel.config(text="状态: 已重置为默认值", fg="blue")
            
            self.printw(f"PI参数已重置为默认值: Kp={default_kp:.4f}, Ki={default_ki:.4f}")
            
        except Exception as e:
            self.printx(e, "重置PI参数时发生异常")
            if hasattr(self, 'piStatusLabel'):
                self.piStatusLabel.config(text="状态: 重置失败", fg="red")

    def _onPIApply(self, *_):
        """
        Callback for PI Apply Parameters button.
        """
        try:
            # Get values from entry fields
            kp_str = self.kpEntry.get().strip()
            ki_str = self.kiEntry.get().strip()
            
            if not kp_str or not ki_str:
                raise ValueError("Kp和Ki参数不能为空")
            
            kp = float(kp_str)
            ki = float(ki_str)
            
            # Validate parameters
            kp, ki = self._validatePIParameters(kp, ki)
            
            # Apply the parameters locally
            self.kp = kp
            self.ki = ki
            
            # Update sliders to match
            self.kpScale.set(kp * 1000)
            self.kiScale.set(ki * 1000)
            
            # Update current parameters display
            self.piCurrentLabel.config(text=f"当前参数: Kp={kp:.4f}, Ki={ki:.4f}")
            
            # Send PISET command to backend
            try:
                # Send to all fans (fanID=0 for broadcast, or iterate through all fans)
                if hasattr(self.network, 'sendPISet'):
                    self.network.sendPISet(fanID=0, kp=kp, ki=ki)
                    self.piStatusLabel.config(text="状态: 参数已发送到后端", fg="green")
                    self.printw(f"PI参数已发送到后端: Kp={kp:.4f}, Ki={ki:.4f}")
                else:
                    self.piStatusLabel.config(text="状态: 参数已应用(本地)", fg="orange")
                    self.printw(f"PI参数已应用(仅本地): Kp={kp:.4f}, Ki={ki:.4f}")
                    self.printw("警告: 网络通信模块不支持sendPISet方法")
            except Exception as network_error:
                self.printx(network_error, "发送PI参数到后端失败")
                self.piStatusLabel.config(text="状态: 发送失败，仅本地应用", fg="orange")
            
        except ValueError as e:
            self.printx(e, "PI参数输入无效")
            if hasattr(self, 'piStatusLabel'):
                self.piStatusLabel.config(text="状态: 参数无效", fg="red")
        except Exception as e:
            self.printx(e, "应用PI参数时发生异常")
            if hasattr(self, 'piStatusLabel'):
                self.piStatusLabel.config(text="状态: 应用失败", fg="red")

    def _onKpScaleChange(self, value):
        """
        Callback for Kp slider change.
        """
        try:
            kp = float(value) / 1000.0  # Convert back from scaled value
            kp = max(0.001, min(0.1, kp))  # Clamp to valid range
            
            # Update entry field
            self.kpEntry.delete(0, tk.END)
            self.kpEntry.insert(0, f"{kp:.4f}")
            
            # Update current parameters display
            ki = float(self.kiEntry.get()) if self.kiEntry.get() else getattr(self, 'ki', 0.001)
            self.piCurrentLabel.config(text=f"当前参数: Kp={kp:.4f}, Ki={ki:.4f}")
            
        except Exception as e:
            pass  # Ignore errors during slider updates

    def _onKiScaleChange(self, value):
        """
        Callback for Ki slider change.
        """
        try:
            ki = float(value) / 1000.0  # Convert back from scaled value
            ki = max(0.0001, min(0.01, ki))  # Clamp to valid range
            
            # Update entry field
            self.kiEntry.delete(0, tk.END)
            self.kiEntry.insert(0, f"{ki:.4f}")
            
            # Update current parameters display
            kp = float(self.kpEntry.get()) if self.kpEntry.get() else getattr(self, 'kp', 0.01)
            self.piCurrentLabel.config(text=f"当前参数: Kp={kp:.4f}, Ki={ki:.4f}")
            
        except Exception as e:
            pass  # Ignore errors during slider updates

    def _showPITuning(self, *_):
        """
        Show PI tuning interface when feedback mode is active.
        """
        try:
            if hasattr(self, 'feedback_active') and self.feedback_active:
                # Show PI tuning frame
                self.piTuningFrame.pack(fill=tk.X, padx=5, pady=5)
                
                # Update current parameters display
                current_kp = getattr(self, 'kp', 0.01)
                current_ki = getattr(self, 'ki', 0.001)
                self.piCurrentLabel.config(text=f"当前参数: Kp={current_kp:.4f}, Ki={current_ki:.4f}")
                
                # Update entry fields and sliders
                self.kpEntry.delete(0, tk.END)
                self.kpEntry.insert(0, f"{current_kp:.4f}")
                self.kiEntry.delete(0, tk.END)
                self.kiEntry.insert(0, f"{current_ki:.4f}")
                
                self.kpScale.set(current_kp * 1000)
                self.kiScale.set(current_ki * 1000)
                
                self.piStatusLabel.config(text="状态: PI调节界面已激活", fg="green")
                
            else:
                self.printw("请先启动反馈控制模式才能显示PI调节界面")
                
        except Exception as e:
            self.printx(e, "显示PI调节界面时发生异常")

    def _onChaseTargetChange(self, *_):
        """
        Callback for CHASE target mode change (All/Selected).
        """
        target_mode = self.chaseTargetVar.get()
        if target_mode == "all":
            # Disable fan selection entry when "All Fans" is selected
            self.chaseFanSelectionEntry.config(state = tk.DISABLED)
        else:
            # Enable fan selection entry when "Selected" is selected
            self.chaseFanSelectionEntry.config(state = tk.NORMAL)

    def _startFeedbackChase(self, target_rpm, selection_mode="all", selection_string=""):
        """
        Start feedback-controlled CHASE mode that replicates Direct Input control logic.
        This method implements RPM feedback control similar to the PI control in Processor.cpp.
        
        Args:
            target_rpm (float): Target RPM for the fans
            selection_mode (str): "all" for all fans, "selected" for specific fans
            selection_string (str): Binary string for fan selection (e.g., "11001010")
        """
        try:
            # Initialize feedback control parameters
            self.feedback_active = True
            self.target_rpm = target_rpm
            self.selection_mode = selection_mode
            self.selection_string = selection_string
            
            # PI control parameters with auto-tuning capability
            self.kp, self.ki = self._getOptimalPIParameters(target_rpm)
            self.integral_error = 0.0
            self.min_dc = 0.1  # Minimum duty cycle (10%)
            self.max_dc = 1.0  # Maximum duty cycle (100%)
            
            # Performance tracking for auto-tuning
            self.error_history = []
            self.response_time_history = []
            self.overshoot_history = []
            self.last_tuning_time = tm.time()
            self.tuning_interval = 30.0  # Re-tune every 30 seconds if needed
            
            # Current duty cycle for each fan (initialize to 50%)
            self.current_dc = {}
            
            # Get fan mapping from display
            if hasattr(self.display, 'currentWidget'):
                current_widget = self.display.currentWidget()
                if hasattr(current_widget, 'mapper') and hasattr(current_widget.mapper, 'maxFans'):
                    max_fans = current_widget.mapper.maxFans
                    for i in range(max_fans):
                        self.current_dc[i] = 0.5  # Start at 50% duty cycle
            
            # Start feedback loop
            self._scheduleFeedbackUpdate()
            
            # Show PI tuning interface
            self._showPITuning()
            
            self.printw("Started feedback-controlled CHASE mode (Target: {} RPM, Kp: {:.4f}, Ki: {:.4f})".format(
                int(target_rpm), self.kp, self.ki))
            
        except Exception as e:
            self.printx(e, "Exception when starting feedback CHASE mode")
            self.feedback_active = False

    def _scheduleFeedbackUpdate(self):
        """
        Schedule the next feedback control update.
        """
        if self.feedback_active:
            # Schedule update every 100ms (similar to embedded control loop)
            self.master.after(100, self._updateFeedbackChase)

    def _getOptimalPIParameters(self, target_rpm):
        """
        Calculate optimal PI parameters based on target RPM and system characteristics.
        Uses Ziegler-Nichols tuning method adapted for fan control systems.
        
        Args:
            target_rpm (float): Target RPM for optimization
            
        Returns:
            tuple: (kp, ki) optimized parameters
        """
        # Base parameters for different RPM ranges
        if target_rpm < 1000:
            # Low RPM: More aggressive control needed
            base_kp = 0.02
            base_ki = 0.002
        elif target_rpm < 3000:
            # Medium RPM: Balanced control
            base_kp = 0.015
            base_ki = 0.0015
        else:
            # High RPM: Conservative control to avoid oscillation
            base_kp = 0.01
            base_ki = 0.001
        
        # Adaptive scaling based on system load
        load_factor = min(target_rpm / 5000.0, 1.0)  # Normalize to max expected RPM
        
        # Apply Cohen-Coon tuning rules for PI control
        kp = base_kp * (1.0 + 0.5 * load_factor)
        ki = base_ki * (1.0 + 0.3 * load_factor)
        
        # Safety limits to prevent instability
        kp = max(0.005, min(0.05, kp))  # Kp range: [0.005, 0.05]
        ki = max(0.0001, min(0.01, ki))  # Ki range: [0.0001, 0.01]
        
        return kp, ki

    def _autoTunePI(self, current_error, current_rpm):
        """
        Automatically tune PI parameters based on system performance.
        Uses real-time performance metrics to optimize control.
        
        Args:
            current_error (float): Current RPM error
            current_rpm (float): Current measured RPM
        """
        current_time = tm.time()
        
        # Only tune if enough time has passed
        if current_time - self.last_tuning_time < self.tuning_interval:
            return
        
        # Collect performance metrics
        self.error_history.append(abs(current_error))
        
        # Keep only recent history (last 20 samples)
        if len(self.error_history) > 20:
            self.error_history = self.error_history[-20:]
        
        # Calculate performance indicators
        avg_error = sum(self.error_history) / len(self.error_history)
        error_variance = sum((e - avg_error)**2 for e in self.error_history) / len(self.error_history)
        
        # Tuning logic based on performance
        if avg_error > self.target_rpm * 0.1:  # High steady-state error
            # Increase integral gain to reduce steady-state error
            self.ki = min(self.ki * 1.2, 0.01)
            self.printw(f"Auto-tune: Increased Ki to {self.ki:.4f} (high error)")
            
        elif error_variance > (self.target_rpm * 0.05)**2:  # High oscillation
            # Reduce gains to improve stability
            self.kp *= 0.9
            self.ki *= 0.9
            self.printw(f"Auto-tune: Reduced gains - Kp: {self.kp:.4f}, Ki: {self.ki:.4f} (oscillation)")
            
        elif avg_error < self.target_rpm * 0.02 and error_variance < (self.target_rpm * 0.02)**2:
            # Good performance, slightly increase responsiveness
            self.kp = min(self.kp * 1.05, 0.05)
            self.printw(f"Auto-tune: Increased Kp to {self.kp:.4f} (good performance)")
        
        # Apply safety limits
        self.kp = max(0.005, min(0.05, self.kp))
        self.ki = max(0.0001, min(0.01, self.ki))
        
        self.last_tuning_time = current_time

    def _validatePIParameters(self, kp, ki):
        """
        Validate and constrain PI parameters to safe operating ranges.
        
        Args:
            kp (float): Proportional gain
            ki (float): Integral gain
            
        Returns:
            tuple: (validated_kp, validated_ki)
        """
        # Define safe operating ranges based on backend documentation
        min_kp, max_kp = 0.1, 2.0
        min_ki, max_ki = 0.01, 0.5
        
        # Constrain parameters
        validated_kp = max(min_kp, min(max_kp, kp))
        validated_ki = max(min_ki, min(max_ki, ki))
        
        # Warn if parameters were constrained
        if validated_kp != kp:
            self.printw(f"Warning: Kp constrained from {kp:.4f} to {validated_kp:.4f}")
        if validated_ki != ki:
            self.printw(f"Warning: Ki constrained from {ki:.4f} to {validated_ki:.4f}")
        
        return validated_kp, validated_ki
    
    def _validatePIParameter(self, value, param_type):
        """
        Validate PI parameter input for Entry widgets.
        
        Args:
            value (str): Input value from Entry widget
            param_type (str): 'kp' or 'ki' to specify parameter type
            
        Returns:
            bool: True if valid, False otherwise
        """
        if value == "" or value == ".":
            return True  # Allow empty or partial decimal input
            
        try:
            float_val = float(value)
            if param_type == 'kp':
                return 0.1 <= float_val <= 2.0
            elif param_type == 'ki':
                return 0.01 <= float_val <= 0.5
            return False
        except ValueError:
            return False

    def _antiWindupProtection(self, integral_error, max_integral=None):
        """
        Implement anti-windup protection to prevent integral saturation.
        
        Args:
            integral_error (float): Current integral error
            max_integral (float): Maximum allowed integral value
            
        Returns:
            float: Protected integral error
        """
        if max_integral is None:
            # Calculate dynamic max_integral based on target RPM
            max_integral = self.target_rpm * 0.1  # 10% of target RPM
        
        # Clamp integral error to prevent windup
        protected_integral = max(-max_integral, min(max_integral, integral_error))
        
        # Log if windup protection activated
        if protected_integral != integral_error:
            self.printw(f"Anti-windup: Integral clamped from {integral_error:.2f} to {protected_integral:.2f}")
        
        return protected_integral

    def _deadZoneControl(self, rpm_error, dead_zone_percent=2.0):
        """
        Implement dead zone control to prevent unnecessary adjustments for small errors.
        
        Args:
            rpm_error (float): Current RPM error
            dead_zone_percent (float): Dead zone as percentage of target RPM
            
        Returns:
            float: Processed RPM error (0 if within dead zone)
        """
        dead_zone_threshold = self.target_rpm * (dead_zone_percent / 100.0)
        
        if abs(rpm_error) < dead_zone_threshold:
            return 0.0
        
        return rpm_error

    def _updateFeedbackChase(self):
        """
        Update feedback control loop - implements PI control similar to Processor.cpp.
        """
        if not self.feedback_active:
            return
            
        try:
            # Get current RPM feedback from the system
            current_widget = self.display.currentWidget()
            if not hasattr(current_widget, 'feedback') or current_widget.feedback is None:
                # No feedback available, schedule next update
                self._scheduleFeedbackUpdate()
                return
            
            # Process each fan based on selection mode
            if self.selection_mode == "all":
                # Control all fans
                self._updateAllFans(current_widget.feedback)
            else:
                # Control selected fans based on selection string
                self._updateSelectedFans(current_widget.feedback)
            
            # Apply the updated duty cycles using display.set() method
            self._applyFeedbackControl()
            
            # Schedule next update
            self._scheduleFeedbackUpdate()
            
        except Exception as e:
            self.printx(e, "Exception in feedback control update")
            self._stopFeedbackChase()

    def _updateAllFans(self, feedback):
        """
        Update duty cycle for all fans using enhanced PI control with optimization features.
        """
        for fan_id, current_rpm in enumerate(feedback):
            if current_rpm is not None and current_rpm > 0:
                # Calculate RPM error
                rpm_error = self.target_rpm - current_rpm
                
                # Apply dead zone control to prevent unnecessary adjustments
                processed_error = self._deadZoneControl(rpm_error)
                
                if processed_error != 0:  # Only update if outside dead zone
                    # Update integral error with anti-windup protection
                    self.integral_error += processed_error
                    self.integral_error = self._antiWindupProtection(self.integral_error)
                    
                    # PI control calculation
                    adjustment = self.kp * processed_error + self.ki * self.integral_error
                    
                    # Update duty cycle
                    if fan_id in self.current_dc:
                        new_dc = self.current_dc[fan_id] + adjustment
                        # Limit duty cycle within bounds
                        new_dc = max(self.min_dc, min(self.max_dc, new_dc))
                        self.current_dc[fan_id] = new_dc
                
                # Auto-tune PI parameters based on performance
                self._autoTunePI(rpm_error, current_rpm)

    def _updateSelectedFans(self, feedback):
        """
        Update duty cycle for selected fans based on selection string with enhanced PI control.
        """
        for fan_id, current_rpm in enumerate(feedback):
            # Check if this fan is selected
            if fan_id < len(self.selection_string) and self.selection_string[fan_id] == '1':
                if current_rpm is not None and current_rpm > 0:
                    # Calculate RPM error
                    rpm_error = self.target_rpm - current_rpm
                    
                    # Apply dead zone control
                    processed_error = self._deadZoneControl(rpm_error)
                    
                    if processed_error != 0:  # Only update if outside dead zone
                        # Update integral error (per fan) with anti-windup protection
                        if not hasattr(self, 'fan_integral_errors'):
                            self.fan_integral_errors = {}
                        if fan_id not in self.fan_integral_errors:
                            self.fan_integral_errors[fan_id] = 0.0
                        
                        self.fan_integral_errors[fan_id] += rpm_error
                        
                        # Apply anti-windup protection
                        self.fan_integral_errors[fan_id] = self._antiWindupProtection(self.fan_integral_errors[fan_id])
                    
                    # PI control calculation
                    adjustment = self.kp * processed_error + self.ki * self.fan_integral_errors[fan_id]
                    
                    # Update duty cycle
                    if fan_id in self.current_dc:
                        new_dc = self.current_dc[fan_id] + adjustment
                        # Limit duty cycle within bounds
                        new_dc = max(self.min_dc, min(self.max_dc, new_dc))
                        self.current_dc[fan_id] = new_dc
                        
                        # Store error for auto-tuning
                        if not hasattr(self, 'error_history'):
                            self.error_history = []
                        self.error_history.append(abs(processed_error))
                        
                        # Limit error history size
                        if len(self.error_history) > 100:
                            self.error_history = self.error_history[-50:]
                    
                    # Perform auto-tuning periodically
                    current_time = tm.time()
                    if (current_time - self.last_tuning_time) > self.tuning_interval:
                        self._autoTunePI()
                        self.last_tuning_time = current_time

    def _applyFeedbackControl(self):
        """
        Apply the calculated duty cycles using the display system.
        This replicates the Direct Input control logic.
        """
        try:
            current_widget = self.display.currentWidget()
            if hasattr(current_widget, 'map') and hasattr(current_widget, 'selected_g'):
                # Create a function that returns the appropriate duty cycle for each fan
                def rpm_feedback_func(r, c, l, s, f, d, p, R, C, L, S, F, P, t, k):
                    """
                    Feedback control function that returns duty cycle based on fan index.
                    This mimics the _const function but with dynamic values.
                    """
                    fan_index = s  # Use fan index from parameters
                    if fan_index in self.current_dc:
                        return self.current_dc[fan_index]
                    return 0.5  # Default 50% if not found
                
                # Apply the feedback function using the map method
                # This replicates how Direct Input uses display.set() -> GridWidget.map()
                current_widget.map(rpm_feedback_func, 0, 0)
                
        except Exception as e:
            self.printx(e, "Exception when applying feedback control")

    def _stopFeedbackChase(self):
        """
        Stop the feedback-controlled CHASE mode.
        """
        try:
            self.feedback_active = False
            
            # Reset all fans to 0% duty cycle (stop)
            self._sendDirect(0, normalize=False)
            
            # Clear feedback control state
            if hasattr(self, 'current_dc'):
                self.current_dc.clear()
            if hasattr(self, 'fan_integral_errors'):
                self.fan_integral_errors.clear()
            
            self.printw("Stopped feedback-controlled CHASE mode")
            
        except Exception as e:
            self.printx(e, "Exception when stopping feedback CHASE mode")

    def _onTypeMenuChange(self, *_):
        self.flowType = self.fileTypes[self.typeMenuVar.get()]

    def _setActiveWidgets(self, state):
        """
        Set all interactive widgets to the given state (either tk.DISABLED or
        tk.NORMAL)
        """
        for widget in self.activeWidgets:
            widget.config(state = state)

    def _onLoad(self, loaded):
        """
        Load callback for FlowLoader.
        """
        if loaded is not None:
            data, filename = loaded
            self.loadedFlow = data
            self.fileField.config(state = tk.NORMAL)
            self.fileField.delete(0, tk.END)
            self.fileField.insert(0, filename.split("/")[-1].split("\\")[-1])
            self.fileField.config(state = tk.DISABLED)

    def _parseFlow(self):
        """
        Extract data from the loaded flow for execution and return whether such
        extraction was successful or not (as bool).
        """

        try:
            if self.flowType == self.FT_LIST:
                values_raw = eval("[" + self.loadedFlow  +"]")
                self.n = len(values_raw)

            elif self.flowType == self.FT_TV:
                lines = self.loadedFlow.split("\n")
                self.n = len(lines)
                self.times, values_raw = [0]*self.n, [0]*self.n
                for i, line in enumerate(lines):
                    if len(line) > 0:
                        time, value = line.split(",")
                        self.times[i], values_raw[i] = float(time),float(value)
                self.tmax = max(self.times)
            else:
                raise RuntimeError("Loaded flow type not available") # TODO

            # Normalize and store extracted values:
            normalize = False
            for value in values_raw:
                if value > 1.0:
                    normalize = True
                    break
            if normalize:
                values_max = max(values_raw)
                self.values = list(map(lambda v: v/values_max, values_raw))
            else:
                self.values = values_raw

            # Debug: print(self.times)  # Uncomment for debugging flow timing
            return True

        except Exception as e:
            self.printx(e, "Exception while parsing flow")
            return False

    def _getInterpolatedDC(self, t):
        """
        Interpolate a duty cycle from the loaded flow's values and times
        list, using the current timestamp.
        """
        # Handle out-of-range cases:
        if t <= self.times[0]:
            return self.values[0]
        elif t >= self.tmax:
            return self.values[-1]

        # Find nearest timestamp:
        # Find nearest time:
        i, ti = 0, self.times[0]
        while t > ti and i < self.n:
            i += 1
            ti = self.times[i]
        t0 = self.times[i - 1]
        v0, vi = self.values[i-1], self.values[i]

        # Interpolate a weighted average of the two values:
        p = (ti - t)/(ti - t0)
        dc =  (v0*p + vi*(1 - p))
        return dc

    def _setupKeyboardBindings(self):
        """
        Setup keyboard bindings for enhanced user experience.
        """
        # Bind common keyboard shortcuts
        self.master.bind('<Control-s>', self._onSendDirect)  # Ctrl+S to send direct
        self.master.bind('<Control-r>', self._sendRandom)    # Ctrl+R to send random
        self.master.bind('<Control-q>', self._onStopChase)   # Ctrl+Q to stop chase
        self.master.bind('<space>', self._onStartChase)      # Space to start chase
        self.master.bind('<Escape>', self._onStopChase)      # Escape to stop chase
        
        # Bind number keys for quick duty cycle settings
        for i in range(10):
            self.master.bind(str(i), lambda e, dc=i*10: self._quickDCCallback(dc))
        
        # Focus management
        self.master.focus_set()

    def _validateNumeric(self, value):
        """
        Validate numeric input for duty cycle and range values.
        Allows empty string, integers, and floats within valid range (0-100).
        """
        if value == "":
            return True  # Allow empty string
        
        try:
            num = float(value)
            # Allow values between 0 and 100 (inclusive)
            return 0 <= num <= 100
        except ValueError:
            return False  # Invalid numeric format

    @staticmethod
    def _nothing(*_):
        """
        Placeholder function to serve as a default callback.
        """
        pass

class FunctionControlWidget(ttk.Frame, pt.PrintClient):
    """
    Container for the dynamic flow control tools.
    """
    SYMBOL = "[DC]"
    DEFAULT_STEP_MS = 1000
    DEFAULT_END = ""

    def __init__(self, master, display, logstart, logstop, pqueue):
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.display = display
        self.logstart, self.logstop = logstart, logstop

        self.grid_columnconfigure(0, weight = 1)
        row = 0

        self.activeWidgets = []

        # Python interpreter ...................................................
        self.grid_rowconfigure(row, weight = 1)
        self.pythonFrame = ttk.LabelFrame(self, text = "Python")
        self.pythonFrame.grid(row = row, sticky = "NEWS")
        row += 1
        self.python = PythonInputWidget(self.pythonFrame, self._applyFunction,
            pqueue)
        self.flat = self.python.flat
        self.python.pack(fill = tk.BOTH, expand = True)

        # Timing ...............................................................
        self.timeFrame = ttk.LabelFrame(self, text = "Time Series")
        self.timeFrame.grid(row = row, sticky = "EW")
        row += 1

        self.timer = tmr.TimerWidget(self.timeFrame,
            startF = self._start,
            stopF = self._stop,
            stepF = self._step,
            endDCF = self.display.set,
            logstartF = self.logstart,
            logstopF = self.logstop)
        self.timer.pack(fill = tk.X, expand = True)

        # Wrap-up:
        self.f = None
        self.widget = None

    def _applyFunction(self, f, t, k):
        """
        To be called by the Python input widget to apply its function once.
        """
        self._stop()
        if f is not None:
            self.f = f
            self.display.map(f, t, k)

    def _start(self, *_):
        self.f = self.python.get()
        if self.f is not None:
            self.widget = self.display.currentWidget()
            self.python.disable()
            for widget in self.activeWidgets:
                widget.config(state = tk.DISABLED)
            return True
        else:
            return False

    def _stop(self, *_):
        self.widget = None
        self.python.enable()
        self.f = None
        for widget in self.activeWidgets:
            widget.config(state = tk.NORMAL)


    def _step(self, t, k):
        """
        Complete one timestep
        """
        self.widget.map(self.f, t, k)


class BuiltinFlow:
    """
    Data structure for pre-built flows.
    """

    PTYPE_GRID, PTYPE_TABLE = range(2)
    ATTR_INT, ATTR_INT_NONNEG, ATTR_INT_POS, ATTR_FLOAT_NONNEG, ATTR_FLOAT_POS,\
    ATTR_BOOL = range(6)


    def __init__(self, name, description, source, ptype, attributes):
        """
        Build a new data structure to contain the data for a built-in flow.

        - name: str, name to display to the user to refer to this flow.
        - description: str, description to display to the user about this flow.
        - source: str, python code to be plugged into the FC Python interpreter.
        - ptype: int, predefined constant (as a class attribute) that indicates
            the kind of parameters the flow's function takes (either those in
            the Grid or in the LiveTable).
        - attributes: dict, mapping from attribute names (str) to their format
            as a corresponding constant as defined in this class' attributes.
        """
        self.name, self.description = name, description
        self.source, self.ptype, self.attributes = source, ptype, attributes

class FlowLibraryWidget(ttk.Frame, pt.PrintClient):
    """
    Container for built-in flows.
    """

    def __init__(self, master, flows, display, pqueue):
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)
        # Setup:
        self.flows = flows
        self.display = display

        self.interactive = []

        LIST_ROW, LIST_COLUMN = 0, 0
        HSCROLL_ROW, HSCROLL_COLUMN = LIST_ROW + 1, LIST_COLUMN
        VSCROLL_ROW, VSCROLL_COLUMN = LIST_ROW, LIST_COLUMN + 1
        DESC_ROW, DESC_COLUMN = HSCROLL_ROW + 1, LIST_COLUMN
        ATTR_ROW, ATTR_COLUMN = DESC_ROW + 1, DESC_COLUMN
        ASCROLL_ROW, ASCROLL_COLUMN = ATTR_ROW, ATTR_COLUMN + 1
        CTRL_ROW, CTRL_COLUMN = ATTR_ROW + 1, ATTR_COLUMN

        self.grid_columnconfigure(LIST_COLUMN, weight = 1)
        self.grid_rowconfigure(ATTR_ROW, weight = 1)

        # TODO
        # Flow list ............................................................
        self.list = ttk.Treeview(self, height = 5)
        self.list.grid(row = LIST_ROW, column = LIST_COLUMN,
            sticky = "NEW")
        # Add columns:
        self.columns = ("Built-in Flows",)
        self.list['columns'] = self.columns
        self.list.column("#0", width = 20, stretch = False)
        for column in self.columns:
            self.list.column(column, anchor = "center")
            self.list.heading(column, text = column)
        # Build scrollbars:
        # See: https://lucasg.github.io/2015/07/21/
        #    How-to-make-a-proper-double-scrollbar-frame-in-Tkinter/
        self.hscrollbar = ttk.Scrollbar(self, orient = tk.HORIZONTAL)
        self.hscrollbar.config(command = self.list.xview)
        self.hscrollbar.grid(row = HSCROLL_ROW,
            column = HSCROLL_COLUMN, sticky = "EW")
        self.vscrollbar = ttk.Scrollbar(self, orient = tk.VERTICAL)
        self.vscrollbar.config(command = self.list.yview)
        self.vscrollbar.grid(row = VSCROLL_ROW,
            column = VSCROLL_COLUMN, sticky = "NS")

        # Build description display
        self.descriptionFrame = ttk.LabelFrame(self, text = "About")
        self.descriptionFrame.grid(row = DESC_ROW, column = DESC_COLUMN,
            sticky = "NEWS", columnspan = 2)
        self.descriptionFrame.grid_columnconfigure(0, weight = 1)

        self.nameDisplay = ttk.Label(self.descriptionFrame, anchor = tk.W, style = "TitleLabel.TLabel")
        self.nameDisplay.grid(row = 0, column = 0, sticky = "EW", pady=(0, 6))

        self.descriptionDisplay = tk.Text(self.descriptionFrame,
            width = 30, height = 2, padx = 10, pady = 0,
            **gus.text_conf,
            state = tk.DISABLED)
        self.descriptionDisplay.grid(row = 1, column = 0, sticky = "NEWS")

        self.dscrollbar = ttk.Scrollbar(self.descriptionFrame,
            orient = tk.VERTICAL)
        self.dscrollbar.config(command = self.descriptionDisplay.yview)
        self.dscrollbar.grid(row = 1, column = 1, sticky = "NS")

        # Build attribute menu NOTE: add scrollbar
        self.attributeFrame = ttk.LabelFrame(self, text = "Configure Flow")
        self.attributeFrame.grid(row = ATTR_ROW, column = ATTR_COLUMN,
            sticky = "NEWS")

        self.attributeDisplay = ttk.Frame(self.attributeFrame)
        self.attributeDisplay.pack(fill = tk.BOTH, expand = True)

        self.ascrollbar = ttk.Scrollbar(self, orient = tk.VERTICAL)
        #self.ascrollbar.config(command = self.attributeDisplay.yview) FIXME
        self.ascrollbar.grid(row = ASCROLL_ROW, column = ASCROLL_COLUMN,
            sticky = "NS")


        # Build control
        self._apply = lambda: None # FIXME
        self.controlFrame = ttk.LabelFrame(self, text = "Control")
        self.controlFrame.grid(row = CTRL_ROW, column = CTRL_COLUMN,
            sticky = "NEWS", columnspan = 2)
        self.applyButton = ttk.Button(self.controlFrame, text = "Apply",
            command = self._apply)
        self.applyButton.pack(side = tk.TOP, fill = tk.X, expand = True)

        # Temporary placeholder for future functionality
        self._startFlow = lambda: None
        self._stopFlow = lambda: None
        self._stepF = lambda: None
        self._sendDirect = lambda: None
        self.logstart = lambda: None
        self.logstop = lambda: None

        self.timer = tmr.TimerWidget(self.controlFrame,
            startF = self._startFlow,
            stopF = self._stopFlow,
            stepF = self._stepF,
            endDCF = lambda dc:self._sendDirect(dc, False),
            logstartF = self.logstart,
            logstopF = self.logstop)
        self.timer.pack(side = tk.TOP, fill = tk.X, expand = True)

        # Add flows
        for category, name in flows:
            self.add(flow, category)

    # API ......................................................................
    def add(self, flow: BuiltinFlow, category: str):
        """
        Add a flow to the library.
        """
        # TODO
        pass

    def config(self, state):
        """
        Set the state of all interactive widgets.
        - state := Tkinter constant, one of tk.NORMAL and tk.DISABLED.
        """
        for widget in self.interactive:
            widget.config(state = state)
    # FIXME

class ControlPanelWidget(ttk.Frame, pt.PrintClient):
    """
    Container for the control GUI tools and peripherals.
    """
    SYMBOL = "[CP]"

    """ Codes for display modes. """
    DM_LIVE = 690
    DM_BUILDER = 691

    def __init__(self, master, mapper, archive, network, external, display,
        setLive, pqueue):
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ................................................................
        self.mapper = mapper
        self.archive = archive
        self.network = network
        self.externalBackEnd = external
        self.display = display
        self.setLive = setLive
        self.grid_columnconfigure(0, weight = 1)
        row = 0

        self.F = fnt.Font(font = gus.typography["label_small"]["font"])
        self.S = ttk.Style()
        try:
            if self.winfo_exists() and hasattr(self, 'S') and self.S:
                self.S.configure('.', font = self.F)
        except (tk.TclError, AttributeError) as e:
            print(f"Error configuring ttk style (application may be closing): {e}")
        except Exception as e:
            print(f"Error configuring ttk style: {e}")
        self.activeWidgets = []
        self.filename = None
        self.fullname = None
        self.inWindows = self.archive[ac.platform] == us.WINDOWS

        # Callbacks and validations implementation
        self._setupCallbacks()
        self._setupValidations()

        # Mode and layer .......................................................
        self.topFrame = ttk.Frame(self)
        self.topFrame.grid(row = row, sticky = "EW")
        row += 1

        self.viewFrame = ttk.LabelFrame(self.topFrame, text = "View")
        self.viewFrame.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)

        self.viewVar = tk.IntVar()
        self.viewVar.trace('w', self._onModeChange)
        self.liveButton = ttk.Radiobutton(self.viewFrame,
            variable = self.viewVar, value = self.DM_LIVE, text = "Live")
        self.liveButton.pack(side = tk.TOP, padx = 5, fill = tk.X,
            expand = True)
        self.builderButton = ttk.Radiobutton(self.viewFrame,
            variable = self.viewVar, value = self.DM_BUILDER,
            text = "Preview")
        self.builderButton.pack(side = tk.TOP, padx = 5, fill = tk.X,
            expand = True)

        # Selection ............................................................
        self.selectFrame = ttk.LabelFrame(self.topFrame, text = "Select")
        self.selectFrame.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)

        self.selectAllButton = ttk.Button(self.selectFrame, text = "Select All",
            command = self.selectAll)
        self.selectAllButton.pack(side = tk.TOP, padx = 5, fill = tk.X,
            expand = True)
        self.deselectAllButton = ttk.Button(self.selectFrame,
            text = "Deselect All", command = self.deselectAll, style = "Secondary.TButton")
        self.deselectAllButton.pack(side = tk.TOP, padx = 5, fill = tk.X,
            expand = True)

        self.bind('<Control-a>', self.selectAll)
        self.bind('<Control-A>', self.selectAll)
        self.bind('<Control-d>', self.deselectAll)
        self.bind('<Control-D>', self.deselectAll)

        # Flow control .........................................................
        self.grid_rowconfigure(row, weight = 1) # FIXME
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row = row, sticky = "NEWS")
        row += 1

        # Basic ................................................................
        self.basic = MainControlWidget(self.notebook, network, display,
            self._onRecordStart, self._onRecordStop, pqueue)
        self.notebook.add(self.basic, text = "Manual")

        # Flow Library .........................................................
        self.library = FlowLibraryWidget(self.notebook, {}, self.display,pqueue)
            # TODO
        self.notebook.add(self.library, text = "Library",state = tk.NORMAL)

        # Functional ...........................................................
        self.functional = FunctionControlWidget(self.notebook, display,
            self._onRecordStart, self._onRecordStop, pqueue)
        self.notebook.add(self.functional, text = "Scripting",
            state = tk.NORMAL)

        # External .............................................................
        self.external = ex.ExternalControlWidget(self.notebook,
            self.archive, self.externalBackEnd, pqueue) # FIXME pass backend
        self.notebook.add(self.external, text = "External",
            state = tk.NORMAL)

        # Record ...............................................................
        # Add spacer:
        self.grid_rowconfigure(row, weight = 0) # FIXME
        row += 1

        self.recordFrame = ttk.LabelFrame(self, text = "Record Data")
        self.recordFrame.grid(row = row, sticky = "EW")
        row += 1

        self.fileFrame = ttk.Frame(self.recordFrame)
        self.fileFrame.pack(side = tk.TOP, fill = tk.X, expand = True)

        self.fileLabel = ttk.Label(self.fileFrame, text = "File: ", style = "Secondary.TLabel")
        self.fileLabel.pack(side = tk.LEFT)
        self.fileField = ttk.Entry(self.fileFrame, width = 20,
            state = tk.DISABLED)
        self.fileField.pack(side = tk.LEFT, fill = tk.X, expand = True)
        self.fileButton = ttk.Button(self.fileFrame, text = "...",
            command = self._onFileButton, style = "Secondary.TButton")
        self.fileButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.fileButton)

        self.dataLogger = DataLogger(self.archive, self.pqueue)
        self.logDirectory = os.getcwd() # Get current working directory

        self.recordControlFrame = ttk.Frame(self.recordFrame)
        self.recordControlFrame.pack(side = tk.TOP, fill = tk.X, expand = True,
            **gus.padc)
        self.recordStartButton = ttk.Button(self.recordControlFrame,
            text = "Start",
            command = self._onRecordStart)
        self.recordStartButton.pack(side = tk.LEFT)
        self.recordPauseButton = ttk.Button(self.recordControlFrame,
            text = "Pause", state = tk.DISABLED,
            command = self._onRecordPause, style = "Secondary.TButton")
        self.recordPauseButton.pack(side = tk.LEFT, padx = 10)

        self.recordIndexVar = tk.BooleanVar()
        self.recordIndexVar.set(False)
        self.recordIndexButton = ttk.Checkbutton(self.recordControlFrame,
            text = "Auto Index", variable = self.recordIndexVar)
        self.recordIndexButton.pack(side = tk.LEFT, **gus.padc)
        self.activeWidgets.append(self.recordIndexButton)

        self.nextIndexLabel = ttk.Label(self.recordControlFrame,
            text = "  Next: ", style = "Secondary.TLabel")
        self.nextIndexLabel.pack(side = tk.LEFT)
        validateN = self.register(gus._validateN)
        self.nextIndexEntry = ttk.Entry(self.recordControlFrame,
            width = 6, validate = 'key',
            validatecommand = (validateN, '%S', '%s', '%d'))
        self.nextIndexEntry.pack(side = tk.LEFT, **gus.padc)
        self.nextIndexEntry.insert(0, "1")
        self.activeWidgets.append(self.nextIndexEntry)

        # Wrap-up ..............................................................
        self.viewVar.set(self.DM_LIVE)

    # API ......................................................................
    def feedbackIn(self, F):
        """
        Process a feedback vector F
        """
        self.dataLogger.feedbackIn(F, tm.time())

    def slavesIn(self, S):
        """
        Process a slave vector S.
        """
        self.dataLogger.slavesIn(S)

    def selectAll(self, event = None):
        self.display.selectAll()

    def deselectAll(self, event = None):
        self.display.deselectAll()

    # TODO: Set layers?

    # Internal methods .........................................................
    def _onModeChange(self, *A):
        """
        To be called when the view mode is changed (between live mode and flow
        builder.)
        """
        if self.viewVar.get() == self.DM_LIVE:
            self.setLive(True)
        elif self.viewVar.get() == self.DM_BUILDER:
            self.setLive(False)

    def _getDefaultFile(self):
        """
        Return the (relative) filename to be used by default.
        """
        return "FC_recording_on_{}.csv".format(tm.strftime(
            "%a_%d_%b_%Y_%H:%M:%S", tm.localtime()))

    def _onFileButton(self, *_):
        """
        To be called when the "..." button to set a filename for the data logger
        is pressed. Will request a filename from the user and, if one is given,
        write it in the corresponding input field.
        """
        # Get filename:
        fetched = self._getFile()

        # Check if this is a valid, new filename:
        if fetched is not None and len(fetched) > 0 and \
            fetched != self.fullname:
            self._setFile(filename = fetched, absolute = True)

    def _getFile(self):
        """
        Ask the user to select a filename for the data logger and return the
        result. If the user cancels the operation, None is returned.
        """
        return fdg.asksaveasfilename(initialdir = self.logDirectory,
            title = "Set Log File",
                initialfile = self.filename if self.filename is not None else \
                    self._getDefaultFile(),
                filetypes = (("CSV", ".csv"),("Plain Text", ".txt")))

    def _setFile(self, filename, absolute = False):
        """
        Set the filename to use for data logs.
            - filename := str, name to use
            - absolute := bool, whether to split the given filename (by / or \
                delimiters).
        """
        # Get the working directory of the file and the filename by itself
        if absolute:
            splitted = filename.split('/' if not self.inWindows else '\\')
            self.logDirectory = ("{}/"*(len(splitted)-1)).format(*splitted[:-1])
            self.filename = splitted[-1]
            self.fullname = filename
        else:
            self.logDirectory = "./" if not self.inWindows else ".\\"
            self.filename = filename
            self.fullname = self.logDirectory + self.filename

        # Place filename in text field:
        self.fileField.config(state = tk.NORMAL)
        self.fileField.delete(0, tk.END)
        self.fileField.insert(0, self.filename)
        self.fileField.config(state = tk.DISABLED)

        # Reset index:
        self.nextIndexEntry.delete(0, tk.END)
        self.nextIndexEntry.insert(0, "1")

    def _setLive(self, *_):
        """
        Set the state of this and sub-modules to "live feedback." Does nothing
        when already in said state.
        """
        if self.viewVar.get() != self.DM_LIVE:
            self.viewVar.set(self.DM_BUILDER)

    def _setBuilder(self, *_):
        """
        Set the state of this and sub-modules to "flow builder." Does nothing
        when already in said state.
        """
        if self.viewVar.get() != self.DM_BUILDER:
            self.viewVar.set(self.DM_LIVE)

    def _onRecordStart(self, event = None):
        """
        Callback for data logger start.
        """
        # TODO
        if self.fullname is None:
            self._setFile(self._getDefaultFile())

        self.fileField.config(state = tk.DISABLED)
        self.recordStartButton.config(text = "Stop",
            command = self._onRecordStop)  # Record stop functionality
        filename = self.fullname

        if self.recordIndexVar.get():
            try:
                index = int(self.nextIndexEntry.get())
            except ValueError:
                pass
            else:
                self.nextIndexEntry.delete(0, tk.END)
                self.nextIndexEntry.insert(0, "{}".format(index + 1))
                name, ext = filename.split(".")[:-1], filename.split(".")[-1]
                filename =  ("{}"*len(name) + "_{}.").format(*name, index) + ext

        self._setActiveWidgets(tk.DISABLED)
        self.dataLogger.start(filename,script = self._getScript(),
            mappings = [str(mapping) for mapping in self.display.getMappings()])

    def _getScript(self):
        """
        Get the "flat" (replace newline by semicolon) Python function
        in the dynamic Python input widget.
        """
        return self.functional.flat()

    def _onRecordStop(self, event = None):
        self.dataLogger.stop()
        self.recordStartButton.config(text = "Start",
            command = self._onRecordStart)  # Record start functionality
        self._setActiveWidgets(tk.NORMAL)

    def _onRecordPause(self, event = None):
        """
        Callback for data logger pause.
        """
        # TODO
        pass

    def _setupCallbacks(self):
        """
        Setup callbacks for control panel widgets.
        """
        # File selection callbacks
        if hasattr(self, 'fileButton'):
            self.fileButton.config(command=self._onFileButton)
        
        # Mode change callbacks
        if hasattr(self, 'modeVar'):
            self.modeVar.trace('w', self._onModeChange)
        
        # Recording control callbacks
        if hasattr(self, 'recordStartButton'):
            self.recordStartButton.config(command=self._onRecordStart)
        if hasattr(self, 'recordStopButton'):
            self.recordStopButton.config(command=self._onRecordStop)
        if hasattr(self, 'recordPauseButton'):
            self.recordPauseButton.config(command=self._onRecordPause)

    def _setupValidations(self):
        """
        Setup input validations for control panel widgets.
        """
        # Register validation function
        vcmd = (self.register(self._validateInput), '%P')
        
        # Apply validation to relevant entry widgets
        for widget_name in ['timeEntry', 'stepEntry', 'valueEntry']:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                if hasattr(widget, 'config'):
                    widget.config(validate='key', validatecommand=vcmd)

    def _validateInput(self, value):
        """
        Validate input for control panel entry widgets.
        
        Args:
            value (str): The input value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if value == "":
            return True
        
        try:
            # Allow positive numbers (int or float)
            float_val = float(value)
            return float_val >= 0
        except ValueError:
            return False

    def _setActiveWidgets(self, state):
        """
        Set all widgets that should be active when not recording and inactive
        when recording to the given state (either tk.NORMAL or tk.DISABLED).
        """
        for widget in self.activeWidgets:
            widget.config(state = state)

class DisplayMaster(ttk.Frame, pt.PrintClient):
    """
    Wrapper around interactive control widgets such as the grid or the live
    table. Allows the user to switch between them and abstracts their specifics
    away from the rest of the control front-end.
    """
    SYMBOL = "[DM]"
    MENU_ROW, MENU_COLUMN = 0, 0
    CONTENT_ROW, CONTENT_COLUMN = 1, 0
    GRID_KWARGS = {'row':CONTENT_ROW, 'column':CONTENT_COLUMN, 'sticky':"NEWS"}

    def __init__(self, master, pqueue):
        """
        Create a new DisplayMaster.

        - feedbackIn(F) : takes a standard feedback vector
        - networkIn(N) : takes a standard network state vector
        - slavesIn(S) : takes a standard slave state vector

        - activate(A) : 'turn on' display using the optional activation vector A
        - deactivate() : 'turn off' display

        - selectAll()
        - deselectAll()
        - map(f, t) : takes a function that accepts the standardized parameters
                    of the PythonInputWidget and returns a normalized duty cycle
                    (in [0, 1])
        - set(dc) : takes a normalized duty cycle ([0, 1])
        - apply()
        - getC() : return a standard control vector
        - limit(dc) : takes a normalized duty cycle ([0, 1])
        - redraw()

        - blockAdjust()
        - unblockAdjust()

        - getMapping()

        See fc.standards.
        """
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)
        self.displays = {}
        self.selected = tk.IntVar()
        self.selected.trace('w', self._update)
        self.current = None
        self.parameterCallbacks = []

        self.grid_rowconfigure(self.CONTENT_ROW, weight = 1)
        self.grid_columnconfigure(self.CONTENT_COLUMN, weight = 1)

        self.menuFrame = ttk.Frame(self)
        self.menuFrame.grid(row = self.MENU_ROW, column = self.MENU_COLUMN,
            sticky = "EW")

        self.digits = 10
        self.counterFormat = "{" + ":0{}d".format(self.digits) + "}"
        self.counterVar = tk.StringVar()
        self.counterVar.set("0"*self.digits)
        self.deltaVar = tk.StringVar()
        self.counterVar.set("00.000")
        self.counterDisplay = ttk.Label(self.menuFrame, style = "Secondary.TLabel",
            textvariable = self.counterVar, width = 10)
        self.counterDisplay.pack(side = tk.LEFT)
        self.deltaDisplay = ttk.Label(self.menuFrame, style = "Secondary.TLabel",
            textvariable = self.deltaVar, width = 5)
        self.deltaDisplay.pack(side = tk.LEFT, padx = 10)
        self.last_time = tm.time()
        self.count = 0

        self.selectorFrame = ttk.Frame(self.menuFrame)
        self.selectorFrame.pack(side = tk.RIGHT, fill= tk.Y)

    # API ----------------------------------------------------------------------

    def add(self, display, text, **pack_kwargs):
        """
        Add DISPLAY to this DisplayMaster. Behaves just like ttk.Notebook.add.
        """
        index = len(self.displays)
        self.displays[index] = display

        button = ttk.Radiobutton(self.selectorFrame, variable = self.selected,
            value = index, text = text)
        button.pack(side = tk.LEFT, **gus.padc)

        if self.current is None:
            display.grid(**self.GRID_KWARGS)
            self.current = index

    def currentWidget(self):
        """
        Get the currently active display widget.
        """
        return self.displays[self.current]

    # Wrapper methods ----------------------------------------------------------
    def feedbackIn(self, F):
        self.count += 1
        self.counterVar.set(self.counterFormat.format(self.count))
        this_time = tm.time()
        self.deltaVar.set("{:02.3f}s".format(this_time - self.last_time))
        self.last_time = this_time
        self.displays[self.current].feedbackIn(F)

    def networkIn(self, N):
        self.displays[self.current].networkIn(N)

    def slavesIn(self, S):
        self.displays[self.current].slavesIn(S)

    def activate(self, A = None):
        for display in self.displays.values():
            display.activate(A)

    def deactivate(self):
        for display in self.displays.values():
            display.deactivate()

    def selectAll(self):
        self.displays[self.current].selectAll()

    def deselectAll(self):
        self.displays[self.current].deselectAll()

    def map(self, f, t, k):
        self.displays[self.current].map(f, t, k)

    def set(self, dc):
        self.displays[self.current].set(dc)

    def apply(self):
        self.displays[self.current].apply()

    def getC(self):
        return self.displays[self.current].getC()

    def limit(self, dc):
        self.displays[self.current].limit(dc)

    def blockAdjust(self):
        self.displays[self.current].blockAdjust()

    def unblockAdjust(self):
        self.displays[self.current].unblockAdjust()

    def redraw(self):
        self.displays[self.current].redraw()

    def getMappings(self):
        mappings = []
        for display in self.displays.values():
            mapping = display.getMapping()
            if mapping is not None:
                mappings.append(mapping)
        return mappings

    # Internal methods ---------------------------------------------------------
    def _update(self, *event):
        new = self.selected.get()
        if new != self.current:
            self.displays[self.current].grid_forget()
            self.displays[new].grid(**self.GRID_KWARGS)
            self.current = new

class GridWidget(gd.BaseGrid, pt.PrintClient):
    """
    Front end for the 2D interactive Grid.
    """
    # TODO: keep backup for live feedback
    SYMBOL = "[GD]"
    RESIZE_MS = 400

    SM_SELECT = 55
    SM_DRAW = 65

    DEFAULT_COLORS = cms.COLORMAP_GALCIT_REVERSED
    DEFAULT_OFF_COLOR = "#303030"
    DEFAULT_EMPTY_COLOR = 'darkgray'
    DEFAULT_HIGH = 100
    DEFAULT_LOW = 0
    CURSOR = "hand1"

    OUTLINE_NORMAL = "black"
    OUTLINE_SELECTED = "orange"
    WIDTH_NORMAL = 1
    WIDTH_SELECTED = 3

    def __init__(self, master, archive, mapper, send, pqueue,
        colors = DEFAULT_COLORS, off_color = DEFAULT_OFF_COLOR,
        high = DEFAULT_HIGH, empty_color = DEFAULT_EMPTY_COLOR):

        # Setup ................................................................
        self.archive = archive
        self.mapper = mapper
        self.send_method = send

        self.fanArray = self.archive[ac.fanArray]
        self.L = self.fanArray[ac.FA_layers]
        self.R, self.C = self.fanArray[ac.FA_rows], self.fanArray[ac.FA_columns]
        self.RC = self.R*self.C
        self.RCL = self.RC*self.L
        self.size_g = self.RC*self.L
        self.range_g = range(self.size_g)
        self.maxRPM = self.archive[ac.maxRPM]
        self.maxFans = self.archive[ac.maxFans]

        print("**", self.R, self.C, self.L, self.RC, self.RCL)
        self.empty_color = empty_color
        self.off_color = off_color
        gd.BaseGrid.__init__(self, master, self.R, self.C, cursor = self.CURSOR,
            empty = self.empty_color)
        pt.PrintClient.__init__(self, pqueue)

        # Mapping ..............................................................
        self.values_g = [0]*self.size_g
        self.selected_g = [False]*self.size_g

        # FIXME transplant behavior that should be in Mapper
        self.getIndex_g = self.mapper.index_KG
        self.getIndex_k = self.mapper.index_GK
        self.getCoordinates_g = self.mapper.tuple_KG
        self.getCoordinates_k = self.mapper.tuple_GK

        self.nslaves = len(self.archive[ac.savedSlaves])
        self.size_k = self.nslaves*self.maxFans
        self.range_k = range(self.size_k)
        self.F_buffer = [0]*(2*self.size_k)

        self.control_buffer = []
        self._resetControlBuffer()

        # Tools ................................................................
        self.toolBar = ttk.Frame(self, style = "Topbar.TFrame", padding = (12, 8))
        self.toolBar.grid(row = self.GRID_ROW + 1, sticky = "WE")

        # Data type control (RPM vs DC) ........................................
        self.maxValue = self.maxRPM
        self.maxValues = {"RPM" : self.maxRPM, "DC" : 1}
        self.offsets = {"RPM" : 0, "DC" : 1}
        self.offset = self.offsets["RPM"]
        self.typeFrame = ttk.Frame(self.toolBar)
        self.typeFrame.pack(side = tk.LEFT, fill = tk.Y)
        self.typeMenuVar = tk.StringVar()
        self.typeMenuVar.trace('w', self._onTypeMenuChange)
        self.typeMenuVar.set("RPM")
        self.typeMenu = ttk.OptionMenu(self.toolBar, self.typeMenuVar,
            self.typeMenuVar.get(), *list(self.offsets.keys()))
        self.typeMenu.config(width = 3)
        self.typeMenu.pack(side = tk.LEFT)

        # Layer control ........................................................
        self.layer = 0
        self.layerFrame = ttk.Frame(self.toolBar)
        self.layerFrame.pack(side = tk.LEFT, fill = tk.Y)
        self.layerVar = tk.StringVar()
        self.layerVar.trace('w', self._onLayerChange)
        self.layerMenu = ttk.OptionMenu(self.layerFrame, self.layerVar,
            "Layer 1", *["Layer {}".format(l + 1) for l in range(self.L)])
        self.layerMenu.pack(side = tk.LEFT, **gus.padc)

        # Layer selection ......................................................
        self.deepVar = tk.BooleanVar()
        self.deepVar.set(True)
        self.deepButton = ttk.Checkbutton(self.toolBar,
            text = "Deep Select", variable = self.deepVar)
        self.deepButton.pack(side = tk.LEFT, **gus.padc)

        # Selection mode control ...............................................
        # FIXME
        self.selectMode = tk.IntVar()
        self.selectButton = ttk.Radiobutton(self.toolBar,
            variable = self.selectMode, value = self.SM_SELECT,
            text = "Rectangle")
        self.selectButton.pack(side = tk.LEFT)
        self.drawButton = ttk.Radiobutton(self.toolBar, text = "Trace",
            variable = self.selectMode, value = self.SM_DRAW)
        self.drawButton.pack(side = tk.LEFT)
        self.selectMode.trace('w', self._onSelectModeChange)

        self.drag_start = None
        self.drag_end = None

        self.selected_count = 0

        # Selection hold .......................................................
        self.holdVar = tk.BooleanVar()
        self.holdVar.set(True)
        self.holdButton = ttk.Checkbutton(self.toolBar,
            text = "Hold Selection", variable = self.holdVar)
        self.holdButton.pack(side = tk.RIGHT, **gus.padc)

        # Color Bar ............................................................
        self.colorBar = ColorBarWidget(self, colors = cms.COLORMAP_GALCIT,
            high = self.maxRPM, unit = "RPM", pqueue = pqueue)
        self.colorBar.grid(row = self.GRID_ROW, column = self.GRID_COLUMN + 1,
            sticky = "NS")

        # Setup ................................................................

        # Automatic resizing:
        self.bind("<Configure>", self._scheduleAdjust)

        self.adjusting = False
        self.colors = colors
        self.numColors = len(colors)
        self.maxColor = self.numColors - 1
        self.high = high
        self.low = 0
        self.rows, self.columns = range(self.R), range(self.C)
        self.dc = 0 # Whether to use duty cycles

        self.is_live = True

        # TODO: (redundant "TODO's" indicate priority)
        # - handle resets on profile changing TODO
        # - handle control vector construction TODO
        # - handle multilayer assignment (how to deal with unselected layers?)
        #   (TODO)
        # - drag, drop, etc..
        # - get selections
        # - [...]
        self.layerVar.set("Layer 1")
        self.selectMode.set(self.SM_SELECT)

        # Configure callbacks:
        self.setLeftClick(self._onLeftClick)
        self.setRightClick(self._onRightClick)
        self.setLeftRelease(self._onLeftRelease)
        self.setRightRelease(self._onRightRelease)
        self.setLeftDoubleClick(self._onDoubleLeft)
        self.setRightDoubleClick(self._onDoubleRight)
        self.setLeftDrag(self._onLeftDrag)
        self.setRightDrag(self._onRightDrag)

    # Standard interface .......................................................
    def activate(self, F_0 = None):
        if F_0 is not None:
            self.feedbackIn(F_0)

    def deactivate(self):
        # Optimized: Pre-allocate RIP array for better performance
        if not hasattr(self, '_rip_buffer') or len(self._rip_buffer) != self.size_g*2:
            self._rip_buffer = [std.RIP] * (self.size_g*2)
        self.feedbackIn(self._rip_buffer)
        pass

    def feedbackIn(self, F):
        """
        Process the feedback vector F according to the grid mapping.
        """
        # Optimized: Cache frequently accessed values and use list comprehension
        if self.built():
            size_g_offset = self.size_g * self.offset
            # Batch process updates for better performance
            updates = [(self.getIndex_g(k), F[k + size_g_offset]) for k in self.range_k]
            for g, value in updates:
                if g >= 0:
                    self.update_g(g, value)
            self.F_buffer = F
        else:
            self.printw("F received while grid isn't built. Ignoring.")

    def networkIn(self, N):
        if N[std.NS_I_CONN] != std.NS_CONNECTED:
            self.deactivate()

    def slavesIn(self, S):
        pass

    def selectAll(self):
        for g in self.range_g:
            self.select_g(g)

    def deselectAll(self):
        for g in self.range_g:
            self.deselect_g(g)

    def map(self, func, t = 0, t_step = 0):
        """
        Map the given function to the entire array, calling it once for each
        fan with the corresponding argument values.

        Note that values that correspond only to mapped fans (such as row,
        column and layer) will default to zero when unavailable.

        - func := function to map
        - t := timestamp (float)
        - t_step := time step (int)
        """
        """
        IMPLEMENTATION NOTES:
        - func(r, c, l, s, f, d, p, R, C, L, S, F, P, t, k)
        PARAMETERS = (P_ROW, P_COLUMN, P_LAYER, P_INDEX, P_FAN, P_DUTY_CYCLE,
        P_RPM, P_ROWS, P_COLUMNS, P_LAYERS, P_INDICES, P_FANS, P_MAX_RPM,P_TIME,
        P_STEP)
        """
        # Optimized: Batch coordinate calculations and reduce function calls
        try:
            # Pre-fill control buffer with current DCs so unselected fans retain their values
            if hasattr(self, 'F_buffer') and self.F_buffer and len(self.F_buffer) >= 2*self.size_k:
                self.control_buffer[:] = self.F_buffer[self.size_k:self.size_k*2]
            
            # Cache method references for better performance
            getIndex_g = self.getIndex_g
            slave_k = self.slave_k
            fan_k = self.fan_k
            getCoordinates_g = self.getCoordinates_g
            
            for k in self.range_k:
                g = getIndex_g(k)
                s, f = slave_k(k), fan_k(k)
                if g == std.PAD: # FIXME prev: if g != std.PAD:
                    l, r, c = 0, 0, 0
                else:
                    l, r, c = getCoordinates_g(s, f)

                if self.selected_count == 0 or (g >= 0 and self.selected_g[g]):
                    self.control_buffer[k] = func(r, c, l, s, f,
                        self.F_buffer[self.size_k + k], self.F_buffer[k],
                        self.R, self.C, self.L, self.nslaves, self.maxFans,
                        self.maxRPM, t, t_step)
        except Exception as e:
            print(k)
            raise e

        else:
            self.send_method(self.control_buffer)
            if not self.holdVar.get():
                self.deselectAll()

    def set(self, dc):
        """
        Map the given duty cycle.
        """
        self.map(self._const(dc), 0, 0)

    def apply(self):
        # FIXME
        pass

    def getC(self):
        # FIXME
        pass

    def limit(self, dc):
        # FIXME
        pass

    def blockAdjust(self):
        self.unbind("<Configure>")
        pass

    def unblockAdjust(self):
        self.bind("<Configure>", self._scheduleAdjust)
        pass

    def redraw(self, event = None):
        self.draw(margin = 20)
        self.colorBar.redraw()

    # Mapping ..................................................................
    def layer_g(self, g):
        """
        Get the layer that corresponds to the given grid-coordinate index.
        """
        return g // self.RC

    def gridi_g(self, g):
        """
        Get the 2D "within layer" index that corresponds to the given
        grid-coordinate index.

        In a single-layer grid, this function makes no difference.
        """
        return g % self.RC

    def slave_k(self, k):
        """
        Get the slave index corresponding to the network-coordinate index k.
        """
        return k // self.maxFans

    def fan_k(self, k):
        """
        Get the fan index corresponding to the network-coordinate index k.
        """
        return k % self.maxFans

    # Activity .................................................................
    def update_g(self, g, value):
        """
        Set the given grid index to the given value, saturating it at this
        grid's maximum value, and update the corresponding cell's color if
        the value is in the observed layer.

        - g := int, G-coordinate index.
        - value := int or float, value to apply.
        """
        self.values_g[g] = value
        fill = self.empty_color

        if value >= 0:
            fill = self.colors[min(self.maxColor,
                int(((value*self.maxColor)/self.maxValue)))]
        elif value == std.RIP:
            fill = self.off_color

        if self.layer_g(g) == self.layer:
            self.filli(self.gridi_g(g), fill)

    # Selection ................................................................
    # Optimized: Use range() instead of while loop for better performance
    def select_i(self, i):
        if self.deepVar.get():
            # Batch select all layers for better performance
            RC = self.RC
            select_g = self.select_g  # Cache method reference
            for l in range(self.L):
                select_g(i + l * RC)
        else:
            self.select_g(i + self.layer * self.RC)

    def deselect_i(self, i):
        if self.deepVar.get():
            l = 0
            while l < self.L:
                self.deselect_g(i + l*self.RC)
                l += 1
        else:
            self.deselect_g(i + self.layer*self.RC)


    def select_g(self, g):
        if not self.selected_g[g]:
            self.selected_count += 1
        self.selected_g[g] = True
        if self.layer_g(g) == self.layer:
            self.outlinei(self.gridi_g(g),
                self.OUTLINE_SELECTED, self.WIDTH_SELECTED)

    def deselect_g(self, g):
        if self.selected_g[g]:
            self.selected_count -= 1
        self.selected_g[g] = False
        if self.layer_g(g) == self.layer:
            self.outlinei(self.gridi_g(g),
                self.OUTLINE_NORMAL, self.WIDTH_NORMAL)

    # Widget ...................................................................
    def blockAdjust(self):
        """
        Deactivate automatic adjustment of widgets upon window resizes.
        """
        self.unbind("<Configure>")

    def unblockAdjust(self):
        """
        Activate automatic adjustment of widgets upon window resizes.
        """
        self.bind("<Configure>", self._scheduleAdjust)

    def getMapping(self):
        """
        Get the mapping data structure of this Grid.
        """
        return [self.getIndex_g(k) for k in self.range_k]

    # Internal methods .........................................................
    def _onLayerChange(self, *A):
        """
        To be called when the view layer is changed.
        """
        # Defensive parse: during early init, layerVar may not be ready
        try:
            self.layer = int(str(self.layerVar.get()).split()[-1]) - 1
        except Exception:
            return
        # Avoid running before essential attributes are set in __init__
        if not hasattr(self, 'colors') or not hasattr(self, 'values_g'):
            return
        self._updateStyle()

    def _onTypeMenuChange(self, *E):
        """
        TO be called when the data type (RPM or DC) is changed.
        """
        self.offset = self.offsets[self.typeMenuVar.get()]
        self.maxValue = self.maxValues[self.typeMenuVar.get()]

    def _onSelectModeChange(self, *E):
        """
        To be called when the direct input mode is changed.
        """
        pass

    def _scheduleAdjust(self, *E):
        try:
            # Check if widget still exists before scheduling
            if not self.winfo_exists():
                return
            
            # Cancel any existing scheduled adjustment to prevent accumulation
            if hasattr(self, '_adjust_timer') and self._adjust_timer:
                self.after_cancel(self._adjust_timer)
                self._adjust_timer = None
            
            # Schedule the adjustment with improved debouncing
            self._adjust_timer = self.after(self.RESIZE_MS, self._adjust)
            self.unbind("<Configure>")
        except (tk.TclError, AttributeError):
            # Widget has been destroyed or other error, ignore
            if hasattr(self, '_adjust_timer'):
                self._adjust_timer = None
            pass

    def _updateStyle(self, event = None):
        """
        Enforce style rules when switching layers.
        """
        l = self.layer
        offset = self.layer*self.RC
        for g in range(offset, offset + self.RC):
            self.update_g(g, self.values_g[g])
            if self.selected_g[g]:
                self.select_g(g)
            else:
                self.deselect_g(g)

    def _resetControlBuffer(self):
        """
        Set the control buffer back to its default value.
        """
        self.control_buffer = [0]*self.size_k

    def _adjust(self, *E):
        try:
            # Clear the timer reference
            if hasattr(self, '_adjust_timer'):
                self._adjust_timer = None
            
            # Check if widget still exists before adjusting
            if not self.winfo_exists():
                return
                
            self.redraw()
            self.bind("<Configure>", self._scheduleAdjust)
        except (tk.TclError, AttributeError):
            # Widget has been destroyed or other error, ignore
            if hasattr(self, '_adjust_timer'):
                self._adjust_timer = None
            pass

    @staticmethod
    def _onLeftClick(grid, i):
        grid.drag_start = i
        grid.drag_end = i
        if i is not None:
            if grid.selected_g[grid.layer*grid.RC + i]:
                grid.deselect_i(i)
            else:
                grid.select_i(i)

    @staticmethod
    def _onRightClick(grid, i):
        grid.drag_start = i
        grid.drag_end = i
        if i is not None:
            grid.deselect_i(i)

    @staticmethod
    def _generalDrag(grid, i, f_g):
        if i != None:
            if grid.selectMode.get() == grid.SM_SELECT:
                if grid.drag_start == None:
                    grid.drag_start = i
                if i != None:
                    grid.drag_end = i
            else:
                f_g(grid.layer*grid.RC + i)


    @staticmethod
    def _onLeftDrag(grid, i):
        if i != None:
            if grid.selectMode.get() == grid.SM_SELECT:
                if grid.drag_start == None:
                    grid.drag_start = i
                grid.drag_end = i
            else:
                grid.select_i(i)

    @staticmethod
    def _onRightDrag(grid, i):
        if i != None:
            if grid.selectMode.get() == grid.SM_SELECT:
                if grid.drag_start == None:
                    grid.drag_start = i
                grid.drag_end = i
            else:
                grid.deselect_i(i)

    @staticmethod
    def _onLeftRelease(grid, i):
        grid._generalRelease(grid, i, grid.select_i)

    @staticmethod
    def _onRightRelease(grid, i):
        grid._generalRelease(grid, i, grid.deselect_i)

    @staticmethod
    def _generalRelease(grid, i, f_i):
        if grid.drag_start != grid.drag_end and grid.drag_start != None and \
            grid.drag_end != None:

            if grid.selectMode.get() == grid.SM_SELECT:
                row_1, row_2 = grid.drag_start//grid.R, grid.drag_end//grid.R
                row_start = min(row_1, row_2)
                row_end = max(row_1, row_2)

                col_1, col_2 = grid.drag_start%grid.R, grid.drag_end%grid.R
                col_start = min(col_1, col_2)
                col_end = max(col_1, col_2)

                for r in range(row_start, row_end + 1):
                    for c in range(col_start, col_end + 1):
                        f_i(r*grid.C + c)

                grid.drag_start = None
                grid.drag_end = None
            else:
                pass

    @staticmethod
    def _onDoubleLeft(grid, i):
        k_i = grid.getIndex_k(i + grid.layer*grid.RC)
        k_0 = grid.slave_k(k_i)*grid.maxFans

        for k in range(k_0, k_0 + grid.maxFans):
            g = grid.getIndex_g(k)
            if g >= 0:
                grid.select_g(g)

    @staticmethod
    def _onDoubleRight(grid, i):
        k_i = grid.getIndex_k(i + grid.layer*grid.RC)
        k_0 = grid.slave_k(k_i)*grid.maxFans

        for k in range(k_0, k_0 + grid.maxFans):
            g = grid.getIndex_g(k)
            if g >= 0:
                grid.deselect_g(g)

    @staticmethod
    def _const(dc):
        """
        Return a function that ignores all arguments and returns the given
        duty cycle.
        """
        def g(*_):
            return dc
        return g

class ColorBarWidget(ttk.Frame):
    """
    Draw a vertical color gradient for color-coding reference.
    """
    SYMBOL = "[CB]"

    def __init__(self, master, colors, pqueue, high = 100, unit = "[?]"):

        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ................................................................
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)
        self.colors = colors
        self.steps = len(colors)
        self.high, self.low = high, 0


        # Widgets ..............................................................
        self.highLabel = ttk.Label(self, text = "{} {}".format(high, unit),
            style = "Secondary.TLabel")
        self.highLabel.grid(row = 0, sticky = "EW")

        self.canvas = tk.Canvas(self, bg = self.colors[-1],
            width = self.highLabel.winfo_width())
        self.canvas.grid(row = 1, sticky = 'NEWS')

        self.lowLabel = ttk.Label(self, text = "{} {}".format(self.low, unit),
            style = "Secondary.TLabel")
        self.lowLabel.grid(row = 2, sticky = "EW")

        print("[REM] Pass MAX RPM to color bar") # FIXME

        self._draw()

    # API ......................................................................
    def redraw(self, *E):
        """
        Rebuild the color bar to adjust to a new size.
        """
        self.canvas.delete(tk.ALL)
        self._draw()

    def setHigh(self, new):
        """
        Set a new high value.
        """
        self.high = new

    # Internal methods .........................................................
    def _draw(self, *E):
        """
        Draw the colorbar.
        """
        self.winfo_toplevel().update_idletasks()
        height = max(self.winfo_height(), self.winfo_reqheight())
        width = self.highLabel.winfo_reqwidth()
        step = height/self.steps
        left, right = 0, width
        y = 0
        self.bind("<Button-1>", self.redraw)
        for i in range(self.steps):
            iid = self.canvas.create_rectangle(
                left, y, right, y + step, fill = self.colors[i],
                width = 0)
            self.canvas.tag_bind(iid, "<ButtonPress-1>", self.redraw)
            y += step
        self.canvas.create_line(left, y, right, y, width = 4)
        self.canvas.create_line(left, y, right, y, width = 2, fill = 'white')

class LiveTable(pt.PrintClient, ttk.Frame):
    """
    Another interactive control widget. This one displays all slaves and fans
    in a tabular fashion and hence needs no mapping.
    """
    SYMBOL = "[LT]"

    MENU_ROW, MENU_COLUMN = 0, 0
    TABLE_ROW, TABLE_COLUMN = 2, 0
    HSCROLL_ROW, HSCROLL_COLUMN = MENU_ROW + 1, TABLE_COLUMN
    VSCROLL_ROW, VSCROLL_COLUMN = TABLE_ROW, TABLE_COLUMN + 1

    INF = float('inf')
    NINF = -INF


    def __init__(self, master, archive, mapper, send_method, network, pqueue):
        """
        Create a new LiveTable in MASTER.

            master := Tkinter parent widget
            archive := FCArchive instance
            send_method := method to which to pass generated control vectors
            pqueue := Queue instance for I-P printing

        """
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)
        self.archive = archive
        self.mapper = mapper
        self.send_method = send_method

        self.maxFans = self.archive[ac.maxFans]
        self.startDisplacement = 2
        self.endDisplacement = self.startDisplacement + self.maxFans

        self.fanArray = self.archive[ac.fanArray]
        self.L = self.fanArray[ac.FA_layers]
        self.R, self.C = self.fanArray[ac.FA_rows], self.fanArray[ac.FA_columns]
        self.RC = self.R*self.C
        self.RCL = self.RC*self.L
        self.size_g = self.RC*self.L
        self.range_g = range(self.size_g)
        self.maxRPM = self.archive[ac.maxRPM]
        self.maxFans = self.archive[ac.maxFans]

        # Mapping ..............................................................
        self.values_g = [0]*self.size_g
        self.selected_g = [False]*self.size_g


        # FIXME transplant behavior that should be in Mapper
        self.getIndex_g = self.mapper.index_KG
        self.getIndex_k = self.mapper.index_GK
        self.getCoordinates_g = self.mapper.tuple_KG
        self.getCoordinates_k = self.mapper.tuple_GK

        self.nslaves = len(self.archive[ac.savedSlaves])
        self.size_k = self.nslaves*self.maxFans
        self.range_k = range(self.size_k)
        self.F_buffer = [0]*(2*self.size_k)

        self.selected_count = 0
        self.control_buffer = []
        self._resetControlBuffer()

        # Build menu ...........................................................
        self.main = ttk.Frame(self)
        self.main.pack(fill = tk.BOTH, expand = True)

        self.main.grid_rowconfigure(self.TABLE_ROW, weight = 1)
        self.main.grid_columnconfigure(self.TABLE_COLUMN, weight = 1)

        # Colors are now handled by themed styles; remove manual bg/fg to avoid mismatches.

        self.topBar = ttk.Frame(self.main, style = "Topbar.TFrame", padding = (12, 8))
        self.topBar.grid(row = self.MENU_ROW, column = self.MENU_COLUMN,
            sticky = "EW")

        self.offset = 0
        self.showMenuVar = tk.StringVar()
        self.showMenuVar.trace('w', self._showMenuCallback)
        self.showMenuVar.set("RPM")
        self.showMenu = ttk.OptionMenu(self.topBar, self.showMenuVar, self.showMenuVar.get(), "RPM","DC")
        self.showMenu.config(width = 3)
        self.showMenu.pack(side = tk.LEFT, **gus.padc)

        self.playPauseFlag = True
        self.playPauseButton = ib.create_pause_button(
            self.topBar,
            command = self._playPause
        )
        self.bind("<space>", self._playPause)
        self.master.bind("<space>",self._playPause)

        self.playPauseButton.pack(side = tk.LEFT, **gus.padc)

        self.printThread = None
        self.donePrinting = False
        self.printMatrixButton = ib.create_icon_button(
            self.topBar,
            text = "Print",
            icon = "print",
            command = self._printMatrix,
            style = "Secondary"
        )
        self.master.bind("<Control-P>",self._printMatrix)
        self.master.bind("<Control-p>",self._printMatrix)

        self.wasPaused = False

        # Sentinel .............................................................
        self.sentinelWidgets = []
        self._sentinelCheck = lambda x: False

        self.sentinelFrame = ttk.Frame(
            self.topBar,
        )

        self.sentinelLabel = ttk.Label(
            self.sentinelFrame,
            text=" Watchdog: ",
            style = "Secondary.TLabel",
        )
        self.sentinelLabel.pack(side=tk.LEFT)

        self.sentinelSecondaryLabel = ttk.Label(
            self.sentinelFrame,
            style = "Secondary.TLabel",
        )
        self.sentinelSecondaryLabel.pack(side=tk.LEFT)

        self.sentinelMenuVar = tk.StringVar()
        self.sentinelMenuVar.set("Above")
        self.sentinelMenu = ttk.OptionMenu(
            self.sentinelFrame,
            self.sentinelMenuVar,
            self.sentinelMenuVar.get(),
            "Above",
            "Below",
            "Outside 10% of",
            "Within 10% of",
            "Not"
        )
        self.sentinelMenu.pack(side = tk.LEFT)
        self.sentinelWidgets.append(self.sentinelMenu)

        validateC = self.register(gus._validateN)
        self.sentinelEntry = ttk.Entry(
            self.sentinelFrame,
            width=5,
            validate='key',
            validatecommand=(validateC, '%S', '%s', '%d'),
        )
        self.sentinelEntry.insert(0, '0')
        self.sentinelEntry.pack(side=tk.LEFT)
        self.sentinelWidgets.append(self.sentinelEntry)

        self.sentinelTerciaryLabel = ttk.Label(
            self.sentinelFrame,
            style = "Secondary.TLabel",
            text = " RPM   "
        )
        self.sentinelTerciaryLabel.pack(side = tk.LEFT)

        self.sentinelActionMenuVar = tk.StringVar()
        self.sentinelActionMenuVar.set("Highlight")
        self.sentinelActionMenu = ttk.OptionMenu(
            self.sentinelFrame,
            self.sentinelActionMenuVar,
            self.sentinelActionMenuVar.get(),
            "Warn me",
            "Highlight",
            "Shut down",
        )
        self.sentinelActionMenu.pack(side = tk.LEFT)
        self.sentinelWidgets.append(self.sentinelActionMenu)

        self.sentinelPauseVar = tk.BooleanVar()
        self.sentinelPauseVar.set(True)
        self.sentinelPauseButton = ttk.Checkbutton(
            self.sentinelFrame,
            text="Freeze",
            variable=self.sentinelPauseVar,
        )
        self.sentinelPauseButton.pack(side=tk.LEFT)
        self.sentinelWidgets.append(self.sentinelPauseButton)

        self.sentinelPrintVar = tk.IntVar()
        self.sentinelPrintButton = ttk.Checkbutton(
            self.sentinelFrame,
            text="Print",
            variable=self.sentinelPrintVar,
        )
        self.sentinelPrintButton.pack(side=tk.LEFT)
        self.sentinelWidgets.append(self.sentinelPrintButton)

        self.sentinelApplyButton = ttk.Button(
            self.sentinelFrame,
            text="Apply",
            command=self._applySentinel,
            state=tk.NORMAL,
        )
        self.sentinelApplyButton.pack(side=tk.LEFT)

        self.sentinelClearButton = ttk.Button(
            self.sentinelFrame,
            text="Clear",
            command=self._clearSentinel,
            state=tk.DISABLED,
            style = "Secondary.TButton",
        )
        self.sentinelClearButton.pack(side=tk.LEFT)

        self.sentinelFrame.pack(side = tk.RIGHT, **gus.padc)
        self.sentinelFlag = False

        # Build table ..........................................................
        self.tableFrame = ttk.Frame(self.main)
        self.tableFrame.grid(row = self.TABLE_ROW, column = self.TABLE_COLUMN,
            sticky = "NEWS")
        self.table = ttk.Treeview(self.tableFrame,
            height = 32)
        self.table.pack(fill = tk.BOTH, expand = True)
        # Add columns:
        self.columns = ("Index", "Max", "Min")
        self.specialColumns = len(self.columns)

        self.style = ttk.Style(self.table)
        self.style.configure('Treeview.Heading', font = gus.typography["label_small"]["font"])

        self.zeroes = ()
        for fanNumber in range(self.maxFans):
            self.columns += ("{}".format(fanNumber+1),)
            self.zeroes += (0,)
        self.columns += ("Pad",)

        self.table['columns'] = self.columns

        self.table.column("#0", width = 20, stretch = True)

        self.boldFontSettings = (gus.typography["code"]["font"][0], gus.typography["code"]["font"][1], "bold")
        self.font = tk.font.Font(font = self.boldFontSettings)
        self.rpmwidth = self.font.measure("12345")
        self.specwidth = self.font.measure("  Index  ")
        # Build columns:
        for column in self.columns[:self.specialColumns]:
            self.table.column(column,
                anchor = "center", stretch = False, width = self.specwidth)
            self.table.heading(column, text = column)

        for column in self.columns[self.specialColumns:-1]:
            self.table.column(column, width = self.rpmwidth,
                anchor = "center", stretch = False)
            self.table.heading(column, text = column)

        self.table.column(self.columns[-1], width = self.rpmwidth,
            anchor = "center", stretch = True)
        self.table.heading(self.columns[-1], text = " ")

        # Configure tags:
        self.table.tag_configure(
            "H", # Highlight
            background= WARNING_LIGHT,
            foreground = WARNING_DARK,
            font = self.boldFontSettings
        )

        self.table.tag_configure(
            "D", # Disconnected
            background= SURFACE_3,
            foreground = TEXT_DISABLED,
            font = self.boldFontSettings
        )

        self.table.tag_configure(
            "N", # Normal
            background= SURFACE_1,
            foreground = TEXT_PRIMARY,
            font = self.boldFontSettings
        )

        # Configure striped rows for better readability
        stripe_bg = gus.SURFACE_2 if hasattr(gus, 'SURFACE_2') else "#f8f9fa"
        self.table.tag_configure(
            "stripe_even",
            background = SURFACE_1
        )
        self.table.tag_configure(
            "stripe_odd",
            background = stripe_bg,
            foreground = TEXT_PRIMARY,
            font = (gus.typography["code"]["font"][0], gus.typography["code"]["font"][1], "normal")
        )

        # Build scrollbars .....................................................
        # See: https://lucasg.github.io/2015/07/21/
        #    How-to-make-a-proper-double-scrollbar-frame-in-Tkinter/
        self.hscrollbar = ttk.Scrollbar(self.main, orient = tk.HORIZONTAL)
        self.hscrollbar.config(command = self.table.xview)
        self.hscrollbar.grid(row = self.HSCROLL_ROW,
            column = self.HSCROLL_COLUMN, sticky = "EW")

        self.vscrollbar = ttk.Scrollbar(self.main, orient = tk.VERTICAL)
        self.vscrollbar.config(command = self.table.yview)
        self.vscrollbar.grid(row = self.VSCROLL_ROW,
            column = self.VSCROLL_COLUMN, sticky = "NS")


        # FIXME verify consistency with new standard
        # Add rows and build slave list:
        self.slaves = {}
        self.fans = range(self.maxFans)
        self.numSlaves = 0

    def networkIn(self, N):
        if not N[std.NS_I_CONN]:
            self.deactivate()

    def slavesIn(self, S):
        pass

    def selectAll(self):
        for index, iid in self.slaves.items():
            self.table.selection_add(iid)

    def deselectAll(self):
        self.table.selection_set(())

    def map(self, func, t = 0, t_step = 0):
        """
        Map the given function to the entire array, calling it once for each
        fan with the corresponding argument values.

        Note that values that correspond only to mapped fans (such as row,
        column and layer) will default to zero when unavailable.

        - func := function to map
        - t := timestamp (float)
        - t_step := time step (int)
        """
        """
        IMPLEMENTATION NOTES:
        - func(r, c, l, s, f, d, p, R, C, L, S, F, P, t, k)
        PARAMETERS = (P_ROW, P_COLUMN, P_LAYER, P_INDEX, P_FAN, P_DUTY_CYCLE,
        P_RPM, P_ROWS, P_COLUMNS, P_LAYERS, P_INDICES, P_FANS, P_MAX_RPM,P_TIME,
        P_STEP)

        * "g" is still relevant here because FC functions use both Grid and
            LiveTable parameters.
        """
        # FIXME why are there redundant implementations of this? See GridWidget
        # FIXME no Exception handling?
        # FIXME performance
        # Pre-fill control buffer with current DCs so unselected fans retain their values
        if hasattr(self, 'F_buffer') and self.F_buffer and len(self.F_buffer) >= 2*self.size_k:
            self.control_buffer[:] = self.F_buffer[self.size_k:self.size_k*2]
        for k in self.range_k:
            g = self.getIndex_g(k)
            s, f  = self.slave_k(k), self.fan_k(k)
            if g == std.PAD: # FIXME prev: if g != std.PAD:
                l, r, c = 0, 0, 0
            else:
                l, r, c = self.getCoordinates_g(s, f)

            if self.selected_count == 0 or (g >= 0 and self.selected_g[g]):
                self.control_buffer[k] = func(r, c, l, s, f,
                    self.F_buffer[self.size_k + k], self.F_buffer[k],
                    self.R, self.C, self.L, self.nslaves, self.maxFans,
                    self.maxRPM, t, t_step)

        self.send_method(self.control_buffer)


    def set(self, dc):
        self.map(self._const(dc), 0, 0)

    def apply(self):
        # FIXME
        pass

    def getC(self):
        # FIXME
        pass

    def limit(self, dc):
        # FIXME
        pass

    def blockAdjust(self):
        # FIXME
        pass

    def unblockAdjust(self):
        # FIXME
        pass

    def redraw(self):
        # FIXME
        print("redraw")
        pass

    def getMapping(self):
        return None

    # Mapping ..................................................................
    def layer_g(self, g):
        """
        Get the layer that corresponds to the given grid-coordinate index.
        """
        return g // self.RC

    def gridi_g(self, g):
        """
        Get the 2D "within layer" index that corresponds to the given
        grid-coordinate index.

        In a single-layer grid, this function makes no difference.
        """
        return g % self.RC

    def slave_k(self, k):
        """
        Get the slave index corresponding to the network-coordinate index k.
        """
        return k // self.maxFans

    def fan_k(self, k):
        """
        Get the fan index corresponding to the network-coordinate index k.
        """
        return k % self.maxFans

    # Selection ................................................................
    def select_i(self, i):
        """
        Select a specific slave by index.
        """
        if 0 <= i < len(self.slaves):
            self.selectedSlaves.add(i)
            self._updateRowStyle(i)
    
    def deselect_i(self, i):
        """
        Deselect a specific slave by index.
        """
        if i in self.selectedSlaves:
            self.selectedSlaves.remove(i)
            self._updateRowStyle(i)
    
    def select_range(self, start, end):
        """
        Select a range of slaves.
        """
        for i in range(max(0, start), min(len(self.slaves), end + 1)):
            self.selectedSlaves.add(i)
            self._updateRowStyle(i)
    
    def _updateRowStyle(self, i):
        """
        Update the visual style of a table row based on selection state.
        """
        if hasattr(self, 'tree') and i < len(self.slaves):
            item_id = self.tree.get_children()[i] if i < len(self.tree.get_children()) else None
            if item_id:
                if i in self.selectedSlaves:
                    self.tree.set(item_id, 'selected', '✓')
                else:
                    self.tree.set(item_id, 'selected', '')

    # Internal methods .........................................................
    def activate(self, A = None):
        """
        Set the display as "active."
            - A := Optional "activation vector" (a feedback vector with which to
                initialize slave lists and display values).
        """
        if A is None:
            for index in self.slaves:
                self.activatei(index)
        else:
            self.feedbackIn(A)

    def activatei(self, i):
        """
        "Turn on" the row corresponding to the slave in index i.
        """
        self.table.item(self.slaves[i], values = (i + 1), tag = "N")

    def deactivate(self):
        """
        Seemingly "turn off" all rows to indicate inactivity; meant to be used,
        primarily, upon network shutdown.
        """
        for index in self.slaves:
            self.deactivatei(index)
        self._resetControlBuffer()

    def deactivatei(self, i):
        """
        "Turn off" the row corresponding to the slave in index i.
        """
        self.table.item(self.slaves[i],
            values = (i + 1,), tag = "D")

    def _resetControlBuffer(self):
        """
        Set the control buffer back to its default value.
        """
        self.control_buffer = [0]*self.size_k

    def _applySentinel(self, event = False):
        """
        Activate a sentinel according to the user's configuration.
        """
        try:
            if self.sentinelEntry.get() != '':
                self.sentinelFlag = True
                self.sentinelApplyButton.config(state = tk.DISABLED)

                self._sentinelCheck = self._assembleSentinel()

                for widget in self.sentinelWidgets:
                    widget.config(state = tk.DISABLED)
                self.sentinelClearButton.config(state = tk.NORMAL)
        except Exception as e:
            self.printx(e, "Exception in live table:")

    def _executeSentinel(self, targetSlave, targetFan, RPM):
        """
        Trigger the sentinel due to the RPM detected in the target fan of the
        target slave.
        """

        # Action:
        action = self.sentinelActionMenuVar.get()

        if action == "Highlight row(s)":
            pass

        elif action == "Warn me":
            self._printe("WARNING: Module {}, Fan {} at {} RPM".format(
                targetSlave + 1, targetFan, RPM))

        elif action == "Shut down":
            network.shutdown()
            if self.playPauseFlag:
                self._playPause()

            self._printe("WARNING: Shutdown triggered by Module {}, Fan {} "\
                "({} RPM)".format(targetSlave + 1, targetFan, RPM))

        # Print (and avoid printing the same matrix twice):
        if self.sentinelPrintVar.get() and \
            self.lastPrintedMatrix < self.matrixCount:
            self._printMatrix(sentinelValues = (targetFan,targetSlave,RPM))
            self.lastPrintedMatrix = self.matrixCount

        # Pause:
        if self.sentinelPauseVar.get() and self.playPauseFlag:
            self._playPause()

    def _assembleSentinel(self):
        """
        Gather the user's configuration from the relevant input widgets and
        build a new sentinel.
        """
        check = self.sentinelMenuVar.get()
        value = int(self.sentinelEntry.get())

        if check == "Above":
            return lambda rpm : rpm > value

        elif check == "Below":
            return lambda rpm : rpm < value

        elif check == "Outside 10% of":
            return lambda rpm : rpm > value*1.1 or rpm < value*.9

        elif check == "Within 10% of":
            return lambda rpm : rpm < value*1.1 and rpm > value*.9

        elif check == "Not":
            return lambda rpm : rpm != value

    def _clearSentinel(self, event = False):
        """
        Deactivate an active sentinel.
        """
        self.sentinelFlag = False
        self.sentinelClearButton.config(state = tk.DISABLED)
        for widget in self.sentinelWidgets:
            widget.config(state = tk.NORMAL)
        self.sentinelApplyButton.config(state = tk.NORMAL)

    def _printMatrix(self, event = None, sentinelValues = None):
        # FIXME should this be here?

        if self.playPauseFlag:
            self.wasPaused = False
            self._playPause()

        else:
            self.wasPaused = True

        # Lock table ...........................................................
        self.playPauseButton.config(state = tk.DISABLED)
        self.printMatrixButton.config(state = tk.DISABLED)

        if not self.sentinelFlag:
            for widget in self.sentinelWidgets:
                widget.config(state = tk.DISABLED)
            self.sentinelApplyButton.config(state = tk.DISABLED)

        else:
            self.sentinelClearButton.config(state = tk.DISABLED)

        # Print ................................................................
        self.donePrinting = False

        self.printThread = threading.Thread(
            name = "FCMkII_LT_Printer",
            target = self._printRoutine,
            args = (sentinelValues,)
        )
        self.printThread.setDaemon(True)
        self.printThread.start()

        self._printChecker()

    def _printChecker(self):
        """
        Each call checks if printing should be deactivated.
        """
        try:
            # Check if widget still exists before scheduling
            if not self.winfo_exists():
                return
                
            if not self.donePrinting:
                self.after(100, self._printChecker)
            else:
                # Unlock table:
                self.playPauseButton.config(state = tk.NORMAL)
                self.printMatrixButton.config(state = tk.NORMAL)
                if not self.sentinelFlag:
                    for widget in self.sentinelWidgets:
                        widget.config(state = tk.NORMAL)
                    self.sentinelApplyButton.config(state = tk.NORMAL)
                    if not self.wasPaused:
                        self._playPause()
                else:
                    self.sentinelClearButton.config(state = tk.NORMAL)
                    if not self.sentinelPauseVar.get():
                        self._playPause()
        except tk.TclError:
            # Widget has been destroyed, ignore
            pass

    def _printRoutine(self, sentinel = None):
        # FIXME incompatible
        try:
            fileName = "FCMkII_table_print_on_{}.csv".format(
                time.strftime("%a_%d_%b_%Y_%H:%M:%S", time.localtime()))

            self._printM("Printing to file")

            with open(fileName, 'w') as f:
                # File setup ...................................................

                f.write("Fan Club MkII data launched on {}  using "\
                    "profile \"{}\" with a maximum of {} fans.\n"\
                    "Matrix number (since live table was launched): {}\n\n".\
                    format(
                        time.strftime(
                            "%a %d %b %Y %H:%M:%S", time.localtime()),
                        self.profile[ac.name],
                        self.profile[ac.maxFans],
                        self.matrixCount
                        )
                    )

                if sentinel is not None:
                    f.write("NOTE: This data log was activated by a watchdog "\
                        "trigger caused by fan {} of module {} being "\
                        "measured at {} RPM "\
                        "(Condition: \"{}\" if \"{}\" {} RPM)\n".\
                        format(
                            sentinel[0]+1,  # Fan
                            sentinel[1]+1,  # Slave
                            sentinel[2],    # RPM value
                            self.sentinelActionMenuVar.get(),
                            self.sentinelMenuVar.get(),
                            self.sentinelEntry.get()
                            )
                    )

                # Headers (fifth line):

                # Write headers:
                f.write("Module,")

                for column in self.columns[self.specialColumns:]:
                    f.write("{} RPM,".format(column))

                # Move to next line:
                f.write('\n')

                # Write matrix:
                for index, row in enumerate(self.latestMatrix):
                    f.write("{},".format(index+1))
                    for value in row[1:]:
                        f.write("{},".format(value))

                    f.write('\n')

            self.donePrinting = True
            self._printM("Done printing",'G')

        except:
            self._printM("ERROR When printing matrix: {}".\
                format(traceback.print_exc()),'E')
            self.donePrinting = True

        # End _printRoutine ====================================================

    def _playPause(self, event = None, force = None):
        """
        Toggle the play and pause statuses.
         """

        if self.playPauseFlag or force is False:
            self.playPauseFlag = False
            self.playPauseButton.config_text("Play")
            self.playPauseButton.config_icon("play")
            self.playPauseButton.config_style("Primary")
        elif not self.playPauseFlag or force is True:
            self.playPauseFlag = True
            self.playPauseButton.config_text("Pause")
            self.playPauseButton.config_icon("pause")
            self.playPauseButton.config_style("Secondary")

    def _showMenuCallback(self, *event):
        if self.showMenuVar.get() == "RPM":
            self.offset = 0
        elif self.showMenuVar.get() == "DC":
            self.offset = 1

    # Standard interface .......................................................
    def feedbackIn(self, F):
        if self.playPauseFlag:
            # Performance optimized: cache frequently accessed values and use batch operations
            L = len(F)//2
            N = L//self.maxFans
            
            # Cache method references for performance
            table_insert = self.table.insert
            table_item = self.table.item
            
            # Batch create new slave entries if needed
            if N > self.numSlaves:
                new_slaves = []
                for index in range(self.numSlaves, N):
                    stripe_tag = "stripe_even" if index % 2 == 0 else "stripe_odd"
                    tags = ('N', stripe_tag)
                    slave_id = table_insert('', 'end',
                        values = (index + 1,) + self.zeroes, tags = tags)
                    new_slaves.append(slave_id)
                
                # Batch update slaves list
                self.slaves.extend(new_slaves)
                self.numSlaves = N

            # Cache constants for performance
            offset = self.offset
            maxFans = self.maxFans
            sentinelFlag = self.sentinelFlag
            slaves = self.slaves
            
            slave_i, vector_i = 0, L * offset
            end_i = L + vector_i
            tag = "N"
            
            # Process data in chunks for better performance
            while vector_i < end_i:
                values = tuple(F[vector_i:vector_i + maxFans])

                if std.RIP in values:
                    # This slave is disconnected
                    stripe_tag = "stripe_even" if slave_i % 2 == 0 else "stripe_odd"
                    tags = ("D", stripe_tag)
                    table_item(slaves[slave_i], values = (slave_i + 1,), tags = tags)
                elif std.PAD not in values:
                    # This slave is active
                    if sentinelFlag:
                        for fan, value in enumerate(values):
                            if self._sentinelCheck(values):
                                tag = "H"
                                self._executeSentinel(slave_i, fan, value)
                    stripe_tag = "stripe_even" if slave_i % 2 == 0 else "stripe_odd"
                    tags = (tag, stripe_tag)
                    table_item(slaves[slave_i],
                        values = (slave_i + 1, max(values), min(values)) + values, 
                        tags = tags)
                slave_i += 1
                vector_i += maxFans

            self.F_buffer = F

        self.built = True

    @staticmethod
    def _const(dc):
        """
        Return a function that ignores any arguments passed and returns the
        given duty cycle.
        - dc: the value to be returned.
        """
        def f(*_):
            return dc
        return f

class DataLogger(pt.PrintClient):
    """
    Print feedback vectors to CSV files.
    """
    SYMBOL = "[DL]"
    STOP = -69
    S_I_NAME, S_I_MAC = 0, 1


    # NOTE:
    # - you cannot add slaves mid-print, as the back-end process takes only F's
    # NOTE: watchdog?

    def __init__(self, archive, pqueue):
        pt.PrintClient.__init__(self, pqueue)

        self.pipeRecv, self.pipeSend = None, None
        self._buildPipes()
        self.archive = archive
        self.process = None

        self.slaves = {}

    # API ----------------------------------------------------------------------

    def start(self, filename, timeout = std.MP_STOP_TIMEOUT_S,
        script = "[NONE]", mappings = ("[NONE]",)):
        """
        Begin data logging.
        """
        try:
            if self.active():
                self.stop(timeout)
            self._buildPipes()
            arr = self.archive[ac.fanArray]
            self.process = mp.Process(
                name = "FC_Log_Backend",
                target = self._routine,
                args = (
                    filename, self.archive[ac.version], self.slaves,
                    self.archive[ac.name], self.archive[ac.maxFans],
                    (arr[ac.FA_rows], arr[ac.FA_columns], arr[ac.FA_layers]),
                    self.pipeRecv, script, mappings, self.pqueue),
                daemon = True,)
            self.process.start()
            self.prints("Data log started")
        except Exception as e:
            self.printx(e, "Exception activating data log:")
            self._sendStop()

    def stop(self, timeout = std.MP_STOP_TIMEOUT_S):
        """
        Stop data logging.
        """
        try:
            if self.active():
                self.printr("Stopping data log")
                self._sendStop()
                self.process.join(timeout)
                if self.process.is_alive():
                    self.process.terminate()
                self.process = None
                self.printr("Data log stopped")
        except Exception as e:
            self.printx(e, "Exception stopping data log:")
            self._sendStop()

    def active(self):
        """
        Return whether the printer back-end is active.
        """
        return self.process is not None and self.process.is_alive()

    def feedbackIn(self, F, t = 0):
        """
        Process the feedback vector F with timestamp t.
        """
        # FIXME: optm. time stamping
        if self.active():
            self.pipeSend.send((F, t))

    def slavesIn(self, S):
        """
        Process a slave data vector.
        """
        length = len(S)
        i = 0
        while i < length:
            index, name, mac = \
                S[i + std.SD_INDEX] + 1, S[i + std.SD_NAME], S[i + std.SD_MAC]
            if index not in self.slaves:
                self.slaves[index] = (name, mac)
            i += std.SD_LEN

    def networkIn(self, N):
        """
        Process a network state vector.
        """
        pass

    # Internal methods ---------------------------------------------------------
    def _sendStop(self):
        """
        Send the stop signal.
        """
        self.pipeSend.send(self.STOP)

    def _buildPipes(self):
        """
        Reset the pipes. Do not use while the back-end is active.
        """
        self.pipeRecv, self.pipeSend = mp.Pipe(False)

    @staticmethod
    def _routine(filename, version, slaves, profileName, maxFans, dimensions,
        pipeRecv, script, mappings, pqueue):
        """
        Routine executed by the back-end process.
        """

        # FIXME exception handling
        # FIXME watch for thread death

        # FIXME performance
        P = pt.PrintClient(pqueue)
        P.symbol = "[DR]"
        P.printr("Setting up data log")
        with open(filename, 'w') as f:
            # (Header) Log basic data:
            f.write("Fan Club MkIV ({}) data log started on {}  using "\
                "profile \"{}\"\n".format(
                    version,tm.strftime("%a %d %b %Y %H:%M:%S", tm.localtime()),
                    profileName))

            # (Header) filename:
            f.write("Filename: \"{}\"\n".format(filename))

            # (Header) Module breakdown:
            f.write("Modules: |")
            rpm_boilerplate = ""
            dc_boilerplate = ""
            for fan in range(maxFans):
                rpm_boilerplate += "s{0}" + "rpm{},".format(fan + 1)
                dc_boilerplate += "s{0}" + "dc{},".format(fan + 1)
            rpm_headers = ""
            dc_headers = ""
            for index, data in slaves.items():
                name, mac = data
                f.write("\"{}\": {} - \"{}\" | ".format(index, name, mac))
                rpm_headers += rpm_boilerplate.format(index)
                dc_headers += dc_boilerplate.format(index)
            f.write("\n")

            # (Header) Dimensions:
            f.write("Dimensions (rows, columns, layers): {}x{}x{}\n".format(
                *dimensions))

            # (Header) Max fans:
            f.write("Max Fans: {}\n".format(maxFans))

            # (Header) Mappings:
            f.write("Fan Array Mapping(s):\n")
            for i, mapping in enumerate(mappings):
                f.write("\tMapping {}: {}\n".format(i + 1, mapping))

            # (Header) Functions in use:
            fn_temp = "Script (Flattened. Replace ; for newline):\n"
            f.write(fn_temp + script + "\n")

            # Header (3/4)
            f.write("Column headers are of the form s[MODULE#][type][FAN#]"\
                "with type being first \"rpm\" and then all \"dc\"\n")

            # Header (4/4):
            f.write("Time (s)," + rpm_headers + dc_headers + "\n")

            P.prints("Data log online")
            t_start = tm.time()
            while True:
                # FIXME performance
                data = pipeRecv.recv()
                if data == DataLogger.STOP:
                    break
                F, t = data
                f.write("{},".format(t - t_start))
                for item in F:
                    f.write("{},".format(item if item != -666 else 'NaN'))
                f.write("\n")
        P.printr("Data logger back-end ending")


## DEMO ########################################################################
if __name__ == "__main__":
    print("FCMkIV Control GUI demo started")
    mw = tk.Tk()
    CW = ControlWidget(mw, print, print)
    CW.pack(fill = tk.BOTH, expand = True)
    mw.mainloop()

    print("FCMkIV Control GUI demo finished")
