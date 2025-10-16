# AI Assistant

Prefix: `/api/ai`

## POST /api/ai/chat
- Body: `{ message: string, conversation_history?: Array<object> }`
- Response: `{ response: string, sources: string[], timestamp: ISO8601 }`
- Notes: Uses Google Generative AI (Gemini). Pulls context from Events, Activities, Clubs, Leadership, Resources, Gallery, Announcements, News.

Example:
```bash
curl -X POST $BASE/api/ai/chat -H 'Content-Type: application/json' \
 -d '{"message":"What events are coming up?"}'
```

## GET /api/ai/health
Returns model availability, API key status.
