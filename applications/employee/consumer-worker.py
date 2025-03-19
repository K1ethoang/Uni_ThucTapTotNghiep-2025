import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process
from threading import Thread, Event
from queue import Queue, Empty

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

consumer_config = {
    'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
    'group.id': settings.CONSUMER_GROUP_ID,
    'enable.auto.commit': False,  # Tắt auto commit để kiểm soát việc commit
    'auto.offset.reset': 'earliest',
}

def consumer_worker(message_queue, stop_event):
    """
    Worker xử lý message từ queue và cập nhật vào MongoDB.
    """
    mongo_db = MongoDb()
    while not stop_event.is_set():
        try:
            message = message_queue.get(timeout=1.0)  # Thêm timeout để kiểm tra stop_event
            # Xử lý message
            payload = json.loads(message)['payload']
            logger.info(f"Processing payload: {payload}")
            mongo_db.replicate_data(payload)

            # Sau khi xử lý thành công, đặt message.queue.task_done()
            message_queue.task_done()
        except Empty:
            continue  # Nếu queue rỗng, kiểm tra lại stop_event
        except Exception as e:
            logger.error(f"Worker error: {e}")

def consume_message(consumer, message_queue, stop_event):
    """
    Consumer nhận message từ Kafka và đưa vào queue.
    """
    while not stop_event.is_set():
        try:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"Kafka error: {msg.error()}")
                continue
            message_queue.put(msg.value().decode("utf-8"))

            # Đợi đến khi xử lý xong rồi mới commit offset
            message_queue.join()
            consumer.commit()
        except Exception as e:
            logger.error(f"Poll error: {e}")
            break
    consumer.close()

def start_consumer_worker():
    consumer = Consumer(consumer_config)
    consumer.subscribe(["^mysql\\.employees\\..*"])
    message_queue = Queue()
    stop_event = Event()  # Tạo Event để báo hiệu dừng

    try:
        # Khởi động consumer thread
        consumer_thread = Thread(target=consume_message, args=(consumer, message_queue, stop_event))
        consumer_thread.start()

        # Khởi động worker threads
        with ThreadPoolExecutor(max_workers=settings.KAFKA_TOTAL_THREAD) as executor:
            for _ in range(10):
                executor.submit(consumer_worker, message_queue, stop_event)

        consumer_thread.join()
    except KeyboardInterrupt:
        logger.info("Stop consumer worker")
        stop_event.set()  # Báo hiệu tất cả thread dừng
    finally:
        consumer.close()

if __name__ == "__main__":
    logger.info("Starting Kafka consumer...")
    processes = []

    # Khởi động các process
    for _ in range(settings.KAFKA_TOTAL_WORKER):
        p = Process(target=start_consumer_worker)
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.info("Stopping Kafka consumer due to KeyboardInterrupt...")
        for p in processes:
            p.terminate()  # Đảm bảo process dừng
            p.join()