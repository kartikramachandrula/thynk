# Thynk: Always Ask Y - Setup Guide

## Overview

Thynk is an AI-powered tutoring system that helps students learn math by monitoring their work through smart glasses, analyzing the content, and providing contextual hints. The system uses Redis for context storage and Claude for intelligent content processing.

## Required Environment Variables

### 1. Anthropic Claude API
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```
- Get your API key from: https://console.anthropic.com/
- Used for context compression and hint generation

### 2. Upstash Redis (Required)
```bash
UPSTASH_REDIS_REST_URL=https://your-redis-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_redis_token_here
```
- Create a free Redis database at: https://console.upstash.com/
- Go to your database → REST API tab to get these values

## System Architecture

### Core Functions

1. **`is_different(content, user_id)`**
   - Compares new content with previously seen content
   - Returns content only if it's different enough (>30% change)
   - Prevents redundant processing

2. **`context_compression(content_data, user_id)`**
   - Uses Claude to extract educationally relevant information
   - Filters out irrelevant content (background objects, etc.)
   - Stores compressed context in Redis with timestamp

3. **`get_context(user_id, max_entries)`**
   - Retrieves recent learning context from Redis
   - Applies exponential decay weighting (recent content = higher weight)
   - Returns weighted context string for hint generation

4. **`give_hint(learned_context, user_question)`**
   - Generates encouraging, step-by-step hints using Claude
   - Uses "Always Ask Y" philosophy (guide, don't solve)
   - Returns markdown-formatted response for frontend

### API Endpoints

#### Main Endpoints
- **POST `/give-hint`** - Generate hints (main frontend endpoint)
- **POST `/analyze-photo`** - OCR + Thynk processing (glasses integration)

#### Testing/Debug Endpoints
- **GET `/context_status`** - View stored context
- **POST `/context-compression`** - Manually compress content
- **GET `/get-context`** - Retrieve current context
- **POST `/is-different`** - Test content difference detection
- **DELETE `/clear-context`** - Clear all stored context

## Integration Flow

1. **Smart Glasses** → Take photo → Send to `/analyze-photo`
2. **OCR Processing** → Extract text from image
3. **Content Analysis** → `is_different()` checks if content changed
4. **Context Storage** → `context_compression()` stores relevant info in Redis
5. **User Request** → Frontend calls `/give-hint` with user question
6. **Hint Generation** → `get_context()` + `give_hint()` → Return markdown hint

## Frontend Integration

The frontend should call the `/give-hint` endpoint when users:
- Click "Get Hint" button
- Ask voice questions (already implemented in glasses app)

```javascript
const response = await fetch('/give-hint', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    learned: userQuestion,
    question: optionalSpecificQuestion
  })
});

const { hint } = await response.json();
// Display hint as markdown in UI
```

## Data Flow

```
Smart Glasses → OCR → is_different() → context_compression() → Redis
                                                                  ↓
Frontend "Get Hint" → give_hint() ← get_context() ← Redis
```

## Testing

1. **Test OCR + Context Storage:**
   ```bash
   curl -X POST "http://localhost:8000/analyze-photo" \
     -H "Content-Type: application/json" \
     -d '{"image_base64": "base64_encoded_image"}'
   ```

2. **Test Hint Generation:**
   ```bash
   curl -X POST "http://localhost:8000/give-hint" \
     -H "Content-Type: application/json" \
     -d '{"learned": "I need help with algebra", "question": "How do I solve x + 5 = 10?"}'
   ```

3. **Check Context Status:**
   ```bash
   curl "http://localhost:8000/context_status"
   ```

## Error Handling

- System gracefully handles missing Redis/Claude connections
- OCR continues to work even if Thynk processing fails
- Fallback hints provided when AI services are unavailable
- All errors logged for debugging

## Performance Considerations

- Context is weighted by recency (exponential decay over ~4 hours)
- Redis stores compressed context (not raw OCR text)
- Maximum 10 context entries retrieved per hint request
- Claude calls limited to 150-300 tokens for cost efficiency