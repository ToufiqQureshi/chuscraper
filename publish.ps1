# Publish to PyPI
Write-Host "Uploading chuscraper to PyPI..."
twine upload dist/*
Read-Host -Prompt "Press Enter to exit"
