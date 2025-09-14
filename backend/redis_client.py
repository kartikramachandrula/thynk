# Created for Thynk: Always Ask Y
# Redis client configuration for Upstash

import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from upstash_redis import Redis
from dotenv import load_dotenv

load_dotenv()

class ThynkRedisClient:
    """Redis client for managing learning context in Thynk system"""
    
    def __init__(self):
        """Initialize Upstash Redis client"""
        self.redis_url = os.getenv("UPSTASH_REDIS_REST_URL")
        self.redis_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        
        if not self.redis_url or not self.redis_token:
            raise ValueError(
                "Missing Upstash Redis credentials. Please set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN in your .env file"
            )
        
        self.client = Redis(url=self.redis_url, token=self.redis_token)
        
        # Key prefixes for organization
        self.CONTEXT_PREFIX = "thynk:context:"
        self.METADATA_PREFIX = "thynk:meta:"
        
    def _get_context_key(self, user_id: str = "default") -> str:
        """Generate context key for user"""
        return f"{self.CONTEXT_PREFIX}{user_id}"
    
    def _get_metadata_key(self, user_id: str = "default") -> str:
        """Generate metadata key for user"""
        return f"{self.METADATA_PREFIX}{user_id}"
    
    async def store_context(self, context: str, user_id: str = "default") -> bool:
        """Store learning context with timestamp"""
        try:
            timestamp = time.time()
            context_data = {
                "content": context,
                "timestamp": timestamp,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store in a sorted set with timestamp as score for easy retrieval by recency
            context_key = self._get_context_key(user_id)
            context_id = f"ctx_{int(timestamp * 1000)}"  # Unique ID with millisecond precision
            
            # Store the context data
            await self.client.hset(context_key, {context_id: json.dumps(context_data)})
            
            # Also maintain a sorted set for easy time-based queries
            sorted_key = f"{context_key}:sorted"
            await self.client.zadd(sorted_key, {context_id: timestamp})
            
            # Update metadata
            meta_key = self._get_metadata_key(user_id)
            await self.client.hincrby(meta_key, "total_entries", 1)
            await self.client.hset(meta_key, {"last_updated": timestamp})
            
            return True
            
        except Exception as e:
            print(f"Error storing context: {e}")
            return False
    
    async def get_recent_context(self, user_id: str = "default", max_entries: int = 10) -> List[Dict[str, Any]]:
        """Get recent context entries, weighted by recency"""
        try:
            context_key = self._get_context_key(user_id)
            sorted_key = f"{context_key}:sorted"
            
            # Get most recent context IDs
            recent_ids = await self.client.zrevrange(sorted_key, 0, max_entries - 1)
            
            if not recent_ids:
                return []
            
            # Retrieve context data
            context_data = []
            for ctx_id in recent_ids:
                ctx_json = await self.client.hget(context_key, ctx_id)
                if ctx_json:
                    ctx = json.loads(ctx_json)
                    context_data.append(ctx)
            
            return context_data
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    async def get_context_summary(self, user_id: str = "default") -> Dict[str, Any]:
        """Get summary of stored context"""
        try:
            meta_key = self._get_metadata_key(user_id)
            metadata = await self.client.hgetall(meta_key)
            
            total_entries = int(metadata.get("total_entries", 0))
            last_updated = float(metadata.get("last_updated", 0))
            
            return {
                "total_entries": total_entries,
                "last_updated": datetime.fromtimestamp(last_updated, timezone.utc).isoformat() if last_updated else None,
                "user_id": user_id
            }
            
        except Exception as e:
            print(f"Error getting context summary: {e}")
            return {"total_entries": 0, "last_updated": None, "user_id": user_id}
    
    async def clear_context(self, user_id: str = "default") -> bool:
        """Clear all context for a user (useful for testing)"""
        try:
            context_key = self._get_context_key(user_id)
            sorted_key = f"{context_key}:sorted"
            meta_key = self._get_metadata_key(user_id)
            
            await self.client.delete(context_key)
            await self.client.delete(sorted_key)
            await self.client.delete(meta_key)
            
            return True
            
        except Exception as e:
            print(f"Error clearing context: {e}")
            return False

# Global Redis client instance
redis_client = ThynkRedisClient()