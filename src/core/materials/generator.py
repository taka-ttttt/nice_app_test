"""材料定義の生成ロジック"""

from ansys.dyna.core import keywords as kwd

from state.materials import MATERIAL_PRESETS, MaterialConfig


class MaterialGenerator:
    """材料キーワード生成器"""

    @classmethod
    def resolve_material(
        cls, preset_key: str, custom: MaterialConfig | None = None
    ) -> MaterialConfig:
        """
        プリセットキーまたはカスタム材料から物性値を解決する

        Args:
            preset_key: プリセットキー ("SPCC", "SUS304", ...) または "custom"
            custom: カスタム材料設定（preset_key="custom"の場合に使用）

        Returns:
            MaterialConfig: 解決された材料設定
        """
        if preset_key == "custom":
            if custom is None:
                raise ValueError("Custom material is specified but custom data is None")
            return custom

        # プリセットから解決
        if preset_key not in MATERIAL_PRESETS:
            # フォールバック: SPCCをデフォルトとする
            preset_key = "SPCC"

        preset = MATERIAL_PRESETS[preset_key]
        return MaterialConfig(
            density=preset["density"],
            youngs_modulus=preset["youngs_modulus"],
            poisson_ratio=preset["poisson_ratio"],
            yield_stress=preset["yield_stress"],
            lcss=preset["lcss"],
            tangent_modulus=0.0,
        )

    @classmethod
    def generate(
        cls,
        mid: int,
        preset_key: str,
        custom_material: MaterialConfig | None = None,
    ) -> kwd.Mat024:
        """
        材料設定からLS-DYNAの材料キーワードを生成する

        Args:
            mid: Material ID
            preset_key: プリセットキー または "custom"
            custom_material: カスタム材料設定（preset_key="custom"の場合）

        Returns:
            Mat024: 生成された材料キーワード
        """
        # 材料物性を解決
        config = cls.resolve_material(preset_key, custom_material)

        # PyDynaオブジェクトの生成
        # MAT_024：Piecewise Linear Plasticity
        mat = kwd.Mat024(
            mid=mid,
            ro=config.density,
            e=config.youngs_modulus,
            pr=config.poisson_ratio,
            sigy=config.yield_stress,
            etan=config.tangent_modulus,
            lcss=config.lcss,
        )

        # プリセット名をタイトルに設定（カスタムの場合は"Custom Material"）
        if preset_key == "custom":
            mat.title = "Custom Material"
        else:
            mat.title = MATERIAL_PRESETS.get(preset_key, {}).get("name", preset_key)

        return mat
