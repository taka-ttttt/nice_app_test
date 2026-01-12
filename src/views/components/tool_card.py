"""
工具カードコンポーネント

工具の設定カードを描画します。
"""

from collections.abc import Callable

from nicegui import ui

from core.config import (
    MeshInfo,
    MotionDirection,
    MotionType,
    ToolConfig,
)


def render_tool_card(
    tool: ToolConfig,
    uploaded_meshes: list[MeshInfo],
    on_delete: Callable[[], None],
    can_delete: bool = True,
) -> None:
    """
    工具カードを描画

    Args:
        tool: 工具設定
        uploaded_meshes: アップロード済みメッシュリスト
        on_delete: 削除時のコールバック
        can_delete: 削除可能かどうか
    """
    # 動的UI更新用のコンテナ
    motion_detail_container = None

    def refresh_motion_details():
        """動作詳細を更新"""
        if motion_detail_container is None:
            return
        motion_detail_container.clear()
        with motion_detail_container:
            render_motion_details()

    def render_motion_details():
        """動作タイプに応じた詳細フィールドを描画"""
        if tool.motion_type == MotionType.FIXED:
            ui.label("固定（動作なし）").classes("text-gray-500 italic text-sm")
            return

        # 動作方向
        direction_options = {d: d.display_name for d in MotionDirection}
        ui.select(
            label="方向",
            options=direction_options,
            value=tool.direction or MotionDirection.NEGATIVE_Z,
            on_change=lambda e: setattr(tool, "direction", e.value),
        ).classes("w-24").props("dense")

        # 値（変位または荷重）
        if tool.motion_type == MotionType.DISPLACEMENT:
            ui.number(
                label="変位 [mm]",
                value=tool.value or 50.0,
                step=1.0,
                format="%.1f",
                on_change=lambda e: setattr(tool, "value", e.value),
            ).classes("w-28").props("dense")
        elif tool.motion_type == MotionType.LOAD:
            ui.number(
                label="荷重 [N]",
                value=tool.value or 1000.0,
                step=100.0,
                format="%.1f",
                on_change=lambda e: setattr(tool, "value", e.value),
            ).classes("w-28").props("dense")

        # 動作時間
        ui.number(
            label="時間 [ms]",
            value=tool.motion_time,
            min=0.001,
            step=0.1,
            format="%.3f",
            on_change=lambda e: setattr(tool, "motion_time", e.value),
        ).classes("w-28").props("dense")

    with ui.card().classes("w-full bg-gray-50 p-3"):
        # ヘッダー行
        with ui.row().classes("w-full items-center justify-between mb-2"):
            ui.input(
                label="工具名",
                value=tool.name,
                on_change=lambda e: setattr(tool, "name", e.value),
            ).classes("w-40").props("dense")

            # 削除ボタン
            delete_btn = (
                ui.button(
                    icon="delete",
                    on_click=lambda: on_delete()
                    if can_delete
                    else ui.notify("最低1つの工具が必要です", type="warning"),
                )
                .props("flat dense color=negative")
                .tooltip("削除")
            )

            if not can_delete:
                delete_btn.props("disable")

        # 基本設定行
        with ui.row().classes("w-full gap-4 flex-wrap items-end"):
            # メッシュ選択
            mesh_options = {"": "-- メッシュを選択 --"}
            mesh_options.update(
                {m.id: f"{m.file_name} - {m.part_name}" for m in uploaded_meshes}
            )

            ui.select(
                label="メッシュ",
                options=mesh_options,
                value=tool.mesh_id if tool.mesh_id else "",
                on_change=lambda e: setattr(
                    tool, "mesh_id", e.value if e.value else None
                ),
            ).classes("w-56").props("dense")

            # 選択中のメッシュ詳細表示（折り畳み）
            if tool.mesh_id:
                selected_mesh = next(
                    (m for m in uploaded_meshes if m.id == tool.mesh_id), None
                )
                if selected_mesh:
                    with (
                        ui.expansion(
                            f"メッシュ詳細: {selected_mesh.part_name}",
                            icon="info",
                        )
                        .classes("w-full mt-2")
                        .props("dense")
                    ):
                        with ui.row().classes("gap-4 text-sm text-gray-600"):
                            ui.label(f"ファイル: {selected_mesh.file_name}")
                            ui.label(f"Part ID: {selected_mesh.part_id}")
                            ui.label(f"要素数: {selected_mesh.element_count:,}")
                            ui.label(f"節点数: {selected_mesh.node_count:,}")
                            ui.label(f"タイプ: {selected_mesh.element_type}")
                            if selected_mesh.has_shared_nodes:
                                with ui.row().classes("items-center gap-1"):
                                    ui.icon("warning", color="orange").classes(
                                        "text-sm"
                                    )
                                    ui.label("節点共有あり").classes("text-orange-600")

            # 動作タイプ
            motion_options = {mt: mt.display_name for mt in MotionType}
            ui.select(
                label="動作タイプ",
                options=motion_options,
                value=tool.motion_type,
                on_change=lambda e: (
                    setattr(tool, "motion_type", e.value),
                    refresh_motion_details(),
                ),
            ).classes("w-28").props("dense")

        # 動作詳細行
        motion_detail_container = ui.row().classes(
            "w-full gap-4 flex-wrap items-end mt-2"
        )
        with motion_detail_container:
            render_motion_details()
