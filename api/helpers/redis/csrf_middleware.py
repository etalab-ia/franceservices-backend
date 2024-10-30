import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse

class CSRFMiddleware(BaseHTTPMiddleware):
	"""
	CSRF / Cross Site Request Forgery Security Middleware for Starlette and FastAPI.
		1. Add this middleware using the middleware= parameter of your app.
		2. request.state.csrftoken will now be available.
		3. Use directly in an HTML <form> POST with <input type="hidden" name="csrftoken" value="{{ csrftoken }}" />
		4. Use with javascript / ajax POST by sending a request header 'csrftoken' with request.state.csrftoken
	Notes
		Users must should start on a "safe page" (a typical GET request) to generate the initial CSRF cookie.
		Uses session level CSRF so you can use frameworks such as htmx, without issues. (https://htmx.org/)
		Token is stored in request.state.csrftoken for use in templates.
	Reference
		https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
	"""
	async def dispatch(self, request, call_next):
		CSRF_TOKEN_NAME = 'csrftoken'
		token_from_cookie = request.cookies.get(CSRF_TOKEN_NAME)
		token_from_header = request.headers.get(CSRF_TOKEN_NAME)

		if request.method not in ("GET", "HEAD", "POST", "PUT", "OPTIONS", "TRACE"):
			if not token_from_cookie or token_from_cookie != token_from_header:
				return PlainTextResponse("CSRF cookie does not match!", status_code=403)

		if not token_from_cookie:
			token_from_cookie = str(uuid.uuid4())
			response = await call_next(request)
			response.set_cookie(CSRF_TOKEN_NAME, token_from_cookie, httponly=False)
			return response

		request.state.csrftoken = token_from_cookie
		return await call_next(request)