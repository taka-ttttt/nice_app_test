"""
メインページ - プレス成形解析条件設定

仕様書に基づくUIレイアウト:
1. 解析概要
2. メッシュ管理
3. 工程・パート設定（サイドバー方式）
4. 全体設定
5. エクスポート
"""

from nicegui import ui, events
from typing import Optional, Dict

from core.config import (
    AnalysisConfig,
    ProcessType,
    AnalysisPurpose,
    FrictionMode,
    MeshInfo,
    MATERIAL_PRESETS,
)
from core.kfile_parser import parse_kfile_from_bytes


# =============================================================================
# アプリケーション状態
# =============================================================================

# グローバル状態（シングルトン）
app_state: Optional[AnalysisConfig] = None


def get_state() -> AnalysisConfig:
    """アプリケーション状態を取得（なければ作成）"""
    global app_state
    if app_state is None:
        app_state = AnalysisConfig()
    return app_state


# =============================================================================
# セクションコンポーネント
# =============================================================================

def render_header() -> None:
    """ヘッダーを描画"""
    with ui.header().classes('bg-blue-800 text-white'):
        ui.label('プレス成形解析条件設定').classes('text-xl font-bold')


def render_analysis_overview() -> None:
    """1. 解析概要セクションを描画"""
    state = get_state()
    
    with ui.card().classes('w-full'):
        ui.label('1. 解析概要').classes('text-lg font-bold mb-4')
        
        with ui.row().classes('w-full gap-4 flex-wrap'):
            # プロジェクト名
            ui.input(
                label='プロジェクト名',
                value=state.project_name,
                on_change=lambda e: setattr(state, 'project_name', e.value),
            ).classes('w-64')
            
            # 加工分類
            process_options = {pt: pt.display_name for pt in ProcessType}
            ui.select(
                label='加工分類',
                options=process_options,
                value=state.process_type,
                on_change=lambda e: setattr(state, 'process_type', e.value),
            ).classes('w-48')
            
            # 解析目的
            purpose_options = {ap: ap.display_name for ap in AnalysisPurpose}
            ui.select(
                label='解析目的',
                options=purpose_options,
                value=state.analysis_purpose,
                on_change=lambda e: setattr(state, 'analysis_purpose', e.value),
            ).classes('w-48')


