from fastapi import APIRouter, Form, Request, Response
from database import query_db, insert_in_db

router = APIRouter()

@router.post("/api/auth/login")
def login(request: Request, username: str = Form(""), password: str = Form("")):
    user = query_db('''
        select * from users where username = ?''',
                    [username], one=True)
    if user is None or not hash(password) == user['pw_hash']:
        return {"error": "username not found"}
    else:
        request.session['user_id'] = user['id']
        return {"success": "login success"}

# TODO validation


@router.post("/api/auth/register")
def register(response: Response, username: str = Form(""), email: str = Form(""), password: str = Form("")):
    user = query_db('''
        select * from users where username = ?''',
                    [username], one=True)
    if user is not None:
        response.status_code = 403
        return {"error": "username already exists"}
    else:
        response.status_code = 204
        insert_in_db('''
            insert into users (username, email, pw_hash)
            values (?, ?, ?)''',
                     [username, email, hash(password)])
        return {"success": "register success"}


@router.get("/api/auth/logout")
def logout(request: Request):
    request.session.pop('user_id', None)
    return {"success": "logout success"}
