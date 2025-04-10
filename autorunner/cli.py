#!/usr/bin/env python3
"""
Auto Clicker - Automates clicking buttons to start and end rounds in an application.
"""

import time
import sys
import logging
from pathlib import Path

import pyautogui
from PIL import Image

from autorunner.config import Config

# Add default configuration attributes if they don't exist
if not hasattr(Config, 'debug_mode'):
    Config.debug_mode = False

if not hasattr(Config, 'confidence_threshold'):
    Config.confidence_threshold = 0.9
    
if not hasattr(Config, 'resize_images'):
    Config.resize_images = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('autorunner.log')
    ]
)
logger = logging.getLogger(__name__)

# Disable PyAutoGUI's fail-safe feature if needed
# pyautogui.FAILSAFE = False


class AutoClicker:
    """Handles automated clicking of buttons based on image recognition."""
    
    def __init__(self, config):
        """Initialize the auto clicker with configuration."""
        self.config = config
        self.images_dir = Path(config.images_dir)
        self.start_button_img = self.images_dir / config.start_button_img
        self.end_button_img = self.images_dir / config.end_button_img
        self.end_button_alt_img = self.images_dir / config.end_button_alt_img
        
        # Get screen dimensions for bounds checking
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"PyAutoGUI reports screen dimensions: {self.screen_width}x{self.screen_height}")
        
        # Initialize scaling factors (will be updated in _verify_screen_dimensions if needed)
        self.scale_factor_x = 1.0
        self.scale_factor_y = 1.0
        
        # Verify screen dimensions by taking a screenshot
        self._verify_screen_dimensions()
        
        # Check if alternative end button exists
        self.has_alt_end_button = Path(self.end_button_alt_img).exists()
        
        # Prepare scaled images if resize mode is enabled
        if getattr(config, 'resize_images', False):
            self.prepare_scaled_images()
        
        # Verify images exist and log their dimensions
        if not self.start_button_img.exists():
            raise FileNotFoundError(f"Start button image not found: {self.start_button_img}")
        else:
            start_img = Image.open(self.start_button_img)
            logger.info(f"Start button image dimensions: {start_img.size}")
            
        if not self.end_button_img.exists():
            raise FileNotFoundError(f"End button image not found: {self.end_button_img}")
        else:
            end_img = Image.open(self.end_button_img)
            logger.info(f"End button image dimensions: {end_img.size}")
            
        # Alternative end button is optional (already checked in __init__)
        if self.has_alt_end_button:
            alt_end_img = Image.open(self.end_button_alt_img)
            logger.info(f"Alt end button image dimensions: {alt_end_img.size}")
            
        # Check if any button extends beyond screen dimensions
        if (start_img.width > self.screen_width or start_img.height > self.screen_height or
            end_img.width > self.screen_width or end_img.height > self.screen_height):
            logger.warning("Some button images are larger than the screen dimensions!")
            logger.warning("This may cause detection issues. Consider using --resize option.")
            
        logger.info("Auto Clicker initialized")
        logger.info(f"Start button image: {self.start_button_img}")
        logger.info(f"End button image: {self.end_button_img}")
        if self.has_alt_end_button:
            logger.info(f"Alternative end button image: {self.end_button_alt_img}")
        else:
            logger.info("No alternative end button image provided")
    
    def _verify_screen_dimensions(self):
        """Verify screen dimensions by taking a screenshot and comparing."""
        try:
            # Take a screenshot to verify dimensions
            screen = pyautogui.screenshot()
            actual_width, actual_height = screen.size
            
            if actual_width != self.screen_width or actual_height != self.screen_height:
                logger.warning(f"Detected screen size mismatch! PyAutoGUI reports {self.screen_width}x{self.screen_height} but screenshot is {actual_width}x{actual_height}")
                
                # Calculate scaling factor
                self.scale_factor_x = actual_width / self.screen_width
                self.scale_factor_y = actual_height / self.screen_height
                logger.info(f"Screen scaling factors: {self.scale_factor_x}x, {self.scale_factor_y}x")
                
                # Update to use the actual dimensions from the screenshot
                self.screen_width, self.screen_height = actual_width, actual_height
                logger.info(f"Updated screen dimensions to: {self.screen_width}x{self.screen_height}")
        except Exception as e:
            logger.error(f"Error verifying screen dimensions: {e}")
    
    def _debug_click_position(self, x, y, description):
        """Take a screenshot and mark where we're about to click for debugging."""
        try:
            # Take a screenshot
            screen = pyautogui.screenshot()
            
            # Draw a marker at the click position
            from PIL import ImageDraw
            draw = ImageDraw.Draw(screen)
            
            # Draw crosshair
            size = 20
            draw.line((x - size, y, x + size, y), fill="red", width=2)
            draw.line((x, y - size, x, y + size), fill="red", width=2)
            
            # Draw circle
            draw.ellipse((x - 10, y - 10, x + 10, y + 10), outline="blue", width=2)
            
            # Save the image
            debug_file = f"debug_click_{description.replace(' ', '_')}.png"
            screen.save(debug_file)
            logger.info(f"Saved click position debug image to {debug_file}")
        except Exception as e:
            logger.error(f"Error creating click debug image: {e}")
            
    def prepare_scaled_images(self):
        """Create scaled versions of button images to match current screen resolution."""
        logger.info("Preparing scaled images for current screen resolution")
        
        # Create a scaled_images directory
        scaled_dir = self.images_dir / "scaled"
        scaled_dir.mkdir(exist_ok=True)
        
        # Scale and save each image
        for img_path, name in [
            (self.start_button_img, "start_button"),
            (self.end_button_img, "end_button"),
            (self.end_button_alt_img, "end_button_alt") if self.has_alt_end_button else (None, None)
        ]:
            if img_path is None:
                continue
                
            try:
                # Open original image
                img = Image.open(img_path)
                
                # Calculate scaling factor (if image is larger than screen)
                scale_x = min(1.0, self.screen_width / img.width)
                scale_y = min(1.0, self.screen_height / img.height)
                scale = min(scale_x, scale_y)
                
                if scale < 1.0:
                    # Resize image
                    new_width = int(img.width * scale)
                    new_height = int(img.height * scale)
                    resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                    
                    # Save scaled image
                    scaled_path = scaled_dir / f"{name}_scaled.png"
                    resized_img.save(scaled_path)
                    logger.info(f"Saved scaled image: {scaled_path} ({new_width}x{new_height})")
                    
                    # Update the image path to use the scaled version
                    if name == "start_button":
                        self.start_button_img = scaled_path
                    elif name == "end_button":
                        self.end_button_img = scaled_path
                    elif name == "end_button_alt":
                        self.end_button_alt_img = scaled_path
            except Exception as e:
                logger.error(f"Error scaling {name} image: {e}")
    
    def find_and_click(self, image_path, description, alt_image_path=None):
        """Find an image on screen and click it if found. Optionally try an alternative image."""
        logger.info(f"Looking for {description}...")
        
        try:
            # Take a screenshot for verification in debug mode
            if self.config.debug_mode:
                screen = pyautogui.screenshot()
                debug_path = f"debug_{description.replace(' ', '_')}.png"
                screen.save(debug_path)
                logger.info(f"Saved current screen to {debug_path}")
            
            # Try to find the image on screen
            location = None
            
            # Try primary image first
            try:
                confidence = getattr(self.config, 'confidence_threshold', 0.9)
                location = pyautogui.locateOnScreen(str(image_path), confidence=confidence)
                if location:
                    logger.info(f"Found {description} at: Left={location.left}, Top={location.top}, Width={location.width}, Height={location.height}")
            except Exception as e:
                if "confidence" in str(e):
                    logger.warning("OpenCV not installed, falling back to exact matching")
                    location = pyautogui.locateOnScreen(str(image_path))
                else:
                    raise
            
            # If primary image not found, try alternative
            if not location and alt_image_path and Path(alt_image_path).is_file():
                logger.info(f"Primary {description} not found, trying alternative...")
                try:
                    location = pyautogui.locateOnScreen(str(alt_image_path), confidence=confidence)
                    if location:
                        logger.info(f"Found alternative {description}")
                except Exception as e:
                    if "confidence" in str(e):
                        location = pyautogui.locateOnScreen(str(alt_image_path))
                    else:
                        raise
            
            # If image found, click it
            if location:
                # Get center of the found image
                center = pyautogui.center(location)
                x, y = int(center.x), int(center.y)
                logger.info(f"Original coordinates: ({x}, {y})")
                
                # Apply scaling correction if needed
                if hasattr(self, 'scale_factor_x') and (self.scale_factor_x != 1.0 or self.scale_factor_y != 1.0):
                    # Convert from screenshot coordinates to PyAutoGUI coordinates
                    pyautogui_x = int(x / self.scale_factor_x)
                    pyautogui_y = int(y / self.scale_factor_y)
                    logger.info(f"Scaling-adjusted coordinates: ({pyautogui_x}, {pyautogui_y})")
                    x, y = pyautogui_x, pyautogui_y
                
                # Check if coordinates are within screen bounds
                screen_width, screen_height = pyautogui.size()
                
                # If coordinates are outside screen bounds or too close to edge, adjust them
                margin = 20  # Safe margin from screen edges
                if x >= screen_width or y >= screen_height or x < margin or y < margin or x > screen_width - margin or y > screen_height - margin:
                    logger.warning(f"Coordinates ({x}, {y}) are outside screen bounds or too close to edge ({screen_width}x{screen_height})")
                    
                    # Use the top-left corner of the match as a reference point
                    # This is more reliable than trying to calculate the center
                    safe_x = location.left + margin
                    safe_y = location.top + margin
                    
                    # Make sure we're within the visible screen area
                    safe_x = min(max(margin, safe_x), screen_width - margin)
                    safe_y = min(max(margin, safe_y), screen_height - margin)
                    
                    logger.info(f"Adjusted to safe coordinates: ({safe_x}, {safe_y})")
                    x, y = safe_x, safe_y
                
                # Move and click with small delays for reliability
                time.sleep(0.2)
                pyautogui.moveTo(x, y, duration=0.3)
                time.sleep(0.1)
                
                # Take a screenshot of where we're about to click if in debug mode
                if self.config.debug_mode:
                    self._debug_click_position(x, y, description)
                
                pyautogui.click()
                
                # Verify click was successful
                logger.info(f"Clicked {description}")
                return True
            else:
                logger.warning(f"{description} not found on screen")
                return False
                
        except Exception as e:
            logger.error(f"Error finding {description}: {e}")
            return False
    
    def run_rounds(self):
        """Run rounds until interrupted by the user."""
        rounds_completed = 0
        looking_for_end_button = False  # Track which button we're looking for
        
        # Always run indefinitely, ignoring num_rounds from config
        max_rounds = float('inf')
        logger.info("Starting infinite rounds (press Ctrl+C to stop)")
        
        try:
            # First, check if we're already in a round by looking for end buttons
            logger.info("Checking initial state...")
            end_found = self.find_and_click(self.end_button_img, "end button")
            if not end_found and self.has_alt_end_button:
                end_found = self.find_and_click(self.end_button_alt_img, "alternative end button")
            
            # If we found and clicked an end button, we were in a round
            if end_found:
                logger.info("Found end button at startup - completing existing round")
                looking_for_end_button = False
                time.sleep(self.config.between_rounds_wait_time)
            else:
                # Check if start button is available
                start_found = self.find_and_click(self.start_button_img, "start button")
                if start_found:
                    logger.info("Found start button at startup - starting new round")
                    looking_for_end_button = True
                    time.sleep(self.config.round_wait_time)
                else:
                    logger.info("No buttons found at startup, will look for start button first")
                    looking_for_end_button = False
            
            # Main loop
            while max_rounds == float('inf') or rounds_completed < max_rounds:
                if looking_for_end_button:
                    # We're in a round, look for end buttons
                    logger.info("Looking for end buttons...")
                    end_clicked = self.find_and_click(self.end_button_img, "end button")
                    
                    # If end button not found, try the alternative end button
                    if not end_clicked and self.has_alt_end_button:
                        end_clicked = self.find_and_click(self.end_button_alt_img, "alternative end button")
                    
                    if end_clicked:
                        rounds_completed += 1
                        logger.info(f"Completed round {rounds_completed}")
                        looking_for_end_button = False  # Now look for start button
                        
                        # Wait before starting next round
                        time.sleep(self.config.between_rounds_wait_time)
                    else:
                        logger.warning("Failed to find end button, retrying...")
                        time.sleep(self.config.retry_delay)
                else:
                    # We're between rounds, look for start button
                    logger.info("Looking for start button...")
                    start_clicked = self.find_and_click(self.start_button_img, "start button")
                    
                    if start_clicked:
                        logger.info(f"Started round {rounds_completed + 1}")
                        looking_for_end_button = True  # Now look for end button
                        
                        # Wait for the round to complete
                        time.sleep(self.config.round_wait_time)
                    else:
                        # Count consecutive failures
                        if not hasattr(self, 'start_button_failures'):
                            self.start_button_failures = 0
                        self.start_button_failures += 1
                        
                        # If we've failed to find the start button multiple times, try clicking in the center
                        if self.start_button_failures >= getattr(self.config, 'max_failures_before_center_click', 5):
                            logger.warning(f"Failed to find start button {self.start_button_failures} times, clicking center of screen")
                            
                            # Click in the center of the screen
                            center_x = self.screen_width // 2
                            center_y = self.screen_height // 2
                            
                            # Apply scaling if needed
                            if hasattr(self, 'scale_factor_x') and (self.scale_factor_x != 1.0 or self.scale_factor_y != 1.0):
                                center_x = int(center_x / self.scale_factor_x)
                                center_y = int(center_y / self.scale_factor_y)
                            
                            logger.info(f"Clicking center of screen at ({center_x}, {center_y})")
                            pyautogui.moveTo(center_x, center_y, duration=0.3)
                            pyautogui.click()
                            
                            # Reset failure counter
                            self.start_button_failures = 0
                            
                            # Wait a bit after center click
                            time.sleep(self.config.retry_delay * 2)
                        else:
                            logger.warning(f"Failed to find start button (attempt {self.start_button_failures}), retrying...")
                            time.sleep(self.config.retry_delay)
                    
            logger.info(f"All {rounds_completed} rounds completed successfully")
            
        except KeyboardInterrupt:
            logger.info(f"Process interrupted by user after {rounds_completed} rounds")
        except Exception as e:
            logger.error(f"Error during execution: {e}")


