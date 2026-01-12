"""
LS-DYNA kファイルパーサー

ansys-dyna-coreのDeckクラスを活用して、
.kファイルからパート情報、要素数、節点数を抽出します。
"""

import os
import tempfile
from contextlib import suppress
from dataclasses import dataclass, field

from ansys.dyna.core import Deck


@dataclass
class ParsedPart:
    """パース結果のパート情報"""

    part_id: int
    part_name: str
    element_count: int
    node_count: int
    element_type: str  # "SHELL", "SOLID", etc.
    node_ids: set[int] = field(default_factory=set)


def parse_kfile(file_path: str) -> tuple[list[ParsedPart], bool]:
    """
    kファイルを解析してパート情報を抽出

    Args:
        file_path: kファイルのパス

    Returns:
        (パートリスト, 節点共有があるか)
    """
    # Deckオブジェクトを作成してkファイルを読み込む
    deck = Deck()

    # エンコーディングを試行
    for encoding in ["utf-8", "shift-jis", "cp932", "latin-1"]:
        try:
            deck.import_file(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    # パート名のマッピングを作成（PARTキーワードから）
    part_names: dict[int, str] = {}
    for part_kwd in deck.get_kwds_by_type("PART"):
        try:
            pid = int(part_kwd.pid)
            title = ""
            if hasattr(part_kwd, "title") and part_kwd.title:
                title = str(part_kwd.title).strip()
            if not title:
                title = f"Part {pid}"
            part_names[pid] = title
        except (AttributeError, ValueError, TypeError):
            continue

    # パート情報を格納
    part_data: dict[int, dict] = {}

    # ELEMENT_SHELL を処理
    _process_element_dataframe(deck, "SHELL", part_data, part_names)

    # ELEMENT_SOLID を処理
    _process_element_dataframe(deck, "SOLID", part_data, part_names)

    # 節点共有のチェック
    has_shared_nodes = _check_shared_nodes(part_data)

    # ParsedPartリストを作成
    result = []
    for pid, data in part_data.items():
        result.append(
            ParsedPart(
                part_id=pid,
                part_name=data["name"],
                element_count=data["element_count"],
                node_count=len(data["node_ids"]),
                element_type=data["element_type"],
                node_ids=data["node_ids"],
            )
        )

    # part_idでソート
    result.sort(key=lambda p: p.part_id)

    return result, has_shared_nodes


def _process_element_dataframe(
    deck: Deck,
    element_subtype: str,
    part_data: dict[int, dict],
    part_names: dict[int, str],
) -> None:
    """
    要素キーワードのDataFrameを処理してパート情報を抽出

    Args:
        deck: Deckオブジェクト
        element_subtype: 要素サブタイプ ("SHELL", "SOLID", etc.)
        part_data: パート情報を格納する辞書
        part_names: パート名のマッピング
    """
    for elem_kwd in deck.get_kwds_by_full_type("ELEMENT", element_subtype):
        try:
            # elementsプロパティでDataFrameを取得
            df = elem_kwd.elements
            if df is None or df.empty:
                continue

            # pidでグループ化
            for pid, group in df.groupby("pid"):
                pid = int(pid)

                # 要素数をカウント
                element_count = len(group)

                # 節点IDを収集（n1〜n8列から）
                node_ids = set()
                for col in ["n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8"]:
                    if col in group.columns:
                        # 0より大きい値のみ（0は未使用ノード）
                        valid_nodes = group[col][group[col] > 0]
                        node_ids.update(valid_nodes.astype(int).tolist())

                # パート情報を更新または作成
                if pid in part_data:
                    # 既存のパートに追加
                    part_data[pid]["element_count"] += element_count
                    part_data[pid]["node_ids"].update(node_ids)
                    # 複数の要素タイプがある場合は最初のものを使用
                else:
                    part_data[pid] = {
                        "name": part_names.get(pid, f"Part {pid}"),
                        "element_count": element_count,
                        "element_type": element_subtype,
                        "node_ids": node_ids,
                    }

        except (AttributeError, ValueError, TypeError):
            # エラーが発生した場合はスキップ
            continue


def _check_shared_nodes(part_data: dict[int, dict]) -> bool:
    """複数パート間で節点が共有されているかチェック"""
    part_list = list(part_data.items())

    for i, data1 in enumerate(part_list):
        for data2 in part_list[i + 1 :]:
            if data1["node_ids"] & data2["node_ids"]:
                return True

    return False


def parse_kfile_from_bytes(
    data: bytes, file_name: str = ""
) -> tuple[list[ParsedPart], bool]:
    """
    バイトデータからkファイルを解析

    Args:
        data: ファイルのバイトデータ
        file_name: ファイル名

    Returns:
        (パートリスト, 節点共有があるか)
    """
    # 一時ファイルに書き込んでDeckで読み込む
    suffix = ".k" if not file_name else os.path.splitext(file_name)[1]
    if not suffix:
        suffix = ".k"

    with tempfile.NamedTemporaryFile(
        mode="wb", suffix=suffix, delete=False
    ) as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name

    try:
        return parse_kfile(tmp_path)
    finally:
        # 一時ファイルを削除
        with suppress(OSError):
            os.unlink(tmp_path)
