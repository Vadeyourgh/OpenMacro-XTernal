"""
OpenMacro XTernal - Python Edition
Memory read helpers for navigating Roblox instance tree.
"""

import re
from typing import Optional, List


class MemoryReader:
    """High-level memory reader for Roblox instance tree navigation."""

    def __init__(self, process_mgr, offsets: dict):
        self.pm = process_mgr
        self.offsets = offsets

    def _offset(self, key: str) -> int:
        """Get offset value by key, converting hex string to int."""
        val = self.offsets.get(key, "0x0")
        if isinstance(val, str):
            if val == "UNKNOWN":
                return 0
            return int(val, 16)
        return int(val)

    def read_string(self, address: int) -> str:
        """Read a std::string from the given address."""
        string_length_offset = self._offset("StringLength")
        length = self.pm.read_int(address + string_length_offset)

        if length <= 0 or length > 1000:
            return ""

        data_addr = address
        if length > 15:
            data_addr = self.pm.read_pointer(address)

        if not data_addr:
            return ""

        raw = self.pm.read_memory(data_addr, length)
        if not raw:
            return ""

        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def read_instance_name(self, instance_addr: int) -> str:
        """Read the Name property of a Roblox instance."""
        name_offset = self._offset("Name")
        name_ptr = self.pm.read_pointer(instance_addr + name_offset)
        if not name_ptr:
            return "<null>"
        return self.read_string(name_ptr)

    def read_class_name(self, instance_addr: int) -> str:
        """Read the ClassName of a Roblox instance."""
        class_desc_offset = self._offset("ClassDescriptor")
        class_desc = self.pm.read_pointer(instance_addr + class_desc_offset)
        if not class_desc:
            return "<unknown>"

        class_name_offset = self._offset("ClassDescriptorToClassName")
        class_name_ptr = self.pm.read_pointer(class_desc + class_name_offset)
        if not class_name_ptr:
            return "<unknown>"

        return self.read_string(class_name_ptr)

    def read_children(self, instance_addr: int) -> List[int]:
        """Read the children list of a Roblox instance."""
        children_offset = self._offset("Children")
        list_ptr = self.pm.read_pointer(instance_addr + children_offset)
        if not list_ptr:
            return []

        array_start = self.pm.read_pointer(list_ptr)
        array_end = self.pm.read_pointer(list_ptr + 8)

        if not array_start or not array_end or array_end <= array_start:
            return []

        entry_size = 0x10
        num_children = (array_end - array_start) // entry_size

        if num_children < 0 or num_children > 1000:
            return []

        children = []
        current_addr = array_start
        for _ in range(num_children):
            child_ptr = self.pm.read_pointer(current_addr)
            if child_ptr:
                children.append(child_ptr)
            current_addr += entry_size

        return children

    def read_parent(self, instance_addr: int) -> int:
        """Read the Parent pointer of a Roblox instance."""
        parent_offset = self._offset("Parent")
        return self.pm.read_pointer(instance_addr + parent_offset)

    def find_child_by_name(self, instance_addr: int, name: str) -> int:
        """Find a child instance by name."""
        for child_ptr in self.read_children(instance_addr):
            if self.read_instance_name(child_ptr) == name:
                return child_ptr
        return 0

    def find_child_by_class(self, instance_addr: int, class_name: str) -> int:
        """Find a child instance by class name."""
        for child_ptr in self.read_children(instance_addr):
            if self.read_class_name(child_ptr) == class_name:
                return child_ptr
        return 0

    def find_descendant_by_name_and_class(
        self, root_addr: int, target_name: str, target_class: str = ""
    ) -> int:
        """BFS search for a descendant by name (and optionally class)."""
        queue = [root_addr]
        index = 0

        while index < len(queue):
            current = queue[index]
            index += 1

            current_name = self.read_instance_name(current)
            current_class = self.read_class_name(current)

            if current_name == target_name and (
                target_class == "" or current_class == target_class
            ):
                return current

            queue.extend(self.read_children(current))

        return 0

    def read_gui_text(self, instance_addr: int) -> str:
        """Read text content from a GUI element."""
        for key in ["TextLabelText", "ContentText"]:
            offset = self._offset(key)
            if offset:
                text = self.read_string(instance_addr + offset)
                if text:
                    return text
        return ""

    def read_frame_position_x(self, frame_addr: int) -> dict:
        """Read frame position (scale X and offset X)."""
        base = self._offset("FramePositionX")
        scale_x = self.pm.read_float(frame_addr + base)
        offset_x = self.pm.read_int(frame_addr + base + 0x4)
        return {"scale": scale_x, "offset": offset_x}

    def read_frame_size_x(self, frame_addr: int) -> dict:
        """Read frame size (scale X and offset X)."""
        base = self._offset("FrameSizeX")
        scale_x = self.pm.read_float(frame_addr + base)
        offset_x = self.pm.read_int(frame_addr + base + 0x4)
        return {"scale": scale_x, "offset": offset_x}

    def read_frame_size_y(self, frame_addr: int) -> float:
        """Read frame size scale Y."""
        base = self._offset("FrameSizeX")
        return self.pm.read_float(frame_addr + base + 0x8)

    def read_progress_bar_percent(self, frame_addr: int) -> float:
        """Read a progress bar's completion as a percentage."""
        size = self.read_frame_size_x(frame_addr)
        return max(0.0, min(100.0, size["scale"] * 100.0))

    def read_power_bar_percent(self, frame_addr: int) -> float:
        """Read power bar percentage (uses Y scale)."""
        scale_y = self.read_frame_size_y(frame_addr)
        return max(0.0, min(100.0, scale_y * 100.0))

    def is_valid_pointer(self, val: int) -> bool:
        """Check if a pointer looks valid (user-space range)."""
        return val != 0 and 0x10000 <= val <= 0x7FFFFFFFFFFF

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize GUI text (strip rich text tags, whitespace)."""
        text = text.replace("\r", "\n")
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n+", "\n", text)
        return text.strip()
