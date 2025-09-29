################################################################################
## Project: Fanclub Mark IV "Master" GUI          ## File: network.py         ##
##----------------------------------------------------------------------------##
##                        WESTLAKE UNIVERSITY                                ##
##                   ADVANCED SYSTEMS LABORATORY                            ##
##----------------------------------------------------------------------------##
##                                                                            ##
##                    ██╗    ██╗███████╗███████╗████████╗                   ##
##                    ██║    ██║██╔════╝██╔════╝╚══██╔══╝                   ##
##                    ██║ █╗ ██║█████╗  ███████╗   ██║                      ##
##                    ██║███╗██║██╔══╝  ╚════██║   ██║                      ##
##                    ╚███╔███╔╝███████╗███████║   ██║                      ##
##                     ╚══╝╚══╝ ╚════════╝╚══════╝   ╚═╝                      ##
##                                                                            ##
##                         LAKE SYSTEMS LABORATORY                          ##
##                                                                            ##
##----------------------------------------------------------------------------##
## Authors: zhaoyang, dashuai                                                ##
## Email: mzymuzhaoyang@gmail.com, dschen2018@gmail.com                     ##
## Date: 2024                                                                ##
## Version: 1.0                                                              ##
################################################################################

""" ABOUT ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 + Graphical interface for the FC network.
 + REMARKS:
 + - For simplicity's sake, initial archive data is ignored, (e.g saved Slaves
 +   are not initialized into the Slave list during construction). Instead,
 +   such data is expected to be received from Communicator status updates.
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ """

## IMPORTS #####################################################################
import os
import time as tm
import shutil as sh

import tkinter as tk
import tkinter.filedialog as fdg
import tkinter.ttk as ttk
import tkinter.font as fnt

from fc.frontend.gui import guiutils as gus
from fc import standards as s, printer as pt
from fc.frontend.gui.theme import TEXT_PRIMARY, TEXT_SECONDARY, ERROR_MAIN

## GLOBALS #####################################################################
TEST_VECTORS = [
    [],
    [
        0, "T1", "MAC_ADDR", s.SS_CONNECTED, 21, "vx.x.x"
    ],
    [
        0, "T1", "MAC_ADDR", s.SS_CONNECTED, 21, "vx.x.x",
        1, "T2", "MAC_ADDR", s.SS_DISCONNECTED, 21, "vx.x.x",
        2, "T3", "MAC_ADDR", s.SS_AVAILABLE, 21, "vx.x.x"
    ],
    [
        1, "T2", "MAC_ADDR", s.SS_CONNECTED, 21, "vx.x.x",
        2, "T3", "MAC_ADDR", s.SS_CONNECTED, 21, "vx.x.x"
    ]
]

## BASE ########################################################################
class NetworkWidget(ttk.Frame, pt.PrintClient):
    """
    Container for all the FC network GUI front-end widgets, except the FC
    status bar.
    """
    SYMBOL = "[NW]"

    def __init__(self, master, network, archive, networkAdd, slavesAdd, pqueue):
        """
        Create a new NetworkWidget inside MASTER, interfaced with the network
        backend using the NETWORK abstraction.
        (See fc.communicator.NetworkAbstraction.)

        NETWORKADD and SLAVESADD are methods to be called on widgets that
        expect to receive incoming network and slaves vectors, respectively.

        PQUEUE is the Queue object to be used for I-P printing.
        """
        # Core setup -----------------------------------------------------------
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.main = ttk.Frame(self)
        self.main.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)

        self.main.grid_columnconfigure(0, weight = 1)
        self.main.grid_rowconfigure(2, weight = 1)

        self.networkAdd, self.slavesAdd = networkAdd, slavesAdd
        self.network = network

        # ----------------------------------------------------------------------
        self.firmwareFrame = ttk.LabelFrame(self.main, text = "Firmware Update")
        self.firmwareFrame.grid(row = 1, sticky = "EW")
        self.firmwareUpdate = FirmwareUpdateWidget(self.firmwareFrame, network,
            pqueue)
        self.firmwareUpdate.pack(fill = tk.BOTH, expand = True)

        self.slaveList = SlaveListWidget(self.main, network, pqueue)
        self.slaveList.grid(row = 2, sticky = "NEWS")

        self.networkFrame = ttk.LabelFrame(self.main, text = "Network Control")
        self.networkFrame.grid(row = 0, sticky = "EW")
        self.networkControl = NetworkControlWidget(self.networkFrame, network,
            self.slaveList, archive, pqueue)
        self.networkControl.pack(fill = tk.BOTH, expand = True)
        self.networkControl.addClient(self.firmwareUpdate)

        self.networkAdd(self.networkControl)
        self.slavesAdd(self.slaveList)

    def profileChange(self):
        self.slaveList.clear()
        # 调用NetworkControlWidget的profileChange方法
        if hasattr(self.networkControl, 'profileChange'):
            self.networkControl.profileChange()

## WIDGETS #####################################################################

