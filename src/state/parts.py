"""ワーク・工具の状態定義"""

import uuid
from dataclasses import dataclass
from enum import Enum

from .materials import MaterialConfig


class MotionType(Enum):
    """動作タイプ"""

    DISPLACEMENT = "displacement"
    LOAD = "load"
    FIXED = "fixed"
    # VELOCITY = "velocity"  # 将来追加予定

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        names = {
            MotionType.DISPLACEMENT: "変位",
            MotionType.LOAD: "荷重",
            MotionType.FIXED: "固定",
        }
        return names.get(self, self.value)


class MotionDirection(Enum):
    """動作方向"""

    POSITIVE_X = "+x"
    NEGATIVE_X = "-x"
    POSITIVE_Y = "+y"
    NEGATIVE_Y = "-y"
    POSITIVE_Z = "+z"
    NEGATIVE_Z = "-z"
    # CUSTOM = "custom"  # 将来追加予定: 任意ベクトル

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        return self.value.upper()

    def to_vector(self) -> tuple[float, float, float]:
        """単位ベクトルに変換"""
        vectors = {
            MotionDirection.POSITIVE_X: (1.0, 0.0, 0.0),
            MotionDirection.NEGATIVE_X: (-1.0, 0.0, 0.0),
            MotionDirection.POSITIVE_Y: (0.0, 1.0, 0.0),
            MotionDirection.NEGATIVE_Y: (0.0, -1.0, 0.0),
            MotionDirection.POSITIVE_Z: (0.0, 0.0, 1.0),
            MotionDirection.NEGATIVE_Z: (0.0, 0.0, -1.0),
        }
        return vectors.get(self, (0.0, 0.0, 0.0))


@dataclass
class WorkpieceConfig:
    """ワーク設定"""

    id: str  # 一意のID
    name: str  # ワーク名
    mesh_id: str  # MeshInfoへの参照
    material_preset: str  # プリセットキー または "custom"
    custom_material: MaterialConfig | None = None
    thickness: float = 1.0  # 板厚 (mm)

    @classmethod
    def create(
        cls,
        name: str = "ワーク",
        mesh_id: str = "",
        material_preset: str = "SPCC",
        thickness: float = 1.0,
    ) -> "WorkpieceConfig":
        """自動生成IDで新しいWorkpieceConfigを作成"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            mesh_id=mesh_id,
            material_preset=material_preset,
            thickness=thickness,
        )

    def get_material(self) -> MaterialConfig:
        """材料設定を取得（プリセットまたはカスタム）"""
        if self.material_preset == "custom" and self.custom_material:
            return self.custom_material
        return MaterialConfig.from_preset(self.material_preset)


@dataclass
class ToolConfig:
    """工具設定"""

    id: str  # 一意のID
    name: str  # 工具名
    mesh_id: str  # MeshInfoへの参照
    motion_type: MotionType  # 動作タイプ
    direction: MotionDirection | None = None  # 動作方向
    value: float | None = None  # 変位量 (mm) または 荷重 (N)
    motion_time: float = 1.0  # 動作時間 (ms)、デフォルト: 1ms

    @classmethod
    def create(
        cls,
        name: str = "工具",
        mesh_id: str = "",
        motion_type: MotionType = MotionType.FIXED,
    ) -> "ToolConfig":
        """自動生成IDで新しいToolConfigを作成"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            mesh_id=mesh_id,
            motion_type=motion_type,
        )
