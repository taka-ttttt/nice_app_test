"""
工程管理コンポーネント

工程一覧（サイドバー）と工程詳細パネルを提供します。
"""

from nicegui import ui

from core.config import (
    AnalysisConfig,
    ProcessType,
    StepConfig,
)

from .tool_card import render_tool_card
from .workpiece_card import render_workpiece_card


# 選択中の工程ID（モジュールレベル状態）
_selected_step_id: str | None = None


def get_selected_step_id() -> str | None:
    """選択中の工程IDを取得"""
    return _selected_step_id


def set_selected_step_id(step_id: str | None) -> None:
    """選択中の工程IDを設定"""
    global _selected_step_id
    _selected_step_id = step_id


def render_step_manager(state: AnalysisConfig) -> None:
    """
    工程管理セクションを描画（サイドバー方式）

    Args:
        state: アプリケーション状態
    """
    global _selected_step_id

    # 初期選択状態を設定
    if _selected_step_id is None and state.steps:
        _selected_step_id = state.steps[0].id

    # コンテナ参照
    step_list_container = None
    step_detail_container = None

    def get_selected_step() -> StepConfig | None:
        """選択中の工程を取得"""
        if _selected_step_id:
            return state.get_step_by_id(_selected_step_id)
        return state.steps[0] if state.steps else None

    def select_step(step_id: str) -> None:
        """工程を選択"""
        global _selected_step_id
        _selected_step_id = step_id
        refresh_step_list()
        refresh_step_detail()

    def add_step() -> None:
        """工程を追加"""
        global _selected_step_id
        new_step = state.add_step()
        _selected_step_id = new_step.id
        refresh_step_list()
        refresh_step_detail()
        ui.notify("工程を追加しました")

    def delete_step() -> None:
        """選択中の工程を削除"""
        global _selected_step_id
        if len(state.steps) <= 1:
            ui.notify("最後の工程は削除できません", type="warning")
            return
        if _selected_step_id and state.remove_step(_selected_step_id):
            _selected_step_id = state.steps[0].id if state.steps else None
            refresh_step_list()
            refresh_step_detail()
            ui.notify("工程を削除しました")

    def duplicate_step() -> None:
        """選択中の工程を複製"""
        global _selected_step_id
        if _selected_step_id:
            new_step = state.duplicate_step(_selected_step_id)
            if new_step:
                _selected_step_id = new_step.id
                refresh_step_list()
                refresh_step_detail()
                ui.notify("工程を複製しました")

    def move_step_up() -> None:
        """選択中の工程を上に移動"""
        if _selected_step_id and state.move_step_up(_selected_step_id):
            refresh_step_list()

    def move_step_down() -> None:
        """選択中の工程を下に移動"""
        if _selected_step_id and state.move_step_down(_selected_step_id):
            refresh_step_list()

    def refresh_step_list() -> None:
        """工程リストを更新"""
        if step_list_container is None:
            return
        step_list_container.clear()
        with step_list_container:
            for step in state.steps:
                is_selected = step.id == _selected_step_id
                btn_class = "w-full text-left" + (" bg-blue-100" if is_selected else "")
                ui.button(
                    f"{step.order}. {step.name}",
                    on_click=lambda s=step: select_step(s.id),
                ).props("flat align=left no-caps").classes(btn_class)

    def refresh_step_detail() -> None:
        """工程詳細を更新"""
        if step_detail_container is None:
            return
        step_detail_container.clear()
        with step_detail_container:
            render_step_detail_content()

    def render_step_detail_content() -> None:
        """工程詳細の内容を描画"""
        current_step = get_selected_step()
        if not current_step:
            ui.label("工程がありません").classes("text-gray-400 italic")
            return

        # 工程情報ヘッダー
        with ui.row().classes("w-full items-center gap-4 mb-4"):
            ui.input(
                label="工程名",
                value=current_step.name,
                on_change=lambda e, s=current_step: (
                    setattr(s, "name", e.value),
                    refresh_step_list(),
                ),
            ).classes("w-48")

            step_type_options = {pt: pt.display_name for pt in ProcessType}
            ui.select(
                label="工程タイプ",
                options=step_type_options,
                value=current_step.step_type,
                on_change=lambda e, s=current_step: setattr(s, "step_type", e.value),
            ).classes("w-40")

        # ワーク設定
        with ui.expansion("ワーク設定", icon="build", value=True).classes("w-full"):
            render_workpieces_section(current_step)

        # 工具設定
        with ui.expansion(
            "工具設定", icon="precision_manufacturing", value=True
        ).classes("w-full"):
            render_tools_section(current_step)

    def render_workpieces_section(step: StepConfig) -> None:
        """ワーク設定セクションを描画"""
        workpiece_container = ui.column().classes("w-full gap-2")

        def refresh_workpieces():
            workpiece_container.clear()
            with workpiece_container:
                for wp in step.workpieces:
                    render_workpiece_card(
                        workpiece=wp,
                        uploaded_meshes=state.uploaded_meshes,
                        on_delete=lambda w=wp: (
                            step.remove_workpiece(w.id),
                            refresh_workpieces(),
                        ),
                        can_delete=len(step.workpieces) > 1,
                    )

                # ワーク追加ボタン
                ui.button(
                    "ワークを追加",
                    icon="add",
                    on_click=lambda: (step.add_workpiece(), refresh_workpieces()),
                ).props("flat dense").classes("mt-2")

        with workpiece_container:
            for wp in step.workpieces:
                render_workpiece_card(
                    workpiece=wp,
                    uploaded_meshes=state.uploaded_meshes,
                    on_delete=lambda w=wp: (
                        step.remove_workpiece(w.id),
                        refresh_workpieces(),
                    ),
                    can_delete=len(step.workpieces) > 1,
                )

            ui.button(
                "ワークを追加",
                icon="add",
                on_click=lambda: (step.add_workpiece(), refresh_workpieces()),
            ).props("flat dense").classes("mt-2")

    def render_tools_section(step: StepConfig) -> None:
        """工具設定セクションを描画"""
        tool_container = ui.column().classes("w-full gap-2")

        def refresh_tools():
            tool_container.clear()
            with tool_container:
                for tool in step.tools:
                    render_tool_card(
                        tool=tool,
                        uploaded_meshes=state.uploaded_meshes,
                        on_delete=lambda t=tool: (
                            step.remove_tool(t.id),
                            refresh_tools(),
                        ),
                        can_delete=len(step.tools) > 1,
                    )

                ui.button(
                    "工具を追加",
                    icon="add",
                    on_click=lambda: (step.add_tool(), refresh_tools()),
                ).props("flat dense").classes("mt-2")

        with tool_container:
            for tool in step.tools:
                render_tool_card(
                    tool=tool,
                    uploaded_meshes=state.uploaded_meshes,
                    on_delete=lambda t=tool: (step.remove_tool(t.id), refresh_tools()),
                    can_delete=len(step.tools) > 1,
                )

            ui.button(
                "工具を追加",
                icon="add",
                on_click=lambda: (step.add_tool(), refresh_tools()),
            ).props("flat dense").classes("mt-2")

    # メインレイアウト
    with ui.card().classes("w-full"):
        ui.label("3. 工程・パート設定").classes("text-lg font-bold mb-4")

        # サイドバー方式のレイアウト
        with ui.splitter(value=25).classes("w-full min-h-[500px]") as splitter:
            # 左側: 工程一覧（サイドバー）
            with splitter.before:
                with ui.column().classes("w-full h-full p-2 bg-gray-50"):
                    ui.label("工程一覧").classes(
                        "font-medium text-sm text-gray-600 mb-2"
                    )

                    # 工程リスト
                    step_list_container = ui.column().classes("w-full gap-1")

                    with step_list_container:
                        for step in state.steps:
                            is_selected = step.id == _selected_step_id
                            btn_class = "w-full text-left" + (
                                " bg-blue-100" if is_selected else ""
                            )
                            ui.button(
                                f"{step.order}. {step.name}",
                                on_click=lambda s=step: select_step(s.id),
                            ).props("flat align=left no-caps").classes(btn_class)

                    ui.separator().classes("my-2")

                    # 工程追加ボタン
                    ui.button(
                        "工程を追加",
                        icon="add",
                        on_click=add_step,
                    ).props("flat dense").classes("w-full")

                    ui.separator().classes("my-2")

                    # 順序変更ボタン
                    with ui.row().classes("w-full gap-1"):
                        ui.button(icon="arrow_upward", on_click=move_step_up).props(
                            "flat dense"
                        ).tooltip("上へ移動")
                        ui.button(icon="arrow_downward", on_click=move_step_down).props(
                            "flat dense"
                        ).tooltip("下へ移動")

                    # 複製・削除ボタン
                    with ui.row().classes("w-full gap-1"):
                        ui.button(icon="content_copy", on_click=duplicate_step).props(
                            "flat dense"
                        ).tooltip("複製")
                        ui.button(icon="delete", on_click=delete_step).props(
                            "flat dense color=negative"
                        ).tooltip("削除")

            # 右側: 選択した工程の詳細
            with splitter.after:
                step_detail_container = ui.column().classes("w-full p-4")

                with step_detail_container:
                    render_step_detail_content()
