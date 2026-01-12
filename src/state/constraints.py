"""拘束条件設定の状態定義"""

import uuid
from dataclasses import dataclass, field


@dataclass
class ConstraintConfig:
    """拘束条件設定"""

    id: str  # 一意のID
    name: str  # 拘束条件名
    x_range: tuple[float, float] = (0.0, 0.0)  # X座標範囲 (min, max)
    y_range: tuple[float, float] = (0.0, 0.0)  # Y座標範囲 (min, max)
    z_range: tuple[float, float] = (0.0, 0.0)  # Z座標範囲 (min, max)
    dof: list[bool] = field(default_factory=lambda: [False] * 6)
    # dof: [tx, ty, tz, rx, ry, rz] - True=拘束, False=自由

    @classmethod
    def create(cls, name: str = "拘束条件") -> "ConstraintConfig":
        """自動生成IDで新しいConstraintConfigを作成"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
        )
