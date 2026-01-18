"""エクスポート関連のユースケースを提供するサービス"""

from pathlib import Path

from core.export.deck_generator import DeckGenerator
from state import AnalysisConfig


class ExportService:
    """エクスポートサービス"""

    @staticmethod
    def export_analysis_deck(state: AnalysisConfig, output_dir: Path) -> str:
        """
        解析設定をファイルにエクスポートする

        Args:
            state: アプリケーション状態
            output_dir: 出力先ディレクトリ

        Returns:
            生成されたメインファイルのパス
        """
        # バリデーション
        if not state.uploaded_meshes and not state.steps:
            # メッシュがなくてもエクスポート自体は許容するが、警告ログなどを出すべき
            # ここでは簡易的に処理続行
            pass

        # Coreを使用してエクスポート実行
        generator = DeckGenerator(str(output_dir))
        output_path = generator.generate(state)

        return output_path
