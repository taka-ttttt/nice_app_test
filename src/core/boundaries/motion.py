"""境界条件（動作・荷重）の設定と生成"""
import numpy as np
import pandas as pd
from ansys.dyna.core import keywords as kwd
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass

from .enums import (
    ConditionType,
    MotionControlType,
    StrokeMode,
    FollowMode,
)
from ..common.direction import Direction, Axis
from ..curves.generators import (
    create_preload_curve,
    create_stroke_curve,
    create_threshold_following_curve,
    create_constant_curve,
)


@dataclass
class PositionLimits:
    """位置制限設定"""
    max_position: float  # 最大位置
    min_position: float  # 最小位置
    
    def to_dict(self) -> Dict[str, float]:
        """辞書形式に変換"""
        return {"max": self.max_position, "min": self.min_position}


@dataclass
class VelocityLimitConfig:
    """速度制限設定"""
    leader_part_id: int  # 基準となるパートID
    limit_multiplier: float = 1.1  # 速度制限倍率（デフォルト1.1倍）


@dataclass
class FollowingConfig:
    """追従設定の設定クラス"""
    leader_pid: int  # 追従対象のパートID
    threshold_displacement: float  # 追従開始の閾値変位量
    follow_mode: FollowMode = FollowMode.DISPLACEMENT


@dataclass
class ToolConditionConfig:
    """工具条件設定の設定クラス"""
    # 基本設定
    condition_type: ConditionType
    part_id: int  # pidよりも明確
    direction: Union[str, Direction]  # Direction オブジェクトまたは文字列（'+z', '-z'など）
    name: str  # titleよりも簡潔
    
    # 強制動作用設定
    motion_control_type: Optional[MotionControlType] = None
    displacement_amount: Optional[float] = None  # より明確
    velocity_amount: Optional[float] = None  # より明確
    motion_time: Optional[float] = None  # ramp_timeから変更
    stroke_mode: StrokeMode = StrokeMode.FORWARD_ONLY
    
    # 追従設定（強制動作時のオプション）
    following_config: Optional[FollowingConfig] = None
    
    # 荷重付与用設定
    load_amount: Optional[float] = None  # より明確
    
    # 制限条件（オプション）
    position_limits: Optional[PositionLimits] = None
    velocity_limit_config: Optional[VelocityLimitConfig] = None
    
    # カーブID設定
    base_curve_id: int = 9000  # より明確


