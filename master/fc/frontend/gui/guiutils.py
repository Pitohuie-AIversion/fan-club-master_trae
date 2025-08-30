################################################################################
## Project: Fanclub Mark IV "Master"              ## File: guiutils.py        ##
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
 + Auxiliary tools for GUI.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import sys
import os
import traceback

import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

# Import comprehensive modern design system
from fc.frontend.gui.theme import (
    # Legacy compatibility
    BG_CT, BG_ACCENT, BG_ERROR, FG_ERROR, BG_SUCCESS, BG_WARNING, 
    BG_LIGHT, FG_PRIMARY, FG_SECONDARY,
    # Modern color system
    PRIMARY_50, PRIMARY_100, PRIMARY_200, PRIMARY_300, PRIMARY_400, PRIMARY_500, 
    PRIMARY_600, PRIMARY_700, PRIMARY_800, PRIMARY_900,
    ACCENT_LIGHT, ACCENT_MAIN, ACCENT_DARK,
    SUCCESS_LIGHT, SUCCESS_MAIN, SUCCESS_DARK,
    ERROR_LIGHT, ERROR_MAIN, ERROR_DARK,
    WARNING_LIGHT, WARNING_MAIN, WARNING_DARK,
    INFO_LIGHT, INFO_MAIN, INFO_DARK,
    SURFACE_1, SURFACE_2, SURFACE_3, SURFACE_4, SURFACE_5,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_DISABLED, TEXT_ON_PRIMARY, TEXT_ON_DARK,
    RADIUS_SMALL, RADIUS_MEDIUM, RADIUS_LARGE, RADIUS_EXTRA_LARGE
)

## MODERN DESIGN SYSTEM ########################################################
# Typography scale
typography = {
    "headline_large": {"font": ("Segoe UI", 14, "bold")},
    "headline_medium": {"font": ("Segoe UI", 12, "bold")},
    "headline_small": {"font": ("Segoe UI", 11, "bold")},
    "title_large": {"font": ("Segoe UI", 10, "bold")},
    "title_medium": {"font": ("Segoe UI", 9, "bold")},
    "title_small": {"font": ("Segoe UI", 8, "bold")},
    "body_large": {"font": ("Segoe UI", 10, "normal")},
    "body_medium": {"font": ("Segoe UI", 9, "normal")},
    "body_small": {"font": ("Segoe UI", 8, "normal")},
    "label_large": {"font": ("Segoe UI", 9, "normal")},
    "label_medium": {"font": ("Segoe UI", 8, "normal")},
    "label_small": {"font": ("Segoe UI", 7, "normal")},
    "code": {"font": ("Consolas", 9, "normal")}
}

# Spacing system
spacing = {
    "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32
}

# Enhanced padding configurations
pad_xs = {"padx": spacing["xs"], "pady": spacing["xs"]}
pad_sm = {"padx": spacing["sm"], "pady": spacing["sm"]}
pad_md = {"padx": spacing["md"], "pady": spacing["md"]}
pad_lg = {"padx": spacing["lg"], "pady": spacing["lg"]}

# Legacy compatibility
efont = typography["code"]
fontc = typography["body_medium"]
padc = pad_sm
lfconf = {**fontc, **padc}
lfpack = {"side":tk.TOP, "anchor":tk.N, "fill":tk.X, "expand":True}
rbconf = {"indicatoron":False, **fontc, **padc}

# Modern button styles with enhanced visual hierarchy
btn_primary = {
    "bg": PRIMARY_500, 
    "fg": TEXT_ON_PRIMARY, 
    "activebackground": PRIMARY_600, 
    "activeforeground": TEXT_ON_PRIMARY, 
    "relief": "flat", 
    "borderwidth": 0,
    "cursor": "hand2",
    **typography["label_large"],
    **pad_md
}

btn_secondary = {
    "bg": SURFACE_3, 
    "fg": TEXT_PRIMARY, 
    "activebackground": SURFACE_4, 
    "activeforeground": TEXT_PRIMARY, 
    "relief": "flat", 
    "borderwidth": 1,
    "highlightthickness": 1,
    "highlightcolor": PRIMARY_300,
    "highlightbackground": SURFACE_4,
    "cursor": "hand2",
    **typography["label_large"],
    **pad_md
}

btn_accent = {
    "bg": ACCENT_MAIN, 
    "fg": TEXT_ON_DARK, 
    "activebackground": ACCENT_DARK, 
    "activeforeground": TEXT_ON_DARK, 
    "relief": "flat", 
    "borderwidth": 0,
    "cursor": "hand2",
    **typography["label_large"],
    **pad_md
}

btn_success = {
    "bg": SUCCESS_MAIN, 
    "fg": TEXT_ON_DARK, 
    "activebackground": SUCCESS_DARK, 
    "activeforeground": TEXT_ON_DARK, 
    "relief": "flat", 
    "borderwidth": 0,
    "cursor": "hand2",
    **typography["label_large"],
    **pad_md
}

btn_error = {
    "bg": ERROR_MAIN, 
    "fg": TEXT_ON_DARK, 
    "activebackground": ERROR_DARK, 
    "activeforeground": TEXT_ON_DARK, 
    "relief": "flat", 
    "borderwidth": 0,
    "cursor": "hand2",
    **typography["label_large"],
    **pad_md
}

btn_warning = {
    "bg": WARNING_MAIN, 
    "fg": TEXT_ON_DARK, 
    "activebackground": WARNING_DARK, 
    "activeforeground": TEXT_ON_DARK, 
    "relief": "flat", 
    "borderwidth": 0,
    "cursor": "hand2",
    **typography["label_large"],
    **pad_md
}

