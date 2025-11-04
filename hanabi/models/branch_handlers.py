from typing import Dict, Any
from .tree_node import TreeNode
import json
import re
import time
from ..utils.timeCount import EventCounter

learnState = True

def update_learn_state(eventCounter: EventCounter):
    """
    根据事件速率和时间窗口更新learnState
    """
    global learnState
    print("update_learn_state called, learning")  # Debugging line
    now = int(time.time() * 1000)
    earliest_time = eventCounter.timestamps[0] if eventCounter.timestamps else now
    print("eventCounter.get_rate():", eventCounter.get_rate())
    print("now - earliest_time:", now - earliest_time)
    if now - earliest_time >= 1000 * 10:
        if eventCounter.get_rate() <= 10: # 每10秒事件数小于10
            learnState = False
    eventCounter.on_event()

class BranchHandler:
    """基础分支处理器"""
    
    def __init__(self, branch_root: TreeNode):
        """
        初始化分支处理器
        
        Args:
            branch_root: 分支根节点
        """
        self.root = branch_root
    
    def handle_event(self, event: Dict[str, Any],eventCounter: EventCounter):
        """
        处理事件的基础方法，需要在子类中实现
        
        Args:
            event: 事件数据
        """
        raise NotImplementedError("This method should be implemented by subclasses")


class ProcessBranchHandler(BranchHandler):
    """进程分支处理器"""
    
    def handle_event(self, event: Dict[str, Any],eventCounter: EventCounter):
        """
        处理进程相关事件
        
        Args:
            event: 进程事件数据
        """
        if learnState == False:
            print("handle_event called with learnState=False")  # Debugging line
            evt_type = event.get("evt.type", "")
            proc_name = event.get("proc.name", "unknown")
            if evt_type not in self.root.children:
                print("warning(T):    " + json.dumps(event, ensure_ascii=False)+"\n")
            elif proc_name not in self.root.children[evt_type].children:
                print("Warning(T):    " + json.dumps(event, ensure_ascii=False)+"\n")
            else:
                cmdline = event.get("proc.cmdline", "")
                keys = re.findall(r'-{1,2}[^\s-]+', cmdline)
                for k in keys:
                    if k not in self.root.children[evt_type].children[proc_name].children:
                        print("Warning(T):    " + json.dumps(event, ensure_ascii=False)+"\n")
                        break
            return
        # 获取进程相关信息
        # 获取operation layer级别的节点，即start、exit、prctl等
        evt_type = event.get("evt.type", "")
        if evt_type not in self.root.children:
            self.root.add_child(evt_type, "process_operation")
        # 获取process layer级别的节点,即相应的proc.name
        proc_name = event.get("proc.name", "unknown")
        if proc_name not in self.root.children[evt_type].children:
            self.root.children[evt_type].add_child(proc_name, "process_name")
        # 获取Attribute Token Bag级别的节点，在进程中就是命令参数
        cmdline = event.get("proc.cmdline", "")
        keys = re.findall(r'-{1,2}[^\s-]+', cmdline)
        for k in keys:
            if k not in self.root.children[evt_type].children[proc_name].children:
                self.root.children[evt_type].children[proc_name].add_child(k, "cmd_argument")
            self.root.children[evt_type].children[proc_name].children[k].events_count += 1
        print("Warning(F):    " + json.dumps(event, ensure_ascii=False)+"\n")

        if learnState == True:
            update_learn_state(eventCounter)

