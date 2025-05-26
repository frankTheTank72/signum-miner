import os
import platform
import subprocess
import sys


def run(cmd, shell=False):
    print('Running:', ' '.join(cmd) if isinstance(cmd, list) else cmd)
    try:
        if shell:
            subprocess.check_call(cmd, shell=True)
        else:
            subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)


def ensure_rust():
    try:
        subprocess.check_call(['cargo', '--version'])
        subprocess.check_call(['rustc', '--version'])
    except Exception:
        print('Rust not found. Installing via rustup...')
        if platform.system() == 'Windows':
            rustup = 'https://win.rustup.rs/'
            run(['powershell', '-Command', f"iwr -useb {rustup} | iex"], shell=False)
        else:
            run('curl https://sh.rustup.rs -sSf | sh -s -- -y', shell=True)
        # load cargo env
        cargo_env = os.path.expanduser('~/.cargo/env')
        if os.path.exists(cargo_env):
            with open(cargo_env) as f:
                exec(f.read(), dict(__file__=cargo_env))


def install_python_deps():
    if os.path.exists('requirements.txt'):
        run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])


def build_project():
    run(['cargo', 'build', '--release'])


def main():
    ensure_rust()
    install_python_deps()
    build_project()
    print('\nAll dependencies installed and project built.')


if __name__ == '__main__':
    main()
