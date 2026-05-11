"""
OpenMacro XTernal - Python Edition
Process attachment and management via ctypes (Windows API).
"""

import ctypes
import ctypes.wintypes
import struct
import re

from .constants import ROBLOX_PROCESS_NAME

# Windows API constants
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
LIST_MODULES_ALL = 0x03
TH32CS_SNAPPROCESS = 0x00000002
MAX_PATH = 260

kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.wintypes.DWORD),
        ("cntUsage", ctypes.wintypes.DWORD),
        ("th32ProcessID", ctypes.wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", ctypes.wintypes.DWORD),
        ("cntThreads", ctypes.wintypes.DWORD),
        ("th32ParentProcessID", ctypes.wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("szExeFile", ctypes.c_char * MAX_PATH),
    ]


class ProcessManager:
    """Manages Roblox process attachment."""

    def __init__(self):
        self.h_process = None
        self.pid = 0
        self.base_address = 0

    @property
    def is_attached(self) -> bool:
        return self.h_process is not None and self.pid != 0 and self.base_address != 0

    def get_roblox_pid(self) -> int:
        """Find the PID of the running Roblox process."""
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == -1:
            return 0

        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

        try:
            if kernel32.Process32First(snapshot, ctypes.byref(entry)):
                while True:
                    exe_name = entry.szExeFile.decode("utf-8", errors="ignore")
                    if exe_name.lower() == ROBLOX_PROCESS_NAME.lower():
                        return entry.th32ProcessID
                    if not kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                        break
        finally:
            kernel32.CloseHandle(snapshot)

        return 0

    def attach(self, pid: int = 0) -> bool:
        """Attach to the Roblox process."""
        if pid == 0:
            pid = self.get_roblox_pid()
        if pid == 0:
            raise RuntimeError("Roblox is not running.")

        self.detach()
        self.pid = pid

        access = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
        handle = kernel32.OpenProcess(access, False, pid)
        if not handle:
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, pid
            )
        if not handle:
            raise RuntimeError(f"Failed to open process {pid}")

        self.h_process = handle

        # Get base address
        self.base_address = self._get_base_address()
        if not self.base_address:
            self.detach()
            raise RuntimeError(f"Failed to get base address for process {pid}")

        return True

    def detach(self):
        """Detach from the current process."""
        if self.h_process:
            kernel32.CloseHandle(self.h_process)
        self.h_process = None
        self.pid = 0
        self.base_address = 0

    def _get_base_address(self) -> int:
        """Get the base module address of the process."""
        h_mods = (ctypes.c_void_p * 1024)()
        cb_needed = ctypes.wintypes.DWORD()

        result = psapi.EnumProcessModulesEx(
            self.h_process,
            ctypes.byref(h_mods),
            ctypes.sizeof(h_mods),
            ctypes.byref(cb_needed),
            LIST_MODULES_ALL,
        )

        if not result:
            return 0

        return h_mods[0] or 0

    def read_memory(self, address: int, size: int) -> bytes:
        """Read raw bytes from process memory."""
        if not self.h_process:
            return b""

        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)

        success = kernel32.ReadProcessMemory(
            self.h_process,
            ctypes.c_void_p(address),
            buf,
            size,
            ctypes.byref(bytes_read),
        )

        if not success:
            return b""

        return buf.raw[:bytes_read.value]

    def read_pointer(self, address: int) -> int:
        """Read a pointer (8 bytes on x64) from process memory."""
        data = self.read_memory(address, 8)
        if len(data) < 8:
            return 0
        return struct.unpack("<Q", data)[0]

    def read_int(self, address: int) -> int:
        """Read a 4-byte signed integer."""
        data = self.read_memory(address, 4)
        if len(data) < 4:
            return 0
        return struct.unpack("<i", data)[0]

    def read_uint(self, address: int) -> int:
        """Read a 4-byte unsigned integer."""
        data = self.read_memory(address, 4)
        if len(data) < 4:
            return 0
        return struct.unpack("<I", data)[0]

    def read_byte(self, address: int) -> int:
        """Read a single byte."""
        data = self.read_memory(address, 1)
        if len(data) < 1:
            return 0
        return data[0]

    def read_float(self, address: int) -> float:
        """Read a 4-byte float."""
        data = self.read_memory(address, 4)
        if len(data) < 4:
            return 0.0
        return struct.unpack("<f", data)[0]

    def read_double(self, address: int) -> float:
        """Read an 8-byte double."""
        data = self.read_memory(address, 8)
        if len(data) < 8:
            return 0.0
        return struct.unpack("<d", data)[0]

    def get_roblox_version_hash(self) -> str:
        """Get the version hash from the running Roblox process path."""
        buf = ctypes.create_unicode_buffer(1024)
        size = ctypes.wintypes.DWORD(1024)

        h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, 0, self.pid)
        if not h_proc:
            return ""

        try:
            kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size))
            exe_path = buf.value
            match = re.search(r"(version-[a-f0-9]+)", exe_path)
            return match.group(1) if match else ""
        finally:
            kernel32.CloseHandle(h_proc)
