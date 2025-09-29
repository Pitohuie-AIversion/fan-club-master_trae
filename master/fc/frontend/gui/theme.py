################################################################################
## Project: Fan Club Mark II "Master" ## File: theme.py                     ##
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES       ##                     ##
##----------------------------------------------------------------------------##
##      ____      __      __  __      _____      __      __    __    ____     ##
##     / __/|   _/ /|    / / / /|  _- __ __\    / /|    / /|  / /|  / _  \    ##
##    / /_ |/  / /  /|  /  // /|/ / /|__| _|   / /|    / /|  / /|/ /   --||   ##
##   / __/|/ _/    /|/ /   / /|/ / /|    __   / /|    / /|  / /|/ / _  \|/    ##
##  / /|_|/ /  /  /|/ / // //|/ / /|__- / /  / /___  / -|_ - /|/ /     /|     ##
## /_/|/   /_/ /_/|/ /_/ /_/|/ |\ ___--|_|  /_____/| |-___-_|/  /____-/|/     ##
## |_|/    |_|/|_|/  |_|/|_|/   \|___|-    |_____|/   |___|     |____|/       ##
##                   _ _    _    ___   _  _      __   __                      ##
##                  | | |  | |  | T_| | || |    |  | |  |                     ##
##                  | _ |  |T|  |  |  |  _|      ||   ||                      ##
##                  || || |_ _| |_|_| |_| _|    |__| |__|                     ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>  ##                ##
## dashuai                    ## <dschen2018@gmail.com>     ##                ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Ultra-modern theme configuration inspired by Material Design 3 and Fluent Design.
 + Features gradients, sophisticated colors, and comprehensive design tokens.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## MODERN COLOR SYSTEM #########################################################
# Primary brand colors with multiple shades
PRIMARY_50 = "#e3f2fd"      # Very light blue
PRIMARY_100 = "#bbdefb"     # Light blue
PRIMARY_200 = "#90caf9"     # Medium light blue
PRIMARY_300 = "#64b5f6"     # Medium blue
PRIMARY_400 = "#42a5f5"     # Medium dark blue
PRIMARY_500 = "#2196f3"     # Primary blue (main)
PRIMARY_600 = "#1e88e5"     # Darker blue
PRIMARY_700 = "#1976d2"     # Dark blue
PRIMARY_800 = "#1565c0"     # Very dark blue
PRIMARY_900 = "#0d47a1"     # Deepest blue

# Accent colors
ACCENT_LIGHT = "#64ffda"    # Cyan accent
ACCENT_MAIN = "#00bcd4"     # Main accent
ACCENT_DARK = "#00acc1"     # Dark accent

# Semantic colors
SUCCESS_LIGHT = "#c8e6c9"   # Light green
SUCCESS_MAIN = "#4caf50"    # Main green
SUCCESS_DARK = "#388e3c"    # Dark green

ERROR_LIGHT = "#ffcdd2"     # Light red
ERROR_MAIN = "#f44336"      # Main red
ERROR_DARK = "#d32f2f"      # Dark red

WARNING_LIGHT = "#fff3e0"   # Light orange
WARNING_MAIN = "#ff9800"    # Main orange
WARNING_DARK = "#f57c00"    # Dark orange

INFO_LIGHT = "#e1f5fe"      # Light blue info
INFO_MAIN = "#03a9f4"       # Main blue info
INFO_DARK = "#0288d1"       # Dark blue info

# Surface colors (backgrounds)
SURFACE_1 = "#ffffff"       # Pure white
SURFACE_2 = "#f8f9fa"       # Very light gray
SURFACE_3 = "#f1f3f4"       # Light gray
SURFACE_4 = "#e8eaed"       # Medium light gray
SURFACE_5 = "#dadce0"       # Medium gray

# Text colors
TEXT_PRIMARY = "#202124"    # Primary text (almost black)
TEXT_SECONDARY = "#5f6368"  # Secondary text (gray)
TEXT_DISABLED = "#9aa0a6"   # Disabled text (light gray)
TEXT_ON_PRIMARY = "#ffffff" # White text on primary background
TEXT_ON_DARK = "#ffffff"    # White text on dark background

# Legacy compatibility (mapped to new system)
BG_CT = SURFACE_3           # Background color
BG_ACCENT = PRIMARY_500     # Accent background
BG_ERROR = ERROR_MAIN       # Error background
FG_ERROR = TEXT_ON_DARK     # Error text
BG_SUCCESS = SUCCESS_MAIN   # Success background
BG_WARNING = WARNING_MAIN   # Warning background
BG_LIGHT = SURFACE_1        # Light background
FG_PRIMARY = TEXT_PRIMARY   # Primary text
FG_SECONDARY = TEXT_SECONDARY # Secondary text

## VISUAL EFFECTS ##############################################################
# Border radius values
RADIUS_SMALL = 4           # Small radius for inputs
RADIUS_MEDIUM = 8          # Medium radius for buttons
RADIUS_LARGE = 12          # Large radius for cards
RADIUS_EXTRA_LARGE = 16    # Extra large radius

# Shadow definitions (for future use with tkinter styling)
SHADOW_LIGHT = "2px 2px 4px rgba(0,0,0,0.1)"
SHADOW_MEDIUM = "4px 4px 8px rgba(0,0,0,0.15)"
SHADOW_HEAVY = "8px 8px 16px rgba(0,0,0,0.2)"

# Gradient definitions (color pairs for gradient effects)
GRADIENT_PRIMARY = (PRIMARY_400, PRIMARY_600)
GRADIENT_ACCENT = (ACCENT_LIGHT, ACCENT_DARK)
GRADIENT_SUCCESS = (SUCCESS_LIGHT, SUCCESS_DARK)
GRADIENT_ERROR = (ERROR_LIGHT, ERROR_DARK)