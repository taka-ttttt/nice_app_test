"""メッシュファイル変換機能

元のメッシュファイルから新しいID体系でメッシュファイルを生成する。
"""

import os


def convert_mesh_file(
    source_path: str,
    target_path: str,
    new_pid: int,
    node_id_offset: int = 0,
    element_id_offset: int = 0,
) -> str:
    """
    メッシュファイルを新しいIDで変換

    Args:
        source_path: 元のメッシュファイルパス
        target_path: 変換後の保存先パス
        new_pid: 新しいPart ID
        node_id_offset: 節点IDのオフセット
        element_id_offset: 要素IDのオフセット

    Returns:
        変換後のファイルパス

    TODO: 後で実装
        - *NODE のID変換（node_id + node_id_offset）
        - *ELEMENT_SHELL / *ELEMENT_SOLID のID変換（element_id + element_id_offset）
        - *PART のPID変更（new_pid）
        - 節点番号参照の更新（要素定義内の節点参照）

    Note:
        現時点では元のファイルパスをそのまま返す（変換はスキップ）
    """
    # TODO: 実装予定
    # 1. source_path のファイルを読み込み
    # 2. *NODE セクションの節点IDを変換
    # 3. *ELEMENT セクションの要素IDと節点参照を変換
    # 4. *PART のPIDを変更
    # 5. target_path に書き出し

    # 現時点では元のファイルパスをそのまま返す
    print(f"TODO: convert_mesh_file - {os.path.basename(source_path)} -> PID={new_pid}")
    return source_path
