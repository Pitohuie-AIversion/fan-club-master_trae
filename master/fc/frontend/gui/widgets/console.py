################################################################################
## Project: Fanclub Mark IV "Master" GUI          ## File: console.py         ##
##----------------------------------------------------------------------------##
## CALIFORNIA INSTITUTE OF TECHNOLOGY ## GRADUATE AEROSPACE LABORATORY ##     ##
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
## Alejandro A. Stefan Zavala ## <astefanz@berkeley.edu>   ##                 ##
## Chris J. Dougherty         ## <cdougher@caltech.edu>    ##                 ##
## Marcel Veismann            ## <mveisman@caltech.edu>    ##                 ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Terminal output for the FC Tkinter GUI
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import os
import time as tm

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.theme import TEXT_ON_DARK, SUCCESS_MAIN, WARNING_MAIN, ERROR_MAIN, INFO_MAIN
from fc import printer as pt

## GLOBALS #####################################################################

# Message tags (for styles):
TAG_REGULAR = "R"
TAG_SUCCESS = "S"
TAG_WARNING = "W"
TAG_ERROR = "E"
TAG_DEBUG = "D"

# Background and foreground colors:
FG_DEFAULT = TEXT_ON_DARK

FG_REGULAR = FG_DEFAULT
FG_SUCCESS = SUCCESS_MAIN
FG_WARNING = WARNING_MAIN
FG_ERROR = TEXT_ON_DARK
FG_DEBUG = INFO_MAIN

BG_DEFAULT = gus.SURFACE_5  # Dark console background from theme
BG_SELECT = gus.PRIMARY_100
BG_REGULAR = BG_DEFAULT
BG_SUCCESS = BG_DEFAULT
BG_WARNING = BG_DEFAULT
BG_ERROR = ERROR_MAIN
BG_DEBUG = BG_DEFAULT


## WIDGET ######################################################################
class ConsoleWidget(tk.Frame):
    """
    Simple terminal-like interface for text output. Mimics fc.utils print
    functions.
    """
    symbol = "[CS]"

    def __init__(self, master, warnMethod):
        tk.Frame.__init__(self, master)
        self.master = master
        self.warn = warnMethod

        self.background = BG_DEFAULT
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        # Build output text field:
        screen_conf = dict(gus.text_conf)
        screen_conf["fg"] = FG_DEFAULT
        screen_conf["bg"] = self.background
        screen_conf["selectbackground"] = BG_SELECT
        screen_conf["state"] = tk.DISABLED
        self.screen = tk.Text(self, **screen_conf)
        self.scrollbar = tk.Scrollbar(self)
        self.scrollbar.grid(row = 0, column = 1, sticky = "NS")
        self.scrollbar.config(command=self.screen.yview)
        self.screen.config(yscrollcommand = self.scrollbar.set)
        self.screen.bind("<1>",
            lambda event: self.screen.focus_set())
        self.screen.grid(row = 0, column = 0, sticky = "NEWS")

        # Configure tags:
        self.screen.tag_config(TAG_REGULAR)
        self.screen.tag_config(TAG_SUCCESS, foreground = FG_SUCCESS)
        self.screen.tag_config(TAG_WARNING,foreground = FG_WARNING)
        self.screen.tag_config(TAG_ERROR,
            foreground = FG_ERROR, background = BG_ERROR)
        self.screen.tag_config(TAG_DEBUG, foreground = FG_DEBUG)

        # Build buttons:
        self.controlFrame = tk.Frame(self)
        self.controlFrame.grid(row = 1, column = 0, columnspan = 2,
            sticky = "EW")

        # Print out button:
        self.saveButton = ttk.Button(self.controlFrame, text = "Print to File",
            command = self._save)
        self.saveButton.pack(side = tk.RIGHT)

        # Clear functionality:
        self.clearButton = ttk.Button(self.controlFrame, text = "Clear",
            command = self._clear, style = "Secondary.TButton")
        self.clearButton.pack(side = tk.RIGHT)

        # Debug button:
        self.debugVar = tk.IntVar()
        self.debugVar.set(0)

        self.debugButton = tk.Checkbutton(self.controlFrame,
            text ="Debug prints", variable = self.debugVar,
            command = self._debug, **gus.cb_primary)
        self.debugButton.pack(side = tk.RIGHT)

        # Autoscroll button:
        self.autoscrollVar = tk.IntVar()
        self.autoscrollVar.set(1)
        self.autoscrollButton = tk.Checkbutton(self.controlFrame,
            text ="Autoscroll", variable = self.autoscrollVar, **gus.cb_primary)
        self.autoscrollButton.pack(side = tk.RIGHT)

    # API ----------------------------------------------------------------------
    def printr(self, message):
        self._print(TAG_REGULAR, message)

    def printw(self, message):
        self._print(TAG_WARNING, message)

    def printe(self, message):
        self._print(TAG_ERROR, message)

    def prints(self, message):
        self._print(TAG_SUCCESS, message)

    def printd(self, message):
        if self.debugVar.get():
            self._print(TAG_DEBUG, message)

    def printx(self, message):
        self._print(TAG_ERROR, message)

    # Internal methods ---------------------------------------------------------
    def _print(self, tag, text):
        """
        Generic print method. To be used internally.
        """
        try:

            # Switch focus to this tab in case of errors of warnings:
            if tag is TAG_ERROR and not self.winfo_ismapped():
                self.warn()

            self.screen.config(state = tk.NORMAL)
            self.screen.insert(tk.END, text + "\n", tag)
            self.screen.config(state = tk.DISABLED)

            # Check for auto scroll:
            if self.autoscrollVar.get() == 1:
                self.screen.see("end")
        except Exception as e:
            gus.popup_exception("FCMkIV Error", "Exception in console printer",
                e)
        return

    def _save(self, *E):
        """
        Callback to save the current contents to a text file.
        """
        try:
            # Get file
            filename = tk.filedialog.asksaveasfilename(
                initialdir = os.getcwd(), # Get current working directory
                initialfile = "FCMkIV_console_log_{}.txt".format(
                        tm.strftime("%a_%d_%b_%Y_%H-%M-%S",
                            tm.localtime())),
                title = "Choose file",
                filetypes = (("Text files","*.txt"),
                    ("All files","*.*")))
            if not filename:
                self.printd("[Terminal print-to-file canceled (no filename)]")
            else:
                with open(filename, 'w') as f:
                    f.write("Fan Club MkIV Terminal log printed on {}\n\n".\
                        format(tm.strftime("%a %d %b %Y %H:%M:%S",
                                tm.localtime())))
                    f.write(self.screen.get(1.0, tk.END))
        except Exception as e:
            gus.popup_exception("FCMKIV Error",
                "Exception in Terminal print-to-file", e)

    def _clear(self, *E):
        self.screen.config(state = tk.NORMAL)
        self.screen.delete(1.0, tk.END)
        self.screen.config(state = tk.DISABLED)
        self.printr(self.symbol + " Console cleared")

    def _debug(self, *E):
        if self.debugVar.get() == 1:
            pt.DEBUGP = True
        else:
            pt.DEBUGP = False
