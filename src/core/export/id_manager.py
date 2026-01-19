"""LS-DYNA用のID管理クラス"""


class IDManager:
    """LS-DYNA用のID管理クラス

    Part ID、Material ID、Section IDなどを一元管理し、
    ID の割り当てと紐付けを行う。
    """

    def __init__(self):
        # Part ID カウンタ
        self._workpiece_pid_counter = 1  # ワークは1から順番
        self._tool_pid_base = 1100  # 工具は1101から（工程ごとに100番台）

        # Material ID カウンタ
        self._mid_counter = 1  # 通常材料は1から
        self._rigid_mid_counter = 9000  # 剛体材料は9000から

        # Section ID（固定）
        self._section_ids = {
            "SHELL": 1,  # elform=16
            "SOLID_TET": 2,  # elform=13
            "SOLID_HEX": 3,  # elform=2
        }

        # 紐付け管理
        self._part_to_material = {}  # PID -> MID
        self._part_to_section = {}  # PID -> SECID
        self._material_preset_to_mid = {}  # プリセットキー -> MID（共有用）
        self._rigid_constraint_to_mid = {}  # 制約条件 -> MID（剛体材料共有用）

    def get_next_workpiece_pid(self) -> int:
        """
        次のワークPIDを取得（1, 2, 3...）

        Returns:
            割り当てられたワークPID
        """
        pid = self._workpiece_pid_counter
        self._workpiece_pid_counter += 1
        return pid

    def get_tool_pid(self, step_order: int, tool_index: int) -> int:
        """
        工具PIDを取得

        工程番号とインデックスから工具のPIDを計算する。
        - 工程1の1番目工具 = 1101
        - 工程1の2番目工具 = 1102
        - 工程2の1番目工具 = 1201

        Args:
            step_order: 工程番号（1, 2, 3...）
            tool_index: 工具のインデックス（0, 1, 2...）

        Returns:
            割り当てられた工具PID
        """
        return self._tool_pid_base + (step_order * 100) + (tool_index + 1)

    def get_next_mid(self) -> int:
        """
        次の通常材料IDを取得

        Returns:
            割り当てられた材料ID
        """
        mid = self._mid_counter
        self._mid_counter += 1
        return mid

    def get_next_rigid_mid(self) -> int:
        """
        次の剛体材料IDを取得（9000, 9001...）

        Returns:
            割り当てられた剛体材料ID
        """
        mid = self._rigid_mid_counter
        self._rigid_mid_counter += 1
        return mid

    def get_or_create_material_id(self, material_preset: str) -> tuple[int, bool]:
        """
        材料プリセットに対応するMIDを取得（既存なら共有、新規なら作成）

        Args:
            material_preset: 材料プリセットキー（例: "SPCC", "SUS304"）

        Returns:
            (MID, is_new) のタプル
            - MID: 材料ID
            - is_new: 新規作成された場合True、既存の場合False
        """
        if material_preset in self._material_preset_to_mid:
            return self._material_preset_to_mid[material_preset], False

        # 新規MID作成
        mid = self.get_next_mid()
        self._material_preset_to_mid[material_preset] = mid
        return mid, True

    def get_or_create_rigid_material_id(self, constraint: str) -> tuple[int, bool]:
        """
        剛体材料の制約条件に対応するMIDを取得（既存なら共有、新規なら作成）

        Args:
            constraint: 制約条件（例: "fixed", "z-free"）

        Returns:
            (MID, is_new) のタプル
            - MID: 剛体材料ID
            - is_new: 新規作成された場合True、既存の場合False
        """
        if constraint in self._rigid_constraint_to_mid:
            return self._rigid_constraint_to_mid[constraint], False

        # 新規MID作成
        mid = self.get_next_rigid_mid()
        self._rigid_constraint_to_mid[constraint] = mid
        return mid, True

    def get_section_id(self, element_type: str) -> int:
        """
        要素タイプからSection IDを取得

        Args:
            element_type: 要素タイプ（"SHELL", "SOLID_TET", "SOLID_HEX"など）

        Returns:
            Section ID
        """
        # 正規化（大文字化、スペース削除）
        normalized_type = element_type.upper().strip()

        # SOLID の場合は SOLID_HEX として扱う（デフォルト）
        if normalized_type == "SOLID":
            normalized_type = "SOLID_HEX"

        return self._section_ids.get(normalized_type, 1)  # デフォルトはShell

    def register_part_material(self, pid: int, mid: int) -> None:
        """
        PartとMaterialの紐付けを登録

        Args:
            pid: Part ID
            mid: Material ID
        """
        self._part_to_material[pid] = mid

    def register_part_section(self, pid: int, secid: int) -> None:
        """
        PartとSectionの紐付けを登録

        Args:
            pid: Part ID
            secid: Section ID
        """
        self._part_to_section[pid] = secid

    def get_part_material(self, pid: int) -> int | None:
        """
        PartのMaterial IDを取得

        Args:
            pid: Part ID

        Returns:
            Material ID、未登録の場合はNone
        """
        return self._part_to_material.get(pid)

    def get_part_section(self, pid: int) -> int | None:
        """
        PartのSection IDを取得

        Args:
            pid: Part ID

        Returns:
            Section ID、未登録の場合はNone
        """
        return self._part_to_section.get(pid)
