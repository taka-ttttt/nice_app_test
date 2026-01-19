"""LS-DYNAデッキファイル生成機能"""

import os
from datetime import datetime
from typing import Any

from ansys.dyna.core import Deck
from ansys.dyna.core import keywords as kwd

from core.contacts.generator import ContactGenerator
from core.export.id_manager import IDManager
from core.export.mesh_converter import convert_mesh_file
from core.materials.generator import MaterialGenerator
from core.materials.sscurve_loader import SSCurveLoader

# 循環参照を防ぐため、TYPE_CHECKINGを使用するか、この時点ではAnalysisConfigをインポートしない
# 実行時に渡されるオブジェクトがAnalysisConfigであることを想定
from state import AnalysisConfig
from state.parts import MotionType


class DeckGenerator:
    """解析デック生成クラス"""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self._cid_counter = 1
        self._mid_counter = 1
        self._lcid_counter = 1  # Load Curve ID用カウンタ（必要に応じて）
        self.id_manager: IDManager | None = None  # generateメソッドで初期化

    def generate(self, config: AnalysisConfig) -> str:
        """
        設定(AnalysisConfig)から.kファイルを生成して保存する

        Args:
            config: 解析設定

        Returns:
            生成されたメインファイルのパス
        """
        # ID管理の初期化
        self.id_manager = IDManager()

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

        # CONTROLキーワードの生成
        self._generate_controls(config, keyword_groups["control_keywords"])

        # Section定義の生成
        self._generate_sections(config, keyword_groups["section_keywords"])

        # 材料定義の生成（カーブ+材料）
        self._generate_materials(config, keyword_groups["material_keywords"])

        # Part定義の生成
        self._generate_parts(config, keyword_groups["part_keywords"])

        # 境界条件の生成
        self._generate_boundaries(config, keyword_groups["boundary_keywords"])

        # 接触条件の生成
        self._generate_contacts(config, keyword_groups["contact_keywords"])

        # Database設定の生成
        self._generate_database(config, keyword_groups["database_keywords"])

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

    def _generate_controls(
        self, config: AnalysisConfig, control_keywords: list[Any]
    ) -> None:
        """
        Control設定の生成

        Args:
            config: 解析設定
            control_keywords: Control キーワードを追加するリスト
        """
        from core.export.control_templates import get_default_control_keywords

        # デフォルトテンプレートを使用
        # TODO: 終了時間をconfigから取得できるようにする
        controls = get_default_control_keywords(end_time=100.0)
        control_keywords.extend(controls)

    def _generate_database(
        self, config: AnalysisConfig, database_keywords: list[Any]
    ) -> None:
        """
        Database設定の生成

        Args:
            config: 解析設定
            database_keywords: Database キーワードを追加するリスト
        """
        from core.export.database_templates import get_default_database_keywords

        # 工程情報
        total_steps = len(config.steps)

        # 現在は1工程目のみ対応（複数工程は後で拡張）
        db_keywords = get_default_database_keywords(
            step_order=1,
            total_steps=total_steps,
            previous_dynain_path=None,
            end_time=100.0,
        )
        database_keywords.extend(db_keywords)

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

    def _generate_sections(
        self, config: AnalysisConfig, section_keywords: list[Any]
    ) -> None:
        """
        Section定義の生成（3種類の固定Section）

        Args:
            config: 解析設定
            section_keywords: Section キーワードを追加するリスト
        """
        # 1. Shell Section (SECID=1, elform=16)
        shell_section = kwd.SectionShell(
            secid=1, elform=16, title="Shell section (elform=16)"
        )
        section_keywords.append(shell_section)

        # 2. Solid Tet Section (SECID=2, elform=13)
        solid_tet_section = kwd.SectionSolid(
            secid=2, elform=13, title="Solid Tet section (elform=13)"
        )
        section_keywords.append(solid_tet_section)

        # 3. Solid Hex Section (SECID=3, elform=2)
        solid_hex_section = kwd.SectionSolid(
            secid=3, elform=2, title="Solid Hex section (elform=2)"
        )
        section_keywords.append(solid_hex_section)

    def _generate_materials(
        self, config: AnalysisConfig, material_keywords: list[Any]
    ) -> None:
        """材料定義の生成（応力-ひずみカーブ + 材料特性 + 剛体材料）"""
        from core.materials.rigid import make_rigid_material

        # === 1. ワーク材料の収集 ===
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

        # === 2. 応力-ひずみカーブの生成（材料より先に定義する必要がある） ===
        for lcss in sorted(lcss_set):  # IDの小さい順に生成
            try:
                curve_keyword = SSCurveLoader.generate_from_lcss(lcss)
                material_keywords.append(curve_keyword)
            except (ValueError, FileNotFoundError) as e:
                # カーブファイルが見つからない場合の警告
                # 実運用ではログに記録するか、ユーザーに通知
                print(f"Warning: Failed to generate curve for lcss={lcss}: {e}")

        # === 3. ワーク材料特性の生成 ===
        for key, custom_mat in material_map.values():
            mid, is_new = self.id_manager.get_or_create_material_id(key)
            if is_new:
                mat_keyword = MaterialGenerator.generate(
                    mid=mid,
                    preset_key=key,
                    custom_material=custom_mat,
                )
                material_keywords.append(mat_keyword)

        # === 4. 工具用の剛体材料の収集と生成 ===
        rigid_constraints = set()  # 使用される制約条件を収集

        for step in config.steps:
            for tool in step.tools:
                # 動作タイプから制約条件を決定
                if tool.motion_type == MotionType.FIXED:
                    constraint = "fixed"
                elif tool.direction:
                    axis = tool.direction.value[1]  # "+x" -> "x"
                    constraint = f"{axis}-free"
                else:
                    constraint = "fixed"

                rigid_constraints.add(constraint)

        # 収集した制約条件ごとに剛体材料を生成
        for constraint in sorted(rigid_constraints):
            mid, is_new = self.id_manager.get_or_create_rigid_material_id(constraint)
            if is_new:
                rigid_mat = make_rigid_material(mid=mid, constraint=constraint)
                material_keywords.append(rigid_mat)

    def _generate_parts(self, config: AnalysisConfig, part_keywords: list[Any]) -> None:
        """
        Part定義の生成

        Args:
            config: 解析設定
            part_keywords: Part キーワードを追加するリスト
        """

        # メッシュ出力先ディレクトリ
        mesh_dir = os.path.join(self.output_dir, "press_analysis", "mesh")
        os.makedirs(mesh_dir, exist_ok=True)

        # 1. 全工程のワークを処理（PID: 1, 2, 3...）
        for step in config.steps:
            for workpiece in step.workpieces:
                if not workpiece.mesh_id:
                    continue  # メッシュ未設定はスキップ

                # メッシュ情報を取得
                mesh = config.get_mesh_by_id(workpiece.mesh_id)
                if not mesh:
                    continue

                # PIDを割り当て
                pid = self.id_manager.get_next_workpiece_pid()

                # 要素タイプからSECIDを決定
                secid = self.id_manager.get_section_id(mesh.element_type)

                # 材料IDを取得（プリセット共有）
                material_preset = workpiece.material_preset
                mid, is_new = self.id_manager.get_or_create_material_id(material_preset)

                # Part-Material-Section の紐付け
                self.id_manager.register_part_material(pid, mid)
                self.id_manager.register_part_section(pid, secid)

                # メッシュファイル変換（TODO: 将来実装）
                target_mesh_path = os.path.join(mesh_dir, f"workpiece_{pid}.k")
                converted_path = convert_mesh_file(
                    source_path=mesh.file_path,
                    target_path=target_mesh_path,
                    new_pid=pid,
                )

                # *PART キーワード生成
                part = kwd.Part(
                    pid=pid,
                    secid=secid,
                    mid=mid,
                    title=f"{workpiece.name} (Step{step.order})",
                )
                part_keywords.append(part)

                # *INCLUDE でメッシュファイル参照（相対パス）
                # includes ディレクトリからの相対パスを計算
                includes_dir = os.path.join(
                    self.output_dir, "press_analysis", "includes"
                )
                relative_mesh_path = os.path.relpath(converted_path, includes_dir)
                include = kwd.Include(filename=relative_mesh_path)
                part_keywords.append(include)

        # 2. 全工程の工具を処理（PID: 1101, 1102, ... 1201, 1202...）
        for step in config.steps:
            for idx, tool in enumerate(step.tools):
                if not tool.mesh_id:
                    continue

                mesh = config.get_mesh_by_id(tool.mesh_id)
                if not mesh:
                    continue

                # PIDを割り当て
                pid = self.id_manager.get_tool_pid(step.order, idx)

                # 要素タイプからSECIDを決定
                secid = self.id_manager.get_section_id(mesh.element_type)

                # 工具の動作タイプから制約条件を決定
                if tool.motion_type == MotionType.FIXED:
                    constraint = "fixed"
                elif tool.direction:
                    # 動作方向が設定されている場合、その軸を自由に
                    axis = tool.direction.value[1]  # "+x" -> "x"
                    constraint = f"{axis}-free"
                else:
                    constraint = "fixed"

                # 剛体材料ID取得（制約条件ごとに共有）
                # Note: 材料は _generate_materials で既に生成済み
                mid, _ = self.id_manager.get_or_create_rigid_material_id(constraint)

                # Part-Material-Section の紐付け
                self.id_manager.register_part_material(pid, mid)
                self.id_manager.register_part_section(pid, secid)

                # メッシュファイル変換
                target_mesh_path = os.path.join(mesh_dir, f"tool_{pid}.k")
                converted_path = convert_mesh_file(
                    source_path=mesh.file_path,
                    target_path=target_mesh_path,
                    new_pid=pid,
                )

                # *PART キーワード生成
                part = kwd.Part(
                    pid=pid,
                    secid=secid,
                    mid=mid,
                    title=f"{tool.name} (Step{step.order})",
                )
                part_keywords.append(part)

                # *INCLUDE でメッシュファイル参照
                includes_dir = os.path.join(
                    self.output_dir, "press_analysis", "includes"
                )
                relative_mesh_path = os.path.relpath(converted_path, includes_dir)
                include = kwd.Include(filename=relative_mesh_path)
                part_keywords.append(include)

    def _generate_boundaries(
        self, config: AnalysisConfig, boundary_keywords: list[Any]
    ) -> None:
        """
        境界条件の生成

        Args:
            config: 解析設定
            boundary_keywords: Boundary キーワードを追加するリスト
        """
        from core.boundaries.enums import ConditionType, MotionControlType
        from core.boundaries.motion import ToolConditionConfig, ToolConditionManager
        from core.export.boundary_generator import generate_symmetry_constraint

        # 1. 工具の運動条件
        # ToolConditionManager を使用して工具条件を生成
        global_config = {
            "motion_time": 1.0,  # デフォルト動作時間
            "hold_time": 0.1,
        }

        tool_manager = ToolConditionManager(global_config)

        for step in config.steps:
            for idx, tool in enumerate(step.tools):
                # PIDを取得
                pid = self.id_manager.get_tool_pid(step.order, idx)

                # ToolConfig から ToolConditionConfig を作成
                if tool.motion_type == MotionType.DISPLACEMENT:
                    if tool.direction and tool.value is not None:
                        tool_config = ToolConditionConfig(
                            condition_type=ConditionType.FORCED_MOTION,
                            part_id=pid,
                            direction=tool.direction.value,
                            name=tool.name,
                            motion_control_type=MotionControlType.DISPLACEMENT,
                            displacement_amount=tool.value,
                            motion_time=tool.motion_time,
                        )
                        result = tool_manager.create_tool_condition(tool_config)

                        # カーブと条件を追加
                        for curve in result["curves"].values():
                            boundary_keywords.append(curve)
                        for condition in result["conditions"].values():
                            boundary_keywords.append(condition)

                elif tool.motion_type == MotionType.LOAD:
                    if tool.direction and tool.value is not None:
                        tool_config = ToolConditionConfig(
                            condition_type=ConditionType.LOAD_APPLICATION,
                            part_id=pid,
                            direction=tool.direction.value,
                            name=tool.name,
                            load_amount=tool.value,
                        )
                        result = tool_manager.create_tool_condition(tool_config)

                        for curve in result["curves"].values():
                            boundary_keywords.append(curve)
                        for condition in result["conditions"].values():
                            boundary_keywords.append(condition)

                # FIXED の場合は何もしない（剛体材料の制約で固定）

        # 2. 対称面条件
        for sym_plane in config.symmetry_planes:
            constraint = generate_symmetry_constraint(sym_plane)
            boundary_keywords.append(constraint)

        # 3. 拘束条件（現状は空）
        # for constraint in config.constraints:
        #     pass


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
