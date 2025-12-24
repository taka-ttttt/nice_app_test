"""境界条件に関するEnum定義"""
from enum import Enum


class ConditionType(Enum):
    """条件設定タイプ"""
    FORCED_MOTION = "forced_motion"  # 強制動作
    LOAD_APPLICATION = "load_application"  # 荷重付与


class MotionControlType(Enum):
    """強制動作の制御タイプ"""
    DISPLACEMENT = "displacement"  # 変位制御
    VELOCITY = "velocity"  # 速度制御


class StrokeMode(Enum):
    """ストロークモード"""
    FORWARD_ONLY = "forward_only"  # 往路のみ
    RECIPROCATING = "reciprocating"  # 往復動作


class FollowMode(Enum):
    """追従モード"""
    DISPLACEMENT = "displacement"  # 変位追従
    VELOCITY = "velocity"  # 速度追従

