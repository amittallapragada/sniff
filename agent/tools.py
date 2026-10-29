"""
Tool definitions for Sniff's capabilities.
Each tool here maps to a dispatcher in agent/core.py.
"""

PLACE_CALL = {
    "name": "place_call",
    "description": (
        "Place an outbound phone call on behalf of the user to complete a mission "
        "such as making a reservation, scheduling an appointment, or handling an errand. "
        "NEVER call this without explicit user approval. Always confirm the plan first and "
        "wait for the user to say yes before placing the call."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "phone_number": {
                "type": "string",
                "description": "The phone number to call in E.164 format, e.g. +12125551234",
            },
            "mission": {
                "type": "string",
                "description": "Clear description of what to accomplish on the call.",
            },
            "context": {
                "type": "string",
                "description": "Any additional context the agent needs (date, party size, preferences, etc.)",
            },
        },
        "required": ["phone_number", "mission"],
    },
}

WEB_SEARCH = {
    "name": "web_search",
    "description": (
        "Search the web and return a list of links with snippets. Good for factual questions, "
        "looking up businesses, checking hours, news, reviews, or general research. "
        "NOT good for flights, hotels, or shopping — use scrappa_search for those. "
        "This is fast and free — use it for information lookups, not price comparisons."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query. Be specific — include dates, locations, and details.",
            },
        },
        "required": ["query"],
    },
}

SCRAPPA_SEARCH = {
    "name": "scrappa_search",
    "description": (
        "Fetches structured, real-time web data via the Scrappa API (https://scrappa.co/api). "
        "Supports 80+ scraping endpoints across major platforms including:\n"
        "- SERP & Search: Google Search, Startpage, Brave Search, Google Finance\n"
        "- Travel & Hospitality: Google Hotels, Booking.com, Tripadvisor, Google Flights\n"
        "- E-Commerce & Shopping: Google Shopping, Vinted\n"
        "- Jobs & Professional: LinkedIn (Jobs/Profiles), Indeed, Google Jobs\n"
        "- Reviews & Media: Trustpilot, YouTube, Substack\n"
        "- Real Estate: LoopNet, Otodom\n\n"
        "WHEN TO USE: Trigger ONLY when the query requires live web searches, real-time prices, "
        "job listings, review aggregation, current stock quotes, or platform-specific structured data.\n"
        "WHEN NOT TO USE: Do NOT trigger for static general knowledge, coding assistance, math, "
        "creative writing, or questions that do not require live web data."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "platform": {
                "type": "string",
                "enum": [
                    "google_search",
                    "google_maps",
                    "google_flights",
                    "google_hotels",
                    "google_shopping",
                    "linkedin",
                    "indeed",
                    "youtube",
                    "trustpilot",
                    "tripadvisor",
                    "booking",
                    "substack",
                    "loopnet",
                    "otodom",
                    "generic_web",
                ],
                "description": "The category/platform of data required to answer the query.",
            },
            "endpoint": {
                "type": "string",
                "description": "The target API path (e.g., 'search', 'flights/v2/round-trip', 'tripadvisor/search', 'substack/post').",
            },
            "params": {
                "type": "object",
                "description": "Key-value parameters strictly matching the requested endpoint requirements.",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Free text search string, product name, business title, or keyword.",
                    },
                    "origin": {
                        "type": "string",
                        "description": "3-letter IATA departure code (e.g., 'JFK', 'SFO') for flight queries.",
                    },
                    "destination": {
                        "type": "string",
                        "description": "3-letter IATA arrival code (e.g., 'LHR', 'CDG') for flight queries.",
                    },
                    "departure_date": {
                        "type": "string",
                        "description": "Date strictly in YYYY-MM-DD format.",
                    },
                    "return_date": {
                        "type": "string",
                        "description": "Return date strictly in YYYY-MM-DD format.",
                    },
                    "location": {
                        "type": "string",
                        "description": "City, ZIP code, or region for localized jobs, real estate, or business searches.",
                    },
                    "url": {
                        "type": "string",
                        "description": "Direct canonical URL or slug when scraping specific posts or listing pages.",
                    },
                },
                "required": ["query"],
            },
        },
        "required": ["platform", "endpoint", "params"],
    },
}

BROWSE_WEB = {
    "name": "browse_web",
    "description": (
        "LAST RESORT — slow and expensive (takes minutes, costs money). "
        "Launch a browser ONLY for tasks that REQUIRE clicking buttons, filling forms, "
        "or making purchases on a specific site. "
        "Do NOT use for research, planning, trip planning, finding information, or anything "
        "you can answer with web_search, scrappa_search, or your own knowledge. "
        "Always provide a start_url. Keep the task focused on ONE simple action."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": (
                    "A specific, single action on a website. Be precise about what to click or fill. "
                    "Example: 'Go to the checkout page and apply promo code SAVE20.'"
                ),
            },
            "start_url": {
                "type": "string",
                "description": "URL to start from. Always provide this. E.g. https://www.google.com/flights",
            },
        },
        "required": ["task", "start_url"],
    },
}

REMEMBER = {
    "name": "remember",
    "description": (
        "Store a preference, fact, or piece of context about the user for future recall. "
        "Use this when the user shares something worth remembering long-term."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The fact or preference to remember.",
            },
        },
        "required": ["content"],
    },
}

ALL_TOOLS = [PLACE_CALL, WEB_SEARCH, SCRAPPA_SEARCH, BROWSE_WEB, REMEMBER]
