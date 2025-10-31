from prometheus_client import start_http_server, Counter, Gauge
import logging
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from hanabi.utils.queue import DockerLogQueue

# --- 1. 初始化日志 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- 2. 定义 Prometheus 指标 ---

# 定义事件计数器的标签。这是我们查询数据的维度。
EVENT_LABELS = [
    'hostname', 'event_type', 'rule', 'priority', 'container_name', 
    'image_repository', 'process_name', 'k8s_namespace', 'k8s_pod'
]
SYSCALL_EVENTS = Counter('syscall_events_total', 'Total number of syscall events observed.', EVENT_LABELS)

# 定义最新事件时间戳的仪表盘
LAST_EVENT_TIMESTAMP = Gauge(
    'syscall_last_event_timestamp_nanoseconds',
    'Timestamp (nanoseconds) of the last processed syscall event.',
    ['hostname']
)

# --- 3. 处理事件数据的函数 ---
def process_event(event_data):
    """从队列中获取 JSON 数据并更新 Prometheus 指标"""
    try:
        # --- 4. 从 JSON 中安全地提取数据 ---
        # 使用 .get() 方法可以避免因缺少字段而导致程序崩溃
        output_fields = event_data.get('output_fields', {})
        
        # 提取标签值，为缺失的值提供默认 'unknown'
        hostname = event_data.get('hostname', 'unknown')
        event_type = output_fields.get('evt.type', 'unknown')
        rule = event_data.get('rule', 'unknown')
        priority = event_data.get('priority', 'unknown')
        container_name = output_fields.get('container.name', 'unknown')
        image_repository = output_fields.get('container.image.repository', 'unknown')
        process_name = output_fields.get('proc.name', 'unknown')
        
        # Kubernetes 字段可能是 null，需要处理
        k8s_namespace = output_fields.get('k8s.ns.name') or 'none'
        k8s_pod = output_fields.get('k8s.pod.name') or 'none'

        # --- 5. 更新 Prometheus 指标 ---
        
        # 增加计数器
        SYSCALL_EVENTS.labels(
            hostname=hostname,
            event_type=event_type,
            rule=rule,
            priority=priority,
            container_name=container_name,
            image_repository=image_repository,
            process_name=process_name,
            k8s_namespace=k8s_namespace,
            k8s_pod=k8s_pod
        ).inc()

        # 更新最新时间戳
        event_timestamp = output_fields.get('evt.time.iso8601')
        if event_timestamp and isinstance(event_timestamp, int):
            LAST_EVENT_TIMESTAMP.labels(hostname=hostname).set(event_timestamp)

        logging.info(f"Processed event from host: {hostname}, type: {event_type}, rule: {rule}")

    except Exception as e:
        logging.error(f"Error processing event: {e}\nData: {event_data}")


# --- 6. 从 DockerLogQueue 消费数据 ---
def consume_events(container_name="falco"):
    """从 DockerLogQueue 持续消费事件"""
    log_queue = None
    try:
        logging.info(f"Starting to consume events from container: {container_name}")
        log_queue = DockerLogQueue(container_name=container_name, max_queue_size=10000)
        log_queue.start()
        
        while True:
            json_obj = log_queue.get(timeout=1)
            if json_obj:
                process_event(json_obj)
                
    except KeyboardInterrupt:
        logging.info("Stopping event consumer...")
    except Exception as e:
        logging.error(f"Error in event consumer: {e}")
    finally:
        if log_queue:
            log_queue.stop()
            stats = log_queue.get_stats()
            logging.info(f"Final stats: {stats}")

if __name__ == '__main__':
    metrics_port = 9876
    container_name = os.getenv('FALCO_CONTAINER', 'falco')
    
    logging.info(f"Metrics endpoint: http://0.0.0.0:{metrics_port}/metrics")
    logging.info(f"Consuming events from container: {container_name}")
    logging.info("=" * 60)
    
    # 启动 Prometheus HTTP 服务器
    start_http_server(metrics_port)
    logging.info(f"✅ Prometheus metrics server started on port {metrics_port}")
    
    # 开始消费事件
    try:
        consume_events(container_name=container_name)
    except KeyboardInterrupt:
        logging.info("\n🛑 Exporter stopped by user")
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}")
        sys.exit(1)
