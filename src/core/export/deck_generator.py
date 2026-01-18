"""LS-DYNAデッキファイル生成機能"""

import os
from datetime import datetime
from typing import Any

from ansys.dyna.core import Deck
from ansys.dyna.core import keywords as kwd

from core.contacts.generator import ContactGenerator
from core.materials.generator import MaterialGenerator
from core.materials.sscurve_loader import SSCurveLoader

# 循環参照を防ぐため、TYPE_CHECKINGを使用するか、この時点ではAnalysisConfigをインポートしない
# 実行時に渡されるオブジェクトがAnalysisConfigであることを想定
from state import AnalysisConfig


class DeckGenerator:
    """解析デック生成クラス"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self._cid_counter = 1
        self._mid_counter = 1
        self._lcid_counter = 1  # Load Curve ID用カウンタ（必要に応じて）

    def generate(self, config: AnalysisConfig) -> str:
        """
        設定(AnalysisConfig)から.kファイルを生成して保存する

        Args:
            config: 解析設定

        Returns:
            生成されたメインファイルのパス
        """
        # Configからキーワードグループへの変換
        # TODO: 各Generatorを使用して適切なキーワードを生成する
        # 現時点では、アーキテクチャ疎通のために最小限のダミー/デフォルトキーワードを設定

        keyword_groups: dict[str, list[Any]] = {
            "control_keywords": [],
            "section_keywords": [],
            "material_keywords": [],  # 材料定義（カーブ+材料を含む）
            "part_keywords": [],
            "boundary_keywords": [],
            "contact_keywords": [],
            "database_keywords": [],
            # スプリングバック用（空リスト）
            "sb_control_keywords": [],
            "sb_part_keywords": [],
            "sb_mesh_keywords": [],
            "sb_boundary_keywords": [],
            "sb_database_keywords": [],
        }

        # CONTROLキーワードの生成（例）
        term = kwd.ControlTermination(endtim=100.0)
        keyword_groups["control_keywords"].append(term)

        # 材料定義の生成（カーブ+材料）
        self._generate_materials(config, keyword_groups["material_keywords"])

        # 接触条件の生成
        self._generate_contacts(config, keyword_groups["contact_keywords"])

        # ファイル生成の実行
        # 既存の関数ロジックを再利用
        results = create_comprehensive_deck_files(
            keyword_groups=keyword_groups,
            project_name=config.output_filename or config.project_name,
            add_timestamp=True,  # タイムスタンプを付けて上書き防止
            base_dir=self.output_dir,
            create_springback=False,  # 今回はメイン解析のみ
        )

        return results["press_analysis"]["main_file"]

    def _generate_contacts(
        self, config: AnalysisConfig, contact_keywords: list[Any]
    ) -> None:
        """接触定義の生成"""
        # プロジェクト全体で一括の接触定義を行う（仮: 全パーツ対象）
        # 将来的にはPart IDの管理クラスから適切なIDを取得して設定する

        # 例: Part ID 0 はLS-DYNAでは通常「すべて」を意味しないが、
        # ContactAutomaticSurfaceToSurfaceのデフォルト挙動や
        # ユーザー定義のSet IDなどを使用する。
        # ここではアーキテクチャ検証のため、ダミーIDを使用。
        master_id = 1
        slave_id = 2

        contact = ContactGenerator.generate(
            cid=self._cid_counter,
            heading="Master Contact",
            part_a_id=master_id,
            part_b_id=slave_id,
            config=config.friction,
        )
        contact_keywords.append(contact)
        self._cid_counter += 1

    def _generate_materials(
        self, config: AnalysisConfig, material_keywords: list[Any]
    ) -> None:
        """材料定義の生成（応力-ひずみカーブ + 材料特性）"""
        # 全工程のWorkpieceから使用されている材料を収集
        # 重複を排除して一度だけ定義する
        material_map: dict[
            str, tuple[str, Any]
        ] = {}  # key: preset_key, value: (preset_key, custom_material)
        lcss_set: set[int] = set()

        for step in config.steps:
            for workpiece in step.workpieces:
                preset_key = workpiece.material_preset
                if preset_key not in material_map:
                    material_map[preset_key] = (preset_key, workpiece.custom_material)

                # 材料設定を取得してlcssを抽出
                material = workpiece.get_material()
                lcss_set.add(material.lcss)

        # 1. 応力-ひずみカーブの生成（材料より先に定義する必要がある）
        for lcss in sorted(lcss_set):  # IDの小さい順に生成
            try:
                curve_keyword = SSCurveLoader.generate_from_lcss(lcss)
                material_keywords.append(curve_keyword)
            except (ValueError, FileNotFoundError) as e:
                # カーブファイルが見つからない場合の警告
                # 実運用ではログに記録するか、ユーザーに通知
                print(f"Warning: Failed to generate curve for lcss={lcss}: {e}")

        # 2. 材料特性の生成
        for key, custom_mat in material_map.values():
            mat_keyword = MaterialGenerator.generate(
                mid=self._mid_counter,
                preset_key=key,
                custom_material=custom_mat,
            )
            material_keywords.append(mat_keyword)
            self._mid_counter += 1


def reset_keywords(all_keywords: list[Any]) -> None:
    """キーワードのdeck参照をリセット

    Args:
        all_keywords: リセット対象のキーワードリスト
    """
    for keyword in all_keywords:
        if hasattr(keyword, "deck"):
            keyword.deck = None

    print("Keywords reset completed.")


def create_comprehensive_deck_files(
    keyword_groups: dict[str, list[Any]],
    project_name: str = "comprehensive_analysis",
    add_timestamp: bool = False,
    base_dir: str = "./projects",
    reset_before_create: bool = True,
    create_springback: bool = True,
) -> dict[str, Any]:
    """メイン解析とスプリングバック解析の両方を生成

    Args:
        keyword_groups: キーワードグループの辞書
        project_name: プロジェクト名
        add_timestamp: タイムスタンプを追加するかどうか
        base_dir: ベースディレクトリ
        reset_before_create: 作成前にキーワードをリセットするかどうか
        create_springback: スプリングバック解析も作成するかどうか

    Returns:
        プロジェクト情報の辞書
    """

    if reset_before_create:
        all_keywords = []
        for group in keyword_groups.values():
            all_keywords.extend(group)
        reset_keywords(all_keywords)

    # タイムスタンプ生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if add_timestamp else ""

    # ベースプロジェクトフォルダを作成
    if add_timestamp:
        base_project_dir = os.path.join(base_dir, f"{project_name}_{timestamp}")
    else:
        base_project_dir = os.path.join(base_dir, project_name)

    os.makedirs(base_project_dir, exist_ok=True)
    print(f"Created base project directory: {base_project_dir}")

    results = {}

    # 1. メイン成形解析プロジェクト作成
    press_project_dir = os.path.join(base_project_dir, "press_analysis")
    press_results = create_press_analysis_project(press_project_dir, keyword_groups)
    results["press_analysis"] = press_results

    # 2. スプリングバック解析プロジェクト作成
    if create_springback:
        sb_project_dir = os.path.join(base_project_dir, "springback_analysis")
        sb_results = create_springback_analysis_project(sb_project_dir, keyword_groups)
        results["springback_analysis"] = sb_results

    print(
        f"\n=== {project_name.replace('_', ' ').title()} 包括プロジェクト作成完了 ==="
    )
    print(f"ベースディレクトリ: {base_project_dir}")
    print(f"メイン解析: {press_results['project_dir']}")
    if create_springback:
        print(f"スプリングバック解析: {sb_results['project_dir']}")

    return results


def create_press_analysis_project(
    project_dir: str, keyword_groups: dict[str, list[Any]]
) -> dict[str, Any]:
    """成形解析プロジェクトを作成

    Args:
        project_dir: プロジェクトディレクトリ
        keyword_groups: キーワードグループの辞書

    Returns:
        プロジェクト情報の辞書
    """
    os.makedirs(project_dir, exist_ok=True)

    # サブディレクトリ作成
    subdirs = ["includes", "results", "mesh"]
    for subdir in subdirs:
        os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)

    # Deck設定情報
    decks_info = [
        {
            "number": "01",
            "name": "controls",
            "title": "Control Parameters",
            "keywords": keyword_groups.get("control_keywords", []),
            "description": "Basic control settings (accuracy, time step, termination, etc.)",
        },
        {
            "number": "02",
            "name": "sections",
            "title": "Section Definitions",
            "keywords": keyword_groups.get("section_keywords", []),
            "description": "Element section definitions (shell, solid, etc.)",
        },
        {
            "number": "03",
            "name": "materials",
            "title": "Material Definitions",
            "keywords": keyword_groups.get("material_keywords", []),
            "description": "Material curves (stress-strain) and material properties",
        },
        {
            "number": "04",
            "name": "parts",
            "title": "Part Definitions",
            "keywords": keyword_groups.get("part_keywords", []),
            "description": "Part definitions and sets",
        },
        {
            "number": "05",
            "name": "boundaries",
            "title": "Boundary Conditions",
            "keywords": keyword_groups.get("boundary_keywords", []),
            "description": "Loads, constraints, and prescribed motions",
        },
        {
            "number": "06",
            "name": "contacts",
            "title": "Contact Definitions",
            "keywords": keyword_groups.get("contact_keywords", []),
            "description": "Contact interfaces and friction",
        },
        {
            "number": "07",
            "name": "outputs",
            "title": "Output Settings",
            "keywords": keyword_groups.get("database_keywords", []),
            "description": "Database output definitions",
        },
    ]

    return create_deck_project(
        project_dir, decks_info, "Press Analysis - Main Input Deck"
    )


def create_springback_analysis_project(
    project_dir: str, keyword_groups: dict[str, list[Any]]
) -> dict[str, Any]:
    """スプリングバック解析プロジェクトを作成

    Args:
        project_dir: プロジェクトディレクトリ
        keyword_groups: キーワードグループの辞書

    Returns:
        プロジェクト情報の辞書
    """
    os.makedirs(project_dir, exist_ok=True)

    # サブディレクトリ作成
    subdirs = ["includes", "results", "mesh"]
    for subdir in subdirs:
        os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)

    # スプリングバック解析用Deck設定情報
    decks_info = [
        {
            "number": "01",
            "name": "controls",
            "title": "Implicit Control Parameters",
            "keywords": keyword_groups.get("sb_control_keywords", []),
            "description": "Implicit solver control settings",
        },
        {
            "number": "02",
            "name": "sections",
            "title": "Section Definitions",
            "keywords": [
                kwd.Include(filename="../press_analysis/includes/02_sections.k")
            ],
            "description": "Include section definitions from press analysis",
        },
        {
            "number": "03",
            "name": "materials",
            "title": "Material Definitions",
            "keywords": [
                kwd.Include(filename="../press_analysis/includes/03_materials.k")
            ],
            "description": "Include material definitions from press analysis",
        },
        {
            "number": "04",
            "name": "parts",
            "title": "Part Definitions",
            "keywords": keyword_groups.get("sb_part_keywords", []),
            "description": "Work piece definition for springback",
        },
        {
            "number": "05",
            "name": "boundaries",
            "title": "Boundary Conditions",
            "keywords": keyword_groups.get("sb_boundary_keywords", []),
            "description": "Springback boundary conditions",
        },
        {
            "number": "06",
            "name": "outputs",
            "title": "Output Settings",
            "keywords": keyword_groups.get("sb_database_keywords", []),
            "description": "Database output and dynain input",
        },
    ]

    return create_deck_project(
        project_dir, decks_info, "Springback Analysis - Main Input Deck"
    )


def create_deck_project(
    project_dir: str, decks_info: list[dict[str, Any]], main_title: str
) -> dict[str, Any]:
    """共通のDeckプロジェクト作成関数

    Args:
        project_dir: プロジェクトディレクトリ
        decks_info: Deck情報のリスト
        main_title: メインDeckのタイトル

    Returns:
        プロジェクト情報の辞書
    """
    include_dir = os.path.join(project_dir, "includes")

    # Deckファイル作成
    deck_files = {}
    include_files = []

    for deck_info in decks_info:
        filename = f"{deck_info['number']}_{deck_info['name']}.k"
        deck = Deck(title=deck_info["title"])
        deck.extend(deck_info["keywords"])

        deck_files[filename] = (deck, include_dir)
        include_files.append(f"includes/{filename}")

    # メインDeck作成
    main_deck = Deck(title=main_title)

    for filename in include_files:
        main_deck.append(kwd.Include(filename=filename))

    # メインファイルを追加
    deck_files["main.dyn"] = (main_deck, project_dir)

    # ファイル出力
    created_files = []
    for filename, (deck, target_dir) in deck_files.items():
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "w") as f:
            f.write(deck.write())
        created_files.append(filepath)
        print(f"Created: {filepath}")

    return {
        "project_dir": project_dir,
        "main_file": os.path.join(project_dir, "main.dyn"),
        "include_files": [os.path.join(project_dir, f) for f in include_files],
        "all_files": created_files,
        "file_order": [
            (f"{info['number']}_{info['name']}.k", info["description"])
            for info in decks_info
        ],
    }
