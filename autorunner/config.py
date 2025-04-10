"""
Configuration settings for the Auto Clicker application.
"""

class Config:
    """Configuration settings."""
    
    # Image paths
    images_dir = "images"
    start_button_img = "start_button.png"
    end_button_img = "end_button.png"
    end_button_alt_img = "end_button_alt.png"  # Alternative end button image
    
    # Timing settings (in seconds)
    startup_delay = 5  # Time to switch to target application
    round_wait_time = 30  # Time to wait for a round to complete
    between_rounds_wait_time = 3  # Time to wait between rounds
    retry_delay = 2  # Time to wait before retrying a failed click
    
    # Recognition settings
    confidence_threshold = 0.8  # Minimum confidence for image recognition (0-1)
    
    # Operation settings
    num_rounds = 10  # Number of rounds to complete
