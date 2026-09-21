# Release

```text
1. Обновить version во всех местах
2. Обновить CHANGELOG.md:

```
   ## [X.Y.Z] - YYYY-MM-DD

   ### Added
   - ...

   ### Changed
   - ...

   ### Fixed
   - ...

   Оставить только нужные секции.
```


# 3. Проверить и собрать
```
pytest
rm -rf dist/
python -m build
python -m twine check dist/*
```

# 4. Commit + tag
```
git add -A
git commit -m "release: vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
```

# 5. GitHub
```
git push origin main
git push origin vX.Y.Z
```

# 6. PyPI
```
python -m twine upload dist/*
```