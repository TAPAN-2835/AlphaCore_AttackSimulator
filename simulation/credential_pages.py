"""
HTML page generators for phishing simulation screens.
These are intentionally minimal — a real project would use Jinja2 templates.
"""

_BASE_CSS = """
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
       background:#f3f4f6;display:flex;justify-content:center;align-items:center;
       height:100vh;margin:0;}
  .card{background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.1);
        padding:40px 48px;max-width:420px;width:100%;}
  h2{margin:0 0 6px;font-size:22px;}
  p{color:#6b7280;font-size:14px;margin:0 0 24px;}
  label{display:block;font-size:13px;font-weight:600;margin-bottom:4px;color:#374151;}
  input{width:100%;padding:10px 12px;border:1px solid #d1d5db;border-radius:6px;
        font-size:14px;box-sizing:border-box;margin-bottom:16px;}
  button{width:100%;padding:11px;background:#2563eb;color:#fff;border:none;
         border-radius:6px;font-size:15px;font-weight:600;cursor:pointer;}
  button:hover{background:#1d4ed8;}
  .logo{font-size:28px;margin-bottom:20px;}
  .alert{background:#fef3c7;border:1px solid #fcd34d;border-radius:6px;
         padding:16px;font-size:14px;color:#92400e;margin-top:20px;}
  .alert strong{display:block;font-size:16px;margin-bottom:4px;}
"""


def microsoft_login_page(token: str, action_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Sign in to your account</title>
  <style>{_BASE_CSS}
    .logo{{color:#0078d4;}}
    button{{background:#0078d4;}}
    button:hover{{background:#005fa3;}}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">🔵 Microsoft</div>
    <h2>Sign in</h2>
    <p>to continue to Microsoft 365</p>
    <form method="POST" action="{action_url}">
      <input type="hidden" name="token" value="{token}">
      <label>Email or phone</label>
      <input type="text" name="username" placeholder="user@company.com" required>
      <label>Password</label>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">Next</button>
    </form>
  </div>
</body>
</html>"""


def corporate_login_page(token: str, action_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Employee Portal — Sign In</title>
  <style>{_BASE_CSS}</style>
</head>
<body>
  <div class="card">
    <div class="logo">🏢</div>
    <h2>Employee Portal</h2>
    <p>Please sign in with your corporate credentials</p>
    <form method="POST" action="{action_url}">
      <input type="hidden" name="token" value="{token}">
      <label>Corporate Email</label>
      <input type="email" name="username" placeholder="you@company.com" required>
      <label>Password</label>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">Sign In</button>
    </form>
  </div>
</body>
</html>"""


def awareness_page() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>⚠️ Phishing Simulation Alert</title>
  <style>
    body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
         background:#0f172a;display:flex;justify-content:center;align-items:center;
         height:100vh;margin:0;}
    .card{background:#1e293b;border:1px solid #f59e0b;border-radius:12px;
          padding:48px;max-width:480px;width:100%;color:#f1f5f9;}
    h1{font-size:28px;color:#f59e0b;margin:0 0 16px;}
    p{line-height:1.7;color:#94a3b8;margin:0 0 16px;}
    ul{color:#94a3b8;line-height:2;}
    .badge{display:inline-block;padding:4px 12px;background:#f59e0b22;
           border:1px solid #f59e0b;border-radius:20px;font-size:13px;
           color:#f59e0b;margin-bottom:24px;}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">⚠️ Security Awareness Training</span>
    <h1>You fell for a phishing simulation.</h1>
    <p>This was a <strong>controlled exercise</strong> run by your IT Security team.
       No real data was captured or stored.</p>
    <p>Remember these warning signs:</p>
    <ul>
      <li>Unexpected login requests via email</li>
      <li>Urgency or threats in the message</li>
      <li>Mismatched sender addresses</li>
      <li>Links that don't match the stated domain</li>
    </ul>
    <p>Please <strong>report suspicious emails</strong> to your IT Security team immediately.</p>
  </div>
</body>
</html>"""
