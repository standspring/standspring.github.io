import sys
from importlib.metadata import PackageNotFoundError, version

print("Python:", sys.executable)
print("Version:", sys.version.split()[0])
print("Virtual environment:", sys.prefix != sys.base_prefix)
try:
    print("requests:", version("requests"))
except PackageNotFoundError:
    print("requests: not installed in this environment")
