
# /api/login

## Request

Method: POST

Mimetype: application/json

Requires:

* uid: a valid user.email or user.mobile
* passwd: raw text that will be salted and hashed to compare to the hash in the database
* command: one of 'login', 'reset-by-email', 'reset-by-sms'.

Example:

```json
{
    "uid": "user@domainname.com", 
    "passwd": "secret", 
    "command": "login"
}
```


## Response

Mimetype: application/json

Always:

* status: ok or error

Example successful login:

```json
{
  "status": "ok",
  "user": {
    "avatar": 0,
    "bio": "Some useful info about me",
    "displayName": "Jane Doe",
    "email": "janedoe@gmail.com",
    "mobile": "5551234",
    "realName": "Jane Doe",
    "status": "active",
    "tutorClass": "10.1",
    "userid": "jdoe"
  }
}
```

Example error:

```json
{
  "error_description": "Password invalid",
  "error_ref": "login",
  "error_title": "Password invalid",
  "status": "error"
}
```

## Logic

```
if request is not json:
    return error (malformed request)
if request doesn't contain fields 'uid', 'passwd' and 'command':
    return error (malformed request)
user = database query Users table where (email==request['uid']) OR (mobile==request['uid'])
if no matching users found:
    return error (user not found)
if not user.is_login_permitted():
    return error (You are blocked)
if request['command'] == 'login':
    if user.validate_password(request['passwd']):
        create session
        return ok and user profile summary data
    else:
        return error (invalid password)
elif request['command'] == 'reset-by-email':
    return error (not yet implemented)
elif request['command'] == 'reset-by-sms':
    return error (not yet implemented)
else:
    return error (malformed request)
```


