"""材料定義"""

from .elastic_plastic import (
    c5210_eh_mat024,
    sus305_mat024,
    sus305_mat125,
)
from .rigid import (
    make_rigid_material,
    rigid_fixed_material,
    rigid_x_free_material,
    rigid_xy_free_material,
    rigid_xyz_free_material,
    rigid_y_free_material,
    rigid_yz_free_material,
    rigid_z_free_material,
    rigid_zx_free_material,
)


__all__ = [
    # 剛体材料
    "make_rigid_material",
    "rigid_fixed_material",
    "rigid_x_free_material",
    "rigid_y_free_material",
    "rigid_z_free_material",
    "rigid_xy_free_material",
    "rigid_yz_free_material",
    "rigid_zx_free_material",
    "rigid_xyz_free_material",
    # 弾塑性材料
    "sus305_mat024",
    "sus305_mat125",
    "c5210_eh_mat024",
]
