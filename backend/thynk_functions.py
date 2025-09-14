# Created for Thynk: Always Ask Y
# Core functions for learning context management

import json
import time
import difflib
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import anthropic
import os
from dotenv import load_dotenv

from redis_client import redis_client

load_dotenv()

# Initialize Anthropic async client
anthropic_client = anthropic.AsyncAnthropic(api_key=os.getenv("CLAUDE_KEY"))

# Store previous content for comparison
_previous_content: Dict[str, str] = {}

def is_different(current_content: Dict[str, str], user_id: str = "default", threshold: float = 0.3) -> Dict[str, Any]:
    """
    Determine if current content is different enough from previous content to warrant processing.
    
    Args:
        current_content: Dictionary with "text" key containing the learned content
        user_id: User identifier for tracking content changes
        threshold: Similarity threshold (0.0 = completely different, 1.0 = identical)
    
    Returns:
        Dictionary with "text" key and "learned" value containing the content
    """
    global _previous_content
    
    try:
        current_text = current_content.get("text", "")
        previous_text = _previous_content.get(user_id, "")
        
        if not current_text.strip():
            return {"text": ""}
        
        if not previous_text:
            # First time seeing content for this user
            _previous_content[user_id] = current_text
            return {"text": current_text}
        
        # Calculate similarity using difflib
        similarity = difflib.SequenceMatcher(None, previous_text, current_text).ratio()
        
        # If content is different enough, update and return it
        if similarity < (1.0 - threshold):
            _previous_content[user_id] = current_text
            return {"text": current_text}
        else:
            # Content too similar, return empty
            return {"text": ""}
            
    except Exception as e:
        print(f"Error in is_different: {e}")
        return {"text": ""}

async def context_compression(content_data: Dict[str, str], user_id: str = "default") -> None:
    """
    Compress and store relevant learning information using Claude.
    
    Args:
        content_data: Dictionary with "text" key containing learned content
        user_id: User identifier for context storage
    """
    try:
        learned_content = content_data.get("text", "")
        
        if not learned_content.strip():
            return
        
        # Use Claude to extract and compress relevant educational information
        compression_prompt = f"""You are an AI tutor assistant analyzing student work and learning materials. 

Your task is to extract and summarize only the most important and educationally relevant information from the following content. This content comes from images of student work, textbooks, or study materials.

Focus on:
- Mathematical problems, equations, and solution steps
- Key concepts, theorems, or formulas being studied
- Student's work progress and problem-solving approaches
- Educational content that would be useful for providing hints or guidance

Ignore:
- Irrelevant background objects or text
- Non-educational content
- Unclear or garbled text from OCR errors
- Personal information or distracting elements

Content to analyze:
{learned_content}

Provide a concise summary (2-3 sentences max) of the most educationally relevant information, or respond with "No relevant educational content found" if there's nothing useful for tutoring purposes."""

        try:
            response = await anthropic_client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=150,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": compression_prompt}
                ]
            )
            
            compressed_content = response.content[0].text.strip()
            
            # Only store if Claude found relevant educational content
            if compressed_content and not compressed_content.lower().startswith("no relevant"):
                success = await redis_client.store_context(compressed_content, user_id)
                if success:
                    print(f"Stored compressed context for user {user_id}: {compressed_content[:100]}...")
                else:
                    print(f"Failed to store context for user {user_id}")
            else:
                print(f"No relevant educational content found for user {user_id}")
                
        except Exception as claude_error:
            print(f"Error calling Claude API: {claude_error}")
            # Fallback: store original content if Claude fails
            await redis_client.store_context(learned_content[:200], user_id)
            
    except Exception as e:
        print(f"Error in context_compression: {e}")

