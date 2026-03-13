import socket
import threading
import time
import random
import multiprocessing as mp
import sys
import os

sys.path.insert(0, os.path.join(os.getcwd(), "master"))

from fc.archive import FCArchive, broadcastIP, broadcastPort, broadcastPeriodMS, periodMS, maxFans, defaultIPAddress, passcode, savedSlaves, SV_name, SV_mac, SV_maxFans
from fc.backend.mkiii.FCCommunicator import FCCommunicator
import fc.standards as s


class FakeSlave:
    def __init__(self, ip, bport, passcode, miso_port=60001, mosi_port=60002, fans=6):
        self.ip = ip
        self.bport = bport
        self.passcode = passcode
        self.miso_port = miso_port
        self.mosi_port = mosi_port
        self.mac = "AA:BB:CC:DD:EE:FF"
        self.version = "MkII-Test"
        self.fans = fans
        self.kp = 0.02
        self.ki = 0.001
        self.integrals = [0.0] * fans
        self.dc = [0.2] * fans
        self.min_dc = 0.2
        self.min_rpm = 1200
        self.max_rpm = 6000
        self.rpm_slope = (self.max_rpm - self.min_rpm) / (1.0 - self.min_dc)
        self.target = [None] * fans
        self.stop = threading.Event()
        self.bsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bsock.bind((ip, bport))
        self.miso_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.miso_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.miso_sock.bind((ip, miso_port))
        self.mosi_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mosi_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mosi_sock.bind((ip, mosi_port))
        self.master_listener_addr = None
        self.master_miso_addr = None
        self.data_index = 0
        self.mosi_index = 0
        self.miso_index = 0

    def _rpm_from_dc(self, d):
        if d <= 0.0:
            return 0
        if d < self.min_dc:
            return int(self.min_rpm)
        return int(self.min_rpm + (d - self.min_dc) * self.rpm_slope)

    def _send_broadcast_reply(self):
        if not self.master_listener_addr:
            return
        reply = f"A|{self.passcode}|{self.mac}|N|{self.miso_port}|{self.mosi_port}|{self.version}"
        self.bsock.sendto(reply.encode("ascii"), self.master_listener_addr)

    def _handle_broadcast(self):
        while not self.stop.is_set():
            try:
                data, src = self.bsock.recvfrom(512)
                msg = data.decode("ascii")
                parts = msg.split("|")
                if len(parts) >= 3 and parts[0] == "N" and parts[1] == self.passcode:
                    lport = int(parts[2])
                    self.master_listener_addr = (src[0], lport)
                    self._send_broadcast_reply()
                elif len(parts) >= 4 and parts[0] in ("C", "c") and parts[1] == self.passcode:
                    fan_id = int(parts[2])
                    target_rpm = int(parts[3])
                    if 0 <= fan_id < self.fans:
                        self.target[fan_id] = target_rpm
                elif len(parts) >= 5 and parts[0] in ("P", "p") and parts[1] == self.passcode:
                    rest = parts[2]
                    if rest.startswith("PISET"):
                        toks = rest.split(" ")
                        if len(toks) == 4:
                            fan_id = int(toks[1])
                            kp = float(toks[2])
                            ki = float(toks[3])
                            self.kp = kp
                            self.ki = ki
            except Exception:
                continue

    def _handle_mosi(self):
        while not self.stop.is_set():
            try:
                data, src = self.mosi_sock.recvfrom(1024)
                msg = data.decode("ascii")
                parts = msg.split("|")
                if len(parts) < 2:
                    continue
                index = int(parts[0])
                code = parts[1]
                self.mosi_index = index
                if index == 0 and code == "H":
                    payload = parts[2] if len(parts) >= 3 else ""
                    try:
                        misop_str = payload.split(",")[0]
                        misop_master = int(misop_str)
                    except Exception:
                        misop_master = src[1]
                    self.master_miso_addr = (src[0], misop_master)
                    kmsg = f"0|K"
                    self.miso_sock.sendto(kmsg.encode("ascii"), self.master_miso_addr)
                    hmsg = f"0|H"
                    self.miso_sock.sendto(hmsg.encode("ascii"), self.master_miso_addr)
                elif code.startswith("S"):
                    payload = parts[2] if len(parts) >= 3 else ""
                    if payload.startswith("D:"):
                        rest = payload[2:]
                        dc_str, sel = rest.split(":")
                        d = float(dc_str)
                        for i, ch in enumerate(sel):
                            if ch == "1" and i < self.fans:
                                self.dc[i] = max(self.min_dc, min(1.0, d))
                    elif payload.startswith("F:"):
                        values = payload[2:].split(",")
                        for i in range(min(len(values), self.fans)):
                            self.dc[i] = max(self.min_dc, min(1.0, float(values[i])))
                elif code == "Q":
                    preply = f"{index}|P"
                    self.miso_sock.sendto(preply.encode("ascii"), self.master_miso_addr)
            except Exception:
                continue

    def _miso_updates(self):
        while not self.stop.is_set():
            time.sleep(0.1)
            for i in range(self.fans):
                if self.target[i] is not None:
                    err = float(self.target[i] - self._rpm_from_dc(self.dc[i]))
                    self.integrals[i] += err
                    adj = self.kp * err + self.ki * self.integrals[i]
                    self.dc[i] = max(self.min_dc, min(1.0, self.dc[i] + adj / 2000.0))
            rpms = [str(self._rpm_from_dc(d)) for d in self.dc]
            dcs = [f"{v:.4f}" for v in self.dc]
            self.data_index += 1
            self.miso_index += 1
            msg = f"{self.miso_index}|T|{self.data_index}|{','.join(rpms)}|{','.join(dcs)}"
            if self.master_miso_addr:
                try:
                    self.miso_sock.sendto(msg.encode("ascii"), self.master_miso_addr)
                except Exception:
                    pass

    def start(self):
        self.tb = threading.Thread(target=self._handle_broadcast, daemon=True)
        self.tm = threading.Thread(target=self._handle_mosi, daemon=True)
        self.to = threading.Thread(target=self._miso_updates, daemon=True)
        self.tb.start(); self.tm.start(); self.to.start()

    def shutdown(self):
        self.stop.set()
        try:
            self.bsock.close(); self.miso_sock.close(); self.mosi_sock.close()
        except Exception:
            pass