def check_screen_dimensions():
    """Check screen dimensions and take a screenshot for verification."""
    logger.info("Checking screen dimensions")
    
    # Get reported screen dimensions from PyAutoGUI
    pyautogui_width, pyautogui_height = pyautogui.size()
    logger.info(f"PyAutoGUI reports screen dimensions: {pyautogui_width}x{pyautogui_height}")
    
    # Take a screenshot to verify
    screen = pyautogui.screenshot()
    actual_width, actual_height = screen.size
    logger.info(f"Screenshot dimensions: {actual_width}x{actual_height}")
    
    # Calculate and display scaling factor
    scale_x = actual_width / pyautogui_width
    scale_y = actual_height / pyautogui_height
    logger.info(f"Screen scaling factors: {scale_x:.2f}x, {scale_y:.2f}x")
    
    # Save the screenshot
    screen.save("screen_dimensions_check.png")
    logger.info("Saved screenshot to screen_dimensions_check.png")
    
    # Draw screen boundaries on the image
    from PIL import ImageDraw
    draw = ImageDraw.Draw(screen)
    
    # Draw rectangle at the edges
    draw.rectangle((0, 0, actual_width-1, actual_height-1), outline="red", width=3)
    
    # Draw crosshair at center
    center_x, center_y = actual_width // 2, actual_height // 2
    size = 50
    draw.line((center_x - size, center_y, center_x + size, center_y), fill="blue", width=2)
    draw.line((center_x, center_y - size, center_x, center_y + size), fill="blue", width=2)
    
    # Save the marked screenshot
    screen.save("screen_boundaries.png")
    logger.info("Saved screen boundaries visualization to screen_boundaries.png")
    
    # Move mouse to each corner to verify bounds
    corners = [
        (10, 10, "top-left"),
        (actual_width - 10, 10, "top-right"),
        (10, actual_height - 10, "bottom-left"),
        (actual_width - 10, actual_height - 10, "bottom-right"),
        (center_x, center_y, "center")
    ]
    
    for x, y, position in corners:
        logger.info(f"Moving mouse to {position} corner ({x}, {y})")
        pyautogui.moveTo(x, y, duration=1)
        time.sleep(0.5)
    
    logger.info("Screen dimension check completed")

