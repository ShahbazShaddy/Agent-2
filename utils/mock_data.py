import logging

logger = logging.getLogger(__name__)

def get_sample_data():
    """
    Returns sample tax comparison data for testing or when the API fails.
    """
    logger.info("Using sample data")
    
    return [
        {
            "type": "WAGES",
            "2023": 75000,
            "2024": 80000,
            "difference": 5000
        },
        {
            "type": "INTEREST_INCOME",
            "2023": 1200,
            "2024": 1500,
            "difference": 300
        },
        {
            "type": "DIVIDENDS",
            "2023": 2500,
            "2024": 2800,
            "difference": 300
        },
        {
            "type": "CAPITAL_GAINS",
            "2023": 5000,
            "2024": 6500,
            "difference": 1500
        },
        {
            "type": "ADJUSTMENTS_TO_INCOME",
            "2023": 3000,
            "2024": 3500,
            "difference": 500
        },
        {
            "type": "STANDARD_DEDUCTION",
            "2023": 12950,
            "2024": 13850,
            "difference": 900
        },
        {
            "type": "TAXABLE_INCOME",
            "2023": 67750,
            "2024": 73450,
            "difference": 5700
        },
        {
            "type": "TAX_BEFORE_CREDITS",
            "2023": 12500,
            "2024": 13800,
            "difference": 1300
        },
        {
            "type": "TAX_CREDITS",
            "2023": 2000,
            "2024": 2000,
            "difference": 0
        },
        {
            "type": "TAX_AFTER_CREDITS",
            "2023": 10500,
            "2024": 11800,
            "difference": 1300
        },
        {
            "type": "REFUND",
            "2023": 1200,
            "2024": 800,
            "difference": -400
        },
        {
            "type": "EFFECTIVE_TAX_RATE",
            "2023": 15,
            "2024": 16,
            "difference": 1
        }
    ]
