import sys
from pathlib import Path
from starlette.types import ASGIApp, Receive, Scope, Send

# Add project root to sys.path so 'jobcopilot' package is resolved cleanly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from jobcopilot.web import app

