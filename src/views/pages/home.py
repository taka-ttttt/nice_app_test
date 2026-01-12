"""
メインページ - プレス成形解析条件設定

仕様書に基づくUIレイアウト:
1. 解析概要
2. メッシュ管理
3. 工程・パート設定（サイドバー方式）
4. 全体設定
5. エクスポート
"""


from nicegui import events, ui

from core.config import (
    AnalysisConfig,
    AnalysisPurpose,
    MeshInfo,
    ProcessType,
)
from core.kfile_parser import parse_kfile_from_bytes
from views.components import (
    render_export_section,
    render_global_settings,
    render_step_manager,
)


# =============================================================================
# アプリケーション状態
# =============================================================================

# グローバル状態（シングルトン）
app_state: AnalysisConfig | None = None


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
    render_step_manager(state)


def render_global_settings_section() -> None:
    """4. 全体設定セクションを描画"""
    state = get_state()
    render_global_settings(state)


def render_export() -> None:
    """5. エクスポートセクションを描画"""
    state = get_state()
    render_export_section(state)


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
        render_global_settings_section()
        render_export()
