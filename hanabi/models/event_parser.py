import json
from typing import Dict, Any, List, Union


class EventParser:
    """Falco事件解析器"""
    
    @staticmethod
    def parse_event_data(data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        解析单个事件数据
        
        Args:
            data: 事件数据，可以是JSON字符串或字典
            
        Returns:
            dict: 解析后的事件字典
        """
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                # 如果不是有效的JSON，返回空字典
                return {}
        elif isinstance(data, dict):
            return data
        else:
            return {}
    
    @staticmethod
    def parse_event_file(file_path: str) -> List[Dict[str, Any]]:
        """
        解析事件文件
        
        Args:
            file_path: 事件文件路径
            
        Returns:
            list: 事件字典列表
        """
        events = []
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
                # 处理可能包含多个JSON对象的文件
                for line in content.split('\n'):
                    if line.strip():
                        # 尝试解析每一行
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except json.JSONDecodeError:
                            # 如果单行解析失败，尝试将整个内容作为JSON处理
                            pass
                
                # 如果按行解析没有结果，尝试将整个文件作为JSON数组处理
                if not events:
                    try:
                        events = json.loads(content)
                        # 确保返回的是列表
                        if not isinstance(events, list):
                            events = [events]
                    except json.JSONDecodeError:
                        pass
                        
        except FileNotFoundError:
            print(f"Warning: File {file_path} not found.")
        except Exception as e:
            print(f"Error parsing event file {file_path}: {str(e)}")
            
        return events
    
    @staticmethod
    def extract_output_fields(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取事件的输出字段
        
        Args:
            event: 原始事件数据
            
        Returns:
            dict: 输出字段字典
        """
        # 如果事件中有output_fields字段，直接返回
        if "output_fields" in event:
            return event["output_fields"]
        
        # 否则返回事件本身，因为它可能已经是输出字段格式
        return event
    
    @staticmethod
    def categorize_event(event: Dict[str, Any]) -> str:
        """
        对事件进行分类
        
        Args:
            event: 事件数据
            
        Returns:
            str: 事件类别 ('process', 'network', 'file', 或 'unknown')
        """
        # 首先尝试从rule字段判断
        rule = event.get("rule", "").lower()
        if rule in ["process", "proc"]:
            return "process"
        elif rule in ["network", "net"]:
            return "network"
        elif rule in ["file"]:
            return "file"
        
        # 如果rule字段不可用，尝试从evt.type判断
        evt_type = event.get("evt.type", "").lower()
        if evt_type in ["execve", "clone", "fork", "vfork"]:
            return "process"
        elif evt_type in ["connect", "accept", "send", "recv", "sendto", "recvfrom"]:
            return "network"
        elif evt_type in ["open", "openat", "close", "read", "write", "unlink", "unlinkat"]:
            return "file"
        
        # 如果无法确定，返回unknown
        return "unknown"