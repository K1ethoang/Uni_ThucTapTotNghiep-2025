import logging
from typing import Dict

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

        # Create
        if op == 'c':
            self.insert_one(collection_name, after)
        # Update
        elif op == 'u' or op == 'r':
            self.update_one(collection_name, before, after)
        # Delete
        elif op == 'd':
            self.remove_one(collection_name, after)

    def insert_one(self, collection_name: str, document: Dict) -> str:
        try:
            result = self.db[collection_name].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert document {document}: {str(e)}")
            raise

    def update_one(self, collection_name: str, before: Dict, after: Dict):
        try:
            if before is None:
                self.insert_one(collection_name, after)
            else:
                result = self.db[collection_name].update_one(
                    before, {"$set": after}, upsert=True
                )
                if result.matched_count:
                    logger.info(f"Updated document in {collection_name} where {before}")
                else:
                    logger.info(f"Inserted new document in {collection_name} due to upsert")
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
