"""メッシュ情報の状態定義"""

import uuid
from dataclasses import dataclass


@dataclass
class MeshInfo:
    """アップロードされたメッシュ情報"""

    id: str  # 一意のID (UUID)
    file_name: str  # オリジナルファイル名
    file_path: str  # サーバー側の一時保存パス
    part_id: int  # *PARTで定義されたパートID
    part_name: str  # *PARTのタイトル
    element_count: int  # 要素数
    element_type: str = "SHELL"  # 要素タイプ (SHELL/SOLID)
    has_shared_nodes: bool = False  # 他パートと節点を共有しているか

    @classmethod
    def create(
        cls,
        file_name: str,
        file_path: str,
        part_id: int,
        part_name: str,
        element_count: int,
        element_type: str = "SHELL",
        has_shared_nodes: bool = False,
    ) -> "MeshInfo":
        """自動生成IDで新しいMeshInfoを作成"""
        return cls(
            id=str(uuid.uuid4()),
            file_name=file_name,
            file_path=file_path,
            part_id=part_id,
            part_name=part_name,
            element_count=element_count,
            element_type=element_type,
            has_shared_nodes=has_shared_nodes,
        )
