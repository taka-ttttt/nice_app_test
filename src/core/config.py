"""
解析設定モデル

UIの状態管理のためのデータクラスを定義します。
プレス成形シミュレーションアプリケーションの解析設定を管理します。
"""

import uuid
from dataclasses import dataclass, field
from enum import Enum


class ProcessType(Enum):
    """加工分類"""

    BENDING = "bending"
    DRAWING = "drawing"
    STRETCHING = "stretching"
    OTHER = "other"

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        names = {
            ProcessType.BENDING: "曲げ加工",
            ProcessType.DRAWING: "絞り加工",
            ProcessType.STRETCHING: "張り出し加工",
            ProcessType.OTHER: "その他",
        }
        return names.get(self, self.value)


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


class MotionType(Enum):
    """動作タイプ"""

    DISPLACEMENT = "displacement"
    LOAD = "load"
    FIXED = "fixed"
    # VELOCITY = "velocity"  # 将来追加予定

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        names = {
            MotionType.DISPLACEMENT: "変位",
            MotionType.LOAD: "荷重",
            MotionType.FIXED: "固定",
        }
        return names.get(self, self.value)


class MotionDirection(Enum):
    """動作方向"""

    POSITIVE_X = "+x"
    NEGATIVE_X = "-x"
    POSITIVE_Y = "+y"
    NEGATIVE_Y = "-y"
    POSITIVE_Z = "+z"
    NEGATIVE_Z = "-z"
    # CUSTOM = "custom"  # 将来追加予定: 任意ベクトル

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        return self.value.upper()

    def to_vector(self) -> tuple[float, float, float]:
        """単位ベクトルに変換"""
        vectors = {
            MotionDirection.POSITIVE_X: (1.0, 0.0, 0.0),
            MotionDirection.NEGATIVE_X: (-1.0, 0.0, 0.0),
            MotionDirection.POSITIVE_Y: (0.0, 1.0, 0.0),
            MotionDirection.NEGATIVE_Y: (0.0, -1.0, 0.0),
            MotionDirection.POSITIVE_Z: (0.0, 0.0, 1.0),
            MotionDirection.NEGATIVE_Z: (0.0, 0.0, -1.0),
        }
        return vectors.get(self, (0.0, 0.0, 0.0))


class FrictionMode(Enum):
    """摩擦係数モード"""

    OIL = "oil"  # 油あり: 静摩擦0.10, 動摩擦0.05
    DRY = "dry"  # 油なし: 静摩擦0.15, 動摩擦0.10
    MANUAL = "manual"  # マニュアル入力


class SymmetryPlaneType(Enum):
    """対称面タイプ"""

    XY = "xy"
    YZ = "yz"
    ZX = "zx"

    @property
    def display_name(self) -> str:
        """UI表示用の名前を取得"""
        return self.value.upper()


# =============================================================================
# 材料プリセット
# =============================================================================

MATERIAL_PRESETS = {
    "SPCC": {
        "name": "軟鋼 (SPCC)",
        "density": 7.83e-9,
        "youngs_modulus": 207000.0,
        "poisson_ratio": 0.28,
        "yield_stress": 280.0,
    },
    "SUS304": {
        "name": "ステンレス鋼 (SUS304)",
        "density": 7.93e-9,
        "youngs_modulus": 193000.0,
        "poisson_ratio": 0.29,
        "yield_stress": 205.0,
    },
    "SUS305": {
        "name": "ステンレス鋼 (SUS305)",
        "density": 7.93e-9,
        "youngs_modulus": 193000.0,
        "poisson_ratio": 0.29,
        "yield_stress": 205.0,
    },
    "A5052": {
        "name": "アルミニウム合金 (A5052)",
        "density": 2.68e-9,
        "youngs_modulus": 70000.0,
        "poisson_ratio": 0.33,
        "yield_stress": 195.0,
    },
    "A6061-T6": {
        "name": "アルミニウム合金 (A6061-T6)",
        "density": 2.70e-9,
        "youngs_modulus": 68900.0,
        "poisson_ratio": 0.33,
        "yield_stress": 276.0,
    },
    "C1100": {
        "name": "銅合金 (C1100)",
        "density": 8.96e-9,
        "youngs_modulus": 118000.0,
        "poisson_ratio": 0.34,
        "yield_stress": 70.0,
    },
    "Ti-6Al-4V": {
        "name": "チタン合金 (Ti-6Al-4V)",
        "density": 4.43e-9,
        "youngs_modulus": 113800.0,
        "poisson_ratio": 0.34,
        "yield_stress": 880.0,
    },
}


# =============================================================================
# データクラス
# =============================================================================


@dataclass
class MaterialConfig:
    """材料特性設定"""

    density: float  # 密度 (ton/mm^3)
    youngs_modulus: float  # ヤング率 (MPa)
    poisson_ratio: float  # ポアソン比
    yield_stress: float  # 降伏応力 (MPa)
    tangent_modulus: float = 0.0  # 接線係数 (MPa)

    @classmethod
    def from_preset(cls, preset_key: str) -> "MaterialConfig":
        """プリセットからMaterialConfigを作成"""
        if preset_key not in MATERIAL_PRESETS:
            raise ValueError(f"Unknown material preset: {preset_key}")
        preset = MATERIAL_PRESETS[preset_key]
        return cls(
            density=preset["density"],
            youngs_modulus=preset["youngs_modulus"],
            poisson_ratio=preset["poisson_ratio"],
            yield_stress=preset["yield_stress"],
        )


@dataclass
class MeshInfo:
    """アップロードされたメッシュ情報"""

    id: str  # 一意のID (UUID)
    file_name: str  # オリジナルファイル名
    file_path: str  # サーバー側の一時保存パス
    part_id: int  # *PARTで定義されたパートID
    part_name: str  # *PARTのタイトル
    element_count: int  # 要素数
    node_count: int  # 節点数
    element_type: str = "SHELL"  # 要素タイプ (SHELL/SOLID)
    has_shared_nodes: bool = False  # 他パートと節点を共有しているか

    @classmethod
    def create(
        cls,
        file_name: str,
        file_path: str,
        part_id: int,
        part_name: str,
        element_count: int,
        node_count: int,
        element_type: str = "SHELL",
        has_shared_nodes: bool = False,
    ) -> "MeshInfo":
        """自動生成IDで新しいMeshInfoを作成"""
        return cls(
            id=str(uuid.uuid4()),
            file_name=file_name,
            file_path=file_path,
            part_id=part_id,
            part_name=part_name,
            element_count=element_count,
            node_count=node_count,
            element_type=element_type,
            has_shared_nodes=has_shared_nodes,
        )


@dataclass
class WorkpieceConfig:
    """ワーク設定"""

    id: str  # 一意のID
    name: str  # ワーク名
    mesh_id: str  # MeshInfoへの参照
    material_preset: str  # プリセットキー または "custom"
    custom_material: MaterialConfig | None = None
    thickness: float = 1.0  # 板厚 (mm)

    @classmethod
    def create(
        cls,
        name: str = "ワーク",
        mesh_id: str = "",
        material_preset: str = "SPCC",
        thickness: float = 1.0,
    ) -> "WorkpieceConfig":
        """自動生成IDで新しいWorkpieceConfigを作成"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            mesh_id=mesh_id,
            material_preset=material_preset,
            thickness=thickness,
        )

    def get_material(self) -> MaterialConfig:
        """材料設定を取得（プリセットまたはカスタム）"""
        if self.material_preset == "custom" and self.custom_material:
            return self.custom_material
        return MaterialConfig.from_preset(self.material_preset)


@dataclass
class ToolConfig:
    """工具設定"""

    id: str  # 一意のID
    name: str  # 工具名
    mesh_id: str  # MeshInfoへの参照
    motion_type: MotionType  # 動作タイプ
    direction: MotionDirection | None = None  # 動作方向
    value: float | None = None  # 変位量 (mm) または 荷重 (N)
    motion_time: float = 1.0  # 動作時間 (ms)、デフォルト: 1ms
    # custom_vector: Optional[Tuple[float, float, float]] = None  # 将来追加予定

    @classmethod
    def create(
        cls,
        name: str = "工具",
        mesh_id: str = "",
        motion_type: MotionType = MotionType.FIXED,
    ) -> "ToolConfig":
        """自動生成IDで新しいToolConfigを作成"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            mesh_id=mesh_id,
            motion_type=motion_type,
        )


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


@dataclass
class SymmetryPlane:
    """対称面設定"""

    plane: SymmetryPlaneType  # 平面タイプ (XY/YZ/ZX)
    coordinate: float = 0.0  # 平面の位置


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