def test_single_click():
    """Test function to find and click just the start button once."""
    logger.info("Testing single click on start button")
    
    # Create images directory if it doesn't exist
    Path(Config.images_dir).mkdir(exist_ok=True)
    
    # Log screen dimensions
    screen_width, screen_height = pyautogui.size()
    logger.info(f"Screen dimensions: {screen_width}x{screen_height}")
    
    # Initialize the auto clicker
    clicker = AutoClicker(Config)
    
    # Give user time to switch to the target application
    logger.info("Switch to your target application...")
    time.sleep(5)
    
    # Take a before screenshot
    screen_before = pyautogui.screenshot()
    screen_before.save("debug_before_click.png")
    logger.info("Saved screenshot before clicking")
    
    # Try to find and click the start button
    result = clicker.find_and_click(clicker.start_button_img, "start button")
    
    # Take an after screenshot
    time.sleep(1)
    screen_after = pyautogui.screenshot()
    screen_after.save("debug_after_click.png")
    logger.info("Saved screenshot after clicking")
    
    if result:
        logger.info("Successfully clicked start button")
    else:
        logger.warning("Failed to find or click start button")
    
    logger.info("Test click completed")

def debug_images():
    """Debug function to show where images are being detected on screen."""
    logger.info("Starting image detection debug mode")
    
    # Create images directory if it doesn't exist
    Path(Config.images_dir).mkdir(exist_ok=True)
    
    # Log screen dimensions
    screen_width, screen_height = pyautogui.size()
    logger.info(f"Screen dimensions: {screen_width}x{screen_height}")
    
    # Initialize the auto clicker
    clicker = AutoClicker(Config)
    
    # Give user time to switch to the target application
    logger.info("Switch to your target application...")
    time.sleep(5)
    
    # Take a full screenshot for reference
    screen = pyautogui.screenshot()
    screen.save("debug_full_screen.png")
    logger.info("Saved full screen screenshot to debug_full_screen.png")
    
    # Try to locate all buttons
    for button_name, img_path in [
        ("start button", clicker.start_button_img),
        ("end button", clicker.end_button_img),
        ("alt end button", clicker.end_button_alt_img if clicker.has_alt_end_button else None)
    ]:
        if img_path is None:
            continue
            
        logger.info(f"Attempting to locate {button_name}...")
        try:
            # Try to find the button with different confidence levels
            for confidence in [0.9, 0.8, 0.7]:
                try:
                    location = pyautogui.locateOnScreen(str(img_path), confidence=confidence)
                    if location:
                        logger.info(f"{button_name} found at confidence {confidence}: {location}")
                        
                        # Draw rectangle and center point on screenshot
                        from PIL import ImageDraw
                        debug_img = screen.copy()
                        draw = ImageDraw.Draw(debug_img)
                        
                        # Draw rectangle around match
                        draw.rectangle(
                            (location.left, location.top, location.left + location.width, location.top + location.height),
                            outline="red",
                            width=3
                        )
                        
                        # Mark center point
                        center = pyautogui.center(location)
                        x, y = int(center.x), int(center.y)
                
                        # Check if coordinates are valid
                        if 0 <= x < screen_width and 0 <= y < screen_height:
                            logger.info(f"Click coordinates ({x}, {y}) are within screen bounds")
                            draw.ellipse((x-5, y-5, x+5, y+5), fill="blue")
                        else:
                            logger.warning(f"Click coordinates ({x}, {y}) are outside screen bounds ({screen_width}x{screen_height})")
                    
                            # Use the top-left corner of the match as a reference point
                            # This is more reliable than trying to calculate the center
                            margin = 20
                            safe_x = location.left + margin
                            safe_y = location.top + margin
                            
                            # Make sure we're within the visible screen area
                            safe_x = min(max(margin, safe_x), screen_width - margin)
                            safe_y = min(max(margin, safe_y), screen_height - margin)
                    
                            logger.info(f"Safe click point: ({safe_x}, {safe_y})")
                            draw.ellipse((safe_x-5, safe_y-5, safe_x+5, safe_y+5), fill="green")
                
                        # Save debug image
                        debug_file = f"debug_{button_name.replace(' ', '_')}.png"
                        debug_img.save(debug_file)
                        logger.info(f"Saved debug image to {debug_file}")
                        
                        break  # Found a match, no need to try lower confidence
                except Exception as e:
                    if "confidence" not in str(e):
                        logger.error(f"Error during debug of {button_name}: {e}")
                        break
            else:
                logger.warning(f"{button_name} not found on screen")
        except Exception as e:
            logger.error(f"Error during debug of {button_name}: {e}")
    
    logger.info("Debug mode completed")


