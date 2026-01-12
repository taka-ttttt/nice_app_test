"""カーブ生成関数"""

import numpy as np
import pandas as pd
from ansys.dyna.core import keywords as kwd


def generate_half_cosine_curve(
    ramp_time: float, hold_time: float = 10.0, num_pts: int = 100
) -> tuple[np.ndarray, np.ndarray]:
    """
    ハーフコサイン波形の時間と値の配列を生成する共通関数

    Parameters:
    - ramp_time: 立上げ時間 [s]
    - hold_time: 保持時間 [s]
    - num_pts: カーブの分割点数

    Returns:
    - (time_array, value_array): 時間配列と値配列のタプル
    """
    # ハーフコサインで 0→1 に単調立上げ
    t_ramp = np.linspace(0.0, ramp_time, num_pts)
    y_ramp = 0.5 * (1.0 - np.cos(np.pi * t_ramp / ramp_time))

    # 一定保持（十分に長い時間を確保）
    t = np.concatenate([t_ramp, [ramp_time, ramp_time + hold_time]])
    y = np.concatenate([y_ramp, [1.0, 1.0]])

    return t, y


def generate_half_cosine_derivative_curve(
    ramp_time: float, hold_time: float = 10.0, num_pts: int = 100
) -> tuple[np.ndarray, np.ndarray]:
    """
    ハーフコサイン波形の微分カーブの時間と値の配列を生成する共通関数

    Parameters:
    - ramp_time: 立上げ時間 [s]
    - hold_time: 保持時間 [s]
    - num_pts: カーブの分割点数

    Returns:
    - (time_array, derivative_array): 時間配列と微分値配列のタプル
    """
    # ランプ部分の微分値
    # 微分: d/dt[0.5(1-cos(πt/T))] = 0.5(π/T)sin(πt/T)
    t_ramp = np.linspace(0.0, ramp_time, num_pts)
    deriv_ramp = 0.5 * (np.pi / ramp_time) * np.sin(np.pi * t_ramp / ramp_time)

    # 保持部分の微分値（一定値なので微分は0）
    t = np.concatenate([t_ramp, [ramp_time, ramp_time + hold_time]])
    deriv = np.concatenate([deriv_ramp, [0.0, 0.0]])

    return t, deriv


def generate_full_cosine_curve(
    cycle_time: float, hold_time: float = 10.0, num_pts: int = 100
) -> tuple[np.ndarray, np.ndarray]:
    """
    フルコサイン波形（往復動作）の時間と値の配列を生成する共通関数
    0→1→0 の往復動作を表現

    Parameters:
    - cycle_time: 1サイクル時間（往復時間） [s]
    - hold_time: 保持時間 [s]
    - num_pts: カーブの分割点数

    Returns:
    - (time_array, value_array): 時間配列と値配列のタプル
    """
    # フルコサインで 0→1→0 の往復動作
    t_cycle = np.linspace(0.0, cycle_time, num_pts)
    y_cycle = 0.5 * (1.0 - np.cos(2.0 * np.pi * t_cycle / cycle_time))

    # 一定保持（十分に長い時間を確保）
    t = np.concatenate([t_cycle, [cycle_time, cycle_time + hold_time]])
    y = np.concatenate([y_cycle, [0.0, 0.0]])

    return t, y


def generate_full_cosine_derivative_curve(
    cycle_time: float, hold_time: float = 10.0, num_pts: int = 100
) -> tuple[np.ndarray, np.ndarray]:
    """
    フルコサイン波形の微分カーブの時間と値の配列を生成する共通関数

    Parameters:
    - cycle_time: 1サイクル時間（往復時間） [s]
    - hold_time: 保持時間 [s]
    - num_pts: カーブの分割点数

    Returns:
    - (time_array, derivative_array): 時間配列と微分値配列のタプル
    """
    # サイクル部分の微分値
    # 微分: d/dt[0.5(1-cos(2πt/T))] = 0.5(2π/T)sin(2πt/T) = (π/T)sin(2πt/T)
    t_cycle = np.linspace(0.0, cycle_time, num_pts)
    deriv_cycle = (np.pi / cycle_time) * np.sin(2.0 * np.pi * t_cycle / cycle_time)

    # 保持部分の微分値（一定値なので微分は0）
    t = np.concatenate([t_cycle, [cycle_time, cycle_time + hold_time]])
    deriv = np.concatenate([deriv_cycle, [0.0, 0.0]])

    return t, deriv


def create_preload_curve(
    lcid: int,
    ramp_time: float = 0.02,
    hold_time: float = 10.0,
    num_pts: int = 100,
    title: str = "Preload curve",
) -> kwd.DefineCurve:
    """
    プリロード用のハーフコサインカーブを作成

    Parameters:
    - lcid: カーブID
    - title: カーブのタイトル
    - ramp_time: 立上げ時間 [s]
    - hold_time: 保持時間 [s] (Noneの場合はConfig.end_timeを想定)
    - num_pts: カーブの分割点数
    """
    # 共通のハーフコサイン波形生成を使用
    t, y = generate_half_cosine_curve(ramp_time, hold_time, num_pts)

    curve_df = pd.DataFrame({"a1": t, "o1": y})
    return kwd.DefineCurve(lcid=lcid, sidr=2, curves=curve_df, title=title)


