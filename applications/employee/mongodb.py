import logging
from typing import Dict
from datetime import datetime, timedelta
from pymongo import MongoClient
from django.conf import settings

logger = logging.getLogger("")


class MongoDb:
    def __init__(self):
        try:
            self.client = MongoClient(
                host=settings.DB_MONGO_HOST,
                port=int(settings.DB_MONGO_PORT),
            )
            self.db = self.client[settings.DB_MONGO_DB]
        except Exception as e:
            logger.error(
                f'Fail to connect to MongoDB url {settings.DB_MONGO_HOST}:{settings.DB_MONGO_PORT}: {str(e)}')
            raise

    def __del__(self):
        self.close()

    def close(self):
        try:
            self.client.close()
        except Exception as e:
            logger.error(f"Failed to close MongoDB connection: {e}")
            raise

    def replicate_data(self, payload_kafka: Dict):
        op = payload_kafka.get('op')
        collection_name = payload_kafka.get('source', {}).get('table')
        before = payload_kafka.get('before', {})
        after = payload_kafka.get('after', {})

        if not collection_name:
            logger.error("Collection name is missing from Kafka payload")
            return

        # Chuyển đổi thời gian trước khi lưu vào MongoDB
        before = self._convert_dates(before)
        after = self._convert_dates(after)

        # Create
        if op == 'c' or op == 'r':
            self.insert_one(collection_name, after)
        # Update
        elif op == 'u':
            self.update_one(collection_name, before, after)
        # Delete
        elif op == 'd':
            self.remove_one(collection_name, before)

    def _convert_dates(self, document: Dict) -> Dict:
        """
        Chuyển đổi các trường from_date và to_date từ số ngày sang datetime.
        """
        if not document:
            return document

        for date_field in ["from_date", "to_date"]:
            if date_field in document and isinstance(document[date_field], int):
                document[date_field] = datetime(1970, 1, 1) + timedelta(days=document[date_field])

        return document

    def insert_one(self, collection_name: str, document: Dict) -> str:
        try:
            result = self.db[collection_name].insert_one(document)
            logger.info(f"Inserted new document in {collection_name} payload {document}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert document {document}: {str(e)}")
            raise

    def update_one(self, collection_name: str, before: Dict, after: Dict):
        try:
            if not before:
                self.insert_one(collection_name, after)
                return

            result = self.db[collection_name].update_one(
                before, {"$set": after}, upsert=False
            )
            if result.matched_count:
                logger.info(f"Updated document in {collection_name} where {before} to {after}")
            else:
                logger.warning(f"No matching document found for update: before {before} after {after}")
        except Exception as e:
            logger.error(f"Failed to update document in {collection_name}: {e}")
            raise

    def remove_one(self, collection_name: str, before: Dict):
        try:
            result = self.db[collection_name].delete_one(before)
            if result.deleted_count:
                logger.info(f"Deleted document from {collection_name} where {before}")
            else:
                logger.warning(f"No document found to delete in {collection_name} where {before}")
        except Exception as e:
            logger.error(f"Failed to delete document in {collection_name}: {e}")
            raise