class NetworkBranchHandler(BranchHandler):
    """网络分支处理器"""
    
    def handle_event(self, event: Dict[str, Any],eventCounter: EventCounter):
        """
        处理网络相关事件
        
        Args:
            event: 网络事件数据
        """
        if learnState == False:
            print("handle_event called with learnState=False")  # Debugging line
            evt_type = event.get("evt.type", "")
            proc_name = event.get("proc.name", "unknown")
            if evt_type not in self.root.children:
                print("Warning(T): " + json.dumps(event, ensure_ascii=False)+"\n")
            elif proc_name not in self.root.children[evt_type].children:
                print("Warning(T): " + json.dumps(event, ensure_ascii=False)+"\n")
            else:
                protocol = event.get("fd.type", "")
                str = event.get("fd.name", "")
                # 检查 fd.name 是否为 None 或空字符串
                if not str:
                    return
                # 检查是否包含 "->" 分隔符
                if "->" not in str:
                    right = ":"
                else:
                    _ , right = str.split("->")
                value = right + ":" + protocol
                if value not in self.root.children[evt_type].children[proc_name].children:
                    print("Warning(T): " + json.dumps(event, ensure_ascii=False)+"\n")
                else:
                    #还要添加计数?
                    pass
            return
        # 获取网络相关信息
        # 获取operation layer级别的节点，即connection、listen、shutdown等
        evt_type = event.get("evt.type", "")
        if evt_type not in self.root.children:
            self.root.add_child(evt_type, "network_operation")
        # 获取process layer级别的节点,即相应的proc.name
        proc_name = event.get("proc.name", "unknown")
        if proc_name not in self.root.children[evt_type].children:
            self.root.children[evt_type].add_child(proc_name, "process_name")
        # 获取Attribute Token Bag级别的节点，在网络中就是ip、port、protocol等
        protocol = event.get("fd.type", "")
        str = event.get("fd.name", "")
        # 检查 fd.name 是否为 None 或空字符串
        if not str:
            return
        if "->" not in str:
            right = ":"
        else:
            _ , right = str.split("->")
        value = right + ":" + protocol
        if value not in self.root.children[evt_type].children[proc_name].children:
            self.root.children[evt_type].children[proc_name].add_child(value, "network_attribute")
        self.root.children[evt_type].children[proc_name].children[value].events_count += 1
        print("Warning(F): " + json.dumps(event, ensure_ascii=False)+"\n")

        if learnState == True:
            update_learn_state(eventCounter)

class FileBranchHandler(BranchHandler):
    """文件分支处理器"""
    
    def handle_event(self, event: Dict[str, Any],eventCounter: EventCounter):
        """
        处理文件相关事件
        
        Args:
            event: 文件事件数据
        """
        if learnState == False:
            print("handle_event called with learnState=False")  # Debugging line
            evt_type = event.get("evt.type", "")
            proc_name = event.get("proc.name", "unknown")
            if evt_type not in self.root.children:
                print("Warning(T): " + json.dumps(event, ensure_ascii=False)+"\n")
            elif proc_name not in self.root.children[evt_type].children:
                print("Warning(T): " + json.dumps(event, ensure_ascii=False)+"\n")
            else:
                directory = event.get("fd.directory", "")
                filename = event.get("fd.name", "")
                if directory not in self.root.children[evt_type].children[proc_name].children:
                    print("Warning(T): " + json.dumps(event, ensure_ascii=False)+"\n")
                elif filename not in self.root.children[evt_type].children[proc_name].children:
                    print("Warning(T): " + json.dumps(event, ensure_ascii=False)+"\n")
                else:
                    #还要添加计数?
                    pass
            return
        # 获取文件相关信息
        # 获取operation layer级别的节点，即create、open、read、write、close等
        evt_type = event.get("evt.type", "")
        if evt_type not in self.root.children:
            self.root.add_child(evt_type, "file_operation")
        # 获取process layer级别的节点,即相应的proc.name
        proc_name = event.get("proc.name", "unknown")
        if proc_name not in self.root.children[evt_type].children:
            self.root.children[evt_type].add_child(proc_name, "process_name")
        # 获取Attribute Token Bag级别的节点，在文件中就是directory和filename
        directory = event.get("fd.directory", "")
        filename = event.get("fd.name", "")
        if directory not in self.root.children[evt_type].children[proc_name].children:
            self.root.children[evt_type].children[proc_name].add_child(directory, "directory_path")
        self.root.children[evt_type].children[proc_name].children[directory].events_count += 1
        if filename not in self.root.children[evt_type].children[proc_name].children:
            self.root.children[evt_type].children[proc_name].add_child(filename, "file_name")
        self.root.children[evt_type].children[proc_name].children[filename].events_count += 1
        print("Warning(F): " + json.dumps(event, ensure_ascii=False)+"\n")

        if learnState == True:
            update_learn_state(eventCounter)
