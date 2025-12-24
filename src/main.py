from nicegui import ui
import plotly.express as px
import pandas as pd

from views import pages


# ルーティング設定
@ui.page('/')
def index_page():
    """ホームページ"""
    pages.home.render()

    # def notify_clicked():
    #     ui.notify("Button clicked")

    # def update_label(e):
    #     label_text.set_text(f"入力されたテキスト: {input_text.value}")

    # def slider_changed(e):
    #     slider_value.set_text(f"選択された値: {e.value}")

    # def open_dialog():
    #     dialog = ui.dialog()
    #     dialog.open()
    #     with dialog:
    #         ui.label("ダイアログです!")
    #         ui.button("Close", on_click=dialog.close)

    # with ui.row():
    #     with ui.column():
    #         input_text = ui.input(label="テキスト入力").on("change", update_label)
    #         label_text = ui.label("入力されたテキスト: ")

    #     with ui.column():
    #         ui.slider(min=0, max=100, step=1, value=50, on_change=slider_changed)
    #         slider_value = ui.label("選択された値: 50")

    # ui.markdown("**Hello, World!**")
    # ui.markdown("## Hello, World!")

    # ui.icon("face")
    # ui.avatar('person', text_color='red', color='gray', size='100px')

    # ui.button("Click me", on_click=notify_clicked)
    # ui.button("ダイアログを開く", on_click=open_dialog)

    # df = pd.DataFrame({
    #     "x": [1, 2, 3, 4, 5],
    #     "y": [1, 2, 3, 4, 5]
    # })
    # fig = px.scatter(df, x="x", y="y")
    # ui.plotly(fig)


ui.run()
