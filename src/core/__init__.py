"""
LS-DYNA解析アプリケーションのコアドメイン

プレス成形シミュレーションのためのドメインロジックを提供します。

主要なエンティティ:
- Tool: 工具（パンチ、ダイ、ブランクホルダー等）
- Workpiece: 被加工材（ブランク）

値オブジェクト:
- Direction: 6方向の単位ベクトル
- Directions: 方向プリセット

設定クラス:
- AnalysisConfig: UI状態管理のためのメイン設定
- StepConfig: 工程設定（ワーク・工具）
- MeshInfo: アップロードされたメッシュ情報

サブパッケージ:
- boundaries: 境界条件（動作、荷重）
- contacts: 接触条件
- curves: カーブ生成
- materials: 材料定義
- common: 共通ユーティリティ
- export: デッキファイル生成
"""

from .common.direction import Direction, Directions
from .config import (
    MATERIAL_PRESETS,
    AnalysisConfig,
    AnalysisPurpose,
    ConstraintConfig,
    FrictionConfig,
    FrictionMode,
    MaterialConfig,
    MeshInfo,
    MotionDirection,
    MotionType,
    ProcessType,
    StepConfig,
    SymmetryPlane,
    SymmetryPlaneType,
    ToolConfig,
    WorkpieceConfig,
)
from .tool import Tool, create_die, create_holder, create_punch
from .workpiece import (
    MaterialProperties,
    Workpiece,
    create_aluminum_workpiece,
    create_stainless_workpiece,
    create_steel_workpiece,
)


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
    # 設定用Enum
    "ProcessType",
    "AnalysisPurpose",
    "MotionType",
    "MotionDirection",
    "FrictionMode",
    "SymmetryPlaneType",
    # 設定用定数
    "MATERIAL_PRESETS",
    # 設定用データクラス
    "MaterialConfig",
    "MeshInfo",
    "WorkpieceConfig",
    "ToolConfig",
    "FrictionConfig",
    "SymmetryPlane",
    "ConstraintConfig",
    "StepConfig",
    "AnalysisConfig",
]
