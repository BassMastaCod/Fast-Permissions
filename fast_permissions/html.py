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
    </style>
</head>
<body>
    <div class="login-form">
        <h2>Login</h2>
        <form action="${path}" method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
'''
