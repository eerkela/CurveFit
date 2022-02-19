from pathlib import Path
import sys
import unittest

sys.path.append(str(Path(__file__).resolve().parent.parent))

# from curvefit.test.color_test import *
from curvefit.test.text_test import *


if __name__ == "__main__":
    unittest.main()
