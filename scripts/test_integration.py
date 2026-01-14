"""
Test the squash integration in main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Run the update_stats function directly
from main import update_stats

print("=" * 80)
print("TESTING SQUASH INTEGRATION")
print("=" * 80)

try:
    update_stats(auto_mode=False)
    print("\n" + "=" * 80)
    print("✅ Integration test completed successfully!")
    print("=" * 80)
except Exception as e:
    print(f"\n❌ Integration test failed: {e}")
    import traceback
    traceback.print_exc()
