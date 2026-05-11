"""
OpenMacro XTernal - Python Edition
High-level memory management: DataModel, LocalPlayer, caching.
"""

import json
import os
from typing import Optional

from .constants import OFFSETS_PATH, KNOWN_ROD_NAMES
from .process import ProcessManager
from .read import MemoryReader


class GameMemory:
    """Manages connection to the Roblox game state via memory reading."""

    def __init__(self):
        self.process = ProcessManager()
        self.offsets: dict = {}
        self.reader: Optional[MemoryReader] = None

        # Cached addresses
        self._data_model = 0
        self._local_player = 0
        self._player_gui = 0
        self._workspace_root = 0
        self._world_statuses = 0
        self._hotbar_gui = 0

        self.rod_name = ""

    @property
    def is_ready(self) -> bool:
        return self.process.is_attached and len(self.offsets) > 0

    def load_offsets(self, path: str = ""):
        """Load offsets from the JSON file."""
        if not path:
            path = OFFSETS_PATH

        # Try to resolve path relative to the package
        if not os.path.exists(path):
            alt_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "..", "settings", "offsets.json"
            )
            if os.path.exists(alt_path):
                path = alt_path

        if not os.path.exists(path):
            raise FileNotFoundError(f"offsets.json not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            self.offsets = json.load(f)

        if "FakeDataModelPointer" not in self.offsets:
            raise ValueError("FakeDataModelPointer not found in offsets")

        self.reader = MemoryReader(self.process, self.offsets)

    def attach(self, pid: int = 0) -> bool:
        """Attach to Roblox and load offsets."""
        self.reset_cache()
        self.process.attach(pid)
        self.load_offsets()
        self.rod_name = self.get_hotbar_rod_name()
        return True

    def detach(self):
        """Detach and reset all state."""
        self.reset_cache()
        self.process.detach()
        self.rod_name = ""

    def reset_cache(self):
        """Clear all cached addresses."""
        self._data_model = 0
        self._local_player = 0
        self._player_gui = 0
        self._workspace_root = 0
        self._world_statuses = 0
        self._hotbar_gui = 0

    def _offset(self, key: str) -> int:
        """Get an offset value."""
        val = self.offsets.get(key, "0x0")
        if isinstance(val, str):
            if val == "UNKNOWN":
                return 0
            return int(val, 16)
        return int(val)

    # --- DataModel resolution ---

    def get_data_model(self) -> int:
        if self._data_model:
            return self._data_model
        if not self.is_ready:
            return 0

        dm = self._resolve_via_fake_data_model()
        if not self.reader.is_valid_pointer(dm):
            dm = self._resolve_via_visual_engine()

        if self.reader.is_valid_pointer(dm):
            self._data_model = dm
        return dm

    def _resolve_via_fake_data_model(self) -> int:
        fdm_offset = self._offset("FakeDataModelPointer")
        fdm_to_dm = self._offset("FakeDataModelToDataModel")

        fake_dm = self.process.read_pointer(self.process.base_address + fdm_offset)
        if not self.reader.is_valid_pointer(fake_dm):
            return 0
        return self.process.read_pointer(fake_dm + fdm_to_dm)

    def _resolve_via_visual_engine(self) -> int:
        for key in ["VisualEnginePointer", "VisualEngineToDataModel1", "VisualEngineToDataModel2"]:
            if key not in self.offsets:
                return 0

        ve_ptr = self._offset("VisualEnginePointer")
        ve = self.process.read_pointer(self.process.base_address + ve_ptr)
        if not self.reader.is_valid_pointer(ve):
            return 0

        fdm = self.process.read_pointer(ve + self._offset("VisualEngineToDataModel1"))
        if not self.reader.is_valid_pointer(fdm):
            return 0

        return self.process.read_pointer(fdm + self._offset("VisualEngineToDataModel2"))

    # --- Players / LocalPlayer ---

    def get_players(self) -> int:
        dm = self.get_data_model()
        if not dm:
            return 0
        for child in self.reader.read_children(dm):
            if self.reader.read_class_name(child) == "Players":
                return child
        return 0

    def get_local_player(self) -> int:
        if self._local_player:
            return self._local_player
        players = self.get_players()
        if not players:
            return 0
        lp_offset = self._offset("LocalPlayer")
        lp = self.process.read_pointer(players + lp_offset)
        if lp:
            self._local_player = lp
        return lp

    def get_player_gui(self) -> int:
        if self._player_gui:
            return self._player_gui
        lp = self.get_local_player()
        if not lp:
            return 0
        for child in self.reader.read_children(lp):
            if self.reader.read_class_name(child) == "PlayerGui":
                self._player_gui = child
                return child
        return 0

    # --- Workspace ---

    def get_workspace(self) -> int:
        if self._workspace_root:
            return self._workspace_root
        dm = self.get_data_model()
        if not dm:
            return 0
        for child in self.reader.read_children(dm):
            name = self.reader.read_instance_name(child)
            cls = self.reader.read_class_name(child)
            if name == "Workspace" or cls == "Workspace":
                self._workspace_root = child
                return child
        return 0

    # --- Hotbar / Rod ---

    def get_hotbar_gui(self) -> int:
        if self._hotbar_gui:
            return self._hotbar_gui
        lp = self.get_local_player()
        if not lp:
            return 0
        pg = self.reader.find_child_by_class(lp, "PlayerGui")
        if not pg:
            return 0
        bp = self.reader.find_child_by_name(pg, "backpack")
        if not bp:
            return 0
        hotbar = self.reader.find_child_by_name(bp, "hotbar")
        if hotbar:
            self._hotbar_gui = hotbar
        return hotbar

    def get_hotbar_rod_name(self) -> str:
        """Detect the equipped rod from the hotbar."""
        hotbar = self.get_hotbar_gui()
        if not hotbar:
            return ""

        fallback = ""
        for slot_ptr in self.reader.read_children(hotbar):
            if self.reader.read_class_name(slot_ptr) != "ImageButton":
                continue
            if self.reader.read_instance_name(slot_ptr) != "ItemTemplate":
                continue

            name_inst = self.reader.find_child_by_name(slot_ptr, "ItemName")
            if not name_inst:
                continue

            tool_text = self.reader.read_gui_text(name_inst)
            pure_name = self._extract_pure_rod_name(tool_text)
            if pure_name:
                return pure_name

            normalized = MemoryReader.normalize_text(tool_text)
            if normalized and not fallback:
                fallback = normalized

        return fallback

    def _extract_pure_rod_name(self, text: str) -> str:
        clean = MemoryReader.normalize_text(text)
        if not clean:
            return ""
        for rod_name in KNOWN_ROD_NAMES:
            if rod_name in clean:
                return rod_name
        for line in clean.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line == "Pinion's Aria" or "rod" in line.lower():
                return line
        return ""

    # --- Character / Equipped tool ---

    def get_character_model(self) -> int:
        workspace = self.get_workspace()
        if not workspace:
            return 0
        lp = self.get_local_player()
        if not lp:
            return 0
        player_name = self.reader.read_instance_name(lp)
        if not player_name or player_name == "<null>":
            return 0
        return self.reader.find_child_by_name(workspace, player_name)

    def get_equipped_tool_name(self) -> str:
        character = self.get_character_model()
        if not character:
            return ""
        for child in self.reader.read_children(character):
            if self.reader.read_class_name(child) == "Tool":
                return self.reader.read_instance_name(child)
        return ""

    def is_anything_equipped(self) -> bool:
        character = self.get_character_model()
        if not character:
            return False
        for child in self.reader.read_children(character):
            if self.reader.read_class_name(child) == "Tool":
                return True
        return False

    def is_rod_equipped(self) -> bool:
        equipped = self.get_equipped_tool_name()
        if not equipped:
            return False
        if self.rod_name:
            return equipped == self.rod_name
        return "rod" in equipped.lower()

    # --- World Status ---

    def get_world_statuses(self) -> int:
        if self._world_statuses:
            return self._world_statuses
        lp = self.get_local_player()
        if not lp:
            return 0
        pg = self.reader.find_child_by_class(lp, "PlayerGui")
        if not pg:
            return 0
        hud = self.reader.find_child_by_name(pg, "hud")
        if not hud:
            return 0
        safezone = self.reader.find_child_by_name(hud, "safezone")
        if not safezone:
            return 0
        ws = self.reader.find_child_by_name(safezone, "worldstatuses")
        if ws:
            self._world_statuses = ws
        return ws

    def get_world_status_text(self, status_name: str) -> str:
        ws = self.get_world_statuses()
        if not ws:
            return ""
        status_addr = self.reader.find_child_by_name(ws, status_name)
        if not status_addr:
            return ""
        label_addr = self.reader.find_child_by_name(status_addr, "label")
        if not label_addr:
            return ""
        text = self.reader.read_gui_text(label_addr)
        return MemoryReader.normalize_text(text)

    def is_night_cycle(self) -> bool:
        cycle_text = self.get_world_status_text("4_cycle").lower()
        return "night" in cycle_text

    def is_aurora_active(self) -> bool:
        for status in ["2_event", "3_weather"]:
            text = self.get_world_status_text(status).lower()
            if "aurora" in text:
                return True
        return False

    # --- Fishing GUI ---

    def get_reel_gui(self) -> int:
        pg = self.get_player_gui()
        if not pg:
            return 0
        return self.reader.find_child_by_name(pg, "reel")

    def is_reel_gui_visible(self, reel_gui: int = 0) -> bool:
        if not reel_gui:
            reel_gui = self.get_reel_gui()
        if not reel_gui:
            return False
        offset = self._offset("ScreenGuiEnabled")
        if not offset:
            return True
        return self.process.read_byte(reel_gui + offset) != 0
