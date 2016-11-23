#!/bin/bash

set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

if [[ ! -d venv ]]; then
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

python generate.py "${@}"
