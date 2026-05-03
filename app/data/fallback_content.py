"""Bundled fallback content for all intent categories"""

from typing import Dict

FALLBACK_DATA: Dict[str, Dict] = {
    "first_time_voter": {
        "title": "First Time Voter Guide",
        "overview": "Welcome! Voting for the first time is an exciting step in participating in democracy. This guide will walk you through everything you need to know to cast your vote confidently.",
        "steps": [
            "Check if you are registered to vote in your area",
            "Verify your polling station location and hours",
            "Gather required identification documents",
            "Review the candidates and ballot measures beforehand",
            "Arrive at your polling station during voting hours",
            "Present your ID and receive your ballot",
            "Mark your choices carefully and privately",
            "Submit your completed ballot to election officials"
        ],
        "documents": [
            "Valid government-issued photo ID (driver's license, passport, or national ID card)",
            "Voter registration confirmation (if available)",
            "Proof of address (utility bill or bank statement if required)"
        ],
        "tips": [
            "Research candidates and issues before election day",
            "Bring a sample ballot or notes to help you remember your choices",
            "Ask poll workers if you have any questions - they're there to help",
            "Double-check your ballot before submitting to ensure accuracy",
            "Polls can be busy during morning and evening rush hours - consider voting mid-day"
        ],
        "next_action": "Verify your voter registration status and locate your assigned polling station"
    },

    "registration": {
        "title": "Voter Registration Process",
        "overview": "Registering to vote is the first step to participating in elections. The process is straightforward and can often be completed online, by mail, or in person.",
        "steps": [
            "Check eligibility requirements (age, citizenship, residency)",
            "Gather required documents (ID, proof of address)",
            "Choose registration method (online, mail, or in-person)",
            "Complete the voter registration form accurately",
            "Submit your application before the registration deadline",
            "Wait for confirmation of your registration",
            "Verify your registration status online before election day"
        ],
        "documents": [
            "Proof of identity (driver's license, passport, or national ID)",
            "Proof of address (utility bill, lease agreement, or bank statement)",
            "Social security number or national identification number",
            "Date of birth documentation"
        ],
        "tips": [
            "Register well before the deadline to avoid last-minute issues",
            "Keep a copy of your registration confirmation for your records",
            "Update your registration if you move or change your name",
            "Check your registration status periodically to ensure it's active",
            "Some areas offer same-day registration at polling places"
        ],
        "next_action": "Visit your local election office website or national voter registration portal to begin the registration process"
    },

    "documents": {
        "title": "Required Identification Documents",
        "overview": "Different jurisdictions have varying ID requirements for voting. Understanding what documents you need will ensure a smooth voting experience.",
        "steps": [
            "Check your local election authority's ID requirements",
            "Verify that your ID is current and not expired",
            "Ensure your name on the ID matches your voter registration",
            "Prepare backup forms of identification if available",
            "Bring your documents to the polling station on election day"
        ],
        "documents": [
            "Government-issued photo ID (driver's license, passport, state ID card)",
            "Voter registration card or confirmation letter",
            "Utility bill or bank statement with your name and address",
            "Student ID with photo (accepted in some jurisdictions)",
            "Military ID or veteran's card",
            "Tribal ID card (if applicable)"
        ],
        "tips": [
            "Check ID requirements specific to your state or region",
            "Renew expired IDs well before election day",
            "If you don't have required ID, ask about alternative options or affidavit procedures",
            "Some jurisdictions offer free voter ID cards",
            "Keep your documents in a safe place leading up to election day"
        ],
        "next_action": "Verify your ID meets local requirements and renew any expired documents"
    },

    "correction": {
        "title": "Correcting Voter Registration Errors",
        "overview": "Mistakes in voter registration can happen. Whether it's a name change, address update, or other error, corrections can be made to ensure your information is accurate.",
        "steps": [
            "Identify the error in your registration (name, address, party affiliation, etc.)",
            "Gather supporting documents for the correction",
            "Access the voter registration update form online or in person",
            "Complete the correction form with accurate information",
            "Submit the form with required documentation",
            "Wait for confirmation of the update",
            "Verify the correction was processed before election day"
        ],
        "documents": [
            "Current voter registration information",
            "Proof of correct information (updated ID, marriage certificate, court order for name changes)",
            "Proof of new address (lease, utility bill, or bank statement)",
            "Completed voter registration update form"
        ],
        "tips": [
            "Make corrections as soon as you notice an error",
            "Keep records of your correction submission",
            "Follow up if you don't receive confirmation within the expected timeframe",
            "Some changes can be made online, while others require in-person visits",
            "Deadlines for corrections may differ from initial registration deadlines"
        ],
        "next_action": "Contact your local election office or visit their website to access the registration correction form"
    },

    "status_check": {
        "title": "Check Your Voter Registration Status",
        "overview": "Verifying your voter registration status ensures you're ready to vote on election day. Most jurisdictions offer online tools to check your status quickly.",
        "steps": [
            "Visit your local election authority's website or national voter portal",
            "Locate the voter registration status check tool",
            "Enter required information (name, date of birth, address)",
            "Review your registration details for accuracy",
            "Note your polling location and district information",
            "Print or save confirmation for your records"
        ],
        "documents": [
            "Personal information (full name, date of birth)",
            "Address information",
            "Driver's license or ID number (may be required)"
        ],
        "tips": [
            "Check your status at least 2-3 weeks before election day",
            "Verify your polling location hasn't changed",
            "Confirm your party affiliation if applicable",
            "If your status shows as inactive or not registered, take immediate action",
            "Save or screenshot your confirmation for reference"
        ],
        "next_action": "Visit your state or national voter registration verification website to check your current status"
    },

    "polling_day": {
        "title": "Polling Day Procedures",
        "overview": "Election day is when you cast your vote. Knowing what to expect at the polling station will help you vote confidently and efficiently.",
        "steps": [
            "Verify your polling location and hours before leaving home",
            "Bring required identification documents",
            "Arrive during less busy hours if possible (mid-morning or early afternoon)",
            "Check in with poll workers and provide your ID",
            "Receive your ballot and voting instructions",
            "Vote privately in a designated booth or area",
            "Review your ballot carefully before submitting",
            "Submit your ballot to election officials or place it in the ballot box",
            "Receive your 'I Voted' sticker (optional but fun!)"
        ],
        "documents": [
            "Valid photo identification",
            "Voter registration card (if you have one)",
            "Sample ballot or notes (optional but helpful)"
        ],
        "tips": [
            "Polls are typically open from early morning to evening - check exact hours",
            "If you're in line when polls close, you can still vote",
            "Ask poll workers for help if you're unsure about anything",
            "Report any issues or irregularities to election officials",
            "Some locations offer curbside voting for those with mobility issues",
            "Take your time - there's no rush once you're in the voting booth"
        ],
        "next_action": "Confirm your polling location, hours, and plan your trip to vote on election day"
    },

    "timeline": {
        "title": "Election Timeline and Key Deadlines",
        "overview": "Elections follow a structured timeline with important deadlines for registration, early voting, and election day. Staying informed about these dates ensures you don't miss your opportunity to vote.",
        "steps": [
            "Note the voter registration deadline for your area",
            "Mark early voting or absentee ballot request deadlines",
            "Identify the early voting period if available",
            "Mark election day on your calendar",
            "Set reminders for each important deadline",
            "Plan ahead for any time off needed to vote"
        ],
        "documents": [
            "Election calendar from your local election authority",
            "Voter registration confirmation with deadlines",
            "Absentee or mail-in ballot application (if applicable)"
        ],
        "tips": [
            "Registration deadlines are typically 2-4 weeks before election day",
            "Early voting can help you avoid election day crowds",
            "Absentee ballot deadlines vary - some require requests weeks in advance",
            "Check if your area offers same-day registration",
            "Sign up for election reminders from your local election office",
            "Different types of elections (primary, general, local) have different dates"
        ],
        "next_action": "Visit your local election authority website to view the complete election calendar and mark all important dates"
    },

    "faq": {
        "title": "Frequently Asked Questions",
        "overview": "Common questions about the voting process, registration, and election procedures. If you need specific information, try asking about registration, documents, polling day, or timelines.",
        "steps": [
            "Identify your specific question or concern",
            "Ask about specific topics like 'voter registration', 'required documents', 'polling day procedures', or 'election timeline'",
            "Contact your local election office for jurisdiction-specific questions",
            "Review official election authority websites for detailed information"
        ],
        "documents": [
            "Varies depending on your specific question - typically ID and proof of address"
        ],
        "tips": [
            "Be specific in your questions for better assistance",
            "Local election offices are the best source for area-specific information",
            "Many questions can be answered on official election websites",
            "Don't hesitate to ask poll workers for help on election day",
            "Voter hotlines are available in many areas for real-time assistance"
        ],
        "next_action": "Ask a specific question about voter registration, required documents, polling procedures, or election timelines for detailed guidance"
    }
}
