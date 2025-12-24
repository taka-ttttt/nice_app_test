"""接触条件の設定と生成"""
from ansys.dyna.core import keywords as kwd


class ContactParams:
    """接触条件の共通パラメータ"""
    # 摩擦係数
    STATIC_FRICTION = 0.15      # 静摩擦係数
    DYNAMIC_FRICTION = 0.12     # 動摩擦係数
    TOOL_FRICTION = 0.0         # 工具間摩擦係数（無摩擦）
    
    # 接触制御パラメータ
    EXPONENTIAL_DECAY = 10000.0  # 指数減衰係数
    VISCOUS_COEFF = 0.0         # 粘性摩擦係数
    VISCOUS_DAMPING = 20.0      # 粘性減衰係数（%）
    TOOL_DAMPING = 10.0         # 工具間減衰係数（%）
    
    # 初期嵌入制御
    IGNORE_INITIAL_PEN = 1      # 初期嵌入を無視（1=有効）
    PENETRATION_CHECK = 0       # 貫通チェック


def create_contact(
    cid: int,
    heading: str,
    surfa: int,
    surfb: int,
    contact_type: str = "work_tool",
    **overrides
) -> kwd.ContactAutomaticSurfaceToSurface:
    """
    接触条件を作成する関数
    
    Parameters:
    -----------
    cid : int
        接触ID
    heading : str
        接触条件の説明
    surfa : int
        接触面A（Part ID）
    surfb : int
        接触面B（Part ID）
    contact_type : str
        接触タイプ ("work_tool" または "tool_tool")
    **overrides : dict
        個別パラメータのオーバーライド
        例: fs=0.2, fd=0.15, vdc=25.0 など
    
    Returns:
    --------
    ContactAutomaticSurfaceToSurface
        作成された接触条件オブジェクト
    """
    # 接触タイプに応じてデフォルトパラメータを選択
    if contact_type == "tool_tool":
        default_params = {
            "fs": ContactParams.TOOL_FRICTION,
            "fd": ContactParams.TOOL_FRICTION,
            "vdc": ContactParams.TOOL_DAMPING,
        }
    else:  # work_tool
        default_params = {
            "fs": ContactParams.STATIC_FRICTION,
            "fd": ContactParams.DYNAMIC_FRICTION,
            "vdc": ContactParams.VISCOUS_DAMPING,
        }
    
    # 共通のデフォルトパラメータを追加
    default_params.update({
        "surfatyp": 3,                              # Part ID指定
        "surfbtyp": 3,                              # Part ID指定
        "dc": ContactParams.EXPONENTIAL_DECAY,      # 指数減衰係数
        "vc": ContactParams.VISCOUS_COEFF,          # 粘性摩擦係数
        "penchk": ContactParams.PENETRATION_CHECK,  # 貫通チェック
        "ignore": ContactParams.IGNORE_INITIAL_PEN  # 初期嵌入を無視
    })
    
    # オーバーライドパラメータでデフォルト値を更新
    final_params = {**default_params, **overrides}
    
    return kwd.ContactAutomaticSurfaceToSurface(
        cid=cid,
        heading=heading,
        surfa=surfa,
        surfb=surfb,
        **final_params
    )

