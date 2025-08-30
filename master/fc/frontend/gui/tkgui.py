################################################################################
## Project: Fanclub Mark IV "Master"  ## File: tkgui.py                       ##
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
 + Tkinter-based Fan Club GUI.
 +
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import tkinter as tk
import tkinter.ttk as ttk

from fc import printer as pt, utils as us
from fc.frontend import frontend as fe
from fc.frontend.gui.widgets import splash as spl, base as bas
import fc.frontend.gui.embedded.icon as icn
from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.theme import SURFACE_2, TEXT_PRIMARY, SURFACE_1, SURFACE_3, PRIMARY_500, PRIMARY_600, TEXT_SECONDARY

## GLOBALS #####################################################################
TITLE = "FC MkIV"
SPLASH_SECONDS = 4

################################################################################
class FCGUI(fe.FCFrontend):
    SYMBOL = "[GI]"

    def __init__(self, archive, pqueue):
        """
        Build a new FCGUI using PQUEUE for printing and ARCHIVE (FCArchive) to
        manage profile data.
        NOTE: The Tkinter root will be created here, and hence visible without
        assembly.

        Optional argument PERIOD sets the seconds between sentinel cycles (i.e
        periodic checks to distribute inter-process data and print messages.)
        defaults to fc.interface.SENTINEL_PERIOD.
        """
        fe.FCFrontend.__init__(self, archive, pqueue)
        self.base = None

        # Fix Windows DPI ......................................................
        if self.platform is us.WINDOWS:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)

        # Build GUI ............................................................
        # Splash:
        splash = spl.SerialSplash(version = "0")
        splash.run(SPLASH_SECONDS)

        # GUI:
        self.root = tk.Tk()
        
        # Apply modern window styling
        self._configure_modern_window()
        
        title = TITLE + " " + self.version
        base = bas.Base(self.root, self.network, self.external, self.mapper,
            self.archive, title, self.version, self.addFeedbackClient,
            self.addNetworkClient, self.addSlaveClient, self._onProfileChange,
            setLive = self.setLive, setF = self.altFeedbackIn,
            pqueue = self.pqueue)
        base.pack(fill = tk.BOTH, expand = True)
        self._setPrintMethods(base)
        self.archiveClient(base)
        self.network.connect()
        base.focusControl()

    def _mainloop(self):
        """
        Overriden. Build GUI and run main loop. See base class.
        """
        self.root.mainloop()

    def print(self, code, text):
        """
        Overriden. See fc.utils.PrintServer.
        """
        self.outputs[code](text)

    # Overriding sentinel thread implementation --------------------------------
    def _setPrintMethods(self, base):
        """
        Get the print methods from the base widgets. Placed here to keep build
        code clean.
        """
        self.outputs = {}
        self.outputs[pt.R], self.outputs[pt.W], self.outputs[pt.E], \
            self.outputs[pt.S], self.outputs[pt.D], self.outputs[pt.X] = \
            base.getConsoleMethods()

    def _configure_modern_window(self):
        """Apply modern styles to the main window."""
        try:
            self.root.configure(bg=SURFACE_2)
            self.root.option_add("*Font", gus.typography["body_medium"]["font"])  
            self.root.option_add("*Foreground", TEXT_PRIMARY)
            self.root.option_add("*Background", SURFACE_2)
            self.root.option_add("*Button.background", gus.btn_primary["bg"])
            self.root.option_add("*Button.foreground", gus.btn_primary["fg"]) 
            self.root.option_add("*Entry.background", gus.entry_conf["bg"]) 
            self.root.option_add("*Entry.foreground", gus.entry_conf["fg"]) 
            
            # Initialize ttk modern style
            self._setup_ttk_style()
        except Exception:
            pass

    def _setup_ttk_style(self):
        """Configure ttk styles for a more modern, cohesive look."""
        try:
            style = ttk.Style(self.root)
            # Use a platform-neutral base theme
            try:
                style.theme_use("clam")
            except Exception:
                pass

            # Base palette
            base_bg = SURFACE_2
            card_bg = SURFACE_1
            accent = PRIMARY_500
            accent_hover = PRIMARY_600
            fg = TEXT_PRIMARY
            fg_muted = TEXT_SECONDARY

            # Global element sizes
            style.configure("TLabel", background=base_bg, foreground=fg)
            style.configure("TFrame", background=base_bg)
            style.configure("TPanedwindow", background=base_bg)

            # New: secondary label style for muted text
            style.configure("Secondary.TLabel", background=base_bg, foreground=fg_muted)

            # New: warning label style for alerts
            style.configure("Warning.TLabel", background=base_bg, foreground=gus.WARNING_MAIN)

            # New: label style with Surface 3 background
            style.configure("Surface3.TLabel", background=SURFACE_3, foreground=fg)

            # New: label style with Surface 1 background
            style.configure("Surface1.TLabel", background=SURFACE_1, foreground=fg)

            # New: sunken label style for status displays
            style.configure("Sunken.TLabel", background=base_bg, foreground=fg, relief="sunken", borderwidth=1, padding=(6, 5))

            # Buttons
            style.configure(
                "TButton",
                background=accent,
                foreground=gus.btn_primary.get("fg", "white"),
                padding=(10, 6),
                borderwidth=0,
                focusthickness=0
            )
            style.map(
                "TButton",
                background=[("active", accent_hover), ("pressed", accent_hover)],
                relief=[("pressed", "flat"), ("!pressed", "flat")]
            )

            # Secondary button style alias
            style.configure(
                "Secondary.TButton",
                background=card_bg,
                foreground=fg,
                padding=(10, 6),
                borderwidth=1
            )

            # Entries
            style.configure(
                "TEntry",
                fieldbackground=gus.entry_conf.get("bg", card_bg),
                background=gus.entry_conf.get("bg", card_bg),
                foreground=gus.entry_conf.get("fg", fg),
                padding=6,
                borderwidth=1
            )
            # Focus/disabled mapping for Entry
            style.map(
                "TEntry",
                fieldbackground=[("focus", card_bg)],
                foreground=[("disabled", fg_muted)],
                bordercolor=[("focus", accent)] if hasattr(ttk, "Style") else []
            )

            # Treeview
            style.configure(
                "Treeview",
                background=card_bg,
                fieldbackground=card_bg,
                foreground=fg,
                rowheight=22,
                borderwidth=0
            )
            style.configure(
                "Treeview.Heading",
                background=base_bg,
                foreground=fg,
                relief="flat",
                padding=(8, 6)
            )
            # Selection colors for Treeview rows
            style.map(
                "Treeview",
                background=[("selected", accent)],
                foreground=[("selected", gus.btn_primary.get("fg", "white"))]
            )

            # Notebook (tabs)
            style.configure(
                "TNotebook",
                background=base_bg,
                borderwidth=0
            )
            style.configure(
                "TNotebook.Tab",
                background=base_bg,
                foreground=fg_muted,
                padding=(12, 6)
            )
            style.map(
                "TNotebook.Tab",
                background=[("selected", card_bg)],
                foreground=[("selected", fg)]
            )

            # Checkbutton
            style.configure(
                "TCheckbutton",
                background=base_bg,
                foreground=fg,
                padding=(6, 4)
            )

            # Scrollbar & Separator for cleaner look
            style.configure("TScrollbar", background=card_bg)
            style.configure("TSeparator", background=SURFACE_3)
        except Exception:
            # Fail silently to avoid blocking UI due to styling errors
            pass
