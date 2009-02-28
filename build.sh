#!/bin/sh

python bin/strip.py morse.py > build/morse.py
python bin/pack.py build/morse.py > dist/morse.py