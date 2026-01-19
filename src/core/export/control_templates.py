"""Control設定のテンプレート"""

from typing import Any

from ansys.dyna.core import keywords as kwd


def get_default_control_keywords(end_time: float = 100.0) -> list[Any]:
    """
    デフォルトのControl設定を返す

    Args:
        end_time: 解析終了時間

    Returns:
        Control キーワードのリスト
    """
    return [
        # 終了時間
        kwd.ControlTermination(endtim=end_time),
        # 精度設定
        kwd.ControlAccuracy(osu=1, inn=4, pidosu=1),
        # 時間ステップ
        kwd.ControlTimestep(dtinit=0.0, tssfac=0.9, dt2ms=-0.001),
        # エネルギー設定
        kwd.ControlEnergy(hgen=2, rwen=2, slnten=2, rylen=2),
        # シェル設定
        kwd.ControlShell(istupd=1, theory=2, bwc=2, miter=1),
        # 接触設定
        kwd.ControlContact(rwpnal=1.0e-6, shlthk=2),
    ]
