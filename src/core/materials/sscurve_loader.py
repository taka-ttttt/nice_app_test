"""応力-ひずみカーブのロードと生成"""

from pathlib import Path

import pandas as pd
from ansys.dyna.core import keywords as kwd

from state.materials import MATERIAL_CURVE_FILES


class SSCurveLoader:
    """応力-ひずみカーブ（Stress-Strain Curve）ローダー"""

    @classmethod
    def load_curve_from_csv(cls, csv_path: str | Path) -> pd.DataFrame:
        """
        CSVファイルから応力-ひずみカーブデータを読み込む

        Args:
            csv_path: CSVファイルのパス

        Returns:
            DataFrame: カラム名 'strain', 'stress' を持つデータ

        Note:
            CSVフォーマット想定:
            - ヘッダー行あり
            - 1列目: plastic_strain (ひずみ)
            - 2列目: true_stress (応力)
        """
        csv_path = Path(csv_path)

        if not csv_path.exists():
            raise FileNotFoundError(f"Curve file not found: {csv_path}")

        # CSVを読み込み
        df = pd.read_csv(csv_path)

        # カラム名を標準化（複数のフォーマットに対応）
        if "plastic_strain" in df.columns and "true_stress" in df.columns:
            df = df.rename(
                columns={"plastic_strain": "strain", "true_stress": "stress"}
            )
        elif "strain" in df.columns and "stress" in df.columns:
            pass  # すでに正しい名前
        else:
            # カラム名がない場合、最初の2列を使用
            df.columns = ["strain", "stress"]

        return df[["strain", "stress"]]

    @classmethod
    def generate_from_csv(
        cls,
        lcss: int,
        csv_path: str | Path,
        title: str | None = None,
    ) -> kwd.DefineCurve:
        """
        CSVファイルから応力-ひずみカーブのキーワードを生成

        Args:
            lcss: Load Curve ID
            csv_path: CSVファイルのパス
            title: カーブのタイトル（Noneの場合はファイル名を使用）

        Returns:
            DefineCurve: 生成されたカーブキーワード
        """
        # CSVからデータを読み込み
        curve_data = cls.load_curve_from_csv(csv_path)

        # PyDynaのDefineCurve用にDataFrameを変換
        # a1: X軸（ひずみ）, o1: Y軸（応力）
        pydyna_df = pd.DataFrame(
            {
                "a1": curve_data["strain"].values,
                "o1": curve_data["stress"].values,
            }
        )

        # タイトルの設定
        if title is None:
            title = Path(csv_path).stem

        # DefineCurveの生成
        # sidr=0: 標準カーブ（時間カーブでない場合）
        return kwd.DefineCurve(
            lcid=lcss,
            sidr=0,
            curves=pydyna_df,
            title=title,
        )

    @classmethod
    def generate_from_lcss(cls, lcss: int) -> kwd.DefineCurve:
        """
        Load Curve IDから対応するCSVファイルを検索してカーブを生成

        Args:
            lcss: Load Curve ID

        Returns:
            DefineCurve: 生成されたカーブキーワード

        Raises:
            ValueError: lcssに対応するCSVファイルが見つからない場合

        Note:
            Phase 1: MATERIAL_CURVE_FILESから検索
            Phase 2 (将来): DBクエリに置き換え
        """
        if lcss not in MATERIAL_CURVE_FILES:
            raise ValueError(
                f"Load curve ID {lcss} not found in MATERIAL_CURVE_FILES. "
                "Available IDs: " + ", ".join(map(str, MATERIAL_CURVE_FILES.keys()))
            )

        csv_path = MATERIAL_CURVE_FILES[lcss]
        return cls.generate_from_csv(lcss, csv_path)

    @classmethod
    def generate_from_db(cls, lcss: int, db_session=None) -> kwd.DefineCurve:
        """
        DBから応力-ひずみカーブを取得してキーワードを生成（将来実装）

        Args:
            lcss: Load Curve ID (curve_id)
            db_session: データベースセッション

        Returns:
            DefineCurve: 生成されたカーブキーワード

        Note:
            Phase 2で実装予定:
            SELECT strain, stress FROM CurvePoints
            WHERE curve_id = lcss
            ORDER BY sequence
        """
        raise NotImplementedError(
            "DB-based curve loading is not yet implemented. "
            "This will be available in Phase 2."
        )
