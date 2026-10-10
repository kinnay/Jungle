
set -e

VERSION=$(python3 increment_version.py)
python3 -m build
twine upload \
    dist/jungle_package-$VERSION.tar.gz \
    dist/jungle_package-$VERSION-py3-none-any.whl