# Enhanced input field styles
entry_conf = {
    "bg": SURFACE_1, 
    "fg": TEXT_PRIMARY, 
    "insertbackground": PRIMARY_500,
    "selectbackground": PRIMARY_100,
    "selectforeground": TEXT_PRIMARY,
    "relief": "flat",
    "borderwidth": 2,
    "highlightthickness": 2,
    "highlightcolor": PRIMARY_500,
    "highlightbackground": SURFACE_4,
    **typography["body_medium"]
}

# Enhanced label styles
label_conf = {
    "bg": SURFACE_2, 
    "fg": TEXT_PRIMARY,
    **typography["body_medium"]
}

label_primary = {
    "bg": SURFACE_2, 
    "fg": TEXT_PRIMARY,
    **typography["title_medium"]
}

label_secondary = {
    "bg": SURFACE_2, 
    "fg": TEXT_SECONDARY,
    **typography["body_small"]
}

# Enhanced frame styles
labelframe_conf = {
    "bg": SURFACE_2,
    "fg": TEXT_PRIMARY,
    **typography["title_small"]
}

frame_primary = {"bg": SURFACE_1}
frame_secondary = {"bg": SURFACE_2}
frame_accent = {"bg": SURFACE_3}

# Enhanced text widget styles
text_conf = {
    "bg": SURFACE_1, 
    "fg": TEXT_PRIMARY, 
    "insertbackground": PRIMARY_500,
    "selectbackground": PRIMARY_100,
    "selectforeground": TEXT_PRIMARY,
    "relief": "flat",
    "borderwidth": 1,
    "highlightthickness": 1,
    "highlightcolor": PRIMARY_300,
    "highlightbackground": SURFACE_4,
    **typography["code"]
}

# Enhanced radiobutton styles
rb_primary = {
    "indicatoron": False,
    "bg": SURFACE_3,
    "fg": TEXT_PRIMARY,
    "activebackground": PRIMARY_100,
    "activeforeground": TEXT_PRIMARY,
    "selectcolor": PRIMARY_500,
    "relief": "flat",
    "borderwidth": 1,
    "highlightthickness": 0,
    "cursor": "hand2",
    **typography["label_medium"],
    **pad_sm
}

# Enhanced checkbutton styles  
cb_primary = {
    "bg": SURFACE_2,
    "fg": TEXT_PRIMARY,
    "activebackground": SURFACE_3,
    "activeforeground": TEXT_PRIMARY,
    "selectcolor": PRIMARY_500,
    "relief": "flat",
    "borderwidth": 0,
    "highlightthickness": 0,
    "cursor": "hand2",
    **typography["label_medium"]
}

def silent(message):
    """
    Provisional replacement for inter-process prints.
    """
    print("[SILENCED]", message)

def default_printr(message):
    """
    Provisional replacement for inter-process printr. (See fc.utils)
    """
    print("[GP]", message)

def default_printx(e, message):
    """
    Provisional replacement for inter-process printx. (See fc.utils)
    """
    print("[GP]", message, e)

def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.
    e.g.
            Logo = resource_path("Logo.png")
    Source:
        https://stackoverflow.com/questions/31836104/
        pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def popup_exception(title, message, exception):
    """
    Build a popup with TITLE, displaying MESSAGE and the traceback on EXCEPTION.
    """
    messagebox.showerror(title = title,
        message = message + "\n\nException:\"{}\"".format(
            traceback.format_exc()))

class PromptLabel(tk.Label):
    """
    A Tkinter Label that creates a popup window requesting a value when
    it is clicked. Besides its required arguments upon construction, it may
    be handled like a regular Tkinter Label.

    NOTE: Do not bind callbacks to this widget upon left click (<Button-1>),
    for this will interfere with the prompt behavior. Instead, incorporate
    the desired behavior into the "callback" method to be passed upon
    construction.
    """

    DIALOGMETHOD = simpledialog.askstring
    N = lambda: ""

    ACTIVE_BG = SURFACE_1
    INACTIVE_BG = SURFACE_2

    def __init__(self, master, title, prompt, callback, starter = "", **kwargs):
        """
        Create a new PromptLabel.
        - master := Tkinter parent widget
        - title := String, title to display in popup window
        - prompt := String, text to write in popup window to request input
        - callback := Function to be called when a new input is given; such
            new input will be passed to it
        - starter := method that returns a String when called without arguments;
            the String is to be used as a starting value for the text entry.
            Defaults to a method that returns an empty String.
        Additionally, all optional keyword arguments accepted by Tkinter
        Labels may be used.
        """
        tk.Label.__init__(self, master, **kwargs)

        self.title = title
        self.prompt = prompt
        self.starter = starter

        self.callback = callback
        self.bind("<Button-1>", self._onClick)

        self.enable()

    def _onClick(self, event = None):
        """
        Handle left click event. Generates prompt and passed its result to the
        given callback.
        """
        if self.enabled:
            self.callback(PromptLabel.DIALOGMETHOD(self.title, self.prompt,
                initialvalue = self.starter(), parent = self.winfo_toplevel()))

    def enable(self):
        """
        Enable the widget's interactive behavior. This is the default state.
        """
        self.enabled = True
        self.config(bg = self.ACTIVE_BG)

    def disable(self):
        """
        Disable the widget's interactive behavior.
        """
        self.enabled = False
        self.config(bg = self.INACTIVE_BG)


def _validateN(newCharacter, textBeforeCall, action):
    try:
        return action == '0' or  newCharacter in '0123456789' or \
            int(newCharacter) > 0
    except:
        return False

def _validateF(newCharacter, textBeforeCall, action):
    try:
        return action == '0' or  newCharacter in '.0123456789' or \
            float(newCharacter) > 0 and float(newCharacter) <= 100
    except:
        return False