def test_comm_pid_integration():
    cmd_recv, cmd_send = mp.Pipe(False)
    ctl_recv, ctl_send = mp.Pipe(False)
    fb_recv, fb_send = mp.Pipe(False)
    sl_recv, sl_send = mp.Pipe(False)
    net_recv, net_send = mp.Pipe(False)
    pqueue = mp.Queue()
    archive = FCArchive(pqueue, "IV-1")
    prof = archive.profile()
    prof[broadcastIP] = "127.0.0.1"
    prof[defaultIPAddress] = "127.0.0.1"
    prof[broadcastPort] = 65000
    prof[broadcastPeriodMS] = 200
    prof[periodMS] = 100
    fans = min(prof[maxFans], 6)
    prof[savedSlaves] = ({SV_name: "TestSlave", SV_mac: "AA:BB:CC:DD:EE:FF", SV_maxFans: fans},)
    slave = FakeSlave("127.0.0.1", prof[broadcastPort], prof[passcode], fans=fans)
    slave.start()
    time.sleep(0.2)
    comm = FCCommunicator(
        prof,
        cmd_recv,
        ctl_recv,
        fb_send,
        sl_send,
        net_send,
        pqueue,
    )
    comm.setSlaveStatus(comm.slaves[0], s.SS_KNOWN, False, ("127.0.0.1", slave.miso_port, slave.mosi_port, slave.version))
    time.sleep(1.0)
    stats_before = comm.get_performance_stats()
    comm.sendChase(1800, fanID=0)
    time.sleep(0.5)
    comm.sendPISet(0, 0.03, 0.002)
    start = time.time()
    rpms = []
    dcs = []
    timeout = time.time() + 5.0
    while time.time() < timeout:
        if fb_recv.poll():
            vec = fb_recv.recv()
            half = len(vec) // 2
            rpms = vec[:half]
            dcs = vec[half:]
            break
        time.sleep(0.05)
    latency_s = time.time() - start
    stats_after = comm.get_performance_stats()
    slave.shutdown()
    assert rpms and dcs
    assert rpms[0] >= 1000
    assert 0.2 <= dcs[0] <= 1.0
    report = {
        "network": {
            "message_send_time": stats_after.get("message_send_time", {}),
            "message_receive_time": stats_after.get("message_receive_time", {}),
            "network_latency": stats_after.get("network_latency", {}),
            "error_count": stats_after.get("error_count", 0),
            "total_messages": stats_after.get("total_messages", 0),
            "initial_errors": stats_before.get("error_count", 0),
        },
        "pid": {
            "target": 1800,
            "rpm_sample": rpms[:fans],
            "dc_sample": dcs[:fans],
            "response_latency_s": latency_s,
        },
    }
    print("TEST_REPORT_BEGIN")
    print(report)
    print("TEST_REPORT_END")


if __name__ == "__main__":
    test_comm_pid_integration()
