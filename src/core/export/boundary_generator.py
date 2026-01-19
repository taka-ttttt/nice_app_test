"""境界条件生成のヘルパー関数"""

from ansys.dyna.core import keywords as kwd

from state.symmetry import SymmetryPlane, SymmetryPlaneType


def generate_symmetry_constraint(sym_plane: SymmetryPlane) -> kwd.ConstrainedGlobal:
    """
    対称面から ConstrainedGlobal を生成

    Args:
        sym_plane: 対称面設定

    Returns:
        ConstrainedGlobal キーワード
    """
    # 平面タイプから方向を決定
    # XY面 -> Z方向拘束 (dir=3)
    # YZ面 -> X方向拘束 (dir=1)
    # ZX面 -> Y方向拘束 (dir=2)
    plane_to_dir = {
        SymmetryPlaneType.YZ: 1,  # x方向
        SymmetryPlaneType.ZX: 2,  # y方向
        SymmetryPlaneType.XY: 3,  # z方向
    }

    dir_num = plane_to_dir[sym_plane.plane]

    # 座標値を設定
    x, y, z = 0.0, 0.0, 0.0
    if dir_num == 1:
        x = sym_plane.coordinate
    elif dir_num == 2:
        y = sym_plane.coordinate
    elif dir_num == 3:
        z = sym_plane.coordinate

    return kwd.ConstrainedGlobal(
        tc=1,  # 並進拘束（方向1つ）
        rc=0,  # 回転拘束なし
        dir=dir_num,
        x=x,
        y=y,
        z=z,
        tol=0.01,  # 許容誤差
    )