def create_stroke_curve(
    lcid: int,
    ramp_time: float,
    hold_time: float = 10.0,
    sfo: float = 1.0,
    num_pts: int = 100,
    curve_type: str = "displacement",
    stroke_mode: str = "forward_only",
    title: str = "Stroke curve",
) -> kwd.DefineCurve:
    """
    ストローク用のカーブを作成（変位または速度、往路のみまたは往復）

    Parameters:
    - lcid: カーブID
    - ramp_time: 立上げ時間 [s] (forward_only時) または 1サイクル時間 [s] (reciprocating時)
    - hold_time: 保持時間 [s]
    - sfo: スケールファクター（y方向の倍率）
    - num_pts: カーブの分割点数
    - curve_type: カーブの種類（"displacement"または"velocity"）
    - stroke_mode: ストロークモード（"forward_only": 往路のみ, "reciprocating": 往復）
    - title: カーブのタイトル
    """
    # カーブタイプの検証
    valid_types = ["displacement", "velocity"]
    if curve_type not in valid_types:
        available = ", ".join(valid_types)
        raise ValueError(f"無効なカーブタイプ: '{curve_type}'. 利用可能: {available}")

    # ストロークモードの検証
    valid_modes = ["forward_only", "reciprocating"]
    if stroke_mode not in valid_modes:
        available = ", ".join(valid_modes)
        raise ValueError(
            f"無効なストロークモード: '{stroke_mode}'. 利用可能: {available}"
        )

    # カーブタイプとストロークモードの組み合わせによる処理
    if stroke_mode == "forward_only":
        if curve_type == "displacement":
            # 変位カーブ（往路のみ）
            t, y = generate_half_cosine_curve(ramp_time, hold_time, num_pts)
        elif curve_type == "velocity":
            # 速度カーブ（往路のみ）
            t, y = generate_half_cosine_derivative_curve(ramp_time, hold_time, num_pts)
    elif stroke_mode == "reciprocating":
        if curve_type == "displacement":
            # 変位カーブ（往復）
            t, y = generate_full_cosine_curve(ramp_time, hold_time, num_pts)
        elif curve_type == "velocity":
            # 速度カーブ（往復）
            t, y = generate_full_cosine_derivative_curve(ramp_time, hold_time, num_pts)

    y_scaled = y * sfo
    curve_df = pd.DataFrame({"a1": t, "o1": y_scaled})

    return kwd.DefineCurve(lcid=lcid, sidr=0, curves=curve_df, title=title)


def create_threshold_following_curve(
    lcid: int,
    threshold_displacement: float,
    reference_curve_data: pd.DataFrame,
    title: str = "Threshold following curve",
) -> kwd.DefineCurve:
    """
    所定変位量に到達してから変位カーブに追従するカーブを作成

    Parameters:
    - lcid: カーブID
    - threshold_displacement: 追従開始の閾値変位量
    - reference_curve_data: 参照する変位カーブのDataFrame（列名: "a1"=時間, "o1"=変位）
    - title: カーブのタイトル

    Returns:
    - DefineCurve: 追従カーブキーワード
    """
    # 参照カーブから時間と変位を取得
    t_ref = reference_curve_data["a1"].values
    y_ref = reference_curve_data["o1"].values

    # 所定変位量に到達する時刻 t_sw を計算
    # 線形補間で正確な交点を求める
    t_sw = None
    y_sw = None

    for i in range(len(y_ref) - 1):
        if y_ref[i] <= threshold_displacement <= y_ref[i + 1]:
            # 線形補間で正確な時刻を計算
            ratio = (threshold_displacement - y_ref[i]) / (y_ref[i + 1] - y_ref[i])
            t_sw = t_ref[i] + ratio * (t_ref[i + 1] - t_ref[i])
            y_sw = threshold_displacement
            break

    if t_sw is None:
        raise ValueError(
            f"閾値変位量 {threshold_displacement} に到達しません。参照カーブの最大値: {max(y_ref)}"
        )

    # 新しいカーブデータを作成
    t_new = []
    y_new = []

    for t, y in zip(t_ref, y_ref, strict=True):
        if t <= t_sw:
            # スイッチ時刻以前は初期位置を保持（0）
            t_new.append(t)
            y_new.append(0.0)
        else:
            # スイッチ時刻以降は増分だけ追従
            t_new.append(t)
            y_new.append(y - y_sw)

    # スイッチ時刻の点を明示的に追加（不連続点を明確にするため）
    if t_sw not in t_new:
        # スイッチ時刻の直前と直後の点を追加
        t_new.insert(-len([t for t in t_ref if t > t_sw]), t_sw)
        y_new.insert(-len([t for t in t_ref if t > t_sw]), 0.0)

    # データフレームに変換
    curve_df = pd.DataFrame({"a1": t_new, "o1": y_new})
    # 時間順にソート
    curve_df = curve_df.sort_values("a1").reset_index(drop=True)

    return kwd.DefineCurve(lcid=lcid, sidr=0, curves=curve_df, title=title)


def create_constant_curve(
    lcid: int, sfo: float, title: str = "Constant curve"
) -> kwd.DefineCurve:
    """
    定数値のカーブを作成（制限条件用）

    Parameters:
    - lcid: カーブID
    - sfo: 定数値
    - title: カーブのタイトル
    """
    # 定数値のカーブ（時間0から大きな時間まで同じ値）
    curve_df = pd.DataFrame({"a1": [0.0, 1e21], "o1": [sfo, sfo]})
    return kwd.DefineCurve(lcid=lcid, sidr=0, curves=curve_df, title=title)
