"""
  Quick install
  cd <YOUR DIRECTORY>
  Download and install in one line:
    curl -X GET https://raw.githubusercontent.com/zackees/install.py/main/install.py -o install.py && python install.py


  To enter the environment run:
    source activate.sh


  Notes:
    This script is tested to work using python2 and python3 from a fresh install. The only side effect
    of running this script is that virtualenv will be globally installed if it isn't already.
"""


import argparse
import os
import shutil
import subprocess
import sys
import warnings

# This activation script adds the ability to run it from any path and also
# aliasing pip3 and python3 to pip/python so that this works across devices.
_ACTIVATE_SH = """
#!/bin/bash

# Function that computes absolute path of a file
abs_path() {
  dir=$(dirname "$1")
  (cd "$dir" &>/dev/null && printf "%s/%s" "$PWD" "${1##*/}")
}

# Navigate to the directory where the current script resides
bashfile=$(abs_path "${BASH_SOURCE[0]}")
selfdir=$(dirname "$bashfile")
cd "$selfdir"

if [[ "$IN_ACTIVATED_ENV" == "1" ]]; then
  IN_ACTIVATED_ENV=1
else
  IN_ACTIVATED_ENV=0
fi

if [[ "$IN_ACTIVATED_ENV" == "1" ]]; then
  # If it is, set the variable 'IN_ACTIVATED_ENV' to true
  IN_ACTIVATED_ENV=1
else
  # Otherwise, set 'IN_ACTIVATED_ENV' to false
  IN_ACTIVATED_ENV=1
fi

# If the 'venv' directory doesn't exist, print a message and exit.
if [[ ! -d "venv" ]]; then
  echo "The 'venv' directory does not exist, creating..."
  if [[ "$IN_ACTIVATED_ENV" == "1" ]]; then
    echo "Cannot install a new environment while in an activated environment. Please launch a new shell and try again."
    exit 1
  fi
  # Check the operating system type.
  # If it is macOS or Linux, then create an alias 'python' for 'python3'
  # and an alias 'pip' for 'pip3'. This is helpful if python2 is the default python in the system.
  echo "OSTYPE: $OSTYPE"
  if [[ "$OSTYPE" == "darwin"* || "$OSTYPE" == "linux-gnu"* ]]; then
    python3 install.py
  else
    python install.py
  fi

  . ./venv/bin/activate
  export IN_ACTIVATED_ENV=1
  export PATH="./:$PATH"
  echo "Environment created."
  pip install -e .
  exit 0
fi

. ./venv/bin/activate
export PATH="./:$PATH"
"""
HERE = os.path.dirname(__file__)
os.chdir(os.path.abspath(HERE))


def _exe(cmd: str, check: bool = True) -> None:
    msg = (
        "########################################\n"
        f"# Executing '{cmd}'\n"
        "########################################\n"
    )
    print(msg)
    sys.stdout.flush()
    sys.stderr.flush()
    # os.system(cmd)
    subprocess.run(cmd, shell=True, check=check)


def is_tool(name):
    """Check whether `name` is on PATH."""
    from shutil import which as find_executable

    return find_executable(name) is not None


def platform_ensure_python_installed() -> None:
    try:
        python_x = "python" if sys.platform == "win32" else "python3"
        stdout = subprocess.check_output([python_x, "--version"], universal_newlines=True)
        print(f"Python is already installed: {stdout}")
        return
    except Exception:
        pass
    if sys.platform == "darwin":
        _exe("brew install python3")
    elif sys.platform == "linux":
        _exe("sudo apt-get install python3")
    elif sys.platform == "win32":
        _exe("choco install python3")


def get_pip() -> str:
    if sys.platform == "win32":
        return "pip"
    return "pip3"

def create_virtual_environment() -> None:
    pip = get_pip()
    if not is_tool("virtualenv"):
        _exe(f"{pip} install virtualenv")
    # Which one is better? virtualenv or venv? This may switch later.
    try:
        _exe("virtualenv -p python310 venv")
    except subprocess.CalledProcessError as exc:
        warnings.warn(f"virtualenv failed because of {exc}, trying venv")
        try:
            _exe("python3 -m venv venv")
        except subprocess.CalledProcessError as exc2:
            warnings.warn(f"couldn't make virtual environment because of {exc2}")
            raise exc2

    # _exe('python3 -m venv venv')
    # Linux/MacOS uses bin and Windows uses Script, so create
    # a soft link in order to always refer to bin for all
    # platforms.
    if sys.platform == "win32":
        target = os.path.join(HERE, "venv", "Scripts")
        link = os.path.join(HERE, "venv", "bin")
        if not os.path.exists(link):
            _exe(f'mklink /J "{link}" "{target}"', check=False)
    with open("activate.sh", encoding="utf-8", mode="w") as fd:
        fd.write(_ACTIVATE_SH)
    if sys.platform != "win32":
        _exe("chmod +x activate.sh")

def check_platform() -> None:
    if sys.platform == "win32":
        is_git_bash = os.environ.get("ComSpec", "").endswith("bash.exe")
        if not is_git_bash:
            print("This script only works with git bash on windows.")
            sys.exit(1)

def main() -> int:
    in_activated_env = os.environ.get("IN_ACTIVATED_ENV", "0") == "1"
    if in_activated_env:
        print(
            "Cannot install a new environment while in an activated environment. Please launch a new shell and try again."
        )
        return 1
    platform_ensure_python_installed()

    parser = argparse.ArgumentParser(description="Install the project.")
    parser.add_argument(
        "--remove", action="store_true", help="Remove the virtual environment"
    )
    args = parser.parse_args()
    if args.remove:
        print("Removing virtual environment")
        shutil.rmtree("venv", ignore_errors=True)
        return 0
    if not os.path.exists("venv"):
        create_virtual_environment()
    else:
        print(f'{os.path.abspath("venv")} already exists')
    assert os.path.exists("activate.sh"), "activate.sh does not exist"
    if os.path.exists("setup.py") or os.path.exists("pyproject.toml"):
        _exe(f"./activate.sh && pip install -e .")
    print(
        'Now use ". activate.sh" (at the project root dir) to enter into the environment.'
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
