"""
Static mock data for Farm AI Assistant API.
"""

CHAT_RESPONSE_DATA = {
    "message_id": "msg-001",
    "conversation_id": "conv-123",
    "content": "Here is the recommended plan.",
    "sections": [
        {
            "type": "recommendation",
            "title": "Irrigation Plan",
            "icon": "droplet",
            "frequency": "3 times per week",
            "amount": "15 liters per plant",
            "timing": "Early morning",
            "expandableExplanation": "Loamy soil holds moisture well, so moderate frequency is enough.",
        },
        {
            "type": "list",
            "title": "Important Notes",
            "icon": "leaf",
            "items": [
                "Avoid watering at noon",
                "Check leaf stress every two days",
            ],
        },
        {
            "type": "warning",
            "title": "Heat Alert",
            "icon": "warning",
            "content": "Increase irrigation if temperature rises above 35°C.",
        },
    ],
}

CHAT_LIST_RESPONSE_DATA = [
    {
        "id": "conv-123",
        "message_count": 4,
    },
    {
        "id": "conv-456",
        "message_count": 2,
    },
]

CHAT_MESSAGES_RESPONSE_DATA = {
    "conversation_id": "conv-123",
    "messages": [
        {
            "message_id": "msg-user-001",
            "conversation_id": "conv-123",
            "role": "user",
            "content": "What is the best irrigation plan for tomato?",
            "sections": [],
            "images": [],
            "created_at": "2025-01-01T08:00:00Z",
        },
        {
            "message_id": "msg-001",
            "conversation_id": "conv-123",
            "role": "assistant",
            "content": "Here is the recommended plan.",
            "sections": CHAT_RESPONSE_DATA["sections"],
            "images": [],
            "created_at": "2025-01-01T08:00:05Z",
        },
    ],
}

CHAT_CREATE_RESPONSE_DATA = {
    "id": "conv-789",
    "message_count": 0,
}

CHAT_DELETE_RESPONSE_DATA = {
    "conversation_id": "conv-123",
}

CONTEXT_RESPONSE_DATA = {
    "soilType": "Loamy",
    "waterEC": "1.2 dS/m",
    "selectedCrop": "Tomato",
    "growthStage": "Flowering",
    "lastIrrigationStatus": "2 days ago",
}