# Network control ==============================================================
class NetworkControlWidget(ttk.Frame, pt.PrintClient):
    """
    GUI front-end for the FC network control tools (such as adding and removing
    Slaves).
    """
    NO_IP = "[NO IP]"
    NO_PORT = "[NO PORT]"

    def __init__(self, master, network, slaveList, archive, pqueue):
        """
        Create a new NetworkControlWidget.

        MASTER := Tkinter parent widget
        NETWORK := NetworkAbstraction for this system
        SLAVELIST := SlaveList instance from which to fetch selections for
            control messages
        ARCHIVE := FCArchive instance for profile configuration
        PQUEUE := Queue instance to use for I-P printing
        """

        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        self.network = network
        self.slaveList = slaveList
        self.archive = archive

        frameconfig = {"side" : tk.TOP, "fill" : tk.BOTH, "expand" : True,
            "padx" : 10, "pady" : 5}

        self.clients = [slaveList]
        # Connection ...........................................................

        # Information to display:
        # - IP Address
        # - Broadcast port
        # - Broadcast IP
        # - Listener port

        self.isConnected = False
        self._connectCallback = network.connect
        self._disconnectCallback = network.disconnect

        self.connectionFrame = ttk.Frame(self)
        self.connectionFrame.pack(**frameconfig)
        
        # Connect button:
        self.connectButton = ttk.Button(self.connectionFrame, text = "Connect",
        command = self._onConnect, width = 12)
        self.connectButton.pack(side = tk.LEFT, padx = 0, fill = tk.Y)

        # Displays:
        self.ips = []
        self.ports = []

        # IP Address:
        self.ipVar = tk.StringVar()
        self.ipVar.set(self.NO_IP)
        self.ips.append(self.ipVar)
        self.__addDisplay("IP Address", self.ipVar)

        # Broadcast IP:
        self.bcipVar = tk.StringVar()
        self.bcipVar.set(self.NO_IP)  # 先设置默认值
        self.ips.append(self.bcipVar)
        name = "Broadcast IP"
        self.bcipFrame = ttk.Frame(self.connectionFrame)
        self.bcipFrame.pack(side = tk.RIGHT, fill = tk.Y, pady = 5, padx = 10)
        self.bcipLabel = ttk.Label(self.bcipFrame, text = name + ":")
        self.bcipLabel.pack(side = tk.TOP, fill = tk.X, padx = 10)
        self.bcipDisplay = gus.PromptLabel(self.bcipFrame,
            title = "Edit broadcast IP",
            prompt = "Enter a valid IP address (IPv4) to which to send "
            "broadcast messages. \n"
            "To send to all addresses on the default "\
            "interface, leave the field empty.",
            callback = self._setBroadcastIP,
            starter = self.bcipVar.get,
            textvariable = self.bcipVar, width = 15,
            relief = tk.SUNKEN, font = gus.typography["code"]["font"], padx = 10, pady = 5)
        self.bcipDisplay.pack(side = tk.TOP, fill = tk.X, pady = 5, padx = 10)
        
        # 在GUI组件创建完成后再加载profile配置
        # 使用更长的延迟确保GUI完全初始化
        self.after(100, self._loadProfileBroadcastIP)

        # Broadcast port:
        self.bcVar = tk.StringVar()
        self.bcVar.set(self.NO_PORT)  # 先设置默认值
        self.ports.append(self.bcVar)
        self.__addDisplay("Broadcast Port", self.bcVar)
        
        # 在GUI组件创建完成后再加载profile配置
        self.after_idle(self._loadProfileBroadcastPort)

        # Listener port:
        self.ltVar = tk.StringVar()
        self.ltVar.set(self.NO_PORT)
        self.ports.append(self.ltVar)
        self.__addDisplay("Listener Port", self.ltVar)
        
        # 在GUI组件创建完成后再加载profile配置
        self.after_idle(self._loadProfileListenerPort)

        # Connection display:
        self.connectionVar = tk.StringVar()
        self.connectionVar.set("[NO CONNECTION]")
        self.connectionLabel = ttk.Label(self.connectionFrame,
            textvariable = self.connectionVar, width = 11,
            style = "Secondary.TLabel")
        self.connectionLabel.pack(side = tk.RIGHT, fill = tk.Y, pady = 3,
            padx = 6)
        self.status = s.SS_DISCONNECTED

        self.activeWidgets = []

        # Target ..............................................................
        self.targetFrame = ttk.Frame(self)
        self.targetFrame.pack(**frameconfig)

        self.targetLabel = ttk.Label(self.targetFrame, text = "Target: ")
        self.targetLabel.pack(side = tk.LEFT)
        self.target = tk.IntVar()
        self.target.set(0)

        self.targetButtons = []

        # Message ..............................................................
        self.messageFrame = ttk.Frame(self)
        self.messageFrame.pack(**frameconfig)

        self.messageLabel = ttk.Label(self.messageFrame, text = "Message: ")
        self.messageLabel.pack(side = tk.LEFT)
        self.message = tk.IntVar()
        self.message.set(0)

        self.messageButtons = []

        # Send .................................................................
        self.sendFrame = ttk.Frame(self)
        self.sendFrame.pack(**frameconfig)
        self.sendButton = ttk.Button(self.sendFrame, text = "Send",
            command = self._send)
        self.sendButton.pack(side = tk.LEFT)
        self._sendCallback = network.commandIn
        self.activeWidgets.append(self.sendButton)

        for message, code in s.MESSAGES.items():
            self._addMessage(message, code)
        for target, code in s.TARGETS.items():
            self._addTarget(target, code)

        # Wrap-up ..............................................................
        self.disconnected()

    # API ......................................................................
    def networkIn(self, N):
        """
        Process a new network state vector N. See standards.py for form.
        """
        connected = N[0]
        if connected:
            if not self.isConnected:
                self.connected()
            self.ipVar.set(N[1])
            
            # 处理广播IP显示 - 将 "<broadcast>" 转换为用户友好的显示
            broadcast_ip = N[2]
            if broadcast_ip == "<broadcast>":
                self.bcipVar.set("Broadcast (Auto)")
            else:
                self.bcipVar.set(broadcast_ip)
                
            self.bcVar.set(N[3])
            self.ltVar.set(N[4])
        else:
            self.disconnected()

    def connecting(self):
        """
        Indicate that a connection is being activated.
        """
        self.connectButton.config(state = tk.DISABLED, text = "Connecting")
        self._setWidgetState(tk.DISABLED)
        self.isConnected = False

    def connected(self):
        """
        Indicate that there is an active network connection.
        """
        self.connectButton.config(state = tk.NORMAL, text = "Disconnect",
            command = self._onDisconnect)
        self.connectionVar.set("Connected")
        # ttk.Label doesn't support direct fg/bg usage, switch to style instead
        style = ttk.Style(self.connectionLabel)
        style.configure('NetworkConnected.TLabel',
                        foreground=s.FOREGROUNDS[s.SS_CONNECTED],
                        background=s.BACKGROUNDS[s.SS_CONNECTED])
        self.connectionLabel.configure(style='NetworkConnected.TLabel')
        self._setWidgetState(tk.NORMAL)
        for client in self.clients:
            client.connected()


    def _setBroadcastIP(self, ip):
        """
        Set the broadcast IP to IP.
        """
        # 处理用户输入的转换
        if ip == "Broadcast (Auto)" or ip == "":
            ip = "<broadcast>"
        
        self.network.setBroadcastIP(ip)

    def _loadProfileBroadcastPort(self):
        """
        从profile加载broadcastPort配置并设置到GUI显示
        """
        try:
            if self.archive:
                profile = self.archive.profile()
                # 使用正确的常量键而不是字符串键
                import fc.archive as ac
                if profile and ac.broadcastPort in profile:
                    broadcast_port = profile[ac.broadcastPort]
                    self.bcVar.set(str(broadcast_port))
                else:
                    # 如果profile中没有配置，显示默认端口
                    self.bcVar.set(self.NO_PORT)
            else:
                self.bcVar.set(self.NO_PORT)
        except Exception as e:
            # 出错时显示默认值
            self.bcVar.set(self.NO_PORT)
            self.printr(f"Error loading profile broadcast port: {e}")

    def _loadProfileListenerPort(self):
        """
        从profile加载externalDefaultListenerPort配置并设置到GUI显示
        """
        try:
            if self.archive:
                profile = self.archive.profile()
                # 使用正确的常量键而不是字符串键
                import fc.archive as ac
                if profile and ac.externalDefaultListenerPort in profile:
                    listener_port = profile[ac.externalDefaultListenerPort]
                    self.ltVar.set(str(listener_port))
                else:
                    # 如果profile中没有配置，显示默认端口
                    self.ltVar.set(self.NO_PORT)
            else:
                self.ltVar.set(self.NO_PORT)
        except Exception as e:
            # 出错时显示默认值
            self.ltVar.set(self.NO_PORT)
            self.printr(f"Error loading profile listener port: {e}")

    def _loadProfileBroadcastIP(self):
        """
        从profile加载broadcastIP配置并设置到GUI显示
        """
        try:
            if self.archive:
                profile = self.archive.profile()
                # 使用正确的常量键而不是字符串键
                import fc.archive as ac
                if profile and ac.broadcastIP in profile:
                    broadcast_ip = profile[ac.broadcastIP]
                    # 将 "<broadcast>" 转换为用户友好的显示
                    if broadcast_ip == "<broadcast>":
                        self.bcipVar.set("Broadcast (Auto)")
                    else:
                        self.bcipVar.set(broadcast_ip)
                    # 强制更新GUI显示
                    self.bcipDisplay.update()
                else:
                    # 如果profile中没有配置，显示默认的广播地址
                    self.bcipVar.set("Broadcast (Auto)")
            else:
                self.bcipVar.set(self.NO_IP)
        except Exception as e:
            # 出错时显示默认值
            self.printr(f"Error loading profile broadcast IP: {e}")
            self.bcipVar.set(self.NO_IP)

    def profileChange(self):
        """
        处理profile变更事件，更新网络设置显示
        """
        self.printr("Debug: NetworkControlWidget.profileChange called!")
        # 重新加载profile中的broadcastIP和broadcastPort配置
        self._loadProfileBroadcastIP()
        self._loadProfileBroadcastPort()
        self._loadProfileListenerPort()
        
        # 如果当前未连接，显示profile配置
        if not self.isConnected:
            try:
                if self.archive:
                    profile = self.archive.profile()
                    if profile:
                        # 更新其他网络设置显示（如果需要）
                        # 注意：IP地址和端口通常在连接时才确定，这里主要处理broadcastIP
                        pass
            except Exception as e:
                self.printr(f"Error updating profile network settings: {e}")

        self.bcipDisplay.enable()
        self.isConnected = True

    def disconnecting(self):
        """
        Indicate that a connection is being terminated.
        """
        self.connectButton.config(state = tk.DISABLED, text = "Disconnecting")
        self._setWidgetState(tk.DISABLED)
        self.isConnected = False

    def disconnected(self):
        """
        Indicate that there is an active network connection.
        """
        self.connectButton.config(state = tk.NORMAL, text = "Connect",
            command = self._onConnect)
        self.connectionVar.set("Disconnected")
        # 只重置IP地址，不重置broadcastIP（保持profile配置）
        self.ipVar.set(self.NO_IP)
        # 只重置监听端口，保留广播端口配置
        self.ltVar.set(self.NO_PORT)
        for client in self.clients:
            client.disconnected()
        # ttk.Label doesn't support direct fg/bg usage, switch to style instead
        style = ttk.Style(self.connectionLabel)
        style.configure('NetworkDisconnected.TLabel',
                        foreground=s.FOREGROUNDS[s.SS_DISCONNECTED],
                        background=s.BACKGROUNDS[s.SS_DISCONNECTED])
        self.connectionLabel.configure(style='NetworkDisconnected.TLabel')
        self._setWidgetState(tk.DISABLED)
        self.bcipDisplay.disable()
        self.isConnected = False

    def addClient(self, client):
        """
        Add CLIENT to the list of widgets to update by calling
        client.connected or client.disconnected upon the corresponding changes
        of status.
        """
        self.clients.append(client)

    def connect(self):
        """
        API to trigger connection. Equivalent to pressing the connect button.
        NOTE: Should be called only when disconnected.
        """
        self._onConnect()


    def disconnect(self):
        """
        API to trigger disconnection. Equivalent to pressing the disconnect
        button.

        NOTE: Should be called only when connected.
        """
        self._onDisconnect()

    # Internal methods .........................................................
    def _onConnect(self, *event):
        self._connectCallback()

    def _onDisconnect(self, *event):
        self._disconnectCallback()

    def _send(self, *E):
        """
        Send the selected target and
        message codes, as well as the current slave list selection.
        """
        self._sendCallback(self.message.get(), self.target.get(),
            self.slaveList.selected())

    def _setWidgetState(self, state):
        """
        Set the state of all network control 'interactive' widgets, such as
        buttons, to the Tkinter state STATE.
        """
        for button in self.activeWidgets:
            button.config(state = state)

    def _addTarget(self, name, code):
        """
        Allow the user to specify the target named NAME with the code CODE
        passed to the send callback.
        """
        button = ttk.Radiobutton(self.targetFrame, text = name, value = code,
            variable = self.target)
        button.config(state = tk.NORMAL if self.isConnected else tk.DISABLED)

        button.pack(side = tk.LEFT, anchor = tk.W, padx = 5)
        self.targetButtons.append(button)
        self.activeWidgets.append(button)

        if len(self.targetButtons) == 1:
            self.target.set(code)

    def _addMessage(self, name, code):
        """
        Allow the user to send the message named NAME with the message code CODE
        passed to the send callback.
        """
        button = ttk.Radiobutton(self.messageFrame, text = name, value = code,
            variable = self.message)
        button.config(state = tk.NORMAL if self.isConnected else tk.DISABLED)

        button.pack(side = tk.LEFT, anchor = tk.W, padx = 5)
        self.messageButtons.append(button)
        self.activeWidgets.append(button)

        if len(self.messageButtons) == 1:
            self.message.set(code)

    def __addDisplay(self, name, variable):
        """
        Private method to add labels to display connection status variables.
        """

        frame = ttk.Frame(self.connectionFrame)
        frame.pack(side = tk.RIGHT, fill = tk.Y, pady = 5, padx = 10)

        label = ttk.Label(frame, text = name + ":")
        label.pack(side = tk.TOP, fill = tk.X, padx = 10)

        display = ttk.Label(frame, textvariable = variable, width = 15,
            style = "Sunken.TLabel", font = gus.typography["code"]["font"])
        display.pack(side = tk.TOP, fill = tk.X, pady = 5, padx = 10)



# Firmware update ==============================================================
class FirmwareUpdateWidget(ttk.Frame, pt.PrintClient):
    """
    GUI front-end for the FC firmware update tools, i.e the Mark III
    "Bootloader."
    """
    SYMBOL = "[FU]"
    READY, LIVE, INACTIVE = range(3)

    def __init__(self, master, network, pqueue):
        """
        Create a new FirmwareUpdateWidget.

        MASTER := Tkinter parent widget
        NETWORK := NetworkAbstraction being used
        PQUEUE := Queue instance for I-P printing
        """
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ...............................................................
        self.network = network

        self.main = ttk.Frame(self)
        self.main.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)

        self.fileFrame = ttk.Frame(self.main)
        self.fileFrame.pack(fill = tk.X, expand = True)

        self.fileLabel = ttk.Label(self.fileFrame, text = "File: ")
        self.fileLabel.pack(side = tk.LEFT, padx = 10, pady = 5)

        self.filename = ""
        self.fileSize = 0
        self.fileVar = tk.StringVar()
        self.fileEntry = ttk.Entry(self.fileFrame, textvariable = self.fileVar)
        self.fileEntry.pack(side = tk.LEFT, fill = tk.X, expand = True,
            padx = 10)
        self.fileEntry.config(state = tk.DISABLED)

        self.fileButton = ttk.Button(self.fileFrame, text = "...",
            command = self._chooseFile)
        self.fileButton.pack(side = tk.LEFT)
        if not hasattr(self, 'setupWidgets'): self.setupWidgets = []
        self.setupWidgets.append(self.fileButton)

        # Version ..............................................................
        self.bottomFrame = ttk.Frame(self.main)
        self.bottomFrame.pack(fill = tk.X, expand = True, pady = 5)

        self.versionLabel = ttk.Label(self.bottomFrame, text = "Version Code: ")
        self.versionLabel.pack(side = tk.LEFT, padx = 10, pady = 5)

        self.version = tk.StringVar()
        self.versionEntry = ttk.Entry(self.bottomFrame, width = 10,
            textvariable = self.version)
        self.versionEntry.pack(side = tk.LEFT, fill = tk.X, expand = False,
            padx = 10)
        self.setupWidgets.append(self.versionEntry)

        # Start ................................................................
        self.startButton = ttk.Button(self.bottomFrame, command = self._start,
            text = "Start")
        self.startButton.pack(side = tk.LEFT, padx = 20)
        # Firmware update status label styles (use ttk.Style instead of per-widget fg/bg)
        self.inactiveLabelConfig = {'text': '(Inactive)'}
        self.readyLabelConfig = {'text': 'Ready'}
        self.liveLabelConfig = {'text': 'LIVE'}

        self._fu_style = ttk.Style()
        self._fu_style.configure(
            "FirmwareInactive.TLabel",
            foreground = TEXT_SECONDARY,
            font = gus.typography['label_small']['font']
        )
        self._fu_style.configure(
            "FirmwareReady.TLabel",
            foreground = TEXT_PRIMARY,
            font = gus.typography['label_small']['font']
        )
        self._fu_style.configure(
            "FirmwareLive.TLabel",
            foreground = ERROR_MAIN,
            font = (
                gus.typography['label_small']['font'][0],
                gus.typography['label_small']['font'][1],
                'bold'
            )
        )

        self.statusLabel = ttk.Label(
            self.bottomFrame,
            text = self.inactiveLabelConfig['text'],
            style = "FirmwareInactive.TLabel"
        )
        self.statusLabel.pack(side = tk.LEFT, padx = 10, pady = 5)

        self.start = network.startBootloader
        self.stop = network.stopBootloader

        self.fileVar.trace('w', self._checkReady)
        self.version.trace('w', self._checkReady)
        self.status = self.INACTIVE
        self._inactive()

        print("[NOTE] Confirm firmware update status consistency?")

    # API ......................................................................
    def connected(self):
        """
        Called when the network switches from disconnected to connected.
        """
        pass

    def disconnected(self):
        """
        Called when the network switches from connected to disconnected.
        """
        self._stop()

    # Internal methods .........................................................
    def _start(self, *args):
        """
        Start a firmware update.
        """
        if self.status == self.READY:
            self.startButton.config(text = "Starting", state = tk.DISABLED)
            self._setWidgetState(tk.DISABLED)
            self.start(self.filename, self.version.get(), self.fileSize)
            self._live()

    def _stop(self, *args):
        """
        Stop an ongoing firmware update if there is one.
        """
        if self.status == self.LIVE:
            self.startButton.config(text = "Stopping", state = tk.DISABLED)
            self.stop()
            self._ready()

    def _chooseFile(self, *args):
        try:
            self._setWidgetState(tk.DISABLED)
            self.fileVar.set(
                fdg.askopenfilename(
                    initialdir = os.getcwd(), # Get current working directory
                    title = "Choose file",
                    filetypes = (("Binary files","*.bin"),("All files","*.*"))
                )
            )
            self.fileEntry.xview_moveto(1.0)

            if len(self.fileVar.get()) > 0:

                self.fileSize = os.path.getsize(self.fileVar.get())

                # Move file to current directory:
                newFileName = os.getcwd() + \
                        os.sep + \
                        os.path.basename(self.fileVar.get())
                try:
                    sh.copyfile(self.fileVar.get(), newFileName)
                except sh.SameFileError:
                    pass

                self.filename = os.path.basename(newFileName)
                self.printd(
                    "Target binary:\n\tFile: {}"\
                    "\n\tSize: {} bytes"\
                    "\n\tCopied as \"{}\" for flashing".\
                    format(
                        self.fileVar.get(),
                        self.fileSize,
                        self.filename
                    )
                )
                self._checkReady()
            else:
                self._inactive()
        except Exception as e:
            self.printx(e)
            self._inactive()

    def _setWidgetState(self, state):
        """
        Set the state of the interface widgets (entries, file chooser button...)
        to STATE (either tk.NORMAL or tk.DISABLED).
        """
        for widget in self.setupWidgets:
            widget.config(state = state)

    def _inactive(self):
        """
        Set the widget as not ready to launch a firmware update.
        """
        self.startButton.config(text = "Start", command = self._start,
            state = tk.DISABLED)
        self.statusLabel.config(
            text = self.inactiveLabelConfig['text'],
            style = "FirmwareInactive.TLabel"
        )
        self._setWidgetState(tk.NORMAL)
        self.status = self.INACTIVE

    def _ready(self):
        """
        Set the widget as ready to launch an update.
        """
        self.startButton.config(text = "Start", command = self._start,
            state = tk.NORMAL)
        self.statusLabel.config(
            text = self.readyLabelConfig['text'],
            style = "FirmwareReady.TLabel"
        )
        self._setWidgetState(tk.NORMAL)
        self.status = self.READY

    def _live(self):
        """
        Set the widget as currently running a firmware update.
        """
        self.startButton.config(text = "Stop", command = self._stop,
            state = tk.NORMAL)
        self.statusLabel.config(
            text = self.liveLabelConfig['text'],
            style = "FirmwareLive.TLabel"
        )
        self._setWidgetState(tk.DISABLED)
        self.status = self.LIVE

    def _checkReady(self, *args):
        """
        Check whether the widget is ready to launch a firmware update and update
        its state accordingly. ARGS is ignored
        """
        if len(self.filename) > 0 and len(self.version.get()) > 0 \
            and self.fileSize > 0:
            self._ready()
        elif self.fileSize == 0 and len(self.filename) > 0:
            self.printx(RuntimeError("Given file \"{}\" is empty".format(
                self.filename)))
        else:
            self._inactive()

