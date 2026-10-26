import sys
import os

# Set testing environment variable
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "testing"
os.environ["LLM_PROVIDER"] = "mock"

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
