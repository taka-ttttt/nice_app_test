"""弾塑性材料の定義"""

from ansys.dyna.core import keywords as kwd


# SUS305 - MAT024 (Piecewise Linear Plasticity)
sus305_mat024 = kwd.Mat024(
    mid=101,
    ro=7.93e-9,
    e=193000.0,
    pr=0.29,
    sigy=205.0,
    etan=0.0,
    lcss=101,
)
sus305_mat024.title = "sus305_mat024"


# SUS305 - MAT125 (Kinematic Hardening)
sus305_mat125 = kwd.Mat125(
    mid=102,
    ro=7.93e-9,
    e=193000.0,
    pr=0.29,
    sigy=205.0,
    etan=0.0,
    lcss=102,
)
sus305_mat125.title = "sus305_mat125"


# C5210-EH (Phosphor Bronze) - MAT024
c5210_eh_mat024 = kwd.Mat024(
    mid=201,
    ro=8.8e-3,
    e=110000.0,
    pr=0.33,
    sigy=593.54,
    etan=0.0,
    lcss=201,
)
c5210_eh_mat024.title = "c5210_eh_mat024"
