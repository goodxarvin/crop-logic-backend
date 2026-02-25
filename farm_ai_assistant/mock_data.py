"""
Static mock data for Farm AI Assistant API.
No database, no dynamic values. All responses are fixed JSON.
"""

CHAT_RESPONSE_DATA = {
    "message_id": "a-1739123456789",
    "conversation_id": "conv-abc123",
    "content": "",
    "sections": [
        {
            "type": "recommendation",
            "title": "Irrigation recommendation",
            "icon": "droplet",
            "frequency": "3 times per week",
            "amount": "15–20 L per plant",
            "timing": "Early morning (05:00–07:00)",
            "expandableExplanation": "Your loamy soil holds moisture well...",
        },
        {
            "type": "list",
            "title": "Key points",
            "icon": "leaf",
            "items": [
                "Avoid midday watering to reduce evaporation",
                "Drip irrigation preferred for root zone targeting",
            ],
        },
        {
            "type": "warning",
            "title": "Weather advisory",
            "icon": "warning",
            "content": "High temps forecasted next week. Consider increasing frequency.",
        },
    ],
}

CONTEXT_RESPONSE_DATA = {
    "soilType": "Loamy",
    "waterEC": "1.2 dS/m",
    "selectedCrop": "Tomato",
    "growthStage": "Flowering",
    "lastIrrigationStatus": "2 days ago",
}
