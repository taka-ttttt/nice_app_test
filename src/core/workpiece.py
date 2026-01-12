"""ワーク（被加工材）エンティティ - プレス成形における被加工材を表現"""

from dataclasses import dataclass
from typing import Any

from ansys.dyna.core import keywords as kwd


@dataclass
class MaterialProperties:
    """材料特性を表す値オブジェクト"""

    density: float  # 密度 (g/mm^3 or ton/mm^3)
    youngs_modulus: float  # ヤング率 (MPa)
    poisson_ratio: float  # ポアソン比
    yield_stress: float  # 降伏応力 (MPa)
    tangent_modulus: float = 0.0  # 接線係数 (MPa)
    stress_strain_curve_id: int | None = None  # 応力-ひずみカーブID

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "density": self.density,
            "youngs_modulus": self.youngs_modulus,
            "poisson_ratio": self.poisson_ratio,
            "yield_stress": self.yield_stress,
            "tangent_modulus": self.tangent_modulus,
            "stress_strain_curve_id": self.stress_strain_curve_id,
        }


@dataclass
class Workpiece:
    """
    ワーク（被加工材）エンティティ

    プレス成形シミュレーションにおける被加工材を表現します。
    材料特性、形状情報、メッシュ情報を管理します。
    """

    # 識別情報
    id: int  # ワークID（part_id）
    name: str = "workpiece"  # ワーク名

    # 形状情報
    mesh_file: str | None = None  # メッシュファイルパス
    thickness: float | None = None  # 板厚 (mm)

    # 材料・セクション
    material_id: int | None = None
    section_id: int | None = None
    material_type: str = "mat024"  # 材料モデルタイプ

    # 材料特性
    material_properties: MaterialProperties | None = None

    def set_material_properties(
        self,
        density: float,
        youngs_modulus: float,
        poisson_ratio: float,
        yield_stress: float,
        tangent_modulus: float = 0.0,
        stress_strain_curve_id: int | None = None,
    ) -> "Workpiece":
        """
        材料特性を設定

        Parameters:
        - density: 密度
        - youngs_modulus: ヤング率
        - poisson_ratio: ポアソン比
        - yield_stress: 降伏応力
        - tangent_modulus: 接線係数（デフォルト: 0.0）
        - stress_strain_curve_id: 応力-ひずみカーブID（オプション）

        Returns:
        - self（メソッドチェーン用）
        """
        self.material_properties = MaterialProperties(
            density=density,
            youngs_modulus=youngs_modulus,
            poisson_ratio=poisson_ratio,
            yield_stress=yield_stress,
            tangent_modulus=tangent_modulus,
            stress_strain_curve_id=stress_strain_curve_id,
        )
        return self

    def set_thickness(self, thickness: float) -> "Workpiece":
        """
        板厚を設定

        Parameters:
        - thickness: 板厚 (mm)

        Returns:
        - self（メソッドチェーン用）
        """
        self.thickness = thickness
        return self

    def set_mesh_file(self, mesh_file: str) -> "Workpiece":
        """
        メッシュファイルを設定

        Parameters:
        - mesh_file: メッシュファイルパス

        Returns:
        - self（メソッドチェーン用）
        """
        self.mesh_file = mesh_file
        return self

    def create_material_mat024(self) -> kwd.Mat024:
        """
        MAT024（Piecewise Linear Plasticity）材料を生成

        Returns:
        - kwd.Mat024: 材料キーワード
        """
        if self.material_properties is None:
            raise ValueError(
                "材料特性が設定されていません。set_material_properties()を先に呼び出してください。"
            )

        props = self.material_properties
        mat = kwd.Mat024(
            mid=self.material_id or self.id,
            ro=props.density,
            e=props.youngs_modulus,
            pr=props.poisson_ratio,
            sigy=props.yield_stress,
            etan=props.tangent_modulus,
        )

        if props.stress_strain_curve_id:
            mat.lcss = props.stress_strain_curve_id

        mat.title = f"{self.name}_mat024"
        return mat

    def create_material_mat125(self) -> kwd.Mat125:
        """
        MAT125（Kinematic Hardening）材料を生成

        Returns:
        - kwd.Mat125: 材料キーワード
        """
        if self.material_properties is None:
            raise ValueError(
                "材料特性が設定されていません。set_material_properties()を先に呼び出してください。"
            )

        props = self.material_properties
        mat = kwd.Mat125(
            mid=self.material_id or self.id,
            ro=props.density,
            e=props.youngs_modulus,
            pr=props.poisson_ratio,
            sigy=props.yield_stress,
            etan=props.tangent_modulus,
        )

        if props.stress_strain_curve_id:
            mat.lcss = props.stress_strain_curve_id

        mat.title = f"{self.name}_mat125"
        return mat

    def create_material(self) -> Any:
        """
        設定されたタイプに基づいて材料を生成

        Returns:
        - 材料キーワード
        """
        material_creators = {
            "mat024": self.create_material_mat024,
            "mat125": self.create_material_mat125,
        }

        if self.material_type not in material_creators:
            available = ", ".join(material_creators.keys())
            raise ValueError(
                f"未対応の材料タイプ: '{self.material_type}'. 利用可能: {available}"
            )

        return material_creators[self.material_type]()

    def create_section_shell(
        self, elform: int = 2, nip: int = 5, shrf: float = 0.833
    ) -> kwd.SectionShell:
        """
        シェルセクションを生成

        Parameters:
        - elform: 要素フォーミュレーション（デフォルト: 2 = BT shell）
        - nip: 積分点数（デフォルト: 5）
        - shrf: せん断補正係数（デフォルト: 0.833）

        Returns:
        - kwd.SectionShell: セクションキーワード
        """
        if self.thickness is None:
            raise ValueError(
                "板厚が設定されていません。set_thickness()を先に呼び出してください。"
            )

        section = kwd.SectionShell(
            secid=self.section_id or self.id,
            elform=elform,
            shrf=shrf,
            nip=nip,
            t1=self.thickness,
            t2=self.thickness,
            t3=self.thickness,
            t4=self.thickness,
        )
        section.title = f"{self.name}_section"
        return section

    def to_dict(self) -> dict[str, Any]:
        """
        ワーク情報を辞書形式で取得

        Returns:
        - ワーク情報の辞書
        """
        return {
            "id": self.id,
            "name": self.name,
            "mesh_file": self.mesh_file,
            "thickness": self.thickness,
            "material_id": self.material_id,
            "section_id": self.section_id,
            "material_type": self.material_type,
            "material_properties": self.material_properties.to_dict()
            if self.material_properties
            else None,
        }

    def __repr__(self) -> str:
        thickness_str = f", thickness={self.thickness}mm" if self.thickness else ""
        return f"Workpiece(id={self.id}, name='{self.name}'{thickness_str})"


