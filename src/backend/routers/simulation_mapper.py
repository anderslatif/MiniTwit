from typing import Union
from pydantic import BaseModel
from fastapi import APIRouter, Response, Query, HTTPException

from services.implementions.auth_service import Auth_Service
from services.implementions.timeline_service import Timeline_Service
from services.implementions.user_service import User_Service

router = APIRouter()

auth_service = Auth_Service()
user_service = User_Service()
timeline_service = Timeline_Service()


@router.get("/latest")
def _(response: Response):
    response.status_code = 200
    return {"latest": timeline_service.get_latest()}


@router.get("/msgs")
def _(latest: Union[str, None] = Query(default=-1), PER_PAGE: Union[int, None] = Query(default=30)):
    timeline_service.record_latest(latest)
    messages = timeline_service.get_public_timeline(PER_PAGE)
    # Messy way of doing conversion. Change it later !
    for x in messages:
        x["content"] = x["text"]
        x["user"] = x["username"]
    return messages


# This is a route that bypasses authorization and our session
# so it is implemented here
@router.get("/msgs/{username}", status_code=204)
def _(username: str, no: Union[int, None] = Query(default=100), latest: Union[int, None] = Query(default=-1)):
    timeline_service.record_latest(latest)
    if not auth_service.check_if_user_exists(username):
        raise HTTPException(status_code=404, detail="User not found")
    
    messages = timeline_service.get_follower_timeline(username, no)
    for x in messages:
        x["content"] = x["text"]
        x["user"] = x["username"]
    return messages


class MessageBody(BaseModel):
    content: Union[str, None]


# This is a route that bypasses authorization and our session
# so it is implemented here
@router.post("/msgs/{username}", status_code=204)
def _(
    response: Response,
    username: str,
    body: MessageBody,
    latest: Union[str, None] = Query(default=-1),
):

    user_id = user_service.get_user_id_from_username(username)
    if user_id is None:
        response.status_code = 404
        return {"error": "user doesn't exist"}

    timeline_service.record_latest(latest)
    user_service.post_message(user_id, body.content)
    # passing a body when redirecting is not supported
    # https://github.com/tiangolo/fastapi/issues/3963
    # thus, I must implement the route here

    return 'Your message "%s" was recorded' % body.content


class Registration(BaseModel):
    username: str
    email: str
    pwd: str


@router.post("/register", status_code=204)
def _(
    response: Response, body: Registration, latest: Union[int, None] = Query(default=-1)
):
    if auth_service.check_if_user_exists(body.username):
        response.status_code = 403
        return {"error": "username already exists"}
    
    timeline_service.record_latest(latest)
    response.status_code = 204
    auth_service.register_user(body.username, body.email, body.pwd)
    return {"success": "register success"}


class FollowMessage(BaseModel):
    follow: Union[str, None]
    unfollow: Union[str, None]


@router.get("/fllws/{username}")
def _(
    username: str,
    response: Response,
    no: Union[str, None] = Query(default=100),
    latest: Union[str, None] = Query(default=-1),
):
    user_id = user_service.get_user_id_from_username(username)

    if not user_id:
        response.status_code = 404
        return {"error": "user doesn't exist"}

    timeline_service.record_latest(latest)

    followers = user_service.get_all_followers(user_id, no)

    response.status_code = 200
    follower_names = [f["username"] for f in followers]
    return {"follows": follower_names}


@router.post("/fllws/{username}")
def _(
    username: str,
    response: Response,
    body: FollowMessage,
    latest: Union[str, None] = Query(default=-1),
):
    user_id = user_service.get_user_id_from_username(username)

    if user_id is None:
        response.status_code = 404
        return {"error": "user doesn't exist"}

    timeline_service.record_latest(latest)

    if body.follow is not None:

        if not user_service.add_follower(user_id, body.follow):
            response.status_code = 404
            return {"error": "user doesn't exist"}
        response.status_code = 204
        return ""

    elif body.unfollow is not None:
        if not user_service.remove_follower(user_id, body.unfollow):
            response.status_code = 404
            return {"error": "user doesn't exist"}

        response.status_code = 204
        return ""

    return {
        "error": "invalid request: missing the value of 'follow' or 'unfollow' in the body"
    }