def main():
    """Main entry point for the application."""
    logger.info("Starting Auto Clicker application")
    
    try:
        # Create images directory if it doesn't exist
        Path(Config.images_dir).mkdir(exist_ok=True)
        
        # Process command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--debug":
                Config.debug_mode = True
                debug_images()
                return 0
            elif sys.argv[1] == "--safe":
                # Enable safe mode with lower confidence threshold
                Config.confidence_threshold = 0.7
                logger.info("Running in safe mode with lower confidence threshold")
            elif sys.argv[1] == "--resize":
                # Enable resize mode to handle different screen sizes
                Config.resize_images = True
                logger.info("Running in resize mode - will scale reference images to match screen")
            elif sys.argv[1] == "--region":
                # Add region mode to only search in a specific screen region
                Config.use_region = True
                logger.info("Running in region mode - will only search in the center of the screen")
            elif sys.argv[1] == "--test-click":
                # Test a single click on the start button
                Config.debug_mode = True
                test_single_click()
                return 0
            elif sys.argv[1] == "--check-screen":
                # Just check screen dimensions and take a screenshot
                check_screen_dimensions()
                return 0
            elif sys.argv[1].startswith("--scale="):
                # Set explicit scaling factor
                try:
                    scale = float(sys.argv[1].split("=")[1])
                    Config.scale_factor = scale
                    logger.info(f"Using explicit scaling factor: {scale}")
                except (IndexError, ValueError) as e:
                    logger.error(f"Invalid scaling factor: {e}")
                    return 1
            elif sys.argv[1].startswith("--rounds="):
                # Set specific number of rounds
                try:
                    rounds = int(sys.argv[1].split("=")[1])
                    Config.num_rounds = rounds
                    logger.info(f"Will run exactly {rounds} rounds")
                except (IndexError, ValueError) as e:
                    logger.error(f"Invalid rounds value: {e}")
                    return 1
        
        # Give user time to switch to the target application
        logger.info(f"Starting in {Config.startup_delay} seconds. Switch to your target application...")
        time.sleep(Config.startup_delay)
        
        # Run the auto clicker
        clicker = AutoClicker(Config)
        clicker.run_rounds()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
