
set -e

deptry .
mypy .

VERSION=$(python3 increment_version.py)
python3 -m build
twine upload \
    dist/jungle_package-$VERSION.tar.gz \
    dist/jungle_package-$VERSION-py3-none-any.whl
git add pyproject.toml
git commit -m "Increment version number"
git push
