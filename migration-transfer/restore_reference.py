from pathlib import Path
import hashlib
root=Path(__file__).resolve().parents[1]
pieces=[root/'migration-transfer/2207.10289.pdf.part01',root/'migration-transfer/2207.10289.pdf.part02']
data=b''.join(p.read_bytes() for p in pieces)
expected="d09a85ce0b317dde5911b185b2703d7dfbfe6a7f995ff8d8fbc99d0196f3801a"
if hashlib.sha256(data).hexdigest()!=expected:raise SystemExit('Reference restoration checksum mismatch')
target=root/'Bachelor_Thesis_RaNN/references/source/2207.10289.pdf'
if target.exists() and target.read_bytes()!=data:raise SystemExit('Refusing to overwrite a different reference file')
target.parent.mkdir(parents=True,exist_ok=True)
target.write_bytes(data)
print('Exact original reference restored; SHA256 verified; no research computation')