# Slave list ===================================================================
class SlaveListWidget(ttk.Frame, pt.PrintClient):
    """
    GUI front-end for the FC Slave List display.
    """
    SYMBOL = "[SL]"

    def __init__(self, master, network, pqueue):
        """
        Create a new SlaveList widget.

        MASTER := Tkinter parent widget
        NETWORK := NetworkAbstraction being used
        PQUEUE := Queue object for I-P printing
        """

        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ...............................................................
        self.network = network

        self.main = ttk.LabelFrame(self, text = "Slave List")
        self.main.pack(fill = tk.BOTH, expand = True, padx = 10, pady = 5)

        self.main.grid_rowconfigure(1, weight = 1)
        self.main.grid_columnconfigure(0, weight = 1)

        # Use component style defaults for fonts; avoid mixing extra font kwargs to prevent duplicates

        # Options ..............................................................
        self.optionsFrame = ttk.Frame(self.main)
        self.optionsFrame.grid(row = 2, sticky = "EW")

        self.sortButton = ttk.Button(self.optionsFrame, text = "Sort",
            command = self.sort, style="TButton")
        self.sortButton.pack(side = tk.LEFT, padx = 10)

        self.selectAllButton = ttk.Button(self.optionsFrame, text = "Select All",
            command = self._selectAll, style="TButton")
        self.selectAllButton.pack(side = tk.LEFT, padx = 10)

        self.deselectAllButton = ttk.Button(self.optionsFrame,
            text = "Deselect All", command = self._deselectAll,
            style="Secondary.TButton")
        self.deselectAllButton.pack(side = tk.LEFT, padx = 10)

        self.autoVar = tk.BooleanVar()
        self.autoVar.set(True)
        self.autoButton = ttk.Checkbutton(self.optionsFrame,
            text = "Move on Change", variable = self.autoVar)
        self.autoButton.pack(side = tk.RIGHT, padx = 10)

        # Slave list ...........................................................
        self.slaveList = ttk.Treeview(self.main, selectmode = "extended")
        self.slaveList["columns"] = \
            ("Index","Name","MAC","Status","Fans", "Version")

        # Configure row height dynamically
        # See: https://stackoverflow.com/questions/26957845/
        #       ttk-treeview-cant-change-row-height
        self.listFontSize = gus.typography["label_small"]["font"][1]
        font = fnt.Font(font=gus.typography["label_small"]["font"])  # base font for row height
        self.style = ttk.Style(self.winfo_toplevel())
        self.style.configure('Treeview',
            rowheight = font.metrics()['linespace'] + 2)

        # Create columns:
        self.slaveList.column('#0', width = 20, stretch = False)
        self.slaveList.column("Index", width = 20, anchor = "center")
        self.slaveList.column("Name", width = 20, anchor = "center")
        self.slaveList.column("MAC", width = 80, anchor = "center")
        self.slaveList.column("Status", width = 70, anchor = "center")
        self.slaveList.column("Fans", width = 50, stretch = True,
            anchor = "center")
        self.slaveList.column("Version", width = 50, anchor = "center")

        # Configure column headings:
        self.slaveList.heading("Index", text = "Index")
        self.slaveList.heading("Name", text = "Name")
        self.slaveList.heading("MAC", text = "MAC")
        self.slaveList.heading("Status", text = "Status")
        self.slaveList.heading("Fans", text = "Fans")
        self.slaveList.heading("Version", text = "Version")

        # Configure tags:
        code_font_regular = (gus.typography["code"]["font"][0], self.listFontSize, "normal")
        code_font_bold = (gus.typography["code"]["font"][0], self.listFontSize, "bold")

        self.slaveList.tag_configure(
            s.SS_CONNECTED,
            background = s.BACKGROUNDS[s.SS_CONNECTED],
            foreground = s.FOREGROUNDS[s.SS_CONNECTED],
            font = code_font_regular)

        self.slaveList.tag_configure(
            s.SS_UPDATING,
            background = s.BACKGROUNDS[s.SS_UPDATING],
            foreground = s.FOREGROUNDS[s.SS_UPDATING],
            font = code_font_bold)

        self.slaveList.tag_configure(
            s.SS_DISCONNECTED,
            background = s.BACKGROUNDS[s.SS_DISCONNECTED],
            foreground = s.FOREGROUNDS[s.SS_DISCONNECTED],
            font = code_font_bold)

        self.slaveList.tag_configure(
            s.SS_KNOWN,
            background = s.BACKGROUNDS[s.SS_KNOWN],
            foreground = s.FOREGROUNDS[s.SS_KNOWN],
            font = code_font_bold)

        self.slaveList.tag_configure(
            s.SS_AVAILABLE,
            background = s.BACKGROUNDS[s.SS_AVAILABLE],
            foreground = s.FOREGROUNDS[s.SS_AVAILABLE],
            font = code_font_regular)

        # Configure striped rows for better readability
        stripe_bg = gus.SURFACE_2 if hasattr(gus, 'SURFACE_2') else "#f8f9fa"
        self.slaveList.tag_configure(
            "stripe_even",
            background = gus.SURFACE_1 if hasattr(gus, 'SURFACE_1') else "#ffffff"
        )
        self.slaveList.tag_configure(
            "stripe_odd", 
            background = stripe_bg
        )

        # Save previous selection:
        self.oldSelection = None

        # Bind command:
        self.slaveList.bind('<Double-1>', self._onDoubleClick)
        self.slaveList.bind('<Control-a>', self._selectAll)
        self.slaveList.bind('<Control-A>', self._selectAll)
        self.slaveList.bind('<Control-d>', self._deselectAll)
        self.slaveList.bind('<Control-D>', self._deselectAll)

        self.slaveList.grid(row = 1, sticky = "NEWS")

        # DATA -------------------------------------------------------------
        self.slaves = {}
        self.indices = []
        self.numSlaves = 0

        self.callback = lambda i: None
        self.testi = 0

    # API ......................................................................
    def slavesIn(self, S):
        """
        Process new slave vector S. See standards.py for form.
        """
        size = len(S)
        if size%s.SD_LEN != 0:
            raise ValueError("Slave vector size is not a multiple of {}".format(
                s.SD_LEN))

        for i in range(0, size, s.SD_LEN):
            slave = tuple(S[i:i+s.SD_LEN])
            index = slave[s.SD_INDEX]
            if index not in self.slaves:
                self.addSlave(slave)
            else:
                self.updateSlave(slave)

    def addSlave(self, slave):
        """
        Add SLAVE to the list. ValueError is raised if a slave with that index
        already exists. SLAVE is expected to be a tuple (or list) of the form
            (INDEX, NAME, MAC, STATUS, FANS, VERSION)
        Where INDEX is an integer that is expected to be unique among slaves,
        MAC and VERSION are strings, STATUS is one of the status codes
        defined as class attributes of this class, FANS is an integer.
        """
        if slave[s.SD_INDEX] in self.slaves:
            raise ValueError("Repeated Slave index {}".format(slave[s.SD_INDEX]))
        elif slave[s.SD_STATUS] not in s.SLAVE_STATUSES:
            raise ValueError("Invalid status tag \"{}\"".format(
                slave[s.SD_STATUS]))
        else:
            index = slave[s.SD_INDEX]
            # Determine stripe tag based on current row count
            stripe_tag = "stripe_even" if len(self.slaves) % 2 == 0 else "stripe_odd"
            # Combine status tag with stripe tag
            tags = (slave[s.SD_STATUS], stripe_tag)
            
            iid = self.slaveList.insert('', 'end',  # Insert at end for proper ordering
                values = (index + 1, slave[s.SD_NAME], slave[s.SD_MAC],
                    s.SLAVE_STATUSES[slave[s.SD_STATUS]], slave[s.SD_FANS],
                    slave[s.SD_VERSION]),
                tags = tags)
            self.slaves[index] = slave + (iid,)
            self.indices.append(index)

    def addSlaves(self, slaves):
        """
        Iterate over SLAVES and add each Slave to the list. ValueError is
        raised if two slaves share the same index.
        """
        for slave in slaves:
            self.addSlave(slave)

    def updateSlave(self, slave):
        """
        Modify the entry on SLAVE. KeyError is raised if there is no slave
        with SLAVE's index.
        """
        index = slave[s.SD_INDEX]
        iid = self.slaves[index][-1]

        self.slaveList.item(
            iid, values = (index + 1, slave[s.SD_NAME], slave[s.SD_MAC],
                s.SLAVE_STATUSES[slave[s.SD_STATUS]], slave[s.SD_FANS],
                slave[s.SD_VERSION]),
            tag = slave[s.SD_STATUS])

        self.slaves[index] = slave + (iid,)

        if self.autoVar.get() \
                and slave[s.SD_STATUS] != self.slaves[index][s.SD_STATUS]:
            self.slaveList.move(iid, '', 0)

    def updateSlaves(self, slaves):
        """
        Iterate over SLAVES and update the existing entry on each one.
        ValueError is raised if one slave's index is not found.
        """
        for slave in slaves:
            self.updateSlave(slave)

    def setStatus(self, index, status):
        """
        Modify only the status of the Slave at index INDEX to STATUS.
        """
        slave = self.slaves[index]
        self.slaves[index] = slave[:s.SD_STATUS] + (status,) \
            + slave[s.SD_STATUS + 1:]

        self.slaveList.item(slave[-1],
            values = (index + 1, slave[s.SD_MAC], s.SLAVE_STATUSES[status],
                slave[s.SD_FANS], slave[s.SD_VERSION]),
            tag = status)

        if self.autoVar.get():
            self.slaveList.move(self.slaves[index][-1], '', 0)

    def connected(self):
        """
        To be called when the network changes from disconnected to connected.
        """
        pass

    def disconnected(self):
        """
        To be called when the network changes from connected to disconnected.
        """
        self.clear()

    def clear(self):
        """
        Empty the list.
        """
        for index, slave in self.slaves.items():
            self.slaveList.delete(slave[-1])
        self.slaves = {}
        self.indices = []

    def selected(self, status = None):
        """
        Return a tuple of the indices of slaves selected. STATUS (optional)
        returns a list of only the indices of slaves with such status code, if
        any exist.
        """
        selected = ()
        for iid in self.slaveList.selection():
            if status is None \
                or self.slaveList.item(iid)['values'][s.SD_STATUS] == status:
                selected += (self.slaveList.item(iid)['values'][s.SD_INDEX]-1, )
        return selected

    def sort(self):
        """
        Sort the Slaves in ascending or descending (toggle) order of index.
        """
        self.indices.reverse()
        for index in self.indices:
            self.slaveList.move(self.slaves[index][-1], '', 0)


    # Internal methods .........................................................
    def _onDoubleClick(self, *A):
        if len(self.slaves) > 0:
            selected = self.selected()
            if len(selected) > 0:
                self.callback(selected[0])


    def _selectAll(self, *A):
        for index, slave in self.slaves.items():
            self.slaveList.selection_add(slave[-1])

    def _deselectAll(self, *A):
        self.slaveList.selection_set(())

    def __testF1(self):
        """ Provisional testing method for development """
        self.slavesIn(TEST_VECTORS[self.testi%len(TEST_VECTORS)])
        self.testi += 1

