# /// script
# requires-python = ">=3.10"
# dependencies = [
# ]
# ///

import os
import sys
import shutil
import subprocess
import distutils.ccompiler
import glob
import zipfile
import sysconfig
import hashlib
import time
import base64

if not 'PROJECT_ROOT' in os.environ:
    os.environ['PROJECT_ROOT'] = os.path.abspath(os.path.dirname(__file__))
project_root = os.environ['PROJECT_ROOT']

for req_bin in ['cargo', 'uv']:
    bin_location = shutil.which(req_bin)
    if not bin_location:
        print(f'Missing Dependency: You must have the tool "{req_bin}" installed and on your PATH to continue but we cannot find it, exiting...')
        sys.exit(1)
    else:
        print(f'Found "{req_bin}" at {bin_location}')

# Compile everything
subprocess.run(['cargo', 'build', '--release'], check=True)

# Copy the C library to *.pyd which python will look up; host_c_dylib_extension resolves to '.dll' on windows and '.so' on linux (mac untested)
host_c_dylib_extension = distutils.ccompiler.new_compiler().shared_lib_extension
all_built_pyd_files = set()
for compiled_shared_lib in glob.glob(os.path.join(project_root, 'target', 'release', f'*{host_c_dylib_extension}')):
    pyd_compiled_shared_lib = compiled_shared_lib[:-4]+'.pyd'
    if os.path.basename(pyd_compiled_shared_lib).casefold().startswith('lib'): # Trim lib* if on linux machine
        pyd_compiled_shared_lib = os.path.join(os.path.dirname(pyd_compiled_shared_lib), os.path.basename(pyd_compiled_shared_lib)[3:])
    print(f'Copying {compiled_shared_lib} to {pyd_compiled_shared_lib}')
    shutil.copyfile(compiled_shared_lib, pyd_compiled_shared_lib)
    all_built_pyd_files.add(pyd_compiled_shared_lib)

# We do not use python's bdist_wheels/setup.py tooling; instead we just build a .zip archive under target/release,
# which guarantees complete control over packaging.

version_num = os.environ.get('VERSION_NUM', '')
if len(version_num) < 1:
    with open(os.path.join(project_root, 'version.txt'), 'r') as fd:
        version_num = fd.read().strip()

standard_calls_whl_file = None
sys_platform_tag = sysconfig.get_platform()
sys_platform_tag = sys_platform_tag.replace('-', '_') # Why? Annoying, but file-paths are snake_case and identifiers are hyphen-separated.

min_cpython_tag = 'cp39'

print(f'Building a wheel w/ version {version_num} for {sys_platform_tag}')
# TODO maybe add a version number in .whl path? Inconvenient for examples/* though.
standard_calls_whl_file = os.path.join(project_root, 'target', 'release', f'standard_calls-{version_num}-{min_cpython_tag}-abi3-{sys_platform_tag}.whl')

if os.path.exists(standard_calls_whl_file):
    os.remove(standard_calls_whl_file)


licence_text = ''
with open(os.path.join(project_root, 'LICENSE.txt'), 'r') as fd:
    licence_text = fd.read().strip()

readme_text = ''
with open(os.path.join(project_root, 'readme.md'), 'r') as fd:
    readme_text = fd.read().strip()

def indent_lines(one_string_lines, line_idx_to_begin_indenting_at, indent_amount):
    lines = [x for x in one_string_lines.splitlines(keepends=False)]
    for i in range(0, len(lines)):
        if i >= line_idx_to_begin_indenting_at:
            lines[i] = (' ' * indent_amount) + lines[i]
    return '\n'.join(lines)

record_lines = []
def record_line_recorder_writestr(zip_file_name, content_bytes):
    global record_lines
    if not isinstance(content_bytes, bytes):
        raise Exception('content_bytes MUST be bytes!')
    sha = hashlib.sha256()
    sha.update(content_bytes)
    record_lines.append(
        f'{zip_file_name},sha256={base64.urlsafe_b64encode(sha.digest()).decode("utf-8")},{len(content_bytes)}'
    )
    return content_bytes

