from nicegui import ui

from views import pages


# ルーティング設定
@ui.page("/")
def index_page():
    """ホームページ"""
    pages.home.render()


ui.run()