class ToolConditionManager:
    """工具条件設定の統一管理クラス"""
    
    def __init__(self, global_config: Dict[str, Any]):
        """
        Parameters:
        global_config: 全体設定（motion_timeやhold_timeなど）
        """
        self.global_config = global_config
        self.curve_id_counter = 9000
        self.created_curves = {}
        self.created_conditions = {}
        self.leader_curves = {}  # リーダーのカーブを保存
        self.leader_motion_data = {}  # リーダーの動作データを保存
    
    def _get_next_curve_id(self) -> int:
        """次のカーブIDを取得"""
        self.curve_id_counter += 1
        return self.curve_id_counter
    
    def _store_leader_motion_data(self, config: ToolConditionConfig):
        """リーダーの動作データを保存"""
        if config.motion_control_type == MotionControlType.DISPLACEMENT:
            self.leader_motion_data[config.part_id] = {
                "type": "displacement",
                "amount": config.displacement_amount,
                "motion_time": config.motion_time or self.global_config.get("motion_time", 0.5)
            }
        elif config.motion_control_type == MotionControlType.VELOCITY:
            self.leader_motion_data[config.part_id] = {
                "type": "velocity",
                "amount": config.velocity_amount,
                "motion_time": config.motion_time or self.global_config.get("motion_time", 0.5)
            }
    
    def _calculate_velocity_limit_from_leader(self, velocity_config: VelocityLimitConfig) -> float:
        """リーダーの動作データから速度制限値を計算"""
        leader_id = velocity_config.leader_part_id
        
        if leader_id not in self.leader_motion_data:
            raise ValueError(f"リーダーパートID {leader_id} の動作データが見つかりません。リーダーを先に作成してください。")
        
        leader_data = self.leader_motion_data[leader_id]
        
        if leader_data["type"] == "displacement":
            # 変位制御の場合、最大速度を計算
            # ハーフコサイン波形の最大速度は π/(2*motion_time) * displacement_amount
            max_velocity = (np.pi / (2 * leader_data["motion_time"])) * leader_data["amount"]
        elif leader_data["type"] == "velocity":
            # 速度制御の場合、設定速度をそのまま使用
            max_velocity = leader_data["amount"]
        else:
            raise ValueError(f"未対応の動作タイプ: {leader_data['type']}")
        
        return abs(max_velocity) * velocity_config.limit_multiplier
    
    def create_tool_condition(self, config: ToolConditionConfig) -> Dict[str, Any]:
        """
        工具条件を作成する統一メソッド
        
        Returns:
        Dict: 作成された条件とカーブの辞書
        """
        if config.condition_type == ConditionType.FORCED_MOTION:
            return self._create_forced_motion_condition(config)
        elif config.condition_type == ConditionType.LOAD_APPLICATION:
            return self._create_load_application_condition(config)
        else:
            raise ValueError(f"未対応の条件タイプ: {config.condition_type}")
    
    def _create_forced_motion_condition(self, config: ToolConditionConfig) -> Dict[str, Any]:
        """強制動作条件を作成"""
        result = {"curves": {}, "conditions": {}}
        
        # 追従設定がある場合の処理
        if config.following_config:
            return self._create_following_motion_condition(config)
        
        # 通常の強制動作処理
        if config.motion_control_type == MotionControlType.DISPLACEMENT:
            result = self._create_displacement_control(config)
        elif config.motion_control_type == MotionControlType.VELOCITY:
            result = self._create_velocity_control(config)
        else:
            raise ValueError(f"motion_control_typeが指定されていません: {config}")
        
        return result
    
    def _create_displacement_control(self, config: ToolConditionConfig) -> Dict[str, Any]:
        """変位制御条件を作成"""
        curve_id = self._get_next_curve_id()
        
        stroke_curve = create_stroke_curve(
            lcid=curve_id,
            ramp_time=config.motion_time or self.global_config.get("motion_time", 0.5),
            sfo=config.displacement_amount,
            curve_type="displacement",
            stroke_mode=config.stroke_mode.value,
            title=f"{config.name} displacement curve"
        )
        
        # リーダーカーブとして保存
        self.leader_curves[config.part_id] = stroke_curve
        
        # リーダーの動作データを保存
        self._store_leader_motion_data(config)
        
        condition = create_stroke_condition(
            pid=config.part_id,
            lcid=curve_id,
            dof=config.direction,
            vad=2,  # 変位制御
            title=config.name
        )
        
        return {
            "curves": {"displacement": stroke_curve},
            "conditions": {"motion": condition}
        }
    
    def _create_velocity_control(self, config: ToolConditionConfig) -> Dict[str, Any]:
        """速度制御条件を作成"""
        curve_id = self._get_next_curve_id()
        
        velocity_curve = create_stroke_curve(
            lcid=curve_id,
            ramp_time=config.motion_time or self.global_config.get("motion_time", 0.5),
            sfo=config.velocity_amount,
            curve_type="velocity",
            stroke_mode=config.stroke_mode.value,
            title=f"{config.name} velocity curve"
        )
        
        # リーダーカーブとして保存
        self.leader_curves[config.part_id] = velocity_curve
        
        # リーダーの動作データを保存
        self._store_leader_motion_data(config)
        
        condition = create_stroke_condition(
            pid=config.part_id,
            lcid=curve_id,
            dof=config.direction,
            vad=0,  # 速度制御
            title=config.name
        )
        
        return {
            "curves": {"velocity": velocity_curve},
            "conditions": {"motion": condition}
        }
    
    def _create_load_application_condition(self, config: ToolConditionConfig) -> Dict[str, Any]:
        """荷重付与条件を作成"""
        result = {"curves": {}, "conditions": {}}
        
        # プリロードカーブを作成
        preload_curve_id = self._get_next_curve_id()
        preload_curve = create_preload_curve(
            lcid=preload_curve_id,
            title=f"{config.name} preload curve"
        )
        result["curves"]["preload"] = preload_curve
        
        # 荷重条件を作成
        load_condition = create_rigid_preload(
            pid=config.part_id,
            lcid=preload_curve_id,
            sf=config.load_amount,
            dof=config.direction,
            title=config.name
        )
        result["conditions"]["load"] = load_condition
        
        # オプション：位置制限条件
        if config.position_limits:
            limit_curves, limit_condition = self._create_position_limits(config)
            result["curves"].update(limit_curves)
            result["conditions"]["limits"] = limit_condition
        
        return result
    
    def _create_position_limits(self, config: ToolConditionConfig) -> tuple:
        """位置制限条件を作成"""
        curves = {}
        limits = config.position_limits
        
        # 最大位置制限カーブ
        max_curve_id = self._get_next_curve_id()
        max_curve = create_constant_curve(
            lcid=max_curve_id,
            sfo=limits.max_position,
            title=f"{config.name} position limit max"
        )
        curves["limit_max"] = max_curve
        
        # 最小位置制限カーブ
        min_curve_id = self._get_next_curve_id()
        min_curve = create_constant_curve(
            lcid=min_curve_id,
            sfo=limits.min_position,
            title=f"{config.name} position limit min"
        )
        curves["limit_min"] = min_curve
        
        # 速度制限カーブ（オプション）
        velocity_limit_curve_id = None
        if config.velocity_limit_config:
            velocity_limit_curve_id = self._get_next_curve_id()
            
            # リーダーの動作データから速度制限値を計算
            velocity_limit_value = self._calculate_velocity_limit_from_leader(config.velocity_limit_config)
            
            velocity_curve = create_stroke_curve(
                lcid=velocity_limit_curve_id,
                ramp_time=self.global_config.get("motion_time", 0.5),
                sfo=velocity_limit_value,
                curve_type="velocity",
                title=f"{config.name} velocity limit (based on leader)"
            )
            curves["velocity_limit"] = velocity_curve
        
        # 制限条件を作成
        limit_direction = config.direction.replace('+', '').replace('-', '')
        limit_condition = create_limit_condition(
            pid=config.part_id,
            limit_direction=limit_direction,
            lcid_max=max_curve_id,
            lcid_min=min_curve_id,
            lcid_velocity_limit=velocity_limit_curve_id,
            title=f"{config.name} limits"
        )
        
        return curves, limit_condition

    def _create_following_motion_condition(self, config: ToolConditionConfig) -> Dict[str, Any]:
        """追従動作条件を作成"""
        result = {"curves": {}, "conditions": {}}
        following = config.following_config
        
        # リーダーのカーブを取得
        if following.leader_pid not in self.leader_curves:
            raise ValueError(f"リーダーPID {following.leader_pid} のカーブが見つかりません。リーダーを先に作成してください。")
        
        leader_curve = self.leader_curves[following.leader_pid]
        
        # 追従カーブを作成
        following_lcid = self._get_next_curve_id()
        
        if following.follow_mode == FollowMode.DISPLACEMENT:
            # 変位追従
            following_curve = create_threshold_following_curve(
                lcid=following_lcid,
                threshold_displacement=following.threshold_displacement,
                reference_curve_data=leader_curve.curves,
                title=f"{config.name} following displacement curve"
            )
            
            condition = create_stroke_condition(
                pid=config.part_id,
                lcid=following_lcid,
                dof=config.direction,
                vad=2,  # 変位制御
                title=config.name
            )
            
        elif following.follow_mode == FollowMode.VELOCITY:
            # 速度追従（リーダーの速度カーブを基に閾値で追従開始）
            following_curve = self._create_velocity_following_curve(
                lcid=following_lcid,
                threshold_displacement=following.threshold_displacement,
                reference_curve_data=leader_curve.curves,
                title=f"{config.name} following velocity curve"
            )
            
            condition = create_stroke_condition(
                pid=config.part_id,
                lcid=following_lcid,
                dof=config.direction,
                vad=0,  # 速度制御
                title=config.name
            )
        
        else:
            raise ValueError(f"未対応の追従モード: {following.follow_mode}")
        
        result["curves"]["following"] = following_curve
        result["conditions"]["following"] = condition
        
        return result
    
    def _create_velocity_following_curve(self, 
                                       lcid: int,
                                       threshold_displacement: float,
                                       reference_curve_data: pd.DataFrame,
                                       title: str) -> kwd.DefineCurve:
        """
        速度追従カーブを作成
        リーダーの変位カーブから閾値到達後に同じ速度で追従するカーブを生成
        """
        # 参照カーブから時間と変位を取得
        t_ref = reference_curve_data["a1"].values
        y_ref = reference_curve_data["o1"].values
        
        # 閾値到達時刻を計算
        t_sw = None
        for i in range(len(y_ref) - 1):
            if y_ref[i] <= threshold_displacement <= y_ref[i + 1]:
                ratio = (threshold_displacement - y_ref[i]) / (y_ref[i + 1] - y_ref[i])
                t_sw = t_ref[i] + ratio * (t_ref[i + 1] - t_ref[i])
                break
        
        if t_sw is None:
            raise ValueError(f"閾値変位量 {threshold_displacement} に到達しません。")
        
        # 速度カーブを作成（閾値到達後にリーダーと同じ速度勾配）
        t_new = []
        v_new = []
        
        for i, (t, y) in enumerate(zip(t_ref, y_ref)):
            if t <= t_sw:
                # 閾値到達前は速度0
                t_new.append(t)
                v_new.append(0.0)
            else:
                # 閾値到達後はリーダーと同じ速度勾配
                if i > 0:
                    dt = t_ref[i] - t_ref[i-1]
                    dy = y_ref[i] - y_ref[i-1]
                    velocity = dy / dt if dt > 0 else 0.0
                    t_new.append(t)
                    v_new.append(velocity)
        
        # データフレームに変換
        curve_df = pd.DataFrame({"a1": t_new, "o1": v_new})
        return kwd.DefineCurve(lcid=lcid, sidr=0, curves=curve_df, title=title)

    def create_tool_set_conditions(self, tool_configs: List[ToolConditionConfig]) -> Dict[str, Any]:
        """
        複数工具の条件を一括作成（追従関係を考慮した順序で処理）
        """
        results = {}
        
        # 追従関係を考慮してソート（リーダーを先に処理）
        sorted_configs = self._sort_configs_by_dependency(tool_configs)
        
        for config in sorted_configs:
            tool_name = config.name.lower().replace(" ", "_")
            results[tool_name] = self.create_tool_condition(config)
        
        return results
    
    def _sort_configs_by_dependency(self, configs: List[ToolConditionConfig]) -> List[ToolConditionConfig]:
        """追従関係を考慮して設定をソート"""
        leaders = []
        followers = []
        
        for config in configs:
            if (config.condition_type == ConditionType.FORCED_MOTION and 
                config.following_config is not None):
                followers.append(config)
            else:
                leaders.append(config)
        
        # リーダーを先に、フォロワーを後に配置
        return leaders + followers


