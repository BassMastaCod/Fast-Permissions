login_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 0; background-color: #f4f4f4; }
        .login-form { width: 300px; margin: 100px auto; padding: 20px; background: white; border: 1px solid #ccc; border-radius: 5px; }
        .login-form h2 { margin-bottom: 20px; }
        .login-form input { width: calc(100% - 20px); margin-bottom: 15px; padding: 8px; border: 1px solid #ccc; border-radius: 5px; }
        .login-form button { padding: 10px 20px; border: none; border-radius: 5px; background: #007BFF; color: white; cursor: pointer; }
        .login-form button:hover { background: #0056b3; }
        .error-message { color: red; margin-bottom: 15px; display: none; }
    </style>
</head>
<body>
    <div class="login-form">
        <h2>Login</h2>
        <div id="error-message" class="error-message"></div>
        <form id="login-form">
            <input type="text" id="username" name="username" placeholder="Username" required>
            <input type="password" id="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const loginForm = document.getElementById('login-form');
            const errorMessage = document.getElementById('error-message');

            // Get the 'from' parameter from URL, default to '../' if not present
            const urlParams = new URLSearchParams(window.location.search);
            const from = urlParams.get('from');
            const redirectTo = from && from.startsWith('/') ? from : '../';

            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();

                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;

                try {
                    errorMessage.style.display = 'none';

                    const response = await fetch('${path}', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: new URLSearchParams({
                            'grant_type': 'password',
                            'username': username,
                            'password': password,
                        }),
                        credentials: 'include'
                    });

                    if (!response.ok) {
                        if (response.status === 400) {
                            throw new Error('Incorrect username or password');
                        } else {
                            throw new Error('Login failed. Please try again.');
                        }
                    }

                    // Successful login - redirect to the appropriate page
                    window.location.href = redirectTo;

                } catch (error) {
                    errorMessage.textContent = error.message;
                    errorMessage.style.display = 'block';
                }
            });
        });
    </script>
</body>
</html>
'''
