# Fast-Permissions

Fast-Permissions is a library designed to add authentication and authorization capabilities to FastAPI applications,
particularly those using the Fast-Controller framework.

## Installation

```bash
pip install Fast-Permissions
```

For PWA functionality, install with the PWA extra:

```bash
pip install Fast-Permissions[pwa]
```

**NOTE**: The rest of the README is AI-generated.
I will rewrite once the library is in a stable state with most of the planned features implemented.

## Usage

Here's a simple example of how to use Fast-Permissions with Fast-Controller:

```python
from fastapi import FastAPI, Request
from typing import Optional

from daomodel.db import create_engine, init_db
from daomodel.fields import Identifier
from fast_controller import Resource, Action
from fast_permissions import RestrictedController
from fast_permissions.models import User
from fast_permissions.service import UserService, Unauthorized

# Define your resources
class Item(Resource, table=True):
    name: Identifier[str]
    description: Optional[str] = None

# Set up the database
engine = create_engine("sqlite:///app.db")
init_db(engine)

# Create the FastAPI app
app = FastAPI()

# Define a function to get the current user from the request
def get_current_user(request: Request) -> User:
    token = request.cookies.get('access_token')
    if not token:
        raise Unauthorized('No access token provided')

    # You'll need to provide a way to get DAOs - this is just an example
    with controller.dao_context() as daos:
        return UserService(daos).from_token(token)

# Create a RestrictedController
controller = RestrictedController(
    app=app, 
    engine=engine,
    get_current_user=get_current_user,
    public_by_default=True  # Set to False to require auth by default
)

# Register your resources, specifying which actions don't require authentication
# When public_by_default=True, all actions are public unless marked restricted
controller.register_resource(Item)

# Create an admin user (for development/testing)
# In production, you would create users through your API
controller.register_admin("secure-password")
```

## Authentication

Fast-Permissions uses cookie-based authentication with JWT tokens. Users can authenticate by sending a POST request to the `/api/sessions` endpoint:

```
POST /api/sessions
Content-Type: application/x-www-form-urlencoded

username=admin&password=secure-password
```

This will set an HTTP-only cookie with the JWT token. The authentication is handled automatically through cookies, so no manual token management is required in the browser.

## Configuration

Before using Fast-Permissions, you need to set a secret key for JWT token signing:

```python
from fast_permissions import config
config.SECRET_KEY = "your-secret-key-here"
```

## User Management

You can manage users through the User resource that is automatically registered by RestrictedController:

```python
# Create a new user
POST /user
{
  "username": "john",
  "password": "password123"
}

# Get a user
GET /user/john

# Update a user's password
PUT /user/john
{
  "password": "new-password"
}

# Delete a user
DELETE /user/john
```

## Resource Ownership

Fast-Permissions provides two base classes for resource ownership:

1. `OrphanableResource`: Resources that can exist without an owner
2. `OwnedResource`: Resources that are deleted when their owner is deleted

Example:

```python
from daomodel.fields import Identifier
from fast_permissions.models import OwnedResource

class Note(OwnedResource, table=True):
    id: Identifier[int]
    content: str
```

When a user creates a Note, they automatically become its owner. Only the owner can modify or delete the Note.


## PWA (Progressive Web App) Support

Fast-Permissions provides PWA support through the `PWAWithAuth` class, which extends the FastPWA library with authentication capabilities.

### Installation

To use PWA features, install with the PWA extra:

```bash
pip install Fast-Permissions[pwa]
```

### Basic PWA Setup

```python
from fast_permissions.pwa import PWAWithAuth

# Create a PWA with authentication
pwa = PWAWithAuth(
    title="My App",
    public_by_default=True,  # Set to False to require auth by default
    unauthorized_redirect="/login"  # Where to redirect when not authenticated
)

# Register a simple login page
pwa.register_simple_login_page()

# Create restricted pages that require authentication
@pwa.restricted_page('/dashboard', 'dashboard.html')
async def dashboard(request):
    return {'title': 'Dashboard'}

# Create public pages (no authentication required)
@pwa.page('/public', 'public.html')
async def public_page(request):
    return {'title': 'Public Page'}
```

### Custom Authentication

You can provide your own authentication function:

```python
from fastapi import Request
from fast_permissions.models import User
from fast_permissions.service import UserService, Unauthorized

def my_get_current_user(request: Request) -> User:
    # Your custom authentication logic
    token = request.cookies.get('access_token')
    if not token:
        raise Unauthorized('No token provided')
    # ... validate token and return user
    return user

pwa = PWAWithAuth(
    title="My App",
    get_current_user=my_get_current_user,
    unauthorized_redirect="/login"
)
```
