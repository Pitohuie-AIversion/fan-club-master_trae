################################################################################
## Project: Fanclub Mark IV "Master" GUI          ## File: console.py         ##
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
from fc.frontend.gui.theme import TEXT_ON_DARK, SUCCESS_MAIN, WARNING_MAIN, ERROR_MAIN, INFO_MAIN, TEXT_PRIMARY, SURFACE_1
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
class ConsoleWidget(ttk.Frame):
    """
    Simple terminal-like interface for text output. Mimics fc.utils print
    functions.
    """
    symbol = "[CS]"

    def __init__(self, master, warnMethod):
        ttk.Frame.__init__(self, master)
        self.master = master
        self.warn = warnMethod

        self.background = BG_DEFAULT
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight = 1)

        # Build output text field - keeping tk.Text as ttk doesn't have Text equivalent
        # But applying modern styling
        screen_conf = dict(gus.text_conf)
        screen_conf["fg"] = FG_DEFAULT
        screen_conf["bg"] = self.background
        screen_conf["selectbackground"] = BG_SELECT
        screen_conf["state"] = tk.DISABLED
        screen_conf["insertbackground"] = FG_DEFAULT  # Cursor color
        screen_conf["selectforeground"] = TEXT_PRIMARY  # Selection text color
        screen_conf["relief"] = tk.FLAT
        screen_conf["borderwidth"] = 0
        screen_conf["highlightthickness"] = 0
        
        # Note: tk.Text is kept as ttk doesn't provide Text widget
        self.screen = tk.Text(self, **screen_conf)
        self.scrollbar = ttk.Scrollbar(self)
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

        # Build toolbar separator and toolbar frame (modern look):
        try:
            self.toolbarSeparator = ttk.Separator(self, orient="horizontal")
            self.toolbarSeparator.grid(row = 1, column = 0, columnspan = 2, sticky = "EW")
        except Exception:
            pass

        # Build buttons (use ttk styles for cohesive UI):
        self.controlFrame = ttk.Frame(self, style="Topbar.TFrame")
        self.controlFrame.grid(row = 2, column = 0, columnspan = 2,
            sticky = "EW")

        # Save log button:
        self.saveButton = ttk.Button(self.controlFrame, text = "Save Log",
            command = self._save)
        self.saveButton.pack(side = tk.RIGHT, padx=6, pady=4)

        # Clear functionality:
        self.clearButton = ttk.Button(self.controlFrame, text = "Clear",
            command = self._clear, style="Secondary.TButton")
        self.clearButton.pack(side = tk.RIGHT, padx=6, pady=4)

        # Copy button (copies selection, or all if none selected):
        self.copyButton = ttk.Button(self.controlFrame, text = "Copy",
            command = self._copy, style="Secondary.TButton")
        self.copyButton.pack(side = tk.RIGHT, padx=6, pady=4)

        # Debug toggle:
        self.debugVar = tk.IntVar()
        self.debugVar.set(0)
        self.debugButton = ttk.Checkbutton(self.controlFrame,
            text ="Debug prints", variable = self.debugVar,
            command = self._debug)
        self.debugButton.pack(side = tk.RIGHT, padx=6, pady=4)

        # Autoscroll toggle:
        self.autoscrollVar = tk.IntVar()
        self.autoscrollVar.set(1)
        self.autoscrollButton = ttk.Checkbutton(self.controlFrame,
            text ="Autoscroll", variable = self.autoscrollVar)
        self.autoscrollButton.pack(side = tk.RIGHT, padx=6, pady=4)

        # Max lines cap:
        self.maxLinesVar = tk.IntVar()
        self.maxLinesVar.set(5000)
        try:
            self.maxLinesSpin = ttk.Spinbox(self.controlFrame, from_=500, to=200000,
                increment=500, width=7, textvariable=self.maxLinesVar)
            self.maxLinesLabel = ttk.Label(self.controlFrame, text=" Max Lines:")
            self.maxLinesSpin.pack(side=tk.RIGHT, padx=6, pady=4)
            self.maxLinesLabel.pack(side=tk.RIGHT, padx=0, pady=4)
        except Exception:
            # Fallback without crashing if ttk.Spinbox unavailable
            try:
                self.maxLinesSpin = tk.Spinbox(self.controlFrame, from_=500, to=200000,
                    increment=500, width=7, textvariable=self.maxLinesVar)
                self.maxLinesLabel = ttk.Label(self.controlFrame, text=" Max Lines:")
                self.maxLinesSpin.pack(side=tk.RIGHT, padx=6, pady=4)
                self.maxLinesLabel.pack(side=tk.RIGHT, padx=0, pady=4)
            except Exception:
                self.maxLinesVar.set(5000)
        
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
            # Check if the widget still exists before proceeding
            if not self.winfo_exists() or not hasattr(self, 'screen') or not self.screen.winfo_exists():
                return

            # Switch focus to this tab in case of errors of warnings:
            if tag == TAG_ERROR and not self.winfo_ismapped():
                self.warn()

            # Determine if we are currently at bottom before insertion
            was_at_bottom = self._is_at_bottom()

            self.screen.config(state = tk.NORMAL)
            self.screen.insert(tk.END, text + "\n", tag)
            # Trim to max lines after insertion
            self._trim_to_max_lines()
            self.screen.config(state = tk.DISABLED)

            # Check for auto scroll: scroll if Autoscroll enabled or we were at bottom
            if self.autoscrollVar.get() == 1 or was_at_bottom:
                self.screen.see("end")
        except tk.TclError:
            # Widget has been destroyed, silently ignore
            pass
        except Exception as e:
            # Only show popup for non-Tkinter errors
            try:
                gus.popup_exception("FCMkIV Error", "Exception in console printer", e)
            except:
                # If even the popup fails, just ignore
                pass
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

    def _copy(self, *E):
        try:
            selection = None
            try:
                selection = self.screen.get(tk.SEL_FIRST, tk.SEL_LAST)
            except Exception:
                # No selection
                selection = self.screen.get(1.0, tk.END)
            if selection:
                self.clipboard_clear()
                self.clipboard_append(selection)
                self.printd(self.symbol + " Copied to clipboard")
        except Exception as e:
            gus.popup_exception("FCMKIV Error",
                "Exception in Console copy-to-clipboard", e)

    def _debug(self, *E):
        if self.debugVar.get() == 1:
            pt.DEBUGP = True
        else:
            pt.DEBUGP = False

    # Utilities ----------------------------------------------------------------
    def _is_at_bottom(self):
        try:
            # Check if the widget still exists
            if not self.winfo_exists() or not hasattr(self, 'screen') or not self.screen.winfo_exists():
                return True
            
            lo, hi = self.screen.yview()
            # hi == 1.0 indicates bottom; use tolerance for floating errors
            return abs(hi - 1.0) < 1e-3
        except tk.TclError:
            # Widget has been destroyed
            return True
        except Exception:
            return True

    def _trim_to_max_lines(self):
        try:
            # Check if the widget still exists
            if not self.winfo_exists() or not hasattr(self, 'screen') or not self.screen.winfo_exists():
                return
                
            max_lines = int(self.maxLinesVar.get()) if self.maxLinesVar else 0
            if max_lines and max_lines > 0:
                # Total number of lines (end index is one past last char)
                end_index = self.screen.index('end-1c')  # exclude trailing newline
                total_lines = int(end_index.split('.')[0]) if end_index else 1
                if total_lines > max_lines:
                    # Compute how many lines to delete from the top
                    excess = total_lines - max_lines
                    # Delete from line 1.0 up to (excess+1).0 to remove full lines
                    self.screen.delete('1.0', f'{excess + 1}.0')
        except tk.TclError:
            # Widget has been destroyed, silently ignore
            pass
        except Exception:
            # Do not crash on trimming errors
            pass
