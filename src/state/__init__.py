"""
アプリケーション状態管理

UIの状態を表現するデータクラスとEnum定義を提供します。
"""

from .analysis import AnalysisConfig, AnalysisPurpose
from .constraints import ConstraintConfig
from .friction import FrictionConfig, FrictionMode
from .materials import MATERIAL_PRESETS, MaterialConfig
from .meshes import MeshInfo
from .parts import MotionDirection, MotionType, ToolConfig, WorkpieceConfig
from .steps import ProcessType, StepConfig
from .symmetry import SymmetryPlane, SymmetryPlaneType


__all__ = [
    # 材料関連
    "MATERIAL_PRESETS",
    "MaterialConfig",
    # メッシュ関連
    "MeshInfo",
    # パーツ関連（工具・ワーク）
    "MotionDirection",
    "MotionType",
    "ToolConfig",
    "WorkpieceConfig",
    # 物理設定関連
    "ConstraintConfig",
    "FrictionMode",
    "FrictionConfig",
    "SymmetryPlane",
    "SymmetryPlaneType",
    # 工程関連
    "ProcessType",
    "StepConfig",
    # 解析設定（ルート状態）
    "AnalysisPurpose",
    "AnalysisConfig",
]
