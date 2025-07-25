#!/usr/bin/python3
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
 + FC execution starts here.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## GLOBALS #####################################################################
VERSION = "0.17"
# Default profile configuration - uncomment one of the options below
# # 可选启动配置（只保留其中一行，注释或删除其它行即可）
# # 可选启动配置（只保留其中一行，注释或删除其它行即可）
# INIT_PROFILE = "MODULE"
INIT_PROFILE = "SEVENSQ"
# INIT_PROFILE = "DEV1"
# INIT_PROFILE = "BOX"
# INIT_PROFILE = "DEV2"
# INIT_PROFILE = "DEV3"
# INIT_PROFILE = "BASE"
# INIT_PROFILE = "CAST"
# INIT_PROFILE = "CAST_SIDE"
# INIT_PROFILE = "CANN"
# INIT_PROFILE = "PROFILES"


REMINDERS = [
    " Look into 'memory leak' in profile switches and data path",
    " Look into control after profile switching ('return 1',",
    " Pass profiles, not archive, " +
        "when profile changes will cause reset",
    " Change all watchdog threads to Tkinter 'after' scheduling",
    " Indexing by 1 in functional input",
    " Standardize notation (also: function argument consistency,",
    " period_ms abstraction barrier in FCInterface",
    " LiveTable and manual control",
    " Enforce consistent slave indices",
    " External control on profile changes",
    " Comms. reset on profile changes",
    " Direct control w/ live table",
    " Auto-update displays to latest data when switching",
    " Change core and print server to use blocked threads",
    " Terminal arguments",
    " Grid position indicators",
    " Switching from preview",
    " Hotkeys",
    " List index out of bounds on control.py:1800 w/ selection",
    " Account for possible name conflicts between fcpy fn parametrs and " +
        "user-defined variables",
]

if __name__ == '__main__':
    #if us.platform() == us.WINDOWS:
    # Windows-specific requirement around processes. See:
    # https://stackoverflow.com/questions/18204782

    ## IMPORTS #################################################################
    import multiprocessing as mp
    import fc.frontend.gui.tkgui as tkg
    import fc.archive as ac
    import fc.backend.communicator as cm
    import fc.utils as us
    import fc.printer as pt
    import fc.builtin.profiles as btp

    import getopt # https://docs.python.org/3.1/library/getopt.html

    import sys


    # Simple command line argument processing - profile name as first argument
    init_profile = INIT_PROFILE
    if len(sys.argv) == 2 and sys.argv[1] in btp.PROFILES:
        init_profile = sys.argv[1]

    # NOTE on writing servers like the ext. ctl. API:
    # - have stop methods handle redundance
    # - call stop method from end of routine
    # - have start methods restart if applicable
    # - have listener threads block at socket and deactivate them by sending
    #   to that socket

    ## MAIN ####################################################################
    # Prints ...................................................................
    print(pt.HEADER)

    for reminder in REMINDERS:
        print("[REM]", reminder)

    # Execution ................................................................
    pqueue = mp.Queue()
    archive = ac.FCArchive(pqueue, VERSION, btp.PROFILES[init_profile])
    interface = tkg.FCGUI(archive, pqueue)
    interface.run()
