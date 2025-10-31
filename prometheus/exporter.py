from flask import Flask, request, jsonify
from prometheus_client import make_wsgi_app, Counter, Gauge
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from waitress import serve
import logging

# --- 1. 初始化 Flask App 和日志 ---
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

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

# --- 3. 创建接收数据的 Webhook 端点 ---
@app.route('/webhook', methods=['POST'])
def webhook():
    """接收实时 JSON 数据流并更新 Prometheus 指标"""
    event_data = request.get_json()
    if not event_data:
        return "Invalid JSON payload", 400

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

        logging.info(f"Processed event from host: {hostname}, type: {event_type}")
        return "OK", 200

    except Exception as e:
        logging.error(f"Error processing event: {e}\nData: {event_data}")
        return "Internal Server Error", 500

# --- 6. 组合 Flask App 和 Prometheus metrics App ---
# 使用 DispatcherMiddleware 将 /metrics 请求路由到 prometheus_client
app_dispatch = DispatcherMiddleware(app, {
    '/metrics': make_wsgi_app()
})

if __name__ == '__main__':
    port = 9876
    logging.info(f"Starting exporter on http://0.0.0.0:{port}")
    logging.info(f"Webhook endpoint: http://0.0.0.0:{port}/webhook")
    logging.info(f"Metrics endpoint: http://0.0.0.0:{port}/metrics")
    serve(app_dispatch, host='0.0.0.0', port=port)
