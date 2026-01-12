"""解析設定の状態定義（ルート状態）"""

from dataclasses import dataclass, field
from enum import Enum

from .constraints import ConstraintConfig
from .friction import FrictionConfig
from .meshes import MeshInfo
from .steps import StepConfig
from .symmetry import SymmetryPlane, SymmetryPlaneType


class AnalysisPurpose(Enum):
    """解析目的"""

    MECHANISM = "mechanism"
    FORMABILITY = "formability"
    OPTIMIZATION = "optimization"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        names = {
            AnalysisPurpose.MECHANISM: "メカニズム確認",
            AnalysisPurpose.FORMABILITY: "成形性検証",
            AnalysisPurpose.OPTIMIZATION: "条件最適化",
            AnalysisPurpose.OTHER: "その他",
        }
        return names.get(self, self.value)


@dataclass
class AnalysisConfig:
    """解析設定全体を管理するメインクラス（ルート状態）"""

    # 解析概要
    project_name: str = "untitled"
    analysis_purpose: AnalysisPurpose = AnalysisPurpose.MECHANISM

    # メッシュ情報（全工程で共有）
    uploaded_meshes: list[MeshInfo] = field(default_factory=list)

    # 工程設定（複数工程対応）
    steps: list[StepConfig] = field(default_factory=list)

    # 全体設定（全工程で共有）
    friction: FrictionConfig = field(default_factory=FrictionConfig)
    symmetry_planes: list[SymmetryPlane] = field(default_factory=list)
    constraints: list[ConstraintConfig] = field(default_factory=list)

    # エクスポート設定
    output_filename: str = ""  # 空の場合はproject_nameを使用

    def __post_init__(self):
        """空の場合はデフォルト工程で初期化"""
        if not self.steps:
            self.add_step()

    @property
    def step_count(self) -> int:
        """工程数を取得"""
        return len(self.steps)

    def get_step_by_order(self, order: int) -> StepConfig | None:
        """順序番号で工程を取得"""
        for step in self.steps:
            if step.order == order:
                return step
        return None

    def get_step_by_id(self, step_id: str) -> StepConfig | None:
        """IDで工程を取得"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def add_step(self, name: str | None = None) -> StepConfig:
        """新しい工程を追加"""
        order = len(self.steps) + 1
        step_name = name or f"工程 {order}"
        step = StepConfig.create(name=step_name, order=order)
        self.steps.append(step)
        return step

    def remove_step(self, step_id: str) -> bool:
        """IDで工程を削除。削除した場合はTrueを返す"""
        for i, step in enumerate(self.steps):
            if step.id == step_id:
                self.steps.pop(i)
                # 残りの工程を再順序付け
                for j, s in enumerate(self.steps):
                    s.order = j + 1
                return True
        return False

    def duplicate_step(self, step_id: str) -> StepConfig | None:
        """工程を複製して元のステップの直後に挿入"""
        source = self.get_step_by_id(step_id)
        if not source:
            return None

        # 元のステップを複製
        new_step = source.duplicate()

        # 挿入位置を決定（元のステップの直後）
        source_index = self.steps.index(source)
        insert_index = source_index + 1

        # 新しいステップを挿入
        self.steps.insert(insert_index, new_step)

        # 挿入位置以降の全ステップの順序を再調整
        for i in range(insert_index, len(self.steps)):
            self.steps[i].order = i + 1

        return new_step

    def move_step_up(self, step_id: str) -> bool:
        """工程を上に移動。移動した場合はTrueを返す"""
        for i, step in enumerate(self.steps):
            if step.id == step_id and i > 0:
                self.steps[i], self.steps[i - 1] = self.steps[i - 1], self.steps[i]
                self.steps[i].order = i + 1
                self.steps[i - 1].order = i
                return True
        return False

    def move_step_down(self, step_id: str) -> bool:
        """工程を下に移動。移動した場合はTrueを返す"""
        for i, step in enumerate(self.steps):
            if step.id == step_id and i < len(self.steps) - 1:
                self.steps[i], self.steps[i + 1] = self.steps[i + 1], self.steps[i]
                self.steps[i].order = i + 1
                self.steps[i + 1].order = i + 2
                return True
        return False

    def get_mesh_by_id(self, mesh_id: str) -> MeshInfo | None:
        """IDでメッシュ情報を取得"""
        for mesh in self.uploaded_meshes:
            if mesh.id == mesh_id:
                return mesh
        return None

    def get_mesh_usage(self, mesh_id: str) -> list[tuple[StepConfig, str, str]]:
        """
        メッシュの全ての使用箇所を取得。
        (step, part_type, part_name) のタプルリストを返す。
        part_type は 'workpiece' または 'tool'。
        """
        usages = []
        for step in self.steps:
            for wp in step.workpieces:
                if wp.mesh_id == mesh_id:
                    usages.append((step, "workpiece", wp.name))
            for tool in step.tools:
                if tool.mesh_id == mesh_id:
                    usages.append((step, "tool", tool.name))
        return usages

    def add_symmetry_plane(
        self,
        plane: SymmetryPlaneType = SymmetryPlaneType.YZ,
        coordinate: float = 0.0,
    ) -> SymmetryPlane | None:
        """
        対称面を追加

        Args:
            plane: 対称面タイプ
            coordinate: 平面の位置座標

        Returns:
            追加された対称面。追加できない場合はNone

        Note:
            - 対称面は最大2つまで追加可能
            - 同じ平面タイプは追加不可
        """
        # 最大数チェック
        if len(self.symmetry_planes) >= 2:
            return None

        # 重複チェック（同じ平面タイプは追加できない）
        for existing in self.symmetry_planes:
            if existing.plane == plane:
                return None

        sym = SymmetryPlane.create(plane=plane, coordinate=coordinate)
        self.symmetry_planes.append(sym)
        return sym

    def remove_symmetry_plane(self, plane_id: str) -> bool:
        """
        対称面を削除

        Args:
            plane_id: 削除する対称面のID

        Returns:
            削除に成功した場合True
        """
        for i, plane in enumerate(self.symmetry_planes):
            if plane.id == plane_id:
                self.symmetry_planes.pop(i)
                return True
        return False

    def add_constraint(self, name: str | None = None) -> ConstraintConfig:
        """新しい拘束条件を追加"""
        constraint_name = name or f"拘束条件 {len(self.constraints) + 1}"
        constraint = ConstraintConfig.create(name=constraint_name)
        self.constraints.append(constraint)
        return constraint

    def remove_constraint(self, constraint_id: str) -> bool:
        """
        拘束条件を削除

        Args:
            constraint_id: 削除する拘束条件のID

        Returns:
            削除に成功した場合True
        """
        for i, constraint in enumerate(self.constraints):
            if constraint.id == constraint_id:
                self.constraints.pop(i)
                return True
        return False

    def get_export_filename(self) -> str:
        """エクスポートファイル名を取得（output_filenameが空の場合はproject_nameを使用）"""
        return self.output_filename or self.project_name
