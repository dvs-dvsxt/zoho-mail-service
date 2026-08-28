# ✉️ Zoho Mail Service — SMTP Email Sending API

> A Flask-based email sending service using **Zoho SMTP**, supporting attachments, authentication, and file upload.

**Zoho Mail Service** wraps Zoho SMTP into a simple HTTP API. It provides login authentication, file upload, and email sending (with optional attachments) via a Flask server.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **Login Auth** | Authenticate before sending emails |
| 📎 **File Upload** | Upload file attachments to the server |
| 📧 **Send Email** | Send email via Zoho SMTP with text + attachments |
| 🔒 **Account Auth** | Hardcoded account validation (edit in config) |
| 🔑 **SMTP TLS** | Zoho SMTP over SSL (port 465) |

---

## 🔌 API Endpoints

### POST `/login`
Authenticate a user.
- **Params**: credentials (username/password)
- **Returns**: authentication result

### POST `/upload`
Upload a file attachment.
- **Params**: file data
- **Returns**: saved file info

### POST `/send`
Send an email.
- **Params**: recipient, subject, body, optional attachment
- **Returns**: send result

---

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- `flask`

### Configure

Edit the config section in `zoho_mail_service.py`:
```python
SMTP_SERVER = "smtp.zoho.com.cn"
SMTP_PORT = 465
SENDER_EMAIL = "yourname@yourname.com"
EMAIL_PASSWORD = "your-app-password"
```

### Run

```bash
python zoho_mail_service.py
```

---

## 📄 License

Licensed under the **MIT License**. See [LICENSE](LICENSE).

---

## ⚠️ Security Note

> Email credentials are **sensitive** — never commit real passwords. This project is for learning/reference; configure credentials securely in production (e.g., environment variables).
