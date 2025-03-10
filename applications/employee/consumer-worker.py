import json
import logging
import multiprocessing
import os
import sys
import django
from confluent_kafka import Consumer, KafkaError
from django.conf import settings
from mongodb import MongoDb

# Setup logging
logger = logging.getLogger("")
logging.basicConfig(level=logging.INFO)

# Setup Django
django_project_dir = os.path.abspath(os.path.join(os.path.dirname(__name__)))
sys.path.append(django_project_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cdc_project.settings")
django.setup()

def consumer_worker(message_queue):
    """
    Worker xử lý message từ queue và cập nhật vào MongoDB.
    """
    mongo_db = MongoDb()  # Tạo MongoDB trong từng process riêng biệt
    while True:
        try:
            message = message_queue.get()
            if message is None:
                break  # Dừng worker nếu nhận được tín hiệu kết thúc

            # Parse payload
            payload = json.loads(message)['payload']
            logger.info(f"Processing payload: {payload}")

            # Update MongoDB
            mongo_db.replicate_data(payload)

        except Exception as e:
            logger.error(f"Worker error: {e}")

def consume_message(message_queue):
    """
    Consumer nhận message từ Kafka và đưa vào queue.
    """
    consumer_config = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': settings.CONSUMER_GROUP_ID,
        'auto.offset.reset': 'earliest',
    }
    consumer = Consumer(consumer_config)
    consumer.subscribe(["^mysql\\.employees\\..*"]) # Lắng nghe các topic có tên mysql.employees.<table>

    while True:
        msgs = consumer.consume(num_messages=10, timeout=1.0)
        if not msgs:
            continue

        for msg in msgs:
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"Kafka error: {msg.error()}")
                break
            try:
                message_queue.put(msg.value().decode("utf-8"))
            except Exception as e:
                logger.error(f"Queue put error: {e}")

        consumer.commit()

def start_consumer_worker():
    multiprocessing.set_start_method("spawn", force=True)  # Đảm bảo Windows hoạt động đúng
    message_queue = multiprocessing.Queue()

    num_consumers = 2
    num_workers = 2
    processes = []

    # Khởi động consumer process
    for _ in range(num_consumers):
        p = multiprocessing.Process(target=consume_message, args=(message_queue,))
        p.start()
        processes.append(p)

    # Khởi động worker process xử lý MongoDB
    for _ in range(num_workers):
        p = multiprocessing.Process(target=consumer_worker, args=(message_queue,))
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.info("Stopping processes...")
    finally:
        for _ in range(num_workers):
            message_queue.put(None)  # Gửi tín hiệu dừng worker

        for p in processes:
            p.terminate()
            p.join()

if __name__ == "__main__":
    logger.info("Starting Kafka consumer with multiprocessing...")
    start_consumer_worker()
    logger.info("Stopping Kafka consumer...")
