#!/usr/bin/python3
##----------------------------------------------------------------------------##
## WESTLAKE UNIVERSITY ## ADVANCED SYSTEMS LABORATORY ##                     ##
## CENTER FOR AUTONOMOUS SYSTEMS AND TECHNOLOGIES                      ##     ##
##----------------------------------------------------------------------------##
##   ______   _    _    _____   __ _    _   _  ____                       ##
##  |__  / | | |  / \  / _ \ \ / // \  | \ | |/ ___|                      ##
##    / /| |_| | / _ \| | | \ V // _ \ |  \| | |  _                       ##
##   / /_|  _  |/ ___ \ |_| || |/ ___ \| |\  | |_| |                      ##
##  /____|_| |_/_/___\_\___/_|_/_/_  \_\_| \_|\____|                      ##
##  |  _ \  / \  / ___|| | | | | | | / \  |_ _|                           ##
##  | | | |/ _ \ \___ \| |_| | | | |/ _ \  | |                            ##
##  | |_| / ___ \ ___) |  _  | |_| / ___ \ | |                            ##
##  |____/_/   \_\____/|_| |_|\___/_/   \_\___|                           ##
##                                                                            ##
##----------------------------------------------------------------------------##
## zhaoyang                   ## <mzymuzhaoyang@gmail.com>   ##              ##
## dashuai                    ## <dschen2018@gmail.com>      ##              ##
##                            ##                             ##              ##
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
INIT_PROFILE = "TENX10"
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
    " Pass profiles, not archive, " + "when profile changes will cause reset",
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
    " Account for possible name conflicts between fcpy fn parametrs and "
    + "user-defined variables",
]

if __name__ == "__main__":
    # if us.platform() == us.WINDOWS:
    # Windows-specific requirement around processes. See:
    # https://stackoverflow.com/questions/18204782

    ## IMPORTS #################################################################
    import multiprocessing as mp
    import logging
    import fc.frontend.gui.tkgui as tkg
    import fc.archive as ac
    import fc.backend.communicator as cm
    import fc.utils as us
    import fc.printer as pt
    import fc.builtin.profiles as btp

    import getopt  # https://docs.python.org/3.1/library/getopt.html

    import sys

    # 配置日志记录
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("fanclub.log"), logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    # Simple command line argument processing - profile name as first argument
    init_profile = INIT_PROFILE
    if len(sys.argv) == 2:
        if sys.argv[1] in btp.PROFILES:
            init_profile = sys.argv[1]
            logger.info("通过命令行参数设置配置文件: %s", init_profile)
        else:
            logger.warning(
                "无效的配置文件名称: %s，使用默认配置: %s", sys.argv[1], INIT_PROFILE
            )
    elif len(sys.argv) > 2:
        logger.warning("过多的命令行参数，仅使用第一个参数作为配置文件名称")

    # NOTE on writing servers like the ext. ctl. API:
    # - have stop methods handle redundance
    # - call stop method from end of routine
    # - have start methods restart if applicable
    # - have listener threads block at socket and deactivate them by sending
    #   to that socket

    ## MAIN ####################################################################
    # Prints ..................................................................
    print(pt.HEADER)

    # 记录启动信息
    logger.info("Fan Club MkIV 启动 - 版本: %s", VERSION)
    logger.info("使用配置文件: %s", init_profile)

    for reminder in REMINDERS:
        print("[REM]", reminder)
        logger.info("提醒: %s", reminder)

    # Execution ...............................................................
    pqueue = mp.Queue()

    # Install global thread exception hook to capture full stack traces
    import threading as th, traceback as tb, faulthandler as fh

    fh.enable()

    def _thread_excepthook(args):
        try:
            tb.print_exception(args.exc_type, args.exc_value, args.exc_traceback)
            logger.error(
                "线程异常: %s",
                getattr(args.thread, "name", "unknown"),
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )
        except Exception as e:
            logger.error("处理线程异常时出错: %s", str(e))
            pass
        try:
            P = pt.printers(pqueue, "[TH]")
            P[pt.X](
                args.exc_value,
                "Unhandled exception in thread: {}".format(
                    getattr(args.thread, "name", "unknown")
                ),
            )
        except Exception as e:
            logger.error("打印线程异常时出错: %s", str(e))
            pass

    try:
        th.excepthook = _thread_excepthook
        logger.info("线程异常处理钩子已安装")
    except Exception as e:
        logger.error("安装线程异常处理钩子失败: %s", str(e))
        pass

    try:
        logger.info("正在初始化FCArchive...")
        archive = ac.FCArchive(pqueue, VERSION, btp.PROFILES[init_profile])
        logger.info("正在初始化GUI界面...")
        interface = tkg.FCGUI(archive, pqueue)
        logger.info("启动GUI界面...")
        interface.run()
    except Exception as e:
        logger.error("应用程序启动失败: %s", str(e), exc_info=True)
        raise
