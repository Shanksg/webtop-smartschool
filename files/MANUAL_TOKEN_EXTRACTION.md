# Quick Manual Token Extraction (2 minutes)

## Step-by-Step Instructions:

### 1. Open SmartSchool in Chrome
Open Chrome and go to: https://webtop.smartschool.co.il/

### 2. Open Developer Tools
Press `Cmd + Option + I` (or right-click → Inspect)

### 3. Go to Network Tab
Click the "Network" tab in Developer Tools

### 4. Enable "Preserve log"
Check the "Preserve log" checkbox at the top of the Network tab

### 5. Login to SmartSchool
- Enter username: **HHC129**
- Enter your password
- Solve the reCAPTCHA
- Click Login

### 6. Find the Token Request
After successful login, in the Network tab:
1. Look for a request named: **GetPupilLessonsAndHomework**
2. Click on it
3. Click the "Headers" tab
4. Scroll down to "Request Headers"
5. Find the line that says: **Authorization: Bearer [long text]**

### 7. Copy the Token
Copy ONLY the long text after "Bearer " (not including "Bearer ")

The token should look like this (very long string):
```
W/T/KaL70Rj8h9Lt7WZn4hTdj2/259fCZ2/U0BZk/1nzshfdWxbRU9r0znBx...
```

### 8. Save the Token
Once you have the token copied, paste it here and I'll save it to the config for you.

---

**Note:** The token is valid for 23 hours. You'll need to repeat this process once per day.
