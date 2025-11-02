# How to Get Your SmartSchool Token

The token is required to access your homework data from SmartSchool.

## Steps:

1. **Open SmartSchool in your browser:**
   - Go to: https://webtop.smartschool.co.il/account/login
   - Login with your username and password

2. **Open Browser DevTools:**
   - **Chrome/Edge**: Press `F12` or `Cmd+Option+I` (Mac) or `Ctrl+Shift+I` (Windows/Linux)
   - **Firefox**: Press `F12` or `Cmd+Option+I` (Mac) or `Ctrl+Shift+I` (Windows/Linux)
   - **Safari**: Enable Developer menu in Preferences → Advanced, then press `Cmd+Option+I`

3. **Find the token:**
   - **Chrome/Edge**:
     - Click the "Application" tab at the top
     - Expand "Cookies" in the left sidebar
     - Click on `https://webtopserver.smartschool.co.il`
     - Find the cookie named `webToken`
     - Double-click the "Value" to select it, then copy

   - **Firefox**:
     - Click the "Storage" tab at the top
     - Expand "Cookies" in the left sidebar
     - Click on `https://webtopserver.smartschool.co.il`
     - Find the cookie named `webToken`
     - Double-click the "Value" to select it, then copy

4. **Save the token:**
   ```bash
   # Option 1: Run this command and paste the token
   echo 'YOUR_TOKEN_HERE' > config/token.txt

   # Option 2: Create the file manually
   # Open a text editor and paste the token, save to: config/token.txt
   ```

5. **Test it:**
   ```bash
   python test_new_homework.py
   ```

## Token Expiration

Tokens typically expire after 24 hours. When you see "API returned error: view is blocked", it means your token has expired and you need to get a new one by following the steps above.

## Troubleshooting

**Can't find the webToken cookie?**
- Make sure you're logged in to SmartSchool first
- Make sure you're looking at `https://webtopserver.smartschool.co.il` (not `webtop.smartschool.co.il`)
- Try refreshing the page after login
- The token might be on the main site - check `https://webtop.smartschool.co.il` as well

**Token still not working?**
- Make sure there are no extra spaces or newlines in config/token.txt
- The token is usually a long string of characters
- Try getting a fresh token by logging out and back in
