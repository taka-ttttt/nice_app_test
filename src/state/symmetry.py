"""対称面設定の状態定義"""

import uuid
from dataclasses import dataclass
from enum import Enum


class SymmetryPlaneType(Enum):
    """対称面タイプ"""

    XY = "xy"
    YZ = "yz"
    ZX = "zx"

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        return self.value.upper()


@dataclass
class SymmetryPlane:
    """対称面設定"""

    id: str  # 一意のID
    plane: SymmetryPlaneType  # 平面タイプ (XY/YZ/ZX)
    coordinate: float = 0.0  # 平面の位置

    @classmethod
    def create(
        cls,
        plane: SymmetryPlaneType = SymmetryPlaneType.YZ,
        coordinate: float = 0.0,
    ) -> "SymmetryPlane":
        """自動生成IDで新しいSymmetryPlaneを作成"""
        return cls(
            id=str(uuid.uuid4()),
            plane=plane,
            coordinate=coordinate,
        )
