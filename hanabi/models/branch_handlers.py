from typing import Dict, Any
from .tree_node import TreeNode
import json


class BranchHandler:
    """基础分支处理器"""
    
    def __init__(self, branch_root: TreeNode):
        """
        初始化分支处理器
        
        Args:
            branch_root: 分支根节点
        """
        self.root = branch_root
    
    def handle_event(self, event: Dict[str, Any]):
        """
        处理事件的基础方法，需要在子类中实现
        
        Args:
            event: 事件数据
        """
        raise NotImplementedError("This method should be implemented by subclasses")


class ProcessBranchHandler(BranchHandler):
    """进程分支处理器"""
    
    def handle_event(self, event: Dict[str, Any]):
        """
        处理进程相关事件
        
        Args:
            event: 进程事件数据
        """
        # 获取进程相关信息
        proc_name = event.get("proc.name", "unknown")
        proc_cmdline = event.get("proc.cmdline", "")
        evt_type = event.get("evt.type", "")
        
        # 在进程分支下创建进程节点
        proc_node = self.root.add_child(proc_name, "process")
        proc_node.increment_events_count()
        
        # 添加进程元数据
        proc_node.update_metadata("cmdline", proc_cmdline)
        
        # 创建事件类型子节点
        if evt_type:
            evt_node = proc_node.add_child(evt_type, "process_event")
            evt_node.increment_events_count()


class NetworkBranchHandler(BranchHandler):
    """网络分支处理器"""
    
    def handle_event(self, event: Dict[str, Any]):
        """
        处理网络相关事件
        
        Args:
            event: 网络事件数据
        """
        # 获取网络相关信息
        evt_type = event.get("evt.type", "")
        fd_name = event.get("fd.name", "")
        fd_type = event.get("fd.type", "")
        
        # 在网络分支下创建事件类型节点
        if evt_type:
            evt_node = self.root.add_child(evt_type, "network_event")
            evt_node.increment_events_count()
            
            # 添加文件描述符信息作为子节点
            if fd_name:
                fd_node = evt_node.add_child(fd_name, "network_connection")
                fd_node.increment_events_count()
                fd_node.update_metadata("fd_type", fd_type)


class FileBranchHandler(BranchHandler):
    """文件分支处理器"""
    
    def handle_event(self, event: Dict[str, Any]):
        """
        处理文件相关事件
        
        Args:
            event: 文件事件数据
        """
        # 获取文件相关信息
        evt_type = event.get("evt.type", "")
        proc_name = event.get("proc.name", "unknown")
        if self.root.children[evt_type] is None:
            self.root.add_child(evt_type, "file")
        if self.root.children[evt_type].children[proc_name] is None:
            self.root.children[evt_type].add_child(proc_name, "process")
