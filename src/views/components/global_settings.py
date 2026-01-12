"""
全体設定コンポーネント

摩擦係数、対称面、拘束条件の設定UIを提供します。
"""

from nicegui import ui

from core.config import (
    AnalysisConfig,
    ConstraintConfig,
    FrictionMode,
    SymmetryPlane,
    SymmetryPlaneType,
)


def render_global_settings(state: AnalysisConfig) -> None:
    """
    全体設定セクションを描画

    Args:
        state: アプリケーション状態
    """
    with ui.card().classes("w-full"):
        ui.label("4. 全体設定").classes("text-lg font-bold mb-4")

        with ui.row().classes("w-full gap-8 flex-wrap"):
            # 摩擦係数
            render_friction_settings(state)

            # 対称面
            render_symmetry_settings(state)

            # 拘束条件
            render_constraint_settings(state)


def render_friction_settings(state: AnalysisConfig) -> None:
    """摩擦係数設定を描画"""
    # マニュアル入力フィールドのコンテナ
    manual_input_container = None

    def update_friction_mode(mode: FrictionMode) -> None:
        """摩擦モードを更新"""
        state.friction.mode = mode
        state.friction.apply_preset()
        refresh_manual_inputs()

    def refresh_manual_inputs() -> None:
        """マニュアル入力フィールドを更新"""
        if manual_input_container is None:
            return
        manual_input_container.clear()
        with manual_input_container:
            if state.friction.mode == FrictionMode.MANUAL:
                with ui.row().classes("gap-4 items-end"):
                    ui.number(
                        label="静摩擦係数",
                        value=state.friction.static_friction,
                        min=0.0,
                        max=1.0,
                        step=0.01,
                        format="%.2f",
                        on_change=lambda e: setattr(
                            state.friction, "static_friction", e.value
                        ),
                    ).classes("w-28").props("dense")

                    ui.number(
                        label="動摩擦係数",
                        value=state.friction.dynamic_friction,
                        min=0.0,
                        max=1.0,
                        step=0.01,
                        format="%.2f",
                        on_change=lambda e: setattr(
                            state.friction, "dynamic_friction", e.value
                        ),
                    ).classes("w-28").props("dense")

    with ui.column().classes("gap-2"):
        ui.label("摩擦係数").classes("font-medium")

        friction_options = {
            FrictionMode.OIL: "油あり (静摩擦: 0.10, 動摩擦: 0.05)",
            FrictionMode.DRY: "油なし (静摩擦: 0.15, 動摩擦: 0.10)",
            FrictionMode.MANUAL: "マニュアル入力",
        }
        ui.radio(
            options=friction_options,
            value=state.friction.mode,
            on_change=lambda e: update_friction_mode(e.value),
        )

        # マニュアル入力コンテナ
        manual_input_container = ui.column().classes("ml-6")
        with manual_input_container:
            if state.friction.mode == FrictionMode.MANUAL:
                with ui.row().classes("gap-4 items-end"):
                    ui.number(
                        label="静摩擦係数",
                        value=state.friction.static_friction,
                        min=0.0,
                        max=1.0,
                        step=0.01,
                        format="%.2f",
                        on_change=lambda e: setattr(
                            state.friction, "static_friction", e.value
                        ),
                    ).classes("w-28").props("dense")

                    ui.number(
                        label="動摩擦係数",
                        value=state.friction.dynamic_friction,
                        min=0.0,
                        max=1.0,
                        step=0.01,
                        format="%.2f",
                        on_change=lambda e: setattr(
                            state.friction, "dynamic_friction", e.value
                        ),
                    ).classes("w-28").props("dense")


def render_symmetry_settings(state: AnalysisConfig) -> None:
    """対称面設定を描画"""
    symmetry_container = None

    def toggle_symmetry(enabled: bool) -> None:
        """対称面の使用を切り替え"""
        if enabled and not state.symmetry_planes:
            # 1つ目の対称面を追加
            add_symmetry_plane()
        elif not enabled:
            state.symmetry_planes.clear()
        refresh_symmetry_planes()

    def add_symmetry_plane() -> None:
        """対称面を追加"""
        if len(state.symmetry_planes) >= 2:
            ui.notify("対称面は最大2つまでです", type="warning")
            return
        plane = SymmetryPlane(
            plane=SymmetryPlaneType.YZ,
            coordinate=0.0,
        )
        state.symmetry_planes.append(plane)
        refresh_symmetry_planes()

    def remove_symmetry_plane(plane: SymmetryPlane) -> None:
        """対称面を削除"""
        if plane in state.symmetry_planes:
            state.symmetry_planes.remove(plane)
        refresh_symmetry_planes()

    def refresh_symmetry_planes() -> None:
        """対称面リストを更新"""
        if symmetry_container is None:
            return
        symmetry_container.clear()
        with symmetry_container:
            if state.symmetry_planes:
                for i, plane in enumerate(state.symmetry_planes):
                    render_symmetry_plane_item(i + 1, plane)

                # 対称面追加ボタン（最大2つまで）
                if len(state.symmetry_planes) < 2:
                    ui.button(
                        "対称面を追加",
                        icon="add",
                        on_click=add_symmetry_plane,
                    ).props("flat dense").classes("mt-2")

    def render_symmetry_plane_item(index: int, plane: SymmetryPlane) -> None:
        """対称面アイテムを描画"""
        with ui.row().classes("items-center gap-2 py-1"):
            ui.label(f"対称面 {index}:").classes("text-sm")

            # 平面タイプ
            plane_options = {pt: pt.display_name for pt in SymmetryPlaneType}
            ui.select(
                label="平面",
                options=plane_options,
                value=plane.plane,
                on_change=lambda e, p=plane: setattr(p, "plane", e.value),
            ).classes("w-20").props("dense")

            # 座標ラベル
            coord_label = {
                SymmetryPlaneType.XY: "Z =",
                SymmetryPlaneType.YZ: "X =",
                SymmetryPlaneType.ZX: "Y =",
            }.get(plane.plane, "X =")
            ui.label(coord_label).classes("text-sm")

            # 座標値
            ui.number(
                value=plane.coordinate,
                step=0.1,
                format="%.1f",
                on_change=lambda e, p=plane: setattr(p, "coordinate", e.value),
            ).classes("w-20").props("dense")

            ui.label("mm").classes("text-sm text-gray-500")

            # 削除ボタン
            ui.button(
                icon="close",
                on_click=lambda p=plane: remove_symmetry_plane(p),
            ).props("flat dense round size=sm color=negative")

    with ui.column().classes("gap-2"):
        ui.label("対称面").classes("font-medium")

        # 対称面使用チェックボックス
        ui.checkbox(
            "対称面を使用",
            value=len(state.symmetry_planes) > 0,
            on_change=lambda e: toggle_symmetry(e.value),
        )

        # 対称面リストコンテナ
        symmetry_container = ui.column().classes("ml-6 gap-1")
        with symmetry_container:
            if state.symmetry_planes:
                for i, plane in enumerate(state.symmetry_planes):
                    render_symmetry_plane_item(i + 1, plane)

                if len(state.symmetry_planes) < 2:
                    ui.button(
                        "対称面を追加",
                        icon="add",
                        on_click=add_symmetry_plane,
                    ).props("flat dense").classes("mt-2")


