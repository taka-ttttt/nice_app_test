from nicegui import ui
import plotly.express as px
import pandas as pd

from views import pages


# ルーティング設定
@ui.page('/')
def index_page():
    """ホームページ"""
    pages.home.render()


ui.run()
