from typing import Dict, Any, Optional
from datetime import datetime


class TreeNode:
    """树节点类，用于表示HBT模型中的节点"""
    
    def __init__(self, name: str, node_type: str):
        """
        初始化树节点
        
        Args:
            name: 节点名称
            node_type: 节点类型 ('process', 'network', 'file')
        """
        self.name = name
        self.node_type = node_type
        self.children: Dict[str, TreeNode] = {}
        self.events_count = 0
        self.metadata: Dict[str, Any] = {}
        self.last_updated = datetime.now()
    
    def add_child(self, child_name: str, child_type: str) -> 'TreeNode':
        """
        添加子节点
        
        Args:
            child_name: 子节点名称
            child_type: 子节点类型
            
        Returns:
            TreeNode: 创建或已存在的子节点
        """
        if child_name not in self.children:
            self.children[child_name] = TreeNode(child_name, child_type)
        return self.children[child_name]
    
    def get_child(self, child_name: str) -> Optional['TreeNode']:
        """
        获取子节点
        
        Args:
            child_name: 子节点名称
            
        Returns:
            TreeNode: 子节点对象，如果不存在返回None
        """
        return self.children.get(child_name)
    
    def increment_events_count(self, count: int = 1):
        """
        增加事件计数
        
        Args:
            count: 增加的数量，默认为1
        """
        self.events_count += count
        self.last_updated = datetime.now()
    
    def update_metadata(self, key: str, value: Any):
        """
        更新元数据
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将节点转换为字典格式
        
        Returns:
            dict: 节点的字典表示
        """
        return {
            "name": self.name,
            "type": self.node_type,
            "events_count": self.events_count,
            "metadata": self.metadata,
            "children": {name: child.to_dict() for name, child in self.children.items()}
        }