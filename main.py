from hanabi.utils.queue import DockerLogQueue
from hanabi.models.hbt import HBTModel
from hanabi.models.event_parser import EventParser
import json

def main():
    print("before DockerLogQueue")
    log_queue = DockerLogQueue(container_name="falco")
    print("after DockerLogQueue")
    print("before log_queue.start()")
    log_queue.start()
    print("after log_queue.start()")

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
            print("cnt:", cnt)
            cnt += 1
            json_obj = log_queue.get(timeout=1)
            if json_obj:
                # 打印原始事件
                print("Raw event:")
                print(json.dumps(json_obj, ensure_ascii=False))
                
                # 解析事件并添加到HBT模型
                output_fields = event_parser.extract_output_fields(json_obj)
                category = event_parser.categorize_event(json_obj)
                
                if category == "process":
                    hbt_model.add_process_event(output_fields)
                elif category == "network":
                    hbt_model.add_network_event(output_fields)
                elif category == "file":
                    hbt_model.add_file_event(output_fields)
                
                # 每处理10个事件打印一次模型统计信息
                stats = get_model_statistics(hbt_model)
                if stats.get("total_events", 0) % 10 == 0:
                    print("Model statistics:")
                    print(json.dumps(stats, ensure_ascii=False))
                    
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
        # 打印最终模型结构
        print("Final HBT model:")
        print(json.dumps(hbt_model.get_model(), ensure_ascii=False, default=str))
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
    print("before main")
    main()
    print("after main")