def record_line_recorder_write(host_file_name, interior_file_name):
    global record_lines
    sha = hashlib.sha256()
    with open(host_file_name, 'rb') as fd:
        host_file_bytes = fd.read()
        sha.update(host_file_bytes)
        record_lines.append(
            f'{interior_file_name},sha256={base64.urlsafe_b64encode(sha.digest()).decode("utf-8")},{len(host_file_bytes)}'
        )

with zipfile.ZipFile(standard_calls_whl_file, "w") as zf:
    zf.mkdir(f'standard_calls')
    for built_pyd_file in all_built_pyd_files:
        zf.write(built_pyd_file, arcname=f'standard_calls/{os.path.basename(built_pyd_file)}')
        record_line_recorder_write(built_pyd_file, f'standard_calls/{os.path.basename(built_pyd_file)}')

    zf.mkdir(f'standard_calls-{version_num}.dist-info')

    # Write dist-info/METADATA file. See https://pypi.org/classifiers/ for details
    zf.writestr(f'standard_calls-{version_num}.dist-info/METADATA', record_line_recorder_writestr(f'standard_calls-{version_num}.dist-info/METADATA', f'''
Metadata-Version: 2.1
Name: standard_calls
Version: {version_num}
Summary: RPC Framework
Author: Jeffrey McAteer
Maintainer-Email: Jeffrey McAteer <jeffrey-dev@jmcateer.pw>
License: {indent_lines(licence_text, 1, 9)}

Classifier: Development Status :: 3 - Alpha
Classifier: Intended Audience :: Science/Research
Classifier: Intended Audience :: Developers
Classifier: License :: OSI Approved :: GNU General Public License v2 (GPLv2)
Classifier: Programming Language :: C
Classifier: Programming Language :: Python
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.10
Classifier: Programming Language :: Python :: 3.11
Classifier: Programming Language :: Python :: 3.12
Classifier: Programming Language :: Python :: 3.13
Classifier: Programming Language :: Python :: 3 :: Only
Classifier: Programming Language :: Python :: Implementation :: CPython
Classifier: Topic :: Software Development
Classifier: Topic :: Scientific/Engineering
Classifier: Operating System :: Microsoft :: Windows
Classifier: Operating System :: POSIX
Classifier: Operating System :: Unix
Classifier: Operating System :: MacOS
Project-URL: homepage, https://github.com/jeffrey-p-mcateer/standard-calls
Project-URL: documentation, https://github.com/jeffrey-p-mcateer/standard-calls
Project-URL: source, https://github.com/jeffrey-p-mcateer/standard-calls
Project-URL: download, https://github.com/jeffrey-p-mcateer/standard-calls
Requires-Python: >=3.9
Description-Content-Type: text/markdown
{readme_text}
'''.strip().encode('utf-8')))
    
    # Write dist-info/WHEEL file. See https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/
    zf.writestr(f'standard_calls-{version_num}.dist-info/WHEEL', record_line_recorder_writestr(f'standard_calls-{version_num}.dist-info/WHEEL', f'''
Wheel-Version: 1.0
Generator: a python script
Root-Is-Purelib: false
Tag: {min_cpython_tag}-abi3-{sys_platform_tag}
'''.strip().encode('utf-8')))
    
    record_lines.append(f'standard_calls-{version_num}.dist-info/RECORD,,') # Must have a recursive entry too -_-
    print(f'record_lines = {record_lines}')
    zf.writestr(f'standard_calls-{version_num}.dist-info/RECORD', (os.linesep.join(record_lines).strip()).encode('utf-8') )

print(f'Built {standard_calls_whl_file}')

time.sleep(0.5)

# Run the first example
subprocess.run(['uv', 'run', os.path.join(project_root, 'examples', 'example01.py') ], check=True)

# TODO docs generation et al


