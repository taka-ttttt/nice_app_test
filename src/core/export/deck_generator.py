"""LS-DYNAデッキファイル生成機能"""
import os
from datetime import datetime
from ansys.dyna.core import Deck, keywords as kwd
from typing import Dict, List, Any


def reset_keywords(all_keywords: List[Any]) -> None:
    """キーワードのdeck参照をリセット
    
    Args:
        all_keywords: リセット対象のキーワードリスト
    """
    for keyword in all_keywords:
        if hasattr(keyword, 'deck'):
            keyword.deck = None
    
    print("Keywords reset completed.")


def create_comprehensive_deck_files(
    keyword_groups: Dict[str, List[Any]], 
    project_name: str = "comprehensive_analysis", 
    add_timestamp: bool = False,
    base_dir: str = "./projects",
    reset_before_create: bool = True,
    create_springback: bool = True
) -> Dict[str, Any]:
    """メイン解析とスプリングバック解析の両方を生成
    
    Args:
        keyword_groups: キーワードグループの辞書
            {
                'section_keywords': [...],
                'material_keywords': [...],
                'part_keywords': [...],
                'boundary_keywords': [...],
                'contact_keywords': [...],
                'control_keywords': [...],
                'database_keywords': [...],
                'sb_control_keywords': [...],
                'sb_part_keywords': [...],
                'sb_mesh_keywords': [...],
                'sb_boundary_keywords': [...],
                'sb_database_keywords': [...]
            }
        project_name: プロジェクト名
        add_timestamp: タイムスタンプを追加するかどうか
        base_dir: ベースディレクトリ
        reset_before_create: 作成前にキーワードをリセットするかどうか
        create_springback: スプリングバック解析も作成するかどうか
    
    Returns:
        プロジェクト情報の辞書
    """
    
    if reset_before_create:
        all_keywords = (
            keyword_groups['section_keywords'] + 
            keyword_groups['material_keywords'] + 
            keyword_groups['part_keywords'] + 
            keyword_groups['boundary_keywords'] + 
            keyword_groups['contact_keywords'] + 
            keyword_groups['control_keywords'] + 
            keyword_groups['database_keywords'] +
            keyword_groups['sb_control_keywords'] +
            keyword_groups['sb_part_keywords'] +
            keyword_groups['sb_mesh_keywords'] +
            keyword_groups['sb_boundary_keywords'] +
            keyword_groups['sb_database_keywords']
        )
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
    results['press_analysis'] = press_results
    
    # 2. スプリングバック解析プロジェクト作成
    if create_springback:
        sb_project_dir = os.path.join(base_project_dir, "springback_analysis")
        sb_results = create_springback_analysis_project(sb_project_dir, keyword_groups)
        results['springback_analysis'] = sb_results
        
    print(f"\n=== {project_name.replace('_', ' ').title()} 包括プロジェクト作成完了 ===")
    print(f"ベースディレクトリ: {base_project_dir}")
    print(f"メイン解析: {press_results['project_dir']}")
    if create_springback:
        print(f"スプリングバック解析: {sb_results['project_dir']}")
    
    return results


def create_press_analysis_project(
    project_dir: str,
    keyword_groups: Dict[str, List[Any]]
) -> Dict[str, Any]:
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
            "keywords": keyword_groups['control_keywords'],
            "description": "Basic control settings (accuracy, time step, termination, etc.)"
        },
        {
            "number": "02", 
            "name": "sections",
            "title": "Section Definitions",
            "keywords": keyword_groups['section_keywords'],
            "description": "Element section definitions (shell, solid, etc.)"
        },
        {
            "number": "03",
            "name": "materials", 
            "title": "Material Definitions",
            "keywords": keyword_groups['material_keywords'],
            "description": "Material models and properties"
        },
        {
            "number": "04",
            "name": "parts",
            "title": "Part Definitions", 
            "keywords": keyword_groups['part_keywords'],
            "description": "Part definitions and sets"
        },
        {
            "number": "05",
            "name": "boundaries",
            "title": "Boundary Conditions",
            "keywords": keyword_groups['boundary_keywords'],
            "description": "Loads, constraints, and prescribed motions"
        },
        {
            "number": "06",
            "name": "contacts",
            "title": "Contact Definitions",
            "keywords": keyword_groups['contact_keywords'],
            "description": "Contact interfaces and friction"
        },
        {
            "number": "07",
            "name": "outputs",
            "title": "Output Settings",
            "keywords": keyword_groups['database_keywords'],
            "description": "Database output definitions"
        }
    ]
    
    return create_deck_project(project_dir, decks_info, "Press Analysis - Main Input Deck")


def create_springback_analysis_project(
    project_dir: str,
    keyword_groups: Dict[str, List[Any]]
) -> Dict[str, Any]:
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
            "keywords": keyword_groups['sb_control_keywords'],
            "description": "Implicit solver control settings"
        },
        {
            "number": "02", 
            "name": "sections",
            "title": "Section Definitions",
            "keywords": [kwd.Include(filename="../press_analysis/includes/02_sections.k")],
            "description": "Include section definitions from press analysis"
        },
        {
            "number": "03",
            "name": "materials", 
            "title": "Material Definitions",
            "keywords": [kwd.Include(filename="../press_analysis/includes/03_materials.k")],
            "description": "Include material definitions from press analysis"
        },
        {
            "number": "04",
            "name": "parts",
            "title": "Part Definitions", 
            "keywords": keyword_groups['sb_part_keywords'],
            "description": "Work piece definition for springback"
        },
        {
            "number": "05",
            "name": "boundaries",
            "title": "Boundary Conditions",
            "keywords": keyword_groups['sb_boundary_keywords'],
            "description": "Springback boundary conditions"
        },
        {
            "number": "06",
            "name": "outputs",
            "title": "Output Settings",
            "keywords": keyword_groups['sb_database_keywords'],
            "description": "Database output and dynain input"
        }
    ]
    
    return create_deck_project(project_dir, decks_info, "Springback Analysis - Main Input Deck")


def create_deck_project(
    project_dir: str,
    decks_info: List[Dict[str, Any]],
    main_title: str
) -> Dict[str, Any]:
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
        deck = Deck(title=deck_info['title'])
        deck.extend(deck_info['keywords'])
        
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
        'project_dir': project_dir,
        'main_file': os.path.join(project_dir, 'main.dyn'),
        'include_files': [os.path.join(project_dir, f) for f in include_files],
        'all_files': created_files,
        'file_order': [(f"{info['number']}_{info['name']}.k", info['description']) for info in decks_info]
    }