def render_constraint_settings(state: AnalysisConfig) -> None:
    """拘束条件設定を描画"""
    constraint_container = None

    def add_constraint() -> None:
        """拘束条件を追加"""
        constraint = ConstraintConfig.create(
            name=f"拘束条件 {len(state.constraints) + 1}"
        )
        state.constraints.append(constraint)
        refresh_constraints()
        ui.notify("拘束条件を追加しました")

    def remove_constraint(constraint: ConstraintConfig) -> None:
        """拘束条件を削除"""
        state.constraints = [c for c in state.constraints if c.id != constraint.id]
        refresh_constraints()

    def refresh_constraints() -> None:
        """拘束条件リストを更新"""
        if constraint_container is None:
            return
        constraint_container.clear()
        with constraint_container:
            if state.constraints:
                for constraint in state.constraints:
                    render_constraint_item(constraint)

            ui.button(
                "拘束条件を追加",
                icon="add",
                on_click=add_constraint,
            ).props("flat dense").classes("mt-2")

    def render_constraint_item(constraint: ConstraintConfig) -> None:
        """拘束条件アイテムを描画"""
        with (
            ui.expansion(
                constraint.name,
                icon="lock",
                value=False,
            )
            .classes("w-full bg-gray-50")
            .props("dense")
        ):
            with ui.column().classes("gap-3 p-2"):
                # 拘束名
                with ui.row().classes("w-full items-center justify-between"):
                    ui.input(
                        label="拘束名",
                        value=constraint.name,
                        on_change=lambda e, c=constraint: setattr(c, "name", e.value),
                    ).classes("w-48").props("dense")

                    ui.button(
                        icon="delete",
                        on_click=lambda c=constraint: remove_constraint(c),
                    ).props("flat dense color=negative").tooltip("削除")

                # 座標範囲
                ui.label("座標範囲").classes("font-medium text-sm")
                with ui.grid(columns=4).classes("gap-2"):
                    # X範囲
                    ui.label("X:").classes("text-sm self-center")
                    ui.number(
                        label="min",
                        value=constraint.x_range[0],
                        step=1.0,
                        format="%.1f",
                        on_change=lambda e, c=constraint: setattr(
                            c, "x_range", (e.value, c.x_range[1])
                        ),
                    ).classes("w-24").props("dense")
                    ui.label("~").classes("text-sm self-center")
                    ui.number(
                        label="max",
                        value=constraint.x_range[1],
                        step=1.0,
                        format="%.1f",
                        on_change=lambda e, c=constraint: setattr(
                            c, "x_range", (c.x_range[0], e.value)
                        ),
                    ).classes("w-24").props("dense")

                    # Y範囲
                    ui.label("Y:").classes("text-sm self-center")
                    ui.number(
                        label="min",
                        value=constraint.y_range[0],
                        step=1.0,
                        format="%.1f",
                        on_change=lambda e, c=constraint: setattr(
                            c, "y_range", (e.value, c.y_range[1])
                        ),
                    ).classes("w-24").props("dense")
                    ui.label("~").classes("text-sm self-center")
                    ui.number(
                        label="max",
                        value=constraint.y_range[1],
                        step=1.0,
                        format="%.1f",
                        on_change=lambda e, c=constraint: setattr(
                            c, "y_range", (c.y_range[0], e.value)
                        ),
                    ).classes("w-24").props("dense")

                    # Z範囲
                    ui.label("Z:").classes("text-sm self-center")
                    ui.number(
                        label="min",
                        value=constraint.z_range[0],
                        step=1.0,
                        format="%.1f",
                        on_change=lambda e, c=constraint: setattr(
                            c, "z_range", (e.value, c.z_range[1])
                        ),
                    ).classes("w-24").props("dense")
                    ui.label("~").classes("text-sm self-center")
                    ui.number(
                        label="max",
                        value=constraint.z_range[1],
                        step=1.0,
                        format="%.1f",
                        on_change=lambda e, c=constraint: setattr(
                            c, "z_range", (c.z_range[0], e.value)
                        ),
                    ).classes("w-24").props("dense")

                # 拘束自由度
                ui.label("拘束する自由度").classes("font-medium text-sm mt-2")
                with ui.row().classes("gap-4"):
                    # 並進
                    with ui.column().classes("gap-1"):
                        ui.checkbox(
                            "X並進",
                            value=constraint.dof[0],
                            on_change=lambda e, c=constraint, i=0: update_dof(
                                c, i, e.value
                            ),
                        )
                        ui.checkbox(
                            "Y並進",
                            value=constraint.dof[1],
                            on_change=lambda e, c=constraint, i=1: update_dof(
                                c, i, e.value
                            ),
                        )
                        ui.checkbox(
                            "Z並進",
                            value=constraint.dof[2],
                            on_change=lambda e, c=constraint, i=2: update_dof(
                                c, i, e.value
                            ),
                        )

                    # 回転
                    with ui.column().classes("gap-1"):
                        ui.checkbox(
                            "X回転",
                            value=constraint.dof[3],
                            on_change=lambda e, c=constraint, i=3: update_dof(
                                c, i, e.value
                            ),
                        )
                        ui.checkbox(
                            "Y回転",
                            value=constraint.dof[4],
                            on_change=lambda e, c=constraint, i=4: update_dof(
                                c, i, e.value
                            ),
                        )
                        ui.checkbox(
                            "Z回転",
                            value=constraint.dof[5],
                            on_change=lambda e, c=constraint, i=5: update_dof(
                                c, i, e.value
                            ),
                        )

    def update_dof(constraint: ConstraintConfig, index: int, value: bool) -> None:
        """自由度の拘束状態を更新"""
        new_dof = constraint.dof.copy()
        new_dof[index] = value
        constraint.dof = new_dof

    with ui.column().classes("gap-2"):
        ui.label("拘束条件").classes("font-medium")

        # 拘束条件リストコンテナ
        constraint_container = ui.column().classes("w-full gap-2")
        with constraint_container:
            if state.constraints:
                for constraint in state.constraints:
                    render_constraint_item(constraint)

            ui.button(
                "拘束条件を追加",
                icon="add",
                on_click=add_constraint,
            ).props("flat dense").classes("mt-2")