def _resolve_direction(dof: Union[str, Direction]) -> Direction:
    """方向を Direction オブジェクトに変換"""
    if isinstance(dof, Direction):
        return dof
    return Direction.from_string(dof)


def _resolve_axis(limit_direction: Union[str, Axis]) -> Axis:
    """軸を Axis オブジェクトに変換"""
    if isinstance(limit_direction, Axis):
        return limit_direction
    return Axis(limit_direction.lower().strip())


def create_rigid_preload(
    pid: int,
    lcid: int,
    sf: float,
    dof: Union[str, Direction],
    title: str = "Rigid preload"
) -> kwd.LoadRigidBody:
    """
    剛体プリロード条件を作成
    
    Parameters:
    - pid: パートID
    - lcid: カーブID
    - sf: 荷重の大きさ（正の値のみ有効）
    - dof: 方向（Direction オブジェクト、または '+x', '-z' などの文字列）
    - title: 境界条件のタイトル
    """
    if sf <= 0:
        raise ValueError(f"sfは正の値である必要があります。入力値: {sf}")
    
    direction = _resolve_direction(dof)
    
    return kwd.LoadRigidBody(
        pid=pid,
        lcid=lcid,
        dof=direction.dof_number,
        sf=sf * direction.scale_factor,
        title=title
    )


