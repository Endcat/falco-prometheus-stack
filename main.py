from hanabi.utils.queue import DockerLogQueue
from hanabi.models.hbt import HBTModel
from hanabi.models.event_parser import EventParser
from hanabi.models.tree_node import TreeNode
from rich.tree import Tree
from rich import print as rprint
import json

def print_tree(node: TreeNode, tree: Tree = None, level: int = 0) -> Tree:
    """将TreeNode转换为Rich树形结构进行可视化输出"""
    if tree is None:
        # 创建根节点
        root_text = f"[bold blue]{node.name}[/bold blue] ({node.node_type})"
        if node.events_count > 0:
            root_text += f" [green]({node.events_count} events)[/green]"
        tree = Tree(root_text)
        # 递归处理子节点
        for child in node.children.values():
            print_tree(child, tree, level + 1)
    else:
        # 创建当前节点文本
        node_text = f"[blue]{node.name}[/blue] ({node.node_type})"
        if node.events_count > 0:
            node_text += f" [green]({node.events_count} events)[/green]"
        
        # 添加节点到树
        branch = tree.add(node_text)
        
        # 递归处理子节点
        for child in node.children.values():
            print_tree(child, branch, level + 1)
    
    return tree

def main():
    log_queue = DockerLogQueue(container_name="falco")
    log_queue.start()

    print("before HBTModel")
    # 创建HBT模型实例
    hbt_model = HBTModel("falco_container")
    print("after HBTModel")
    print("before EventParser")
    # 初始化事件解析器
    event_parser = EventParser()
    print("after EventParser")
    
    try:
        cnt = 0
        while True:
            json_obj = log_queue.get(timeout=1)
            if json_obj:
                cnt += 1
                print("log:", cnt)
                # 解析事件并添加到HBT模型
                output_fields = event_parser.extract_output_fields(json_obj)
                category = event_parser.categorize_event(json_obj)
                
                if category == "process":
                    print("process log")
                    hbt_model.add_process_event(output_fields)
                elif category == "network":
                    print("network log")
                    hbt_model.add_network_event(output_fields)
                elif category == "file":
                    print("file log")
                    hbt_model.add_file_event(output_fields)

                    
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
        # 打印最终模型结构
        print("Final HBT model (JSON format):")
        print(json.dumps(hbt_model.get_model(), ensure_ascii=False, default=str))
        
        # 以树形结构打印模型
        print("\nFinal HBT model (Tree format):")
        model_dict = hbt_model.get_model()
        hbt_structure = model_dict["hbt_structure"]
        # 重建根节点
        root_node = TreeNode(hbt_structure["name"], hbt_structure["type"])
        root_node.events_count = hbt_structure["events_count"]
        root_node.metadata = hbt_structure["metadata"]
        # 递归重建子节点
        def rebuild_tree(node_dict, parent_node):
            for child_name, child_dict in node_dict["children"].items():
                child_node = parent_node.add_child(child_name, child_dict["type"])
                child_node.events_count = child_dict["events_count"]
                child_node.metadata = child_dict["metadata"]
                rebuild_tree(child_dict, child_node)
        rebuild_tree(hbt_structure, root_node)
        # 打印树形结构
        tree = print_tree(root_node)
        rprint(tree)
    finally:
        log_queue.stop()


def get_model_statistics(hbt_model):
    """获取HBT模型的统计信息"""
    # 这里简化实现，实际应用中可以从HBTBuilder获取统计信息
    model = hbt_model.get_model()
    return {
        "container_id": model["container_id"],
        "total_events": 0  # 简化实现，实际应计算所有事件数量
    }


if __name__ == "__main__":
    main()
