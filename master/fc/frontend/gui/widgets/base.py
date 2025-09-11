################################################################################
## Project: Fanclub Mark IV "Master" base window  ## File: base.py            ##
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
 + Basic container for all other FC GUI widgets.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import time as tm
import tkinter as tk
import tkinter.ttk as ttk

from fc.frontend.gui import guiutils as gus
from fc.frontend.gui.widgets import network as ntw, control as ctr, \
    profile as pro, console as csl
# from fc.frontend.gui.embedded import caltech_white as cte
from fc.frontend.gui.embedded import brand_zd as bzd
import fc.frontend.gui.embedded.icon as icn
from fc import printer as pt, utils as us
from fc.frontend.gui.animations import AnimationManager, animate_color_transition, ease_in_out_cubic
from fc.frontend.gui.responsive import ResponsiveLayoutManager, ResponsiveMixin
from fc.frontend.gui.visual_effects import initialize_visual_effects
from fc.frontend.gui.performance import initialize_performance_optimization
from fc.frontend.gui.ux_enhancements import initialize_ux_enhancements

## AUXILIARY GLOBALS ###########################################################
# Import theme colors
from fc.frontend.gui.theme import (
    BG_CT, BG_ACCENT, BG_ERROR, FG_ERROR, BG_SUCCESS, BG_WARNING,
    BG_LIGHT, FG_PRIMARY, FG_SECONDARY, SURFACE_2
)
from fc.frontend.gui.theme_manager import theme_manager

NOPE = lambda m: print("[SILENCED]: ", m)

