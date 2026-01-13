from dataclasses import dataclass

from ansys.dyna.core import Deck


# 定数定義
ELEMENT_TYPE_SOLID = "SOLID"
ELEMENT_TYPE_SHELL = "SHELL"
ELEMENT_TYPE_MIXED = "MIXED"

SUPPORTED_ENCODINGS = ["utf-8", "shift-jis", "cp932", "latin-1"]


@dataclass(frozen=True)
class ParsedPart:
    """パース結果のパート情報"""

    part_id: int
    part_name: str
    element_count: int
    element_type: str

    def with_added_elements(self, count: int, elem_type: str) -> "ParsedPart":
        """
        要素を追加した新しいインスタンスを返す

        Args:
            count: 追加する要素数
            elem_type: 追加する要素のタイプ

        Returns:
            要素が追加された新しいParsedPartインスタンス
        """
        new_type = (
            ELEMENT_TYPE_MIXED if self.element_type != elem_type else self.element_type
        )
        return ParsedPart(
            part_id=self.part_id,
            part_name=self.part_name,
            element_count=self.element_count + count,
            element_type=new_type,
        )


def extract_parts_from_mesh(file_path: str) -> tuple[list[ParsedPart], bool]:
    """
    メッシュファイル（.kファイル）からパート情報を抽出

    Args:
        file_path: メッシュファイル（.kファイル）のパス

    Returns:
        (パートリスト, 節点共有フラグ) のタプル

    Raises:
        RuntimeError: ファイルの読み込みに失敗した場合
    """
    deck = _load_k_file(file_path)

    # パートを辞書で管理
    parts_dict: dict[int, ParsedPart] = {}

    parts_dict = _process_elements(parts_dict, deck, ELEMENT_TYPE_SOLID)
    parts_dict = _process_elements(parts_dict, deck, ELEMENT_TYPE_SHELL)

    # PARTキーワードからパート名があれば更新
    parts_dict = _update_part_names(parts_dict, deck)

    has_shared_nodes = _check_shared_nodes(deck)

    # part_idでソートしてリストに変換
    parts = sorted(parts_dict.values(), key=lambda p: p.part_id)
    return parts, has_shared_nodes


def _load_k_file(file_path: str) -> Deck:
    """kファイルを読み込む（複数エンコーディングを試行）"""
    deck = Deck()

    for encoding in SUPPORTED_ENCODINGS:
        try:
            deck.import_file(file_path, encoding=encoding)
            return deck
        except UnicodeDecodeError:
            continue

    raise RuntimeError(
        f"全てのエンコーディングで読み込みに失敗: {file_path}",
    )


def _process_elements(
    existing_parts: dict[int, ParsedPart], deck: Deck, element_type: str
) -> dict[int, ParsedPart]:
    """
    指定タイプの要素を処理してパート辞書を返す

    Args:
        existing_parts: 既存のパート辞書
        deck: 解析対象のDeck
        element_type: 処理する要素タイプ（SOLID または SHELL）

    Returns:
        更新されたパート辞書（新しい辞書）
    """
    # 元のデータをコピー
    parts = existing_parts.copy()

    element_kwds = deck.get_kwds_by_full_type("ELEMENT", element_type)

    for kwd in element_kwds:
        elem_df = kwd.elements
        if elem_df is None or elem_df.empty:
            continue

        # パートIDごとにグループ化して処理
        for pid_raw, group in elem_df.groupby("pid"):
            try:
                pid = int(pid_raw)
            except (ValueError, TypeError):
                continue

            element_count = len(group)

            # 既存のパートを更新または新規作成
            if pid in parts:
                existing = parts[pid]
                parts[pid] = existing.with_added_elements(element_count, element_type)
            else:
                parts[pid] = ParsedPart(
                    part_id=pid,
                    part_name=f"Part {pid}",
                    element_count=element_count,
                    element_type=element_type,
                )

    return parts


def _update_part_names(
    existing_parts: dict[int, ParsedPart], deck: Deck
) -> dict[int, ParsedPart]:
    """
    *PARTキーワードからパート名を取得して更新する

    Args:
        existing_parts: 既存のパート辞書
        deck: 解析対象のDeck

    Returns:
        パート名が更新されたパート辞書（新しい辞書）
    """
    # *PARTキーワードを取得
    part_kwds = deck.get_kwds_by_full_type("PART", "")
    if not part_kwds:
        return existing_parts

    # 元のデータをコピー
    parts = existing_parts.copy()

    for kwd in part_kwds:
        # partsテーブル（DataFrame）を取得
        parts_df = kwd.parts
        if parts_df is None or parts_df.empty:
            continue

        # 各パート行を処理
        for _, row in parts_df.iterrows():
            try:
                pid = int(row["pid"])
                part_name = row.get("heading", "")

                # パート名が存在し、該当するパートIDが辞書にある場合は更新
                if part_name and pid in parts:
                    existing = parts[pid]
                    parts[pid] = ParsedPart(
                        part_id=existing.part_id,
                        part_name=part_name.strip(),
                        element_count=existing.element_count,
                        element_type=existing.element_type,
                    )
            except (ValueError, TypeError, KeyError):
                # パートIDの変換や列アクセスに失敗した場合はスキップ
                continue
    return parts


def _check_shared_nodes(deck: Deck) -> bool:
    """
    複数パート間で節点が共有されているかチェック

    Note:
        現在は未実装で常に False を返す
    """
    # TODO: 節点共有のチェックロジックを実装
    return False
