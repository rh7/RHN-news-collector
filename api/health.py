"""Health check endpoint for monitoring"""
from datetime import datetime


def handler(request):
    """Simple health check"""
    return {
        'statusCode': 200,
        'body': {
            'status': 'healthy',
            'service': 'news-collector',
            'timestamp': datetime.utcnow().isoformat()
        }
    }


