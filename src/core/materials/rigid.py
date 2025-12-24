"""剛体材料（MAT_RIGID）の定義"""
from ansys.dyna.core import keywords as kwd


def make_rigid_material(mid: int = 9000, constraint: str = "fixed", **overrides) -> kwd.Mat020:
    """
    剛体材料（MAT_RIGID）を作成
    
    Parameters:
    - mid: Material ID
    - constraint: 制約条件（デフォルト: "fixed"）
        - "fixed": 完全固定
        - "x-free": X方向自由
        - "y-free": Y方向自由  
        - "z-free": Z方向自由
        - "xy-free": XY方向自由
        - "yz-free": YZ方向自由
        - "zx-free": ZX方向自由
        - "xyz-free": XYZ方向自由
    - overrides: その他のパラメータ上書き
    """
    m = kwd.Mat020(mid=mid)
    m.ro = 7.83e-3    # 密度 (g/mm^3)
    m.e = 207000.0    # ヤング率 (MPa)
    m.pr = 0.28       # ポアソン比
    
    # 制約条件の設定（デフォルトで"fixed"が適用される）
    # 並進拘束のマッピング（con1用）
    # 0: 制約なし, 1: x拘束, 2: y拘束, 3: z拘束, 4: xy拘束, 5: yz拘束, 6: zx拘束, 7: xyz拘束
    constraint_map = {
        "fixed": 7,       # 完全固定（全方向拘束）
        "x-free": 6,      # X方向自由（YZ拘束）
        "y-free": 5,      # Y方向自由（ZX拘束）  
        "z-free": 4,      # Z方向自由（XY拘束）
        "xy-free": 3,     # XY方向自由（Z拘束）
        "yz-free": 1,     # YZ方向自由（X拘束）
        "zx-free": 2,     # ZX方向自由（Y拘束）
        "xyz-free": 0,    # XYZ方向自由（拘束なし）
    }
    constraint_lower = constraint.lower()
    if constraint_lower not in constraint_map:
        available = ", ".join(constraint_map.keys())
        raise ValueError(f"無効な制約条件: '{constraint}'. 利用可能: {available}")
    
    # グローバル拘束を使用
    m.cmo = 1.0  # グローバル方向の拘束を適用
    m.con1 = constraint_map[constraint_lower]  # 並進拘束
    m.con2 = 7  # 回転は全方向拘束（x, y, z回転すべて固定）
    m.title = f"rigid_{constraint_lower}"
        
    # パラメータの上書き
    for k, v in overrides.items():
        setattr(m, k, v)
    
    return m


# rigid materials template
rigid_fixed_material = make_rigid_material(mid=9000, constraint="fixed")
rigid_x_free_material = make_rigid_material(mid=9001, constraint="x-free")
rigid_y_free_material = make_rigid_material(mid=9002, constraint="y-free")
rigid_z_free_material = make_rigid_material(mid=9003, constraint="z-free")
rigid_xy_free_material = make_rigid_material(mid=9004, constraint="xy-free")
rigid_yz_free_material = make_rigid_material(mid=9005, constraint="yz-free")
rigid_zx_free_material = make_rigid_material(mid=9006, constraint="zx-free")
rigid_xyz_free_material = make_rigid_material(mid=9007, constraint="xyz-free")