@dataclass
class StepConfig:
    """工程設定（1工程分のワーク・工具設定をまとめる）"""

    id: str  # 一意のID (UUID)
    name: str  # 工程名（例: "曲げ1"）
    step_type: ProcessType  # 工程タイプ（曲げ/絞り/張り出し/その他）
    order: int  # 工程の順序 (1, 2, 3, ...)

    # 工程ごとのパート設定
    workpieces: list[WorkpieceConfig] = field(default_factory=list)
    tools: list[ToolConfig] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        name: str = "工程",
        step_type: ProcessType = ProcessType.BENDING,
        order: int = 1,
    ) -> "StepConfig":
        """自動生成IDとデフォルトパートで新しいStepConfigを作成"""
        step = cls(
            id=str(uuid.uuid4()),
            name=name,
            step_type=step_type,
            order=order,
        )
        # デフォルトのワークと工具を追加
        step.workpieces.append(WorkpieceConfig.create(name="ワーク 1"))
        step.tools.append(ToolConfig.create(name="工具 1"))
        return step

    def add_workpiece(self, name: str | None = None) -> WorkpieceConfig:
        """この工程に新しいワークを追加"""
        wp_name = name or f"ワーク {len(self.workpieces) + 1}"
        workpiece = WorkpieceConfig.create(name=wp_name)
        self.workpieces.append(workpiece)
        return workpiece

    def add_tool(self, name: str | None = None) -> ToolConfig:
        """この工程に新しい工具を追加"""
        tool_name = name or f"工具 {len(self.tools) + 1}"
        tool = ToolConfig.create(name=tool_name)
        self.tools.append(tool)
        return tool

    def remove_workpiece(self, workpiece_id: str) -> bool:
        """IDでワークを削除。削除した場合はTrueを返す"""
        for i, wp in enumerate(self.workpieces):
            if wp.id == workpiece_id:
                self.workpieces.pop(i)
                return True
        return False

    def remove_tool(self, tool_id: str) -> bool:
        """IDで工具を削除。削除した場合はTrueを返す"""
        for i, tool in enumerate(self.tools):
            if tool.id == tool_id:
                self.tools.pop(i)
                return True
        return False


@dataclass
class AnalysisConfig:
    """解析設定全体を管理するメインクラス"""

    # 解析概要
    project_name: str = "untitled"
    process_type: ProcessType = ProcessType.BENDING
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
        """工程を複製。新しい工程を返す。見つからない場合はNone"""
        source = self.get_step_by_id(step_id)
        if not source:
            return None

        # コピーした設定で新しい工程を作成
        new_step = StepConfig.create(
            name=f"{source.name} (コピー)",
            step_type=source.step_type,
            order=len(self.steps) + 1,
        )
        # デフォルトパートをクリアしてソースからコピー
        new_step.workpieces.clear()
        new_step.tools.clear()

        for wp in source.workpieces:
            new_wp = WorkpieceConfig.create(
                name=wp.name,
                mesh_id=wp.mesh_id,
                material_preset=wp.material_preset,
                thickness=wp.thickness,
            )
            new_wp.custom_material = wp.custom_material
            new_step.workpieces.append(new_wp)

        for tool in source.tools:
            new_tool = ToolConfig.create(
                name=tool.name,
                mesh_id=tool.mesh_id,
                motion_type=tool.motion_type,
            )
            new_tool.direction = tool.direction
            new_tool.value = tool.value
            new_tool.motion_time = tool.motion_time
            new_step.tools.append(new_tool)

        self.steps.append(new_step)
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
    ) -> SymmetryPlane:
        """対称面を追加"""
        sym = SymmetryPlane(plane=plane, coordinate=coordinate)
        self.symmetry_planes.append(sym)
        return sym

    def add_constraint(self, name: str | None = None) -> ConstraintConfig:
        """新しい拘束条件を追加"""
        constraint_name = name or f"拘束条件 {len(self.constraints) + 1}"
        constraint = ConstraintConfig.create(name=constraint_name)
        self.constraints.append(constraint)
        return constraint

    def get_export_filename(self) -> str:
        """エクスポートファイル名を取得（output_filenameが空の場合はproject_nameを使用）"""
        return self.output_filename or self.project_name
