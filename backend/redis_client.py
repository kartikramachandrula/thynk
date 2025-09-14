# Created for Thynk: Always Ask Y
# Redis client configuration for Upstash

import os
import json
import time
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from upstash_redis.asyncio import Redis
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
        self.LECTURE_PREFIX = "thynk:lecture:"
        self.METADATA_PREFIX = "thynk:meta:"
        
    def _get_context_key(self, user_id: str = "default") -> str:
        """Generate context key for user"""
        return f"{self.CONTEXT_PREFIX}{user_id}"
    
    def _get_lecture_key(self, user_id: str = "default") -> str:
        """Generate lecture transcription key for user"""
        return f"{self.LECTURE_PREFIX}{user_id}"
    
    def _get_metadata_key(self, user_id: str = "default") -> str:
        """Generate metadata key for user"""
        return f"{self.METADATA_PREFIX}{user_id}"
    
    async def store_context(self, context: str, user_id: str = "default", context_type: str = "general") -> bool:
        """Store learning context with timestamp and type"""
        try:
            timestamp = time.time()
            context_data = {
                "content": context,
                "timestamp": timestamp,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "type": context_type
            }
            
            # Store in a sorted set with timestamp as score for easy retrieval by recency
            context_key = self._get_context_key(user_id)
            context_id = f"ctx_{int(timestamp * 1000)}"  # Unique ID with millisecond precision
            
            # Store the context data
            await self.client.hset(context_key, context_id, json.dumps(context_data))
            
            # Also maintain a sorted set for easy time-based queries
            sorted_key = f"{context_key}:sorted"
            await self.client.zadd(sorted_key, {context_id: timestamp})
            
            # Update metadata
            meta_key = self._get_metadata_key(user_id)
            await self.client.hincrby(meta_key, "total_entries", 1)
            await self.client.hset(meta_key, "last_updated", timestamp)
            
            return True
            
        except Exception as e:
            print(f"Error storing context: {e}")
            return False
    
    async def store_lecture_transcription(self, transcription: str, user_id: str = "default", confidence: float = 0.8) -> bool:
        """Store lecture transcription with timestamp and confidence"""
        try:
            timestamp = time.time()
            lecture_data = {
                "content": transcription,
                "timestamp": timestamp,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "type": "lecture",
                "confidence": confidence
            }
            
            # Store in lecture-specific key
            lecture_key = self._get_lecture_key(user_id)
            lecture_id = f"lec_{int(timestamp * 1000)}"  # Unique ID with millisecond precision
            
            # Store the lecture data
            await self.client.hset(lecture_key, lecture_id, json.dumps(lecture_data))
            
            # Also maintain a sorted set for easy time-based queries
            sorted_key = f"{lecture_key}:sorted"
            await self.client.zadd(sorted_key, {lecture_id: timestamp})
            
            # Update metadata
            meta_key = self._get_metadata_key(user_id)
            await self.client.hincrby(meta_key, "lecture_entries", 1)
            await self.client.hset(meta_key, "last_lecture_updated", timestamp)
            
            return True
            
        except Exception as e:
            print(f"Error storing lecture transcription: {e}")
            return False
    
    async def get_weighted_context(self, user_id: str = "default", max_entries: int = 50, include_lectures: bool = True, lecture_base_weight: float = 0.3, decay_factor: float = 0.1) -> List[Dict[str, Any]]:
        """Get context entries with exponential decay weighting based on recency"""
        try:
            all_context = []
            current_time = time.time()
            
            # Get general context entries
            context_key = self._get_context_key(user_id)
            sorted_key = f"{context_key}:sorted"
            
            # Get more entries to apply decay weighting (up to 70% of max for general context)
            general_limit = max_entries if not include_lectures else int(max_entries * 0.7)
            recent_ids = await self.client.zrevrange(sorted_key, 0, general_limit - 1)
            
            # Retrieve general context data with exponential decay weighting
            for i, ctx_id in enumerate(recent_ids):
                ctx_json = await self.client.hget(context_key, ctx_id)
                if ctx_json:
                    ctx = json.loads(ctx_json)
                    # Calculate exponential decay based on position (more recent = higher weight)
                    decay_weight = math.exp(-decay_factor * i)
                    ctx['weight'] = decay_weight
                    ctx['source'] = 'context'
                    ctx['position'] = i
                    all_context.append(ctx)
            
            # Get lecture transcriptions if requested
            if include_lectures:
                lecture_key = self._get_lecture_key(user_id)
                lecture_sorted_key = f"{lecture_key}:sorted"
                
                # Get lecture entries (remaining 30% of max entries)
                lecture_limit = max_entries - len(all_context)
                lecture_ids = await self.client.zrevrange(lecture_sorted_key, 0, lecture_limit - 1)
                
                # Retrieve lecture data with exponential decay + base weight reduction
                for i, lec_id in enumerate(lecture_ids):
                    lec_json = await self.client.hget(lecture_key, lec_id)
                    if lec_json:
                        lec = json.loads(lec_json)
                        # Apply both exponential decay and lecture base weight
                        decay_weight = math.exp(-decay_factor * i)
                        lec['weight'] = decay_weight * lecture_base_weight
                        lec['source'] = 'lecture'
                        lec['position'] = i
                        all_context.append(lec)
            
            # Sort by weight (highest first), then by timestamp for ties
            all_context.sort(key=lambda x: (x['weight'], x['timestamp']), reverse=True)
            return all_context[:max_entries]
            
        except Exception as e:
            print(f"Error retrieving weighted context: {e}")
            return []
    
    async def get_recent_context(self, user_id: str = "default", max_entries: int = 10) -> List[Dict[str, Any]]:
        """Get recent context entries (backward compatibility)"""
        return await self.get_weighted_context(user_id, max_entries, include_lectures=False)
    
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
    
    async def clear_context(self, user_id: str = "default", clear_lectures: bool = False) -> bool:
        """Clear context for a user (useful for testing)"""
        try:
            context_key = self._get_context_key(user_id)
            sorted_key = f"{context_key}:sorted"
            meta_key = self._get_metadata_key(user_id)
            
            await self.client.delete(context_key)
            await self.client.delete(sorted_key)
            
            if clear_lectures:
                lecture_key = self._get_lecture_key(user_id)
                lecture_sorted_key = f"{lecture_key}:sorted"
                await self.client.delete(lecture_key)
                await self.client.delete(lecture_sorted_key)
            
            await self.client.delete(meta_key)
            
            return True
            
        except Exception as e:
            print(f"Error clearing context: {e}")
            return False

# Global Redis client instance
redis_client = ThynkRedisClient()