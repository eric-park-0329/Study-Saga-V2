import db as DB

def register(email: str, password: str, gender: str = "female"):
    DB.bootstrap()
    ok = DB.create_user(email, password)
    if ok:
        u = DB.auth_user(email, password)
        if u:
            DB.set_gender(u["id"], (gender or "female"))
    return ok, ("Registered" if ok else "Email already exists.")

def login(email: str, password: str):
    DB.bootstrap()
    user = DB.auth_user(email, password)
    if not user:
        return False, "Invalid credentials.", None
    token = DB.issue_session(user["id"])
    user["token"] = token
    return True, "Logged in.", user