# Network status bar ===========================================================
class StatusBarWidget(ttk.Frame, pt.PrintClient):
    """
    GUI front-end for the FC "status bar."
    """
    SYMBOL = "[SB]"

    TOTAL = 100
    CONNECTED_STR = "Connected"
    DISCONNECTED_STR = "Disconnected"

    def __init__(self, master, shutdown, pqueue):
        """
        Horizontal bar that contains a breakdown of all slave statuses in
        the network, plus a connect/disconnect button.

        MASTER := Tkinter parent widget
        SHUTDOWN := Method to call when the shutdown button is pressed
        PQUEUE := Queue object to be used for I-P printing
        """
        ttk.Frame.__init__(self, master)
        pt.PrintClient.__init__(self, pqueue)

        # Setup ...............................................................

        # Status counters ......................................................
        self.statusFrame = ttk.Frame(self, relief = tk.SUNKEN, borderwidth = 0)
        self.statusFrame.pack(side = tk.LEFT)

        self.statusFrames = {}
        self.statusVars, self.statusLabels, self.statusDisplays  = {}, {}, {}

        for code, name in ((self.TOTAL, "Total"),) \
            + tuple(s.SLAVE_STATUSES.items()):
            self.statusFrames[code] = ttk.Frame(self.statusFrame)
            self.statusFrames[code].pack(side = tk.LEFT, padx = 5, pady = 1)

            self.statusVars[code] = tk.IntVar()
            self.statusVars[code].set(0)

            # Create per-status styles for label and display
            _style = ttk.Style(self)
            _label_style = f"StatusBarLabel-{code}.TLabel"
            _display_style = f"StatusBarDisplay-{code}.TLabel"
            _fg_color = s.FOREGROUNDS[code] if code in s.FOREGROUNDS else TEXT_PRIMARY
            _style.configure(_label_style, foreground=_fg_color)
            _style.configure(_display_style, foreground=_fg_color, relief='sunken', borderwidth=1)

            self.statusLabels[code] = ttk.Label(
                self.statusFrames[code],
                text = name,
                width = 14,
                style = _label_style,
            )
            self.statusLabels[code].pack(side = tk.TOP)

            self.statusDisplays[code] = ttk.Label(
                self.statusFrames[code],
                textvariable = self.statusVars[code],
                style = _display_style,
            )
            self.statusDisplays[code].pack(side = tk.TOP, fill = tk.X, padx = 2)

        self.connectionVar = tk.StringVar()
        self.connectionVar.set("[NO CONNECTION]")
        self.connectionLabel = ttk.Label(self.statusFrame,
            textvariable = self.connectionVar, width = 11,
            style = "Sunken.TLabel")
        self.connectionLabel.pack(side = tk.RIGHT, fill = tk.Y, pady = 3,
            padx = 6)
        self.status = s.SS_DISCONNECTED

        # Buttons ..............................................................
        self._shutdownCallback = shutdown

        self.buttonFrame = ttk.Frame(self)
        self.buttonFrame.pack(side = tk.RIGHT, fill = tk.Y)

        self.shutdownButton = ttk.Button(self.buttonFrame, text = "SHUTDOWN",
            command = self._onShutdown, style = "Secondary.TButton")
        self.shutdownButton.pack(side = tk.RIGHT, fill = tk.Y)

        # Slave data:
        self.slaves = {}

        # Initialize:
        self.disconnected()

    # API ......................................................................
    def networkIn(self, N):
        """
        Process a new network status vector.
        """
        connected = N[0]
        if not connected and self.status == s.SS_CONNECTED:
            self.disconnected()
        if connected and self.status == s.SS_DISCONNECTED:
            self.connected()

    def slavesIn(self, S):
        """
        Process a new slaves status vector.
        """
        size = len(S)
        for offset in range(0, size, s.SD_LEN):
            index = S[offset + s.SD_INDEX]
            status = S[offset + s.SD_STATUS]
            if index in self.slaves:
                if self.slaves[index] != status:
                    self.addCount(self.slaves[index], -1)
                    self.addCount(status, 1)
                    self.slaves[index] = status
            else:
                self.addTotal(1)
                self.addCount(status, 1)
                self.slaves[index] = status

    def connected(self):
        """
        Handle network switching to connected.
        """
        self.connectionVar.set(self.CONNECTED_STR)
        style = ttk.Style(self.connectionLabel)
        style.configure('NetworkConnected.TLabel',
                        relief='sunken',
                        foreground=s.FOREGROUNDS[s.SS_CONNECTED],
                        background=s.BACKGROUNDS[s.SS_CONNECTED])
        self.connectionLabel.configure(style='NetworkConnected.TLabel')
        self.status = s.SS_CONNECTED

    def disconnected(self):
        """
        Handle network switching to disconnected.
        """
        self.clear()
        self.connectionVar.set(self.DISCONNECTED_STR)
        style = ttk.Style(self.connectionLabel)
        style.configure('NetworkDisconnected.TLabel',
                        relief='sunken',
                        foreground=s.FOREGROUNDS[s.SS_DISCONNECTED],
                        background=s.BACKGROUNDS[s.SS_DISCONNECTED])
        self.connectionLabel.configure(style='NetworkDisconnected.TLabel')
        self.status = s.SS_DISCONNECTED

    def setCount(self, status, count):
        """
        Set the status counter that corresponds to status code STATUS to COUNT.
        """
        self.statusVars[status].set(count)

    def addCount(self, status, count = 1):
        """
        Add COUNT (defaults to 1) to the current value in the status counter
        that corresponds to status code STATUS.
        """
        self.statusVars[status].set(count + self.statusVars[status].get())

    def getCount(self, status):
        """
        Return the current count corresponding to status code STATUS.
        """
        return self.statusVars[status].get()

    def setTotal(self, count):
        """
        Set the total counter to COUNT.
        """
        self.statusVars[self.TOTAL].set(count)

    def addTotal(self, count = 1):
        """
        Add COUNT (defaults to 1) to the total counter.
        """
        self.statusVars[self.TOTAL].set(count \
            + self.statusVars[self.TOTAL].get())

    def getTotal(self):
        """
        Return the current total.
        """
        return self.statusVars[self.TOTAL].get()

    def clear(self):
        """
        Reset data
        """
        for count in self.statusVars.values():
            count.set(0)
            self.slaves = {}

    def profileChange(self):
        self.clear()

    # Internal methods .........................................................
    def _onShutdown(self, *event):
        self._shutdownCallback()

## DEMO ########################################################################
if __name__ == "__main__":
    print("FCMkIV Network GUI demo started")
    print("[No Network GUI demo implemented]")
    print("FCMkIV Network GUI demo finished")

