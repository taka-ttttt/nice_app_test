from nicegui import ui
from typing import Optional

# 材質リスト（既定値）
MATERIAL_OPTIONS = [
    'アルミニウム合金 (A6061-T6)',
    'ステンレス鋼 (SUS304)',
    '炭素鋼 (S45C)',
    '軟鋼 (SPCC)',
    'チタン合金 (Ti-6Al-4V)',
    '銅合金 (C1100)',
]

# 動作タイプ
MOTION_TYPES = {
    'displacement': '変位',
    'load': '荷重',
    'fixed': '固定',
}

# 方向オプション
DIRECTION_OPTIONS = {
    'x': 'X方向',
    'y': 'Y方向',
    'z': 'Z方向',
    'custom': '任意ベクトル',
}


def render() -> None:

    # ファイルアップロード
    with ui.card().classes('w-full'):
        ui.label("ファイルアップロード").classes('text-lg font-bold')
        ui.upload(
            label=".kファイルをアップロード",
            multiple=True,
            auto_upload=True,
            on_upload=lambda e: ui.notify(f'アップロード完了: {e.file.name}', type='positive'),
            on_rejected=lambda e: ui.notify(f'エラー: .kファイルではありません', type='negative')
        ).props('accept=.k')

    # ワーク条件設定
    with ui.card().classes('w-full'):
        ui.label("ワーク設定").classes('text-lg font-bold')
        
        with ui.row():
            # 材質選択
            ui.select(
                label='材質',
                options=MATERIAL_OPTIONS,
                value=MATERIAL_OPTIONS[0],
            ).classes('w-64')
            
            # 板厚入力
            ui.number(
                label='板厚 [mm]',
                value=0.1,
                min=0.01,
                max=10.0,
                step=0.01,
                format='%.2f',
            ).classes('w-32')

    # 工具条件設定
    with ui.card().classes('w-full'):
        ui.label("工具条件設定").classes('text-lg font-bold')
        
        # 工具リストを管理
        tool_counter = {'count': 0}
        tool_cards = []
        
        # 工具リストコンテナ
        tools_container = ui.column().classes('w-full gap-2')
        
        def create_tool_card(tool_id: int):
            """個別の工具設定カードを作成"""
            with ui.card().classes('w-full bg-gray-50 p-3') as tool_card:
                # ヘッダー（工具番号と削除ボタン）
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label(f"工具 {tool_id}").classes('font-bold text-blue-600')
                    
                    def delete_this_card(tc=tool_card):
                        tc.delete()
                    
                    ui.button(
                        icon='delete',
                        on_click=delete_this_card
                    ).props('flat dense color="negative"')
                
                # 動作タイプ選択
                with ui.row().classes('w-full items-center gap-4'):
                    ui.label("動作タイプ:").classes('font-medium text-sm')
                    motion_toggle = ui.toggle(
                        options=MOTION_TYPES,
                        value='displacement',
                    ).props('toggle-color="primary" text-color="black" no-caps dense')
                
                # 動作方向設定
                with ui.row().classes('w-full items-end gap-4'):
                    direction_select = ui.select(
                        label='動作方向',
                        options=DIRECTION_OPTIONS,
                        value='x',
                    ).classes('w-32')
                    
                    # 任意ベクトル入力用コンテナ
                    with ui.row().classes('gap-2') as vector_container:
                        ui.number(label='Vx', value=1.0, step=0.1, format='%.2f').classes('w-20')
                        ui.number(label='Vy', value=0.0, step=0.1, format='%.2f').classes('w-20')
                        ui.number(label='Vz', value=0.0, step=0.1, format='%.2f').classes('w-20')
                    vector_container.set_visibility(False)
                
                # 値入力（変位量/荷重値）
                with ui.row().classes('w-full items-end gap-4'):
                    displacement_input = ui.number(
                        label='変位量 [mm]',
                        value=10.0,
                        step=0.1,
                        format='%.2f',
                    ).classes('w-32')
                    
                    load_input = ui.number(
                        label='荷重値 [N]',
                        value=100.0,
                        step=1.0,
                        format='%.1f',
                    ).classes('w-32')
                    load_input.set_visibility(False)
                
                # イベントハンドラ
                def on_direction_change(e, vc=vector_container):
                    vc.set_visibility(e.value == 'custom')
                
                def on_motion_type_change(e, disp=displacement_input, load=load_input):
                    if e.value == 'displacement':
                        disp.set_visibility(True)
                        load.set_visibility(False)
                    elif e.value == 'load':
                        disp.set_visibility(False)
                        load.set_visibility(True)
                    else:  # fixed
                        disp.set_visibility(False)
                        load.set_visibility(False)
                
                direction_select.on_value_change(on_direction_change)
                motion_toggle.on_value_change(on_motion_type_change)
            
            return tool_card
        
        def add_tool():
            """新しい工具を追加"""
            tool_counter['count'] += 1
            card = create_tool_card(tool_counter['count'])
            card.move(tools_container)
            tool_cards.append(card)
        
        # 初期状態で1つの工具を追加（コンテナ内に直接作成）
        with tools_container:
            tool_counter['count'] += 1
            initial_card = create_tool_card(tool_counter['count'])
            tool_cards.append(initial_card)
        
        # 工具追加ボタン
        ui.button(
            "工具を追加",
            icon='add',
            on_click=add_tool
        ).props('outline').classes('mt-2')


