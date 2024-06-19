from app import crud


def decode_api_token(token):
    return crud.user.resolve_user_token(str(token))
