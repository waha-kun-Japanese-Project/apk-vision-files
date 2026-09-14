"""
RabbitMQ connection and queue management for Vision Service.
"""

import pika
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from Infrastructure.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RabbitMQBroker:
    """RabbitMQ connection manager for Vision Service."""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self._connect()
    
    def _connect(self):
        """Establish connection to RabbitMQ."""
        try:
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
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
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