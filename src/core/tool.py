"""工具エンティティ - プレス成形における工具を表現"""

from dataclasses import dataclass, field
from typing import Any

from .boundaries.enums import ConditionType, MotionControlType, StrokeMode
from .boundaries.motion import (
    FollowingConfig,
    PositionLimits,
    ToolConditionConfig,
    VelocityLimitConfig,
)
from .common.direction import Direction
from .materials.rigid import make_rigid_material


@dataclass
class Tool:
    """
    工具エンティティ

    プレス成形シミュレーションにおける工具（パンチ、ダイ、ブランクホルダー等）を表現します。
    工具のプロパティ、動作設定、接触対象を管理します。
    """

    # 識別情報
    id: int  # 工具ID（part_id）
    name: str  # 工具名（"upper_punch", "die" など）
    tool_type: str  # 工具タイプ（"punch", "die", "holder" など）

    # 形状・メッシュ
    mesh_file: str | None = None  # メッシュファイルパス

    # 材料・セクション
    material_id: int | None = None
    section_id: int | None = None
    material_constraint: str = "fixed"  # 剛体材料の制約条件

    # 動作設定
    motion_config: ToolConditionConfig | None = None

    # 接触対象（Part ID のリスト）
    contact_targets: list[int] = field(default_factory=list)

    def set_displacement_motion(
        self,
        direction: str | Direction,
        displacement: float,
        motion_time: float,
        stroke_mode: StrokeMode = StrokeMode.FORWARD_ONLY,
    ) -> "Tool":
        """
        変位制御の動作を設定

        Parameters:
        - direction: 動作方向（Direction オブジェクト、または '+x', '-z' などの文字列）
        - displacement: 変位量
        - motion_time: 動作時間
        - stroke_mode: ストロークモード（往路のみ/往復）

        Returns:
        - self（メソッドチェーン用）

        Examples:
            # プリセットを使用
            punch.set_displacement_motion(Directions.NEGATIVE_Z, 50.0, 0.5)

            # 文字列を使用
            punch.set_displacement_motion("-z", 50.0, 0.5)
        """
        self.motion_config = ToolConditionConfig(
            condition_type=ConditionType.FORCED_MOTION,
            part_id=self.id,
            direction=direction,
            name=self.name,
            motion_control_type=MotionControlType.DISPLACEMENT,
            displacement_amount=displacement,
            motion_time=motion_time,
            stroke_mode=stroke_mode,
        )
        return self

    def set_velocity_motion(
        self,
        direction: str | Direction,
        velocity: float,
        motion_time: float,
        stroke_mode: StrokeMode = StrokeMode.FORWARD_ONLY,
    ) -> "Tool":
        """
        速度制御の動作を設定

        Parameters:
        - direction: 動作方向（Direction オブジェクト、または '+x', '-z' などの文字列）
        - velocity: 速度
        - motion_time: 動作時間
        - stroke_mode: ストロークモード（往路のみ/往復）

        Returns:
        - self（メソッドチェーン用）
        """
        self.motion_config = ToolConditionConfig(
            condition_type=ConditionType.FORCED_MOTION,
            part_id=self.id,
            direction=direction,
            name=self.name,
            motion_control_type=MotionControlType.VELOCITY,
            velocity_amount=velocity,
            motion_time=motion_time,
            stroke_mode=stroke_mode,
        )
        return self

    def set_load(
        self,
        direction: str | Direction,
        load_amount: float,
        position_limits: PositionLimits | None = None,
        velocity_limit_config: VelocityLimitConfig | None = None,
    ) -> "Tool":
        """
        荷重制御を設定（ブランクホルダー等向け）

        Parameters:
        - direction: 荷重方向（Direction オブジェクト、または '+x', '-z' などの文字列）
        - load_amount: 荷重の大きさ
        - position_limits: 位置制限（オプション）
        - velocity_limit_config: 速度制限設定（オプション）

        Returns:
        - self（メソッドチェーン用）
        """
        self.motion_config = ToolConditionConfig(
            condition_type=ConditionType.LOAD_APPLICATION,
            part_id=self.id,
            direction=direction,
            name=self.name,
            load_amount=load_amount,
            position_limits=position_limits,
            velocity_limit_config=velocity_limit_config,
        )
        return self

    def set_following(
        self,
        leader_tool: "Tool",
        threshold_displacement: float,
        direction: str | Direction,
    ) -> "Tool":
        """
        追従動作を設定（リーダー工具に追従）

        Parameters:
        - leader_tool: 追従対象の工具
        - threshold_displacement: 追従開始の閾値変位量
        - direction: 動作方向（Direction オブジェクト、または '+x', '-z' などの文字列）

        Returns:
        - self（メソッドチェーン用）
        """
        following_config = FollowingConfig(
            leader_pid=leader_tool.id, threshold_displacement=threshold_displacement
        )

        self.motion_config = ToolConditionConfig(
            condition_type=ConditionType.FORCED_MOTION,
            part_id=self.id,
            direction=direction,
            name=self.name,
            motion_control_type=MotionControlType.DISPLACEMENT,
            following_config=following_config,
        )
        return self

    def add_contact_target(self, target_id: int) -> "Tool":
        """
        接触対象を追加

        Parameters:
        - target_id: 接触対象のPart ID

        Returns:
        - self（メソッドチェーン用）
        """
        if target_id not in self.contact_targets:
            self.contact_targets.append(target_id)
        return self

    def create_material(self) -> Any:
        """
        工具用の剛体材料を生成

        Returns:
        - kwd.Mat020: 剛体材料キーワード
        """
        return make_rigid_material(
            mid=self.material_id or self.id, constraint=self.material_constraint
        )

    def get_condition_config(self) -> ToolConditionConfig | None:
        """
        工具の条件設定を取得

        Returns:
        - ToolConditionConfig or None
        """
        return self.motion_config

    def to_dict(self) -> dict[str, Any]:
        """
        工具情報を辞書形式で取得

        Returns:
        - 工具情報の辞書
        """
        return {
            "id": self.id,
            "name": self.name,
            "tool_type": self.tool_type,
            "mesh_file": self.mesh_file,
            "material_id": self.material_id,
            "section_id": self.section_id,
            "material_constraint": self.material_constraint,
            "has_motion": self.motion_config is not None,
            "contact_targets": self.contact_targets,
        }

    def __repr__(self) -> str:
        return f"Tool(id={self.id}, name='{self.name}', type='{self.tool_type}')"


# ファクトリ関数
def create_punch(
    tool_id: int, name: str = "punch", material_constraint: str = "z-free"
) -> Tool:
    """パンチ工具を作成"""
    return Tool(
        id=tool_id,
        name=name,
        tool_type="punch",
        material_constraint=material_constraint,
    )


def create_die(
    tool_id: int, name: str = "die", material_constraint: str = "fixed"
) -> Tool:
    """ダイ工具を作成"""
    return Tool(
        id=tool_id, name=name, tool_type="die", material_constraint=material_constraint
    )


def create_holder(
    tool_id: int, name: str = "blank_holder", material_constraint: str = "z-free"
) -> Tool:
    """ブランクホルダー工具を作成"""
    return Tool(
        id=tool_id,
        name=name,
        tool_type="holder",
        material_constraint=material_constraint,
    )
