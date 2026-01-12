"""摩擦係数設定の状態定義"""

from dataclasses import dataclass
from enum import Enum


class FrictionMode(Enum):
    """摩擦係数モード"""

    OIL = "oil"  # 油あり: 静摩擦0.10, 動摩擦0.05
    DRY = "dry"  # 油なし: 静摩擦0.15, 動摩擦0.10
    MANUAL = "manual"  # マニュアル入力


@dataclass
class FrictionConfig:
    """摩擦係数設定"""

    mode: FrictionMode = FrictionMode.OIL
    static_friction: float = 0.10  # 静摩擦係数
    dynamic_friction: float = 0.05  # 動摩擦係数

    def __post_init__(self):
        """モードに基づいてプリセット値を適用"""
        self.apply_preset()

    def apply_preset(self) -> None:
        """摩擦モードに基づいてプリセット値を適用"""
        if self.mode == FrictionMode.OIL:
            self.static_friction = 0.10
            self.dynamic_friction = 0.05
        elif self.mode == FrictionMode.DRY:
            self.static_friction = 0.15
            self.dynamic_friction = 0.10
        # MANUALモードはユーザー指定値を保持