## MAIN ########################################################################
class Base(ttk.Frame, ResponsiveMixin):

    ERROR_MESSAGE = \
        "[There are error messages in the console. Click here.]"

    SYMBOL = "[BS]"

    def __init__(self, master, network, external, mapper, archive, title,
        version, feedbackAdd, networkAdd, slavesAdd, profileCallback,
        setLive, setF, pqueue):
        """
        Create a new GUI base on the Tkinter root MASTER, with title TITLE and
        showing the version VERSION.

        Parameters:
        - master: Tkinter root window
        - network: Network backend instance
        - external: External control backend instance
        - mapper: Grid mapper instance
        - archive: Configuration archive instance
        - title: Window title string
        - version: Software version string
        - feedbackAdd: Method to register feedback vector clients
        - networkAdd: Method to register network vector clients
        - slavesAdd: Method to register slave vector clients
        - profileCallback: Method called when profile changes
        - setLive: Method to set live mode
        - setF: Method to set feedback vector
        - pqueue: Queue object for inter-process printing
        """
        ttk.Frame.__init__(self, master = master)
        pt.PrintClient.__init__(self, pqueue, self.SYMBOL)
        ResponsiveMixin.__init__(self)

        # Streamlined GUI printing setup
        self.pqueue = pqueue

        # Core setup -----------------------------------------------------------
        self.network = network
        self.external = external
        self.mapper = mapper
        self.archive = archive
        self.feedbackAdd = feedbackAdd
        self.networkAdd = networkAdd
        self.slavesAdd = slavesAdd

        self.setLive, self.setF = setLive, setF
        
        # Initialize animation manager
        self.animation_manager = AnimationManager(self)
        
        # Initialize responsive layout manager
        self.responsive_manager = ResponsiveLayoutManager(self.master)
        
        # Initialize visual effects manager
        self.visual_effects = initialize_visual_effects(self.master)
        
        # Initialize performance optimization manager
        self.performance_manager = initialize_performance_optimization(self.master)
        
        # Initialize UX enhancements manager
        self.ux_manager = initialize_ux_enhancements(self.master, "FanClub")
        
        # Setup UX callbacks
        self._setup_ux_callbacks()
        
        # Initialize UI density setting
        self._ui_density = 'comfortable'  # Default to comfortable density

        self.screenWidth = self.master.winfo_screenwidth()
        self.screenHeight = self.master.winfo_screenheight()

        self.winfo_toplevel().title(title)
        
        # Modern base background to match theme surfaces
        try:
            self.configure(background=SURFACE_2)
        except Exception:
            pass
        
        # Set window icon
        try:
            self.icon = tk.PhotoImage(data=icn.ICON)
            self.winfo_toplevel().iconphoto(True, self.icon)
        except Exception as e:
            self.printd(f"Could not set window icon: {e}")

        """
        self.winfo_toplevel().geometry("{}x{}".format(
            self.screenWidth//2, self.screenHeight//2))
        """

        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(1, weight = 1)

        self.version = version
        # Containers -----------------------------------------------------------

        # Top bar ..............................................................
        self.topBar = ttk.Frame(self, style="Topbar.TFrame", padding=(12, 8))
        self.topBar.grid(row = 0, sticky = 'EW')

        # Brand icon using embedded PNG (no dependencies required)
        try:
            from fc.frontend.gui.embedded import brand_zd_png as bzd_png
            
            # Load pre-rendered PNG from base64
            self.brandImage = tk.PhotoImage(data=bzd_png.PNG_B64)
            self.brandLabel = ttk.Label(self.topBar, image=self.brandImage, style="Topbar.TLabel")
            self.brandLabel.pack(side = tk.LEFT, ipady = 0, pady=(0,0), padx = 10)
            print("Brand image loaded from embedded PNG successfully")
            
        except Exception as e:
            # High-contrast fallback text; log the cause
            try:
                self.printd(f"Brand PNG loading failed: {e}, falling back to text")
            except Exception:
                pass
            self.brandLabel = ttk.Label(self.topBar, text="ZHAOYANG · DASHUAI", style="Topbar.TLabel")
            self.brandLabel.pack(side = tk.LEFT, ipady = 0, pady=(0,0), padx = 10)
        self.errorLabel = ttk.Label(self.topBar, text=self.ERROR_MESSAGE, style="ErrorBanner.TLabel")
        self.errorLabel.bind("<Button-1>", self.focusConsole)
        self.warning = False

        self.topWidgets = []

        # Settings menu
        self.settingsButton = ttk.Button(self.topBar, text=" Settings ",
            command=self._settingsCallback, style="Secondary.TButton")
        self.settingsButton.pack(side=tk.RIGHT, padx=6, pady=8)
        self.topWidgets.append(self.settingsButton)
        
        # Help:
        # self.helpButton = tk.Button(self.topBar, text=" Help ", 
        #     command=self._helpCallback, **gus.btn_primary)
        self.helpButton = ttk.Button(self.topBar, text=" Help ",
            command=self._helpCallback, style="Secondary.TButton")
        self.helpButton.pack(side=tk.RIGHT, padx=6, pady=8)
        self.topWidgets.append(self.helpButton)

        # Subtle divider at the bottom of top bar for hierarchy
        try:
            self.topSeparator = ttk.Separator(self.topBar, orient="horizontal")
            self.topSeparator.pack(side=tk.BOTTOM, fill=tk.X)
        except Exception:
            pass

        # Notebook .............................................................
        self.notebook = ttk.Notebook(self)
        # self.profileTab = tk.Frame(self.notebook, bg=BG_LIGHT)
        # self.networkTab = tk.Frame(self.notebook, bg=BG_LIGHT)
        # self.controlTab = tk.Frame(self.notebook, bg=BG_LIGHT)
        # self.consoleTab = tk.Frame(self.notebook, bg=BG_LIGHT)
        self.profileTab = ttk.Frame(self.notebook)
        self.networkTab = ttk.Frame(self.notebook)
        self.controlTab = ttk.Frame(self.notebook)
        self.consoleTab = ttk.Frame(self.notebook)

        # Profile tab:
        self.profileCard = ttk.Frame(self.profileTab, style="Card.TFrame")
        self.profileCard.pack(fill = tk.BOTH, expand = True, padx = 20, pady = 20)
        ttk.Label(self.profileCard, text="Profile", style="TitleLabel.TLabel").pack(anchor=tk.W, pady=(0, 8))
        self.profileWidget = pro.ProfileDisplay(self.profileCard, archive,
            profileCallback, pqueue)
        self.profileWidget.pack(fill = tk.BOTH, expand = True)

        # Network tab:
        self.networkCard = ttk.Frame(self.networkTab, style="Card.TFrame")
        self.networkCard.pack(fill = tk.BOTH, expand = True, padx = 20, pady = 20)
        ttk.Label(self.networkCard, text="Network", style="TitleLabel.TLabel").pack(anchor=tk.W, pady=(0, 8))
        self.networkWidget = ntw.NetworkWidget(self.networkCard,
            network = network, archive = archive, networkAdd = self.networkAdd,
            slavesAdd = self.slavesAdd, pqueue = pqueue)
        self.networkWidget.pack(fill = tk.BOTH, expand = True)

        # Control tab:
        self.controlCard = ttk.Frame(self.controlTab, style="Card.TFrame")
        self.controlCard.pack(fill = tk.BOTH, expand = True, padx = 20, pady = 20)
        ttk.Label(self.controlCard, text="Control", style="TitleLabel.TLabel").pack(anchor=tk.W, pady=(0, 8))
        self.controlWidget = ctr.ControlWidget(self.controlCard,
            network = network,
            external = external,
            mapper = mapper,
            archive = archive,
            setLiveBE = self.setLive,
            setFBE = self.setF,
            pqueue = pqueue)

        self.controlWidget.pack(fill = tk.BOTH, expand = True)
        self.feedbackAdd(self.controlWidget)
        self.slavesAdd(self.controlWidget)
        self.networkAdd(self.controlWidget)

        # Console tab:
        self.consoleCard = ttk.Frame(self.consoleTab, style="Card.TFrame")
        self.consoleCard.pack(fill = tk.BOTH, expand = True, padx = 20, pady = 20)
        ttk.Label(self.consoleCard, text="Console", style="TitleLabel.TLabel").pack(anchor=tk.W, pady=(0, 8))
        self.consoleWidget = csl.ConsoleWidget(self.consoleCard,
            self._consoleWarning)
        self.consoleWidget.pack(fill = tk.BOTH, expand = True)
        self.consoleTab.bind("<Visibility>", self._consoleCalm)

        self.notebook.add(self.profileTab, text = "Profile")
        self.notebook.add(self.networkTab, text = "Network")
        self.notebook.add(self.controlTab, text = "Control")
        self.notebook.add(self.consoleTab, text = "Console")

        self.notebook.grid(row = 1, sticky = 'NWES')

        # Bottom bar ...........................................................
        self.bottomBar = ttk.Frame(self, style="Bottombar.TFrame", padding=(12, 6))
        self.bottomBar.grid(row=2, sticky='EW')
        self.bottomWidget = ntw.StatusBarWidget(self.bottomBar,
            network.shutdown, pqueue)
        self.bottomWidget.pack(side = tk.LEFT, fill = tk.X, expand = True,
            pady = 6, padx = 8)
        self.networkAdd(self.bottomWidget)
        self.slavesAdd(self.bottomWidget)
        
        # Register theme change callback
        theme_manager.register_callback(self._on_theme_change)
        
        # Register widgets for responsive layout
        self.responsive_manager.register_widget(self.notebook, "notebook")
        self.responsive_manager.register_widget(self.topBar, "topbar")
        self.responsive_manager.register_widget(self.bottomBar, "bottombar")
        self.responsive_manager.register_widget(self.profileWidget, "profile")
        self.responsive_manager.register_widget(self.networkWidget, "network")
        self.responsive_manager.register_widget(self.controlWidget, "control")
        self.responsive_manager.register_widget(self.consoleWidget, "console")

    def focusProfile(self, *_):
        self.notebook.select(0)

    def focusNetwork(self, *_):
        self.notebook.select(1)

    def focusControl(self, *_):
        self.controlWidget.blockAdjust()
        self.notebook.select(2)
        self.controlWidget.redraw()
        self.after(50, self.controlWidget.unblockAdjust)

    def focusConsole(self, *_):
        self.notebook.select(3)

    def getConsoleMethods(self):
        c = self.consoleWidget
        return (c.printr, c.printw, c.printe, c.prints, c.printd, c.printx)

    def profileChange(self):
        self.networkWidget.profileChange()
        self.controlWidget.profileChange()
        self.bottomWidget.profileChange()

    # Internal methods ---------------------------------------------------------
    def _settingsCallback(self):
        """
        To be called when the Settings button is pressed.
        """
        self._show_settings_menu()
    
    def _show_settings_menu(self):
        """
        Show the settings menu with theme and density options in a traditional panel style.
        """
        import tkinter.messagebox as msgbox
        
        # Create settings window with traditional panel appearance
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Settings")
        settings_window.geometry("650x600")
        settings_window.resizable(True, True)
        settings_window.minsize(600, 550)
        
        # Center the window
        settings_window.transient(self.master)
        settings_window.grab_set()
        
        # Apply current theme to settings window
        try:
            bg_color = theme_manager.get_color('SURFACE_2')
            settings_window.configure(bg=bg_color)
        except Exception:
            bg_color = '#f0f0f0'
            settings_window.configure(bg=bg_color)
        
        # Create main container with traditional layout
        main_container = ttk.Frame(settings_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title with icon
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(title_frame, text="⚙️ Settings", 
                               font=("Segoe UI", 14, "bold"))
        title_label.pack(side=tk.LEFT)
        
        # Create notebook for tabbed interface (traditional settings style)
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Appearance tab
        appearance_tab = ttk.Frame(notebook)
        notebook.add(appearance_tab, text="Appearance")
        
        # Theme section in appearance tab
        theme_section = ttk.LabelFrame(appearance_tab, text="Theme")
        theme_section.pack(fill=tk.X, padx=10, pady=10)
        
        # Current theme display
        try:
            current_theme = theme_manager.get_theme().title()
            print(f"[DEBUG] Settings window - Current theme from manager: {current_theme}")
        except Exception as e:
            current_theme = "Light"
            print(f"[DEBUG] Settings window - Error getting theme, defaulting to Light: {e}")
            
        theme_info_frame = ttk.Frame(theme_section)
        theme_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(theme_info_frame, text="Current theme:").pack(side=tk.LEFT)
        theme_value_label = ttk.Label(theme_info_frame, text=current_theme, 
                                     font=("Segoe UI", 9, "bold"))
        theme_value_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Theme selection with radio buttons
        theme_var = tk.StringVar(value=current_theme.lower())
        print(f"[DEBUG] Settings window - Theme variable initialized to: {theme_var.get()}")
        theme_radio_frame = ttk.Frame(theme_section)
        theme_radio_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        light_radio = ttk.Radiobutton(theme_radio_frame, text="Light Theme", 
                                     variable=theme_var, value="light")
        light_radio.pack(anchor=tk.W, pady=2)
        
        dark_radio = ttk.Radiobutton(theme_radio_frame, text="Dark Theme", 
                                    variable=theme_var, value="dark")
        dark_radio.pack(anchor=tk.W, pady=2)
        
        # Layout section in appearance tab
        layout_section = ttk.LabelFrame(appearance_tab, text="Layout Density")
        layout_section.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Get current density
        current_density = getattr(self, '_ui_density', 'comfortable')
        
        # Density info
        density_info_frame = ttk.Frame(layout_section)
        density_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(density_info_frame, text="Current density:").pack(side=tk.LEFT)
        density_value_label = ttk.Label(density_info_frame, text=current_density.title(), 
                                       font=("Segoe UI", 9, "bold"))
        density_value_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Density selection with radio buttons
        density_var = tk.StringVar(value=current_density)
        density_radio_frame = ttk.Frame(layout_section)
        density_radio_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        comfortable_radio = ttk.Radiobutton(density_radio_frame, text="Comfortable (Recommended)", 
                                           variable=density_var, value="comfortable")
        comfortable_radio.pack(anchor=tk.W, pady=2)
        
        compact_radio = ttk.Radiobutton(density_radio_frame, text="Compact", 
                                       variable=density_var, value="compact")
        compact_radio.pack(anchor=tk.W, pady=2)
        
        # General tab
        general_tab = ttk.Frame(notebook)
        notebook.add(general_tab, text="General")
        
        # Application info section
        app_section = ttk.LabelFrame(general_tab, text="Application Information")
        app_section.pack(fill=tk.X, padx=10, pady=10)
        
        info_frame = ttk.Frame(app_section)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text="Fan Club MkIV", 
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text="Version: 4.0").pack(anchor=tk.W, pady=(5, 0))
        ttk.Label(info_frame, text="Enhanced UI with modern features").pack(anchor=tk.W, pady=(2, 0))
        
        # Shortcuts section
        shortcuts_section = ttk.LabelFrame(general_tab, text="Keyboard Shortcuts")
        shortcuts_section.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        shortcuts_frame = ttk.Frame(shortcuts_section)
        shortcuts_frame.pack(fill=tk.X, padx=10, pady=10)
        
        shortcuts_text = [
            "Ctrl+T: Toggle Theme",
            "Ctrl+D: Toggle Density",
            "Ctrl+,: Open Settings",
            "F5: Refresh Interface",
            "Ctrl+1-4: Switch Tabs"
        ]
        
        for shortcut in shortcuts_text:
            ttk.Label(shortcuts_frame, text=shortcut).pack(anchor=tk.W, pady=1)
        
        # Button frame at bottom
        button_frame = ttk.Frame(main_container)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Apply and Cancel buttons (traditional style)
        def apply_settings():
            try:
                # Apply theme if changed
                new_theme = theme_var.get()
                print(f"[DEBUG] Current theme: {current_theme}, New theme: {new_theme}")
                if new_theme != current_theme.lower():
                    print(f"[DEBUG] Applying theme change from {current_theme} to {new_theme}")
                    theme_manager.set_theme(new_theme)
                    theme_value_label.config(text=new_theme.title())
                    print(f"[DEBUG] Theme applied successfully")
                else:
                    print(f"[DEBUG] No theme change needed")
                
                # Apply density if changed
                new_density = density_var.get()
                if new_density != current_density:
                    self._ui_density = new_density
                    self._apply_density_settings(new_density)
                    density_value_label.config(text=new_density.title())
                
                msgbox.showinfo("Settings", "Settings applied successfully!")
            except Exception as e:
                msgbox.showerror("Error", f"Failed to apply settings: {e}")
        
        ttk.Button(button_frame, text="Apply", command=apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="OK", command=lambda: (apply_settings(), settings_window.destroy())).pack(side=tk.RIGHT, padx=(0, 5))
    
    def _toggle_theme_and_close(self, window):
        """
        Toggle theme and close settings window with animation.
        Enhanced with performance optimization.
        """
        # Animate theme transition with performance optimization
        def complete_toggle():
            # Use performance-optimized theme switching
            self.performance_manager.optimized_theme_switch(theme_manager, 
                'dark' if theme_manager.current_theme == 'light' else 'light')
            window.destroy()
        
        # Use color transition for smooth theme change
        animate_color_transition(window, duration=300, easing=ease_in_out_cubic, callback=complete_toggle)
    
    def _toggle_density_and_close(self, window):
        """
        Toggle UI density and close settings window with animation.
        """
        # Animate density transition
        def complete_toggle():
            current_density = getattr(self, '_ui_density', 'comfortable')
            new_density = 'compact' if current_density == 'comfortable' else 'comfortable'
            self._ui_density = new_density
            self._apply_density_settings(new_density)
            window.destroy()
        
        # Use color transition for smooth density change
        animate_color_transition(window, duration=200, easing=ease_in_out_cubic, callback=complete_toggle)
    
    def _apply_density_settings(self, density):
        """
        Apply density settings to all UI components.
        Enhanced with comprehensive control sizing and font adjustments.
        """
        try:
            style = ttk.Style(self.master)
            
            if density == 'compact':
                # Compact density settings - smaller, tighter layout
                # Basic controls
                style.configure("Treeview", rowheight=18, font=("Segoe UI", 8))
                style.configure("Treeview.Heading", font=("Segoe UI", 8, "bold"))
                style.configure("TButton", padding=(6, 3), font=("Segoe UI", 8))
                style.configure("Secondary.TButton", padding=(6, 3), font=("Segoe UI", 8))
                style.configure("TEntry", padding=3, font=("Segoe UI", 8))
                style.configure("TLabel", padding=(3, 1), font=("Segoe UI", 8))
                style.configure("TFrame", padding=3)
                style.configure("TLabelFrame", padding=4, font=("Segoe UI", 8, "bold"))
                
                # Additional controls
                style.configure("TCheckbutton", padding=(3, 1), font=("Segoe UI", 8))
                style.configure("TRadiobutton", padding=(3, 1), font=("Segoe UI", 8))
                style.configure("TCombobox", padding=3, font=("Segoe UI", 8))
                style.configure("TScale", sliderlength=15)
                style.configure("TProgressbar", thickness=8)
                style.configure("TScrollbar", width=12)
                
                # Notebook tabs
                style.configure("TNotebook.Tab", padding=(8, 4), font=("Segoe UI", 8))
                
                # Special styles
                style.configure("Topbar.TLabel", padding=(3, 1), font=("Segoe UI", 8))
                style.configure("TitleLabel.TLabel", padding=(3, 2), font=("Segoe UI", 9, "bold"))
                style.configure("Card.TFrame", padding=(8, 6))
                
            else:
                # Comfortable density settings (default) - spacious, readable
                # Basic controls
                style.configure("Treeview", rowheight=24, font=("Segoe UI", 9))
                style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
                style.configure("TButton", padding=(10, 6), font=("Segoe UI", 9))
                style.configure("Secondary.TButton", padding=(10, 6), font=("Segoe UI", 9))
                style.configure("TEntry", padding=6, font=("Segoe UI", 9))
                style.configure("TLabel", padding=(6, 4), font=("Segoe UI", 9))
                style.configure("TFrame", padding=6)
                style.configure("TLabelFrame", padding=8, font=("Segoe UI", 9, "bold"))
                
                # Additional controls
                style.configure("TCheckbutton", padding=(6, 4), font=("Segoe UI", 9))
                style.configure("TRadiobutton", padding=(6, 4), font=("Segoe UI", 9))
                style.configure("TCombobox", padding=6, font=("Segoe UI", 9))
                style.configure("TScale", sliderlength=20)
                style.configure("TProgressbar", thickness=12)
                style.configure("TScrollbar", width=16)
                
                # Notebook tabs
                style.configure("TNotebook.Tab", padding=(12, 8), font=("Segoe UI", 9))
                
                # Special styles
                style.configure("Topbar.TLabel", padding=(6, 4), font=("Segoe UI", 9))
                style.configure("TitleLabel.TLabel", padding=(6, 4), font=("Segoe UI", 10, "bold"))
                style.configure("Card.TFrame", padding=(16, 12))
            
            # Store current density for future reference
            self._ui_density = density
            
            # Force refresh of all widgets
            self.master.update_idletasks()
            
            print(f"Applied {density} density settings successfully")
            
        except Exception as e:
            print(f"Error applying density settings: {e}")
    
    def _on_theme_change(self):
        """
        Called when theme changes to update all UI elements.
        Simplified version for reliable theme switching.
        """
        try:
            print(f"[DEBUG] _on_theme_change called - updating main interface")
            
            # Get new theme colors
            new_bg = theme_manager.get_color('SURFACE_2')
            
            # Apply ttk theme immediately
            style = ttk.Style(self.master)
            theme_manager.apply_ttk_theme(style)
            print(f"[DEBUG] TTK theme applied")
            
            # Update main window background
            if hasattr(self.master, 'configure'):
                self.master.configure(bg=new_bg)
                print(f"[DEBUG] Main window background updated to {new_bg}")
            
            # Update this frame's background
            try:
                self.configure(style='TFrame')
                print(f"[DEBUG] Base frame style updated")
            except:
                pass
            
            # Force refresh of all widgets
            self.master.update_idletasks()
            print(f"[DEBUG] Interface refresh completed")
            
        except Exception as e:
            print(f"[ERROR] Error updating theme: {e}")
            import traceback
            traceback.print_exc()
    
    def _setup_ux_callbacks(self):
        """
        设置用户体验增强的回调函数
        """
        callbacks = {
            'toggle_density': self._toggle_density_shortcut,
            'open_settings': self._show_settings_menu,
            'switch_tab': self._switch_tab_shortcut
        }
        self.ux_manager.set_app_callbacks(callbacks)
        
        # 为主要控件添加工具提示
        self._add_tooltips()
    
    def _toggle_density_shortcut(self):
        """
        密度切换快捷键回调
        """
        current_density = getattr(self, '_ui_density', 'comfortable')
        new_density = 'compact' if current_density == 'comfortable' else 'comfortable'
        self._ui_density = new_density
        self._apply_density_settings(new_density)
    
    def _switch_tab_shortcut(self, tab_index: int):
        """
        标签页切换快捷键回调
        """
        try:
            if hasattr(self, 'notebook') and 0 <= tab_index < self.notebook.index('end'):
                self.notebook.select(tab_index)
        except tk.TclError:
            pass
    
    def _add_tooltips(self):
        """
        为主要控件添加工具提示
        """
        try:
            # 为标签页添加工具提示
            if hasattr(self, 'notebook'):
                tab_tooltips = [
                    "Profile - 配置文件管理和显示 (Ctrl+1)",
                    "Network - 网络设置和连接管理 (Ctrl+2)", 
                    "Control - 风扇控制和监控 (Ctrl+3)",
                    "Console - 系统日志和调试信息 (Ctrl+4)"
                ]
                
                for i, tooltip_text in enumerate(tab_tooltips):
                    try:
                        tab_id = self.notebook.tabs()[i]
                        # 注意：ttk.Notebook的标签页工具提示需要特殊处理
                        # 这里我们为整个notebook添加一个通用提示
                        if i == 0:  # 只为第一个标签添加，避免重复
                            self.ux_manager.add_tooltip(self.notebook, 
                                "使用 Ctrl+1-4 快速切换标签页")
                    except (IndexError, tk.TclError):
                        continue
            
            # 为其他重要控件添加工具提示（如果存在的话）
            # 这些控件可能在子类中定义，所以使用hasattr检查
            
        except Exception as e:
            print(f"Error adding tooltips: {e}")
    
    def _helpCallback(self):
        """
        To be called when the Help button is pressed.
        """
        # Open help documentation or show help dialog
        help_text = f"""Fanclub Mark IV GUI Help
        
Version: {self.version}
        
Tabs:
        - Profile: Configure system profiles
        - Network: Manage network connections
        - Control: System control interface
        - Console: View system messages
        
For more information, contact support."""
        
        import tkinter.messagebox as msgbox
        msgbox.showinfo("Help", help_text)

    def _consoleWarning(self):
        """
        To be used by the console to warn the user of errors.
        """
        self.errorLabel.pack(side = tk.LEFT, padx = 100, pady=4, fill = tk.Y)
        self.warning = True

    def _consoleCalm(self, *E):
        """
        To be called after the console is  warnings have been checked.
        """
        if self.warning:
            self.errorLabel.pack_forget()


## DEMO ########################################################################
if __name__ == '__main__':
    import splash as spl
    import profile as pro

    print("FC GUI Base demo started")

    print("FC GUI Base demo not implemented")

    print("FC GUI Base demo finished")

