"""仅用标准库校验迁移清单；不导入科研模块，不运行实验。"""
import argparse,csv,hashlib,json
from pathlib import Path,PurePosixPath


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def verify(root,manifest):
    errors=[];checked=0
    with manifest.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            rel=PurePosixPath(row['path'])
            if rel.is_absolute() or '..' in rel.parts or '\\' in row['path']:
                errors.append({'path':row['path'],'reason':'unsafe manifest path'});continue
            path=root.joinpath(*rel.parts)
            if path.is_symlink() or not path.is_file():
                errors.append({'path':row['path'],'reason':'missing, symlink, or non-file'});continue
            if root.resolve() not in path.resolve().parents:
                errors.append({'path':row['path'],'reason':'outside project root'});continue
            if path.stat().st_size!=int(row['bytes']) or digest(path)!=row['sha256']:
                errors.append({'path':row['path'],'reason':'size/hash mismatch'})
            checked+=1
    return {'checked_files':checked,'failures':errors,'passed':not errors,'scope':'only files listed in manifest; local new files are not errors'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--manifest',type=Path);args=parser.parse_args()
    root=args.root.resolve();manifest=args.manifest or root/'migration/manifest_sha256.csv'
    result=verify(root,manifest);print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
