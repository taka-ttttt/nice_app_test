"""接触条件の生成ロジック"""

from dataclasses import dataclass

from ansys.dyna.core import keywords as kwd

from state.friction import FrictionConfig, FrictionMode


@dataclass(frozen=True)
class FrictionCoefficients:
    """摩擦係数の組み合わせ"""

    fs: float  # 静摩擦
    fd: float  # 動摩擦


# 摩擦係数の物理プリセット定義
# StateではなくCore（ドメイン知識）としてここに保持する
FRICTION_PRESETS = {
    FrictionMode.OIL: FrictionCoefficients(fs=0.10, fd=0.05),
    FrictionMode.DRY: FrictionCoefficients(fs=0.15, fd=0.10),
}


class ContactGenerator:
    """接触条件キーワード生成器"""

    # 物理パラメータ定数
    DEFAULT_EXPONENTIAL_DECAY = 10000.0
    DEFAULT_VISCOUS_DAMPING = 20.0
    DEFAULT_TOOL_DAMPING = 10.0

    @classmethod
    def resolve_friction(cls, config: FrictionConfig) -> tuple[float, float]:
        """設定から実際の摩擦係数を解決する"""
        if config.mode == FrictionMode.MANUAL:
            return config.manual_static_friction, config.manual_dynamic_friction

        # プリセットから解決
        # 万が一未定義のモードなら安全側に倒してOil相当にするかエラーにする
        # ここではOilをデフォルトとする
        preset = FRICTION_PRESETS.get(config.mode, FRICTION_PRESETS[FrictionMode.OIL])
        return preset.fs, preset.fd

    @classmethod
    def generate(
        cls,
        cid: int,
        heading: str,
        part_a_id: int,
        part_b_id: int,
        config: FrictionConfig,
        is_tool_contact: bool = False,
    ) -> kwd.ContactAutomaticSurfaceToSurface:
        """
        FrictionConfigから接触キーワードを生成する

        Args:
            cid: Contact ID
            heading: ヘッダーコメント
            part_a_id: Master Part ID
            part_b_id: Slave Part ID
            config: UIで設定された摩擦設定
            is_tool_contact: 工具同士の接触かどうか（減衰などを変える場合）

        Returns:
            ContactAutomaticSurfaceToSurface: 生成された接触キーワード
        """

        # 1. 摩擦係数の決定
        if is_tool_contact:
            # 工具間は摩擦なし
            fs = 0.0
            fd = 0.0
            vdc = cls.DEFAULT_TOOL_DAMPING
        else:
            # ワーク接触はConfigから解決
            fs, fd = cls.resolve_friction(config)
            vdc = cls.DEFAULT_VISCOUS_DAMPING

        # 2. PyDynaオブジェクトの生成
        return kwd.ContactAutomaticSurfaceToSurface(
            cid=cid,
            title=heading,
            surfa=part_a_id,
            surfb=part_b_id,
            fs=fs,
            fd=fd,
            vdc=vdc,
            # ソルバー推奨の固定パラメータ
            surfatyp=3,  # Part ID
            surfbtyp=3,  # Part ID
            dc=cls.DEFAULT_EXPONENTIAL_DECAY,
            penchk=0,  # 貫通チェック
            ignore=1,  # 初期嵌入無視
        )