def create_stroke_condition(
    pid: int,
    lcid: int,
    dof: Union[str, Direction],
    sf: float = 1.0,
    vad: int = 2,
    title: str = "Stroke condition"
) -> kwd.BoundaryPrescribedMotion:
    """
    ストローク条件を作成
    
    Parameters:
    - pid: パートID
    - lcid: カーブID
    - dof: 方向（Direction オブジェクト、または '+x', '-z' などの文字列）
    - sf: スケールファクター（正の値のみ有効）
    - vad: 制御方法（0: 速度, 1: 加速度, 2: 変位）
    - title: 境界条件のタイトル
    """
    if sf <= 0:
        raise ValueError(f"sfは正の値である必要があります。入力値: {sf}")
    
    direction = _resolve_direction(dof)

    # 制御方法の検証
    valid_vad = [0, 1, 2]
    if vad not in valid_vad:
        available = ", ".join(str(v) for v in valid_vad)
        raise ValueError(f"無効な制御方法: '{vad}'. 利用可能: {available}")
    
    return kwd.BoundaryPrescribedMotion(
        pid=pid,
        lcid=lcid,
        dof=direction.dof_number,
        sf=sf * direction.scale_factor,
        vad=vad,
        title=title
    )


def create_limit_condition(
    pid: int,
    limit_direction: Union[str, Axis],
    lcid_max: int,
    lcid_min: int,
    lcid_velocity_limit: int = None,
    title: str = "Limit condition"
) -> kwd.ConstrainedRigidBodyStoppers:
    """
    剛体の位置制限条件を作成
    
    Parameters:
    - pid: パートID
    - limit_direction: 制限方向（Axis オブジェクト、または 'x', 'y', 'z' の文字列）
    - lcid_max: 最大値用カーブID（既に定義済み）
    - lcid_min: 最小値用カーブID（既に定義済み）
    - lcid_velocity_limit: 速度制限用カーブID（既に定義済み）
    - title: 制限条件のタイトル
    
    Returns:
    - ConstrainedRigidBodyStoppers: 制限条件キーワード
    """
    axis = _resolve_axis(limit_direction)
    
    # 制限条件を作成
    return kwd.ConstrainedRigidBodyStoppers(
        pid=pid,
        lcmax=-lcid_max,
        lcmin=-lcid_min,
        lcvmx=lcid_velocity_limit,
        dir=axis.dof_number,
        title=title
    )

