"""摩擦係数設定の状態定義"""

from dataclasses import dataclass
from enum import Enum


class FrictionMode(Enum):
    """摩擦係数モード"""

    OIL = "oil"  # 油あり
    DRY = "dry"  # 油なし
    MANUAL = "manual"  # マニュアル入力


@dataclass
class FrictionConfig:
    """摩擦係数設定"""

    mode: FrictionMode = FrictionMode.OIL
    # マニュアルモード時のみ使用される値
    manual_static_friction: float = 0.10
    manual_dynamic_friction: float = 0.05

    @property
    def static_friction(self) -> float:
        """
        UI表示用の静摩擦係数取得ヘルパー
        注意: 実際の解析値はCore側で決定されるため、これはあくまでUI表示の目安や
        Manualモード時の値を返すためのもの。
        """
        # UIの互換性のためにプロパティとして残すが、
        # 本来はUI側で解決するか、manual値を表示すべき
        if self.mode == FrictionMode.MANUAL:
            return self.manual_static_friction
        # プリセット値はCoreが知っているため、ここでは仮の値を返すか、
        # あるいはUI表示用として割り切って定数を定義するか。
        # 今回は「Stateは値を持たない」方針なので、Manual以外はNoneや0を返すのが
        # 厳密だが、UIバインディングの都合上、Manual値を返しておくのが無難。
        return self.manual_static_friction

    @property
    def dynamic_friction(self) -> float:
        """UI表示用の動摩擦係数取得ヘルパー"""
        return self.manual_dynamic_friction
