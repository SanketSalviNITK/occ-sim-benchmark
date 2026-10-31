"""Rebuild results/MANIFEST.sha256: MAIN section (all results/ files except legacy/) + separate LEGACY section (results/legacy/)."""
import subprocess, hashlib, sys
tag = sys.argv[1] if len(sys.argv) > 1 else 'untagged'
fs = sorted(f for f in subprocess.check_output(['git', 'ls-files', '-co', '--exclude-standard', 'results']).decode().split() if f != 'results/MANIFEST.sha256')
main = [f for f in fs if not f.startswith('results/legacy/')]; leg = [f for f in fs if f.startswith('results/legacy/')]
h = lambda f: hashlib.sha256(open(f, 'rb').read()).hexdigest() + '  ' + f + '\n'
with open('results/MANIFEST.sha256', 'w') as o:
    o.write(f'# results sha256 manifest ({tag}). Sections: MAIN ({len(main)} files) and LEGACY ({len(leg)} files, results/legacy/, hashed but excluded from all claims).\n')
    o.write('# == MAIN ==\n'); o.writelines(map(h, main))
    o.write('# == LEGACY (results/legacy/; excluded from claims) ==\n'); o.writelines(map(h, leg))
print(len(main), len(leg))
