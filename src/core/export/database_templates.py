"""Database設定のテンプレート"""

from typing import Any

from ansys.dyna.core import keywords as kwd


def get_default_database_keywords(
    step_order: int = 1,
    total_steps: int = 1,
    previous_dynain_path: str | None = None,
    end_time: float = 100.0,
) -> list[Any]:
    """
    デフォルトのDatabase設定を返す

    Args:
        step_order: 現在の工程番号（1から）
        total_steps: 全工程数
        previous_dynain_path: 前工程のdynainファイルパス（2工程目以降）
        end_time: 解析終了時間

    Returns:
        Database キーワードのリスト
    """
    keywords = [
        # d3plot出力
        kwd.DatabaseBinaryD3plot(dt=1.0),
        # 履歴出力
        kwd.DatabaseBinaryD3thdt(dt=0.1),
        # 出力変数
        kwd.DatabaseExtentBinary(neiph=6, neips=6, maxint=3),
        # 節点履歴
        kwd.DatabaseHistoryNodeLocal(id1=0, id2=0, id3=0, id4=0),
        # グローバル統計
        kwd.DatabaseGlstat(dt=0.1),
    ]

    # 最終工程でない場合は dynain 出力
    if step_order < total_steps:
        # dynain出力（最終時刻で出力）
        keywords.append(kwd.DatabaseBinaryIntfor(dt=end_time))

    # 2工程目以降は前工程のdynain読み込み
    if step_order > 1 and previous_dynain_path:
        keywords.append(kwd.Include(filename=previous_dynain_path))

    return keywords
