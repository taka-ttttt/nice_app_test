"""方向（単位ベクトル）を表す値オブジェクト"""
from dataclasses import dataclass
from enum import Enum

import numpy as np


class Axis(Enum):
    """座標軸"""
    X = "x"
    Y = "y"
    Z = "z"
    
    @property
    def dof_number(self) -> int:
        """
        LS-DYNA用のDOF番号を取得
        
        LS-DYNAでは:
        - DOF 1: X方向（並進）
        - DOF 2: Y方向（並進）
        - DOF 3: Z方向（並進）
        """
        dof_mapping = {
            Axis.X: 1,
            Axis.Y: 2,
            Axis.Z: 3,
        }
        return dof_mapping[self]


class Sign(Enum):
    """符号（正/負）"""
    POSITIVE = 1
    NEGATIVE = -1
    
    @property
    def multiplier(self) -> float:
        """スケールファクター用の乗数"""
        return float(self.value)


@dataclass(frozen=True)
class Direction:
    """
    6方向の単位ベクトルを表す値オブジェクト
    
    境界条件の動作方向や荷重方向を表現するために使用します。
    frozen=True により、インスタンス生成後の変更は不可能です。
    
    使用例:
        # プリセットを使用
        direction = Directions.NEGATIVE_Z
        
        # 文字列から生成
        direction = Direction.from_string("-z")
        
        # 直接生成
        direction = Direction(Axis.Z, Sign.NEGATIVE)
    """
    axis: Axis
    sign: Sign
    
    @property
    def dof_number(self) -> int:
        """
        LS-DYNA用のDOF番号を取得
        
        Returns:
            int: DOF番号 (1=X, 2=Y, 3=Z)
        """
        return self.axis.dof_number
    
    @property
    def scale_factor(self) -> float:
        """
        スケールファクターの符号を取得
        
        正方向なら +1.0、負方向なら -1.0 を返します。
        境界条件の荷重や変位の符号付けに使用します。
        
        Returns:
            float: 1.0 または -1.0
        """
        return self.sign.multiplier
    
    @property
    def unit_vector(self) -> tuple[float, float, float]:
        """
        単位ベクトルをタプルで取得
        
        Returns:
            Tuple[float, float, float]: (x, y, z) の単位ベクトル
        """
        vec = [0.0, 0.0, 0.0]
        index = self.dof_number - 1  # DOF番号は1始まり、インデックスは0始まり
        vec[index] = self.scale_factor
        return tuple(vec)
    
    def to_numpy(self) -> np.ndarray:
        """
        NumPy配列として取得
        
        Returns:
            np.ndarray: 3要素の単位ベクトル
        """
        return np.array(self.unit_vector)
    
    def __str__(self) -> str:
        """文字列表現 (例: '+Z', '-X')"""
        sign_str = "+" if self.sign == Sign.POSITIVE else "-"
        return f"{sign_str}{self.axis.value.upper()}"
    
    def __repr__(self) -> str:
        return f"Direction({self.axis.name}, {self.sign.name})"
    
    @classmethod
    def from_string(cls, direction_str: str) -> "Direction":
        """
        文字列から Direction を生成
        
        Parameters:
            direction_str: 方向を表す文字列 (例: '+z', '-X', '+Y')
        
        Returns:
            Direction: 対応する Direction インスタンス
        
        Raises:
            ValueError: 無効な文字列形式の場合
        """
        direction_str = direction_str.strip()
        
        if len(direction_str) != 2:
            raise ValueError(
                f"無効な方向文字列: '{direction_str}'. "
                f"'+x', '-z' などの形式で指定してください。"
            )
        
        sign_char = direction_str[0]
        axis_char = direction_str[1].lower()
        
        # 符号の解析
        if sign_char == '+':
            sign = Sign.POSITIVE
        elif sign_char == '-':
            sign = Sign.NEGATIVE
        else:
            raise ValueError(
                f"無効な符号: '{sign_char}'. '+' または '-' を使用してください。"
            )
        
        # 軸の解析
        try:
            axis = Axis(axis_char)
        except ValueError:
            raise ValueError(
                f"無効な軸: '{axis_char}'. 'x', 'y', 'z' を使用してください。"
            )
        
        return cls(axis=axis, sign=sign)


class _DirectionsMeta(type):
    """Directionsクラスの属性変更を防ぐメタクラス"""
    
    _initialized = False
    
    def __setattr__(cls, name: str, value) -> None:
        if cls._initialized and name != "_initialized":
            raise AttributeError(
                f"Directions.{name} は変更できません。"
                "方向プリセットは不変です。"
            )
        super().__setattr__(name, value)
    
    def __delattr__(cls, name: str) -> None:
        raise AttributeError(
            f"Directions.{name} は削除できません。"
            "方向プリセットは不変です。"
        )


class Directions(metaclass=_DirectionsMeta):
    """
    6方向のプリセット定義
    
    このクラスの属性は変更・削除できません。
    
    使用例:
        from src.core.common import Directions
        
        direction = Directions.NEGATIVE_Z
        print(direction.dof_number)    # 3
        print(direction.scale_factor)  # -1.0
    """
    
    # X軸方向
    POSITIVE_X: Direction = Direction(Axis.X, Sign.POSITIVE)
    NEGATIVE_X: Direction = Direction(Axis.X, Sign.NEGATIVE)
    
    # Y軸方向
    POSITIVE_Y: Direction = Direction(Axis.Y, Sign.POSITIVE)
    NEGATIVE_Y: Direction = Direction(Axis.Y, Sign.NEGATIVE)
    
    # Z軸方向
    POSITIVE_Z: Direction = Direction(Axis.Z, Sign.POSITIVE)
    NEGATIVE_Z: Direction = Direction(Axis.Z, Sign.NEGATIVE)
    
    @classmethod
    def all(cls) -> tuple[Direction, ...]:
        """全6方向のタプルを取得"""
        return (
            cls.POSITIVE_X, cls.NEGATIVE_X,
            cls.POSITIVE_Y, cls.NEGATIVE_Y,
            cls.POSITIVE_Z, cls.NEGATIVE_Z,
        )
    
    @classmethod
    def from_string(cls, direction_str: str) -> Direction:
        """
        文字列から対応するプリセットを取得
        
        Direction.from_string() のエイリアス
        """
        return Direction.from_string(direction_str)


# メタクラスの初期化完了フラグを設定（これ以降の変更を禁止）
Directions._initialized = True

