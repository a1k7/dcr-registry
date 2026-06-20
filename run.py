#!/usr/bin/env python3
"""
DecisionAssure Capability Registry (DCR)
Run with: python run.py
"""

import os
import sys
from web.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)