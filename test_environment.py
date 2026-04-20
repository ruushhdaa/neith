# test_environment.py
# Run this to confirm NEITH's environment is correctly set up

print("Testing NEITH environment...\n")

try:
    import torch
    print(f"✓ PyTorch {torch.__version__}")
except ImportError as e:
    print(f"✗ PyTorch failed: {e}")

try:
    import torch_geometric
    print(f"✓ PyTorch Geometric {torch_geometric.__version__}")
except ImportError as e:
    print(f"✗ PyG failed: {e}")

try:
    import scapy
    print(f"✓ Scapy {scapy.__version__}")
except ImportError as e:
    print(f"✗ Scapy failed: {e}")

try:
    from mapie.regression import MapieRegressor
    print(f"✓ MAPIE imported successfully")
except (ImportError, AttributeError) as e:
    # Try the alternative path if the first one fails
    try:
        from mapie.estimators import MapieRegressor
        print(f"✓ MAPIE (via estimators) imported successfully")
    except ImportError:
        print(f"✗ MAPIE failed: {e}")

try:
    from river.drift import ADWIN
    print(f"✓ River/ADWIN imported successfully")
except ImportError as e:
    print(f"✗ River failed: {e}")

try:
    import flask
    print(f"✓ Flask {flask.__version__}")
except ImportError as e:
    print(f"✗ Flask failed: {e}")

print("\nEnvironment check complete.")
print("If all show ✓ — you are ready to build NEITH.")