# 🚀 How to Run SAVE2SERVE HUB

## Quick Start Guide

### Step 1: Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate
```

**Windows (Git Bash):**
```bash
source venv/Scripts/activate
```

### Step 2: Install Dependencies (if not already installed)

```bash
pip install flask
```

**Optional - For location capture feature:**
```bash
pip install geocoder
```

### Step 3: Setup Database (First Time Only)

If you're running for the first time or want to reset the database:

```bash
python setup.py
```

This will:
- Create a fresh database (`food.db`)
- Create all necessary tables
- Add test accounts:
  - **Admin**: username `admin`, password `admin123`
  - **Hotel**: email `hotel@test.com`, password `hotel123`
  - **NGO**: email `ngo@test.com`, password `ngo123`
- Add sample food items

**Note:** If `food.db` already exists, the app will use it automatically. You can skip this step if the database is already set up.

### Step 4: Run the Application

```bash
python app.py
```

The server will start on **http://localhost:5000**

### Step 5: Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

## 📋 Available Routes

- **Home**: `http://localhost:5000/`
- **Hotel Login**: `http://localhost:5000/login/hotel`
- **NGO Login**: `http://localhost:5000/login/ngo`
- **Admin Login**: `http://localhost:5000/login/admin`
- **Hotel Register**: `http://localhost:5000/register/hotel`
- **NGO Register**: `http://localhost:5000/register/ngo`

## 🔑 Test Accounts (after running setup.py)

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`

### Hotel Account
- **Email**: `hotel@test.com`
- **Password**: `hotel123`

### NGO Account
- **Email**: `ngo@test.com`
- **Password**: `ngo123`

## 🛠️ Troubleshooting

### Port 5000 Already in Use
If you get an error that port 5000 is already in use:
1. Close any other applications using port 5000
2. Or modify `app.py` line 419 to use a different port:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=True)
   ```

### Database Errors
If you encounter database errors:
1. Delete `food.db` file
2. Run `python setup.py` again to recreate the database

### Module Not Found Errors
Make sure you've activated the virtual environment and installed Flask:
```bash
pip install flask
```

### Location Capture Not Working
This is optional. The app works without it. To enable:
```bash
pip install geocoder
```

## 📝 Development Mode

The app runs in debug mode by default, which means:
- Auto-reloads when you make code changes
- Shows detailed error messages
- Not suitable for production

## 🛑 Stopping the Server

Press `Ctrl + C` in the terminal to stop the server.