def render_mesh_management() -> None:
    """2. メッシュ管理セクションを描画"""
    state = get_state()
    
    # メッシュリストのコンテナ（動的更新用）
    mesh_list_container = None
    
    def handle_upload(e: events.UploadEventArguments) -> None:
        """ファイルアップロード処理"""
        try:
            # ファイル内容を読み取り
            content = e.content.read()
            file_name = e.name
            
            # kファイルを解析
            parts, has_shared = parse_kfile_from_bytes(content, file_name)
            
            if not parts:
                ui.notify(f'{file_name}: パート情報が見つかりませんでした', type='warning')
                return
            
            # パートごとにMeshInfoを作成
            for part in parts:
                mesh = MeshInfo.create(
                    file_name=file_name,
                    file_path="",  # サーバー保存は後で実装
                    part_id=part.part_id,
                    part_name=part.part_name,
                    element_count=part.element_count,
                    node_count=part.node_count,
                    element_type=part.element_type,
                    has_shared_nodes=has_shared,
                )
                state.uploaded_meshes.append(mesh)
            
            ui.notify(f'{file_name}: {len(parts)}個のパートを読み込みました', type='positive')
            
            # メッシュリストを更新
            refresh_mesh_list()
            
        except Exception as ex:
            ui.notify(f'エラー: {str(ex)}', type='negative')
    
    def delete_mesh(mesh_id: str) -> None:
        """メッシュを削除"""
        state.uploaded_meshes = [m for m in state.uploaded_meshes if m.id != mesh_id]
        ui.notify('メッシュを削除しました')
        refresh_mesh_list()
    
    def get_mesh_usage_status(mesh_id: str) -> str:
        """メッシュの使用状況を取得"""
        usages = state.get_mesh_usage(mesh_id)
        if usages:
            return "✓ 使用中"
        return "⚠ 未割当"
    
    def refresh_mesh_list() -> None:
        """メッシュリストを更新"""
        if mesh_list_container is None:
            return
        
        mesh_list_container.clear()
        with mesh_list_container:
            if not state.uploaded_meshes:
                ui.label('メッシュがアップロードされていません').classes('text-gray-400 italic py-4')
            else:
                for mesh in state.uploaded_meshes:
                    render_mesh_item(mesh)
    
    def render_mesh_item(mesh: MeshInfo) -> None:
        """メッシュアイテムを描画"""
        usage_status = get_mesh_usage_status(mesh.id)
        is_used = "使用中" in usage_status
        
        with ui.row().classes('w-full items-center gap-4 py-2 px-3 hover:bg-gray-100 rounded'):
            # ファイルアイコン
            ui.icon('description').classes('text-blue-600')
            
            # ファイル名
            ui.label(mesh.file_name).classes('w-32 truncate')
            
            # パート情報
            ui.label(f'Part {mesh.part_id}: {mesh.part_name}').classes('w-48 truncate text-gray-600')
            
            # 要素数
            ui.label(f'要素: {mesh.element_count:,}').classes('w-24 text-sm text-gray-500')
            
            # 節点共有警告
            if mesh.has_shared_nodes:
                with ui.row().classes('items-center gap-1'):
                    ui.icon('warning', color='orange').classes('text-sm')
                    ui.label('節点共有あり').classes('text-sm text-orange-600')
            
            # 使用状況
            status_class = 'text-green-600' if is_used else 'text-orange-600'
            ui.label(usage_status).classes(f'w-20 text-sm {status_class}')
            
            # スペーサー
            ui.element('div').classes('flex-grow')
            
            # 削除ボタン
            ui.button(
                icon='delete',
                on_click=lambda m=mesh: delete_mesh(m.id),
            ).props('flat dense color=negative').tooltip('削除')
    
    with ui.card().classes('w-full'):
        ui.label('2. メッシュ管理').classes('text-lg font-bold mb-4')
        
        # ファイルアップロード
        ui.upload(
            label='.kファイルをアップロード（ドラッグ&ドロップ可）',
            multiple=True,
            auto_upload=True,
            on_upload=handle_upload,
            on_rejected=lambda e: ui.notify('エラー: .kファイルではありません', type='negative'),
        ).props('accept=.k').classes('w-full')
        
        # メッシュリスト
        ui.separator().classes('my-4')
        
        with ui.card().classes('w-full bg-gray-50 p-4'):
            ui.label('アップロード済みメッシュ').classes('font-medium text-sm text-gray-600 mb-2')
            
            # メッシュリストコンテナ
            mesh_list_container = ui.column().classes('w-full gap-1')
            
            # 初期表示
            with mesh_list_container:
                if not state.uploaded_meshes:
                    ui.label('メッシュがアップロードされていません').classes('text-gray-400 italic py-4')
                else:
                    for mesh in state.uploaded_meshes:
                        render_mesh_item(mesh)


def render_step_parts_setting() -> None:
    """3. 工程・パート設定セクションを描画（サイドバー方式）"""
    state = get_state()
    
    with ui.card().classes('w-full'):
        ui.label('3. 工程・パート設定').classes('text-lg font-bold mb-4')
        
        # サイドバー方式のレイアウト
        with ui.splitter(value=25).classes('w-full h-96') as splitter:
            
            # 左側: 工程一覧（サイドバー）
            with splitter.before:
                with ui.column().classes('w-full h-full p-2 bg-gray-50'):
                    ui.label('工程一覧').classes('font-medium text-sm text-gray-600 mb-2')
                    
                    # 工程リスト
                    step_list_container = ui.column().classes('w-full gap-1')
                    
                    def render_step_list():
                        """工程リストを更新"""
                        step_list_container.clear()
                        with step_list_container:
                            for i, step in enumerate(state.steps):
                                is_selected = i == 0  # 最初の工程を選択状態に
                                btn_class = 'w-full' + (' bg-blue-100' if is_selected else '')
                                ui.button(
                                    f'{step.order}. {step.name}',
                                    on_click=lambda s=step: select_step(s.id),
                                ).props('flat align=left').classes(btn_class)
                    
                    render_step_list()
                    
                    ui.separator().classes('my-2')
                    
                    # 工程追加ボタン
                    ui.button(
                        '工程を追加',
                        icon='add',
                        on_click=lambda: add_step_and_refresh(),
                    ).props('flat dense').classes('w-full')
                    
                    ui.separator().classes('my-2')
                    
                    # 順序変更・複製・削除ボタン
                    with ui.row().classes('w-full gap-1'):
                        ui.button(icon='arrow_upward').props('flat dense').tooltip('上へ移動')
                        ui.button(icon='arrow_downward').props('flat dense').tooltip('下へ移動')
                    with ui.row().classes('w-full gap-1'):
                        ui.button(icon='content_copy').props('flat dense').tooltip('複製')
                        ui.button(icon='delete').props('flat dense color=negative').tooltip('削除')
            
            # 右側: 選択した工程の詳細
            with splitter.after:
                with ui.column().classes('w-full h-full p-4'):
                    # 工程詳細（プレースホルダー）
                    if state.steps:
                        current_step = state.steps[0]
                        ui.label(f'工程: {current_step.name}').classes('text-lg font-medium mb-4')
                        
                        # ワーク設定（プレースホルダー）
                        with ui.expansion('ワーク設定', icon='build').classes('w-full'):
                            ui.label('Step 4で実装予定').classes('text-gray-400 italic')
                        
                        # 工具設定（プレースホルダー）
                        with ui.expansion('工具設定', icon='precision_manufacturing').classes('w-full'):
                            ui.label('Step 4で実装予定').classes('text-gray-400 italic')
                    else:
                        ui.label('工程がありません').classes('text-gray-400 italic')
    
    def select_step(step_id: str):
        """工程を選択"""
        # Step 4で実装
        ui.notify(f'工程を選択: {step_id}')
    
    def add_step_and_refresh():
        """工程を追加してリストを更新"""
        state.add_step()
        ui.notify('工程を追加しました')
        # 実際のリフレッシュはStep 4で実装


