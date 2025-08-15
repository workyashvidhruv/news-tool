#!/bin/bash

echo "🚀 Pushing to GitHub..."
echo ""
echo "If you get a password prompt, use your GitHub Personal Access Token"
echo "NOT your regular GitHub password!"
echo ""
echo "To get a token:"
echo "1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)"
echo "2. Click 'Generate new token (classic)'"
echo "3. Select 'repo' permissions"
echo "4. Copy the token and use it as password"
echo ""

git push -u origin main

echo ""
echo "✅ Done! Check your GitHub repository: https://github.com/workyashvidhruv/news-tool"
