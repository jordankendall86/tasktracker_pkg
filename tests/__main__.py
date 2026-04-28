import unittest
from pathlib import Path

def main():
    tests_dir = Path(__file__).resolve().parent
    suite = unittest.defaultTestLoader.discover(str(tests_dir))
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    main()