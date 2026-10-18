"""检查导出候选及历史ZIP中的常见凭据；只记录位置与规则，不显示值。"""
import argparse,json,re,zipfile
from pathlib import Path

SKIP={'.venv','.cache','__pycache__','.git'}
RULES={
 'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
 'openai_key':rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}',
 'github_token':rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})',
 'aws_access_key':rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
 'google_api_key':rb'\bAIza[0-9A-Za-z_-]{35}\b',
 'credential_url':rb'https?://[^\s/<>"\x27:]{1,100}:[^\s/<>"\x27@]{4,150}@',
 'bearer_token':rb'(?i)\bBearer[ \t]+[A-Za-z0-9_.-]{32,}',
 'jwt':rb'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',
 'secret_assignment':rb'(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)["\x27]?[ \t]*[:=][ \t]*["\x27][A-Za-z0-9_./+=-]{24,}["\x27]',
 'cookie_header':rb'(?im)^(?:set-cookie|cookie):[ \t]*[^\r\n]{20,}'
}
COMPILED={key:re.compile(value) for key,value in RULES.items()}


def suspicious_name(name):
    p=Path(name);base=p.name.lower()
    return (base=='.env' or base.startswith('.env.') or base in {'credentials','credentials.json','id_rsa','id_ed25519','cookies.txt','cookies.json'} or p.suffix.lower() in {'.pem','.key','.p12','.pfx'})


def scan(name,data):
    findings=[]
    if suspicious_name(name):findings.append({'path':name,'rule':'sensitive_filename'})
    for rule,pattern in COMPILED.items():
        if pattern.search(data):findings.append({'path':name,'rule':rule})
    return findings


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--historical-archive',type=Path,action='append',default=[]);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
    findings=[];files=0;entries=0;errors=[]
    for path in sorted(args.root.rglob('*')):
        rel=path.relative_to(args.root)
        if any(x in SKIP for x in rel.parts) or path.suffix=='.pyc' or path==args.report:continue
        if path.is_symlink():findings.append({'path':str(rel),'rule':'symlink_not_exportable'});continue
        if path.is_file():
            files+=1
            if suspicious_name(rel):findings.append({'path':rel.as_posix(),'rule':'sensitive_filename'});continue
            try:findings.extend(scan(rel.as_posix(),path.read_bytes()))
            except OSError as e:errors.append({'path':str(rel),'error':type(e).__name__})
    archive_counts={}
    for path in args.historical_archive:
        count=0
        try:
            with zipfile.ZipFile(path) as z:
                for info in z.infolist():
                    if info.is_dir():continue
                    count+=1;entries+=1
                    findings.extend(scan(path.name+'!'+info.filename,z.read(info)))
            archive_counts[path.name]=count
        except (OSError,zipfile.BadZipFile,RuntimeError) as e:errors.append({'path':path.name,'error':type(e).__name__})
    result={'files_scanned':files,'historical_zip_entries_scanned':entries,'historical_archives':archive_counts,'findings':findings,'errors':errors,'passed':not findings and not errors,'method':'sensitive filenames and common credential patterns; no matching values logged; not an exhaustive guarantee for arbitrary custom secrets'}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='historical_archives'},ensure_ascii=False))
    raise SystemExit(0 if result['passed'] else 1)


if __name__=='__main__':main()