def render_global_settings() -> None:
    """4. 全体設定セクションを描画"""
    state = get_state()
    
    with ui.card().classes('w-full'):
        ui.label('4. 全体設定').classes('text-lg font-bold mb-4')
        
        with ui.row().classes('w-full gap-8 flex-wrap'):
            # 摩擦係数
            with ui.column().classes('gap-2'):
                ui.label('摩擦係数').classes('font-medium')
                friction_options = {
                    FrictionMode.OIL: '油あり (静摩擦: 0.10, 動摩擦: 0.05)',
                    FrictionMode.DRY: '油なし (静摩擦: 0.15, 動摩擦: 0.10)',
                    FrictionMode.MANUAL: 'マニュアル入力',
                }
                ui.radio(
                    options=friction_options,
                    value=state.friction.mode,
                    on_change=lambda e: update_friction_mode(e.value),
                )
            
            # 対称面（プレースホルダー）
            with ui.column().classes('gap-2'):
                ui.label('対称面').classes('font-medium')
                ui.checkbox('対称面を使用')
                ui.label('Step 5で詳細実装').classes('text-gray-400 italic text-sm')
            
            # 拘束条件（プレースホルダー）
            with ui.column().classes('gap-2'):
                ui.label('拘束条件').classes('font-medium')
                ui.button('拘束条件を追加', icon='add').props('flat')
                ui.label('Step 5で詳細実装').classes('text-gray-400 italic text-sm')
    
    def update_friction_mode(mode: FrictionMode):
        """摩擦モードを更新"""
        state.friction.mode = mode
        state.friction.apply_preset()


def render_export() -> None:
    """5. エクスポートセクションを描画"""
    state = get_state()
    
    with ui.card().classes('w-full'):
        ui.label('5. エクスポート').classes('text-lg font-bold mb-4')
        
        with ui.row().classes('w-full gap-4 items-end'):
            # ファイル名
            ui.input(
                label='出力ファイル名',
                value=state.output_filename or state.project_name,
                placeholder=state.project_name,
                on_change=lambda e: setattr(state, 'output_filename', e.value),
            ).classes('w-64')
            
            # エクスポートボタン
            ui.button(
                'エクスポート',
                icon='download',
                on_click=lambda: export_config(),
            ).props('color=primary')
    
    def export_config():
        """設定をエクスポート"""
        # Step 5で実装
        ui.notify(f'エクスポート: {state.get_export_filename()}', type='info')


# =============================================================================
# メインレンダリング
# =============================================================================

def render() -> None:
    """メインページを描画"""
    
    # ヘッダー
    render_header()
    
    # メインコンテンツ
    with ui.column().classes('w-full max-w-6xl mx-auto p-4 gap-4'):
        render_analysis_overview()
        render_mesh_management()
        render_step_parts_setting()
        render_global_settings()
        render_export()