async def get_context(user_id: str = "default", max_entries: int = 10) -> Dict[str, Any]:
    """
    Retrieve and weight context based on recency for providing educational hints.
    
    Args:
        user_id: User identifier
        max_entries: Maximum number of context entries to retrieve
    
    Returns:
        Dictionary with "entries" count and "context" string of weighted information
    """
    try:
        # Get recent context entries
        recent_contexts = await redis_client.get_recent_context(user_id, max_entries)
        
        if not recent_contexts:
            return {"entries": 0, "context": "No previous learning context available."}
        
        # Weight contexts by recency (more recent = higher weight)
        current_time = time.time()
        weighted_contexts = []
        
        for ctx in recent_contexts:
            timestamp = ctx.get("timestamp", current_time)
            age_hours = (current_time - timestamp) / 3600  # Age in hours
            
            # Exponential decay: recent content gets higher weight
            weight = max(0.1, 1.0 / (1.0 + age_hours * 0.5))  # Decays over ~4 hours
            
            weighted_contexts.append({
                "content": ctx.get("content", ""),
                "weight": weight,
                "age_hours": age_hours
            })
        
        # Sort by weight (most relevant first)
        weighted_contexts.sort(key=lambda x: x["weight"], reverse=True)
        
        # Combine contexts with weight indicators
        context_parts = []
        for i, ctx in enumerate(weighted_contexts):
            if ctx["content"].strip():
                age_indicator = "recent" if ctx["age_hours"] < 1 else "earlier"
                context_parts.append(f"[{age_indicator}] {ctx['content']}")
        
        combined_context = " | ".join(context_parts) if context_parts else "No relevant context available."
        
        return {
            "entries": len(recent_contexts),
            "context": combined_context
        }
        
    except Exception as e:
        print(f"Error in get_context: {e}")
        return {"entries": 0, "context": "Error retrieving context."}

async def give_hint(learned_context: str, user_question: str = "") -> str:
    """
    Generate a helpful hint using the learned context and Claude.
    
    Args:
        learned_context: Context from user's learning session
        user_question: Optional specific question from the user
    
    Returns:
        Markdown-formatted hint string for display on frontend
    """
    try:
        # Get weighted context including lecture transcriptions with exponential decay
        weighted_context = await redis_client.get_weighted_context(
            user_id="default", 
            max_entries=50, 
            include_lectures=True, 
            lecture_base_weight=0.3,
            decay_factor=0.1
        )
        
        # Build context string with exponential decay weights for the AI
        context_parts = []
        for ctx in weighted_context:
            # Use exponential decay weight to determine priority
            if ctx['weight'] >= 0.8:
                weight_indicator = "[CRITICAL]"
            elif ctx['weight'] >= 0.5:
                weight_indicator = "[HIGH PRIORITY]"
            elif ctx['weight'] >= 0.2:
                weight_indicator = "[MEDIUM]"
            else:
                weight_indicator = "[BACKGROUND]"
            
            source_type = ctx.get('source', 'unknown')
            weight_score = f"w={ctx['weight']:.2f}"
            context_parts.append(f"{weight_indicator} ({source_type}, {weight_score}): {ctx['content']}")
        
        stored_context = "\n\n".join(context_parts) if context_parts else "No previous context available."
        
        # Add context summary for the AI
        context_summary = f"\n\n[CONTEXT SUMMARY: {len(weighted_context)} entries retrieved with exponential decay weighting]"
        
        # Combine stored context with any immediate context
        full_context = f"{stored_context}{context_summary}\n\n[CURRENT SESSION]: {learned_context}" if learned_context else f"{stored_context}{context_summary}"
        
        # Build the hint generation prompt
        hint_prompt = f"""You are Thynk, an encouraging AI tutor that helps students learn math step-by-step. Your motto is "Always Ask Y" - meaning you help students discover answers through guided questions rather than giving direct solutions.

Based on the learning context below, provide a helpful hint for the next step. Your hint should:

1. **Be encouraging and supportive**
2. **Guide rather than solve** - ask leading questions or give gentle nudges
3. **Focus on the immediate next step**, not the entire solution
4. **Use clear, student-friendly language**
5. **Format your response in markdown** for web display

Learning Context:
{full_context}

{"User's specific question: " + user_question if user_question else ""}

Provide your hint in markdown format, keeping it concise but helpful (2-4 sentences max):"""

        try:
            response = await anthropic_client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=300,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": hint_prompt}
                ]
            )
            
            hint_text = response.content[0].text.strip()
            
            # Ensure it's properly formatted
            if not hint_text.startswith("#") and not hint_text.startswith("*"):
                hint_text = f"💡 **Hint:** {hint_text}"
            
            return hint_text
            
        except Exception as claude_error:
            print(f"Error calling Claude for hint: {claude_error}")
            return "💡 **Hint:** I'm having trouble generating a hint right now. Try breaking down the problem into smaller steps and focus on what you know so far!"
            
    except Exception as e:
        print(f"Error in give_hint: {e}")
        return "💡 **Hint:** Keep going! Look at what you've written so far and think about the next logical step."