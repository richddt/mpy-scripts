
import sys
import subprocess
import hashlib
from pathlib import Path

MPREMOTE = str(Path.home() / ".local/bin/mpremote")
PORT = "/dev/cu.usbmodem1234561"
CHUNK_SIZE = 32

if len(sys.argv) != 3:
    print("Usage: python3 fern_upload.py LOCAL_FILE REMOTE_FILE")
    sys.exit(1)

local_file = Path(sys.argv[1])
remote_file = sys.argv[2]
data = local_file.read_bytes()

def execute(code):
    result = subprocess.run(
        [MPREMOTE, "connect", PORT, "exec", code],
        capture_output=True,
        text=True
    )
    if result.returncode:
        print(result.stdout, result.stderr)
        raise RuntimeError("mpremote command failed")
    return result.stdout.strip()

# Initialize destination file
execute("open(%r, 'wb').close()" % remote_file)

# Upload 32 bytes per command
for offset in range(0, len(data), CHUNK_SIZE):
    chunk = data[offset:offset + CHUNK_SIZE]
    code = "f=open(%r,'ab');f.write(bytes.fromhex(%r));f.close()" % (
        remote_file, chunk.hex()
    )
    execute(code)
    print("Uploaded %d / %d bytes" %
          (min(offset + CHUNK_SIZE, len(data)), len(data)))

# Verify by comparing SHA-256 hashes
local_hash = hashlib.sha256(data).hexdigest()

remote_hash = execute(
    "import hashlib;print(hashlib.sha256(open(%r,'rb').read()).digest().hex())"
    % remote_file
)

print("Local SHA256: ", local_hash)
print("Remote SHA256:", remote_hash)

if local_hash == remote_hash:
    print("SUCCESS: File verified!")
else:
    print("ERROR: File verification failed!")
    sys.exit(1)
