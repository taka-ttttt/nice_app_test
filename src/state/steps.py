"""工程設定の状態定義"""

import uuid
from dataclasses import dataclass, field
from enum import Enum

from .parts import ToolConfig, WorkpieceConfig


class ProcessType(Enum):
    """加工分類"""

    BENDING = "bending"
    DRAWING = "drawing"
    STRETCHING = "stretching"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        names = {
            ProcessType.BENDING: "曲げ加工",
            ProcessType.DRAWING: "絞り加工",
            ProcessType.STRETCHING: "張り出し加工",
            ProcessType.OTHER: "その他",
        }
        return names.get(self, self.value)


@dataclass
class StepConfig:
    """工程設定（1工程分のワーク・工具設定をまとめる）"""

    id: str  # 一意のID (UUID)
    name: str  # 工程名（例: "曲げ1"）
    step_type: ProcessType  # 工程タイプ（曲げ/絞り/張り出し/その他）
    order: int  # 工程の順序 (1, 2, 3, ...)

    # 工程ごとのパート設定
    workpieces: list[WorkpieceConfig] = field(default_factory=list)
    tools: list[ToolConfig] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str = "工程",
        step_type: ProcessType = ProcessType.BENDING,
        order: int = 1,
    ) -> "StepConfig":
        """自動生成IDとデフォルトパートで新しいStepConfigを作成"""
        step = cls(
            id=str(uuid.uuid4()),
            name=name,
            step_type=step_type,
            order=order,
        )
        # デフォルトのワークと工具を追加
        step.workpieces.append(WorkpieceConfig.create(name="ワーク 1"))
        step.tools.append(ToolConfig.create(name="工具 1"))
        return step

    def duplicate(self) -> "StepConfig":
        """このステップを複製"""
        new_step = StepConfig.create(
            name=f"{self.name} (コピー)",
            step_type=self.step_type,
            order=self.order,  # 呼び出し側で調整
        )
        new_step.workpieces.clear()
        new_step.tools.clear()

        for wp in self.workpieces:
            new_wp = WorkpieceConfig.create(
                name=wp.name,
                mesh_id=wp.mesh_id,
                material_preset=wp.material_preset,
                thickness=wp.thickness,
            )
            new_wp.custom_material = wp.custom_material
            new_step.workpieces.append(new_wp)

        for tool in self.tools:
            new_tool = ToolConfig.create(
                name=tool.name,
                mesh_id=tool.mesh_id,
                motion_type=tool.motion_type,
            )
            new_tool.direction = tool.direction
            new_tool.value = tool.value
            new_tool.motion_time = tool.motion_time
            new_step.tools.append(new_tool)

        return new_step

    def add_workpiece(self, name: str | None = None) -> WorkpieceConfig:
        """この工程に新しいワークを追加"""
        wp_name = name or f"ワーク {len(self.workpieces) + 1}"
        workpiece = WorkpieceConfig.create(name=wp_name)
        self.workpieces.append(workpiece)
        return workpiece

    def add_tool(self, name: str | None = None) -> ToolConfig:
        """この工程に新しい工具を追加"""
        tool_name = name or f"工具 {len(self.tools) + 1}"
        tool = ToolConfig.create(name=tool_name)
        self.tools.append(tool)
        return tool

    def remove_workpiece(self, workpiece_id: str) -> bool:
        """IDでワークを削除。削除した場合はTrueを返す"""
        for i, wp in enumerate(self.workpieces):
            if wp.id == workpiece_id:
                self.workpieces.pop(i)
                return True
        return False

    def remove_tool(self, tool_id: str) -> bool:
        """IDで工具を削除。削除した場合はTrueを返す"""
        for i, tool in enumerate(self.tools):
            if tool.id == tool_id:
                self.tools.pop(i)
                return True
        return False
