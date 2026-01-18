"""
エクスポートUIコンポーネント

エクスポートセクションのUIを提供します。
"""

from pathlib import Path

from nicegui import ui

from services.export_service import ExportService
from state import AnalysisConfig


def render_export_section(state: AnalysisConfig) -> None:
    """
    エクスポートセクションを描画

    Args:
        state: アプリケーション状態
    """

    def handle_export() -> None:
        """エクスポートボタンのハンドラ"""
        try:
            # プロジェクトディレクトリをベースにする（本来は設定ファイルなどで管理）
            base_output_dir = Path("output")

            # Service層を通じてエクスポート実行
            output_path = ExportService.export_analysis_deck(state, base_output_dir)

            ui.notify(f"エクスポート完了: {output_path}", type="positive")

        except Exception as e:
            ui.notify(f"エクスポートエラー: {str(e)}", type="negative")

    with ui.card().classes("w-full"):
        ui.label("5. エクスポート").classes("text-lg font-bold mb-4")

        with ui.row().classes("w-full gap-4 items-end"):
            # ファイル名
            ui.input(
                label="出力ファイル名",
                value=state.output_filename or state.project_name,
                placeholder=state.project_name,
                on_change=lambda e: setattr(state, "output_filename", e.value),
            ).classes("w-64")

            # エクスポートボタン
            ui.button(
                "エクスポート",
                icon="download",
                on_click=handle_export,
            ).props("color=primary")

        # エクスポート情報
        ui.separator().classes("my-4")

        with ui.expansion("エクスポート詳細", icon="info").classes("w-full"):
            render_export_details(state)


def render_export_details(state: AnalysisConfig) -> None:
    """エクスポート詳細情報を描画"""
    with ui.column().classes("gap-2 text-sm text-gray-600"):
        ui.label(f"プロジェクト名: {state.project_name}")
        ui.label(f"工程数: {state.step_count}")
        ui.label(f"アップロード済みメッシュ: {len(state.uploaded_meshes)}個")

        if state.symmetry_planes:
            planes = ", ".join(
                f"{p.plane.display_name}={p.coordinate}mm"
                for p in state.symmetry_planes
            )
            ui.label(f"対称面: {planes}")

        if state.constraints:
            ui.label(f"拘束条件: {len(state.constraints)}個")

        ui.label(
            f"摩擦係数: 静={state.friction.static_friction:.2f}, "
            f"動={state.friction.dynamic_friction:.2f}"
        )