# ファクトリ関数
def create_steel_workpiece(
    workpiece_id: int, name: str = "steel_blank", thickness: float = 1.0
) -> Workpiece:
    """
    スチール材ワークを作成

    一般的なスチール材（例：SPCC）のデフォルト特性を設定
    """
    workpiece = Workpiece(
        id=workpiece_id, name=name, thickness=thickness, material_type="mat024"
    )
    workpiece.set_material_properties(
        density=7.83e-9,  # ton/mm^3
        youngs_modulus=207000.0,  # MPa
        poisson_ratio=0.28,
        yield_stress=280.0,  # MPa
    )
    return workpiece


def create_stainless_workpiece(
    workpiece_id: int, name: str = "sus_blank", thickness: float = 1.0
) -> Workpiece:
    """
    ステンレス材ワークを作成

    SUS305のデフォルト特性を設定
    """
    workpiece = Workpiece(
        id=workpiece_id, name=name, thickness=thickness, material_type="mat024"
    )
    workpiece.set_material_properties(
        density=7.93e-9,  # ton/mm^3
        youngs_modulus=193000.0,  # MPa
        poisson_ratio=0.29,
        yield_stress=205.0,  # MPa
    )
    return workpiece


def create_aluminum_workpiece(
    workpiece_id: int, name: str = "aluminum_blank", thickness: float = 1.0
) -> Workpiece:
    """
    アルミニウム材ワークを作成

    A5052のデフォルト特性を設定
    """
    workpiece = Workpiece(
        id=workpiece_id, name=name, thickness=thickness, material_type="mat024"
    )
    workpiece.set_material_properties(
        density=2.68e-9,  # ton/mm^3
        youngs_modulus=70000.0,  # MPa
        poisson_ratio=0.33,
        yield_stress=195.0,  # MPa
    )
    return workpiece
