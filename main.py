from hanabi.utils.queue import DockerLogQueue
import json

def main():
    log_queue = DockerLogQueue(container_name="falco")
    log_queue.start()

    try:
        while True:
            json_obj = log_queue.get(timeout=1)
            if json_obj:
                print(json.dumps(json_obj, ensure_ascii=False))
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
    finally:
        log_queue.stop()


if __name__ == "__main__":
    main()
