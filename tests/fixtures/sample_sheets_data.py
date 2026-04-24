"""Sample Google Sheets data for testing"""

from typing import List, Dict


# Valid sheet data with all required columns
VALID_SHEET_DATA: List[List[str]] = [
    # Header row
    ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
    # Data rows
    [
        "registration",
        "Voter Registration Guide",
        "Learn how to register to vote in your area",
        "Visit the registration website|Fill out the online form|Submit your application|Wait for confirmation",
        "Valid government-issued ID|Proof of address (utility bill or lease)",
        "Register at least 30 days before election day|Double-check all information before submitting",
        "Check your email for confirmation within 7-10 business days"
    ],
    [
        "first_time_voter",
        "First Time Voter Guide",
        "Everything you need to know as a first-time voter",
        "Register to vote|Learn about the candidates|Find your polling location|Bring required documents|Cast your vote",
        "Valid ID|Voter registration confirmation",
        "Research candidates before election day|Arrive early to avoid long lines|Don't hesitate to ask poll workers for help",
        "Mark your calendar for election day and plan your visit"
    ],
    [
        "documents",
        "Required Voting Documents",
        "Documents you need to bring when voting",
        "Check your state's ID requirements|Prepare acceptable forms of identification|Bring backup documents if possible",
        "Driver's license|State ID card|Passport|Military ID|Student ID (in some states)",
        "Check if your state requires photo ID|Some states accept utility bills as ID|Keep documents in a safe place",
        "Verify your state's specific requirements on the official election website"
    ]
]


# Invalid sheet data (missing required columns)
INVALID_SHEET_DATA_MISSING_COLUMNS: List[List[str]] = [
    ["category", "title"],  # Missing required columns
    ["registration", "Voter Registration"]
]


# Invalid sheet data (missing required fields in rows)
INVALID_SHEET_DATA_MISSING_FIELDS: List[List[str]] = [
    ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
    ["", "No Category", "This row has no category", "Step 1", "Doc 1", "Tip 1", "Next"],  # Empty category
    ["registration", "", "No title", "Step 1", "Doc 1", "Tip 1", "Next"],  # Empty title
]


# Malformed sheet data (inconsistent column count)
MALFORMED_SHEET_DATA: List[List[str]] = [
    ["category", "title", "overview", "steps", "documents", "tips", "next_action"],
    ["registration", "Title"],  # Too few columns
    ["documents", "Title", "Overview", "Steps", "Docs", "Tips", "Next", "Extra"],  # Too many columns
]


def get_valid_parsed_data() -> Dict[str, Dict]:
    """Returns expected parsed data structure from valid sheet data"""
    return {
        "registration": {
            "category": "registration",
            "title": "Voter Registration Guide",
            "overview": "Learn how to register to vote in your area",
            "steps": [
                "Visit the registration website",
                "Fill out the online form",
                "Submit your application",
                "Wait for confirmation"
            ],
            "documents": [
                "Valid government-issued ID",
                "Proof of address (utility bill or lease)"
            ],
            "tips": [
                "Register at least 30 days before election day",
                "Double-check all information before submitting"
            ],
            "next_action": "Check your email for confirmation within 7-10 business days"
        },
        "first_time_voter": {
            "category": "first_time_voter",
            "title": "First Time Voter Guide",
            "overview": "Everything you need to know as a first-time voter",
            "steps": [
                "Register to vote",
                "Learn about the candidates",
                "Find your polling location",
                "Bring required documents",
                "Cast your vote"
            ],
            "documents": [
                "Valid ID",
                "Voter registration confirmation"
            ],
            "tips": [
                "Research candidates before election day",
                "Arrive early to avoid long lines",
                "Don't hesitate to ask poll workers for help"
            ],
            "next_action": "Mark your calendar for election day and plan your visit"
        },
        "documents": {
            "category": "documents",
            "title": "Required Voting Documents",
            "overview": "Documents you need to bring when voting",
            "steps": [
                "Check your state's ID requirements",
                "Prepare acceptable forms of identification",
                "Bring backup documents if possible"
            ],
            "documents": [
                "Driver's license",
                "State ID card",
                "Passport",
                "Military ID",
                "Student ID (in some states)"
            ],
            "tips": [
                "Check if your state requires photo ID",
                "Some states accept utility bills as ID",
                "Keep documents in a safe place"
            ],
            "next_action": "Verify your state's specific requirements on the official election website"
        }
    }
