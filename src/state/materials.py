"""材料設定とプリセット定義"""

from dataclasses import dataclass


# 材料プリセット
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
