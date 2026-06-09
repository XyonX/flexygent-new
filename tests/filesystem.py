import os

# ── paste your three functions here ──────────────────────────────────────────

def read_file(file_name:str,output_length =8000 ):
    file_handler = open(file_name,"r")

    content = file_handler.read()

    file_handler.close()

    return content[:8000]

def replace(file_name,old_string,new_string):

    with open(file_name,"r") as f:
        content = f.read()

    if old_string not in content:
        return f"Error: could not find the target string in {file_name}"
    if content.count(old_string)>1:
        return f"Error: found multiple matches, be more specific"
    new_content = content.replace(old_string,new_string,1)

    with open(file_name,"w") as f:
        f.write(new_content)
    
    return f"Successfully edited {file_name}"

def write_file(file_name,content):

    # for append we use "a"
    file_handler = open(file_name,"w")
    file_handler.write(content)
    file_handler.close()

# ── test helpers ──────────────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
TEST_FILE = "test_temp.txt"

def check(label, condition):
    print(f"  [{PASS if condition else FAIL}] {label}")
    return condition

def cleanup():
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)

# ── tests ─────────────────────────────────────────────────────────────────────

def test_write_and_read():
    print("\n--- write_file + read_file ---")
    write_file(TEST_FILE, "hello world")
    content = read_file(TEST_FILE)
    check("write then read returns correct content", content == "hello world")

def test_read_truncation():
    print("\n--- read_file truncation ---")
    big_content = "x" * 10000
    write_file(TEST_FILE, big_content)
    result = read_file(TEST_FILE, output_length=8000)
    check("truncates to 8000 chars", len(result) == 8000)

def test_replace_basic():
    print("\n--- replace: basic case ---")
    write_file(TEST_FILE, "def foo():\n    x = 1\n    return x\n")
    result = replace(TEST_FILE, "    x = 1", "    x = 99")
    check("returns success message", "Successfully" in result)
    content = read_file(TEST_FILE)
    check("old string is gone", "    x = 1" not in content)
    check("new string is present", "    x = 99" in content)
    check("rest of file untouched", "def foo():" in content and "return x" in content)

def test_replace_multiline():
    print("\n--- replace: multiline block ---")
    original = "def foo():\n    x = 1\n    return x\n\ndef bar():\n    pass\n"
    write_file(TEST_FILE, original)
    old = "def bar():\n    pass"
    new = "def bar():\n    return 42"
    result = replace(TEST_FILE, old, new)
    check("returns success message", "Successfully" in result)
    content = read_file(TEST_FILE)
    check("new block present", "return 42" in content)
    check("foo function untouched", "def foo():" in content)

def test_replace_not_found():
    print("\n--- replace: string not found ---")
    write_file(TEST_FILE, "hello world")
    result = replace(TEST_FILE, "this does not exist", "something")
    check("returns error message", "Error" in result)
    check("file unchanged", read_file(TEST_FILE) == "hello world")

def test_replace_multiple_matches():
    print("\n--- replace: multiple matches ---")
    write_file(TEST_FILE, "foo bar foo bar foo")
    result = replace(TEST_FILE, "foo", "baz")
    check("returns multiple match error", "multiple" in result)
    check("file unchanged", read_file(TEST_FILE) == "foo bar foo bar foo")

def test_replace_at_start():
    print("\n--- replace: match at start of file ---")
    write_file(TEST_FILE, "import os\nimport sys\n")
    result = replace(TEST_FILE, "import os", "import pathlib")
    check("success", "Successfully" in result)
    content = read_file(TEST_FILE)
    check("import pathlib present", "import pathlib" in content)
    check("import sys untouched", "import sys" in content)

def test_replace_at_end():
    print("\n--- replace: match at end of file ---")
    write_file(TEST_FILE, "line one\nlast line")
    result = replace(TEST_FILE, "last line", "replaced last line")
    check("success", "Successfully" in result)
    check("end replaced", "replaced last line" in read_file(TEST_FILE))

def test_write_overwrites():
    print("\n--- write_file overwrites existing content ---")
    write_file(TEST_FILE, "original content")
    write_file(TEST_FILE, "new content")
    content = read_file(TEST_FILE)
    check("old content gone", "original" not in content)
    check("new content present", content == "new content")

# ── run all ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 45)
    print("  flexygent filesystem tools — test suite")
    print("=" * 45)
    try:
        test_write_and_read()
        test_read_truncation()
        test_replace_basic()
        test_replace_multiline()
        test_replace_not_found()
        test_replace_multiple_matches()
        test_replace_at_start()
        test_replace_at_end()
        test_write_overwrites()
    finally:
        cleanup()
        print("\ntemp file cleaned up")
    print("\ndone.")
