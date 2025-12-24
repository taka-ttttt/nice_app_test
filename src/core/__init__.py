"""
LS-DYNA解析アプリケーションのコアドメイン

このパッケージは、プレス成形シミュレーションのためのドメインロジックを提供します。

主要なエンティティ:
- Tool: 工具（パンチ、ダイ、ブランクホルダー等）
- Workpiece: 被加工材（ブランク）

値オブジェクト:
- Direction: 6方向の単位ベクトル
- Directions: 方向プリセット

サブパッケージ:
- boundaries: 境界条件（動作、荷重）
- contacts: 接触条件
- curves: カーブ生成
- materials: 材料定義
- common: 共通ユーティリティ
- export: デッキファイル生成
"""

from .tool import Tool, create_punch, create_die, create_holder
from .workpiece import (
    Workpiece,
    MaterialProperties,
    create_steel_workpiece,
    create_stainless_workpiece,
    create_aluminum_workpiece,
)
from .common.direction import Direction, Directions

__all__ = [
    # エンティティ
    "Tool",
    "Workpiece",
    "MaterialProperties",
    # 値オブジェクト
    "Direction",
    "Directions",
    # ファクトリ関数
    "create_punch",
    "create_die",
    "create_holder",
    "create_steel_workpiece",
    "create_stainless_workpiece",
    "create_aluminum_workpiece",
]

