"""
ワークカードコンポーネント

ワーク（被加工材）の設定カードを描画します。
"""

from collections.abc import Callable

from nicegui import ui

from core.config import (
    MATERIAL_PRESETS,
    MeshInfo,
    WorkpieceConfig,
)


def render_workpiece_card(
    workpiece: WorkpieceConfig,
    uploaded_meshes: list[MeshInfo],
    on_delete: Callable[[], None],
    can_delete: bool = True,
) -> None:
    """
    ワークカードを描画
    
    Args:
        workpiece: ワーク設定
        uploaded_meshes: アップロード済みメッシュリスト
        on_delete: 削除時のコールバック
        can_delete: 削除可能かどうか
    """
    with ui.card().classes('w-full bg-gray-50 p-3'):
        # ヘッダー行
        with ui.row().classes('w-full items-center justify-between mb-2'):
            ui.input(
                label='ワーク名',
                value=workpiece.name,
                on_change=lambda e: setattr(workpiece, 'name', e.value),
            ).classes('w-40').props('dense')
            
            # 削除ボタン
            delete_btn = ui.button(
                icon='delete',
                on_click=lambda: on_delete() if can_delete else ui.notify('最低1つのワークが必要です', type='warning'),
            ).props('flat dense color=negative').tooltip('削除')
            
            if not can_delete:
                delete_btn.props('disable')
        
        # 設定行
        with ui.row().classes('w-full gap-4 flex-wrap items-end'):
            # メッシュ選択
            mesh_options = {'': '-- メッシュを選択 --'}
            mesh_options.update({m.id: f'{m.file_name} - {m.part_name}' for m in uploaded_meshes})
            
            mesh_select = ui.select(
                label='メッシュ',
                options=mesh_options,
                value=workpiece.mesh_id if workpiece.mesh_id else '',
                on_change=lambda e: setattr(workpiece, 'mesh_id', e.value if e.value else None),
            ).classes('w-56').props('dense')
            
            # 選択中のメッシュ詳細表示（折り畳み）
            if workpiece.mesh_id:
                selected_mesh = next((m for m in uploaded_meshes if m.id == workpiece.mesh_id), None)
                if selected_mesh:
                    with ui.expansion(
                        f'メッシュ詳細: {selected_mesh.part_name}',
                        icon='info',
                    ).classes('w-full mt-2').props('dense'):
                        with ui.row().classes('gap-4 text-sm text-gray-600'):
                            ui.label(f'ファイル: {selected_mesh.file_name}')
                            ui.label(f'Part ID: {selected_mesh.part_id}')
                            ui.label(f'要素数: {selected_mesh.element_count:,}')
                            ui.label(f'節点数: {selected_mesh.node_count:,}')
                            ui.label(f'タイプ: {selected_mesh.element_type}')
                            if selected_mesh.has_shared_nodes:
                                with ui.row().classes('items-center gap-1'):
                                    ui.icon('warning', color='orange').classes('text-sm')
                                    ui.label('節点共有あり').classes('text-orange-600')
            
            # 材質選択
            material_options = {k: v['name'] for k, v in MATERIAL_PRESETS.items()}
            material_options['custom'] = 'カスタム'
            ui.select(
                label='材質',
                options=material_options,
                value=workpiece.material_preset,
                on_change=lambda e: setattr(workpiece, 'material_preset', e.value),
            ).classes('w-48').props('dense')
            
            # 板厚
            ui.number(
                label='板厚 [mm]',
                value=workpiece.thickness,
                min=0.01,
                max=100.0,
                step=0.1,
                format='%.2f',
                on_change=lambda e: setattr(workpiece, 'thickness', e.value),
            ).classes('w-28').props('dense')

