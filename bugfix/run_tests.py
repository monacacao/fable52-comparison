import sys, importlib, traceback
sys.path.insert(0, ".")
m = importlib.import_module(sys.argv[1] if len(sys.argv) > 1 else "test_shop")
names = [n for n in dir(m) if n.startswith("test_")]
fail = 0
for n in names:
    try:
        getattr(m, n)(); print("PASS", n)
    except Exception as e:
        fail += 1; print("FAIL", n, "-", type(e).__name__, e)
print(f"{len(names)-fail}/{len(names)} passed")
