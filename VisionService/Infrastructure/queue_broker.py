"""
RabbitMQ connection and queue management for Vision Service.
"""

import pika
import json
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime

from VisionService.Infrastructure.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RabbitMQBroker:
    """RabbitMQ connection manager for Vision Service."""

    # CHANGED: added retry-with-backoff. Previously a single failed
    # connection attempt raised immediately, which - combined with the
    # Dockerfile running the worker in the same process group as the API -
    # could take the whole container down if RabbitMQ wasn't reachable yet
    # at startup. Retrying here means the worker recovers on its own once
    # RabbitMQ comes up, instead of needing the whole pod to crash-loop.
    def __init__(self, max_retries: int = 5, retry_delay_seconds: float = 3.0):
        self.connection = None
        self.channel = None
        self._connect(max_retries=max_retries, retry_delay_seconds=retry_delay_seconds)

    def _connect(self, max_retries: int = 5, retry_delay_seconds: float = 3.0):
        """Establish connection to RabbitMQ, retrying with backoff."""
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASSWORD
        )
        parameters = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host='/',
            credentials=credentials,
            heartbeat=600
        )

        last_error: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()

                # Declare queues (durable = survive RabbitMQ restart)
                self.channel.queue_declare(
                    queue='vision.prediction.requests',
                    durable=True
                )
                self.channel.queue_declare(
                    queue='vision.prediction.results',
                    durable=True
                )

                logger.info(f"Connected to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
                return
            except Exception as e:
                last_error = e
                logger.warning(
                    f"RabbitMQ connection attempt {attempt}/{max_retries} failed: {e}"
                )
                if attempt < max_retries:
                    time.sleep(retry_delay_seconds)

        logger.error(f"Failed to connect to RabbitMQ after {max_retries} attempts: {last_error}")
        raise last_error
    
    def publish_request(self, request_id: str, image_path: str):
        """
        Publish a prediction request to the queue.
        
        Args:
            request_id: Unique request ID
            image_path: Path to the image file
        """
        try:
            message = {
                'request_id': request_id,
                'image_path': image_path,
                'timestamp': datetime.now().isoformat()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='vision.prediction.requests',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )
            logger.info(f"Published request: {request_id}")
        except Exception as e:
            logger.error(f"Failed to publish request: {e}")
            raise
    
    def publish_result(self, request_id: str, result: Dict[str, Any], processing_time: float):
        """
        Publish a prediction result to the results queue.
        
        Args:
            request_id: Unique request ID
            result: Prediction result dictionary
            processing_time: Time taken to process
        """
        try:
            message = {
                'request_id': request_id,
                'success': True,
                'result': result,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='vision.prediction.results',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            logger.info(f"Published result: {request_id}")
        except Exception as e:
            logger.error(f"Failed to publish result: {e}")
            raise
    
    def publish_error(self, request_id: str, error_message: str, processing_time: float):
        """
        Publish an error result to the results queue.
        
        Args:
            request_id: Unique request ID
            error_message: Error description
            processing_time: Time taken before failure
        """
        try:
            message = {
                'request_id': request_id,
                'success': False,
                'error': error_message,
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }
            
            self.channel.basic_publish(
                exchange='',
                routing_key='vision.prediction.results',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json'
                )
            )
            logger.info(f"Published error: {request_id}")
        except Exception as e:
            logger.error(f"Failed to publish error: {e}")
            raise
    
    def consume_requests(self, callback):
        """
        Consume prediction requests from the queue.
        
        Args:
            callback: Function to process requests
        """
        try:
            self.channel.basic_qos(prefetch_count=1)  # Process one at a time
            self.channel.basic_consume(
                queue='vision.prediction.requests',
                on_message_callback=callback,
                auto_ack=False
            )
            logger.info("Started consuming requests from queue")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Failed to consume requests: {e}")
            raise
    
    def close(self):
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("RabbitMQ connection closed")