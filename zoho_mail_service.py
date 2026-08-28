import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import secrets
import os
import shutil
import string
import hashlib
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# ==================== 配置 ====================
SMTP_SERVER = "smtp.zoho.com.cn"
SMTP_PORT = 465
SENDER_EMAIL = "yourname@yourname"

# ==================== 邮件密码（用户自己填写） ====================
EMAIL_PASSWORD = "不能看."  

# ==================== 硬编码账户 ====================
AUTH_ACCOUNTS = "不能看"
# ==================== 存储 Cookie（永久有效） ====================
COOKIE_STORE = {}

# ==================== 工具函数 ====================

def generate_high_entropy_cookie():
    """生成 4096 位高熵 Cookie"""
    entropy = secrets.token_bytes(512)
    cookie = hashlib.sha3_512(entropy).hexdigest() + secrets.token_hex(256)
    return cookie[:4096]


def generate_token():
    """生成 32 位令牌（随机数+字母+特殊字符）"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    token = ''.join(secrets.choice(chars) for _ in range(32))
    return token


def validate_cookie(cookie):
    """验证 Cookie 是否有效（永久有效）"""
    if cookie not in COOKIE_STORE:
        return None
    return COOKIE_STORE[cookie]


def get_upload_dir(token):
    """获取令牌对应的上传目录"""
    return os.path.join(os.path.dirname(__file__), 'uploads', token)


def delete_upload_dir(token):
    """删除令牌对应的上传目录"""
    upload_dir = get_upload_dir(token)
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
        return True
    return False


# ==================== API 接口 ====================

@app.route('/login', methods=['POST'])
def login():
    """
    登录接口
    请求体: {
        "aid": "w9M3nR8...",
        "username": "dvsadmin",
        "password": "G7#kLp$..."
    }
    返回: {"code": 200, "cookie": "xxx"}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求体不能为空"}), 400
        
        aid = data.get('aid')
        username = data.get('username')
        password = data.get('password')
        
        if not aid:
            return jsonify({"code": 400, "message": "缺少 aid"}), 400
        if not username:
            return jsonify({"code": 400, "message": "缺少 username"}), 400
        if not password:
            return jsonify({"code": 400, "message": "缺少 password"}), 400
        
        if aid not in AUTH_ACCOUNTS:
            return jsonify({"code": 401, "message": "aid 不存在"}), 401
        
        account = AUTH_ACCOUNTS[aid]
        if account['username'] != username:
            return jsonify({"code": 401, "message": "用户名错误"}), 401
        if account['password'] != password:
            return jsonify({"code": 401, "message": "密码错误"}), 401
        
        if not EMAIL_PASSWORD:
            return jsonify({"code": 500, "message": "系统未配置邮件密码，请联系管理员"}), 500
        
        cookie = generate_high_entropy_cookie()
        
        COOKIE_STORE[cookie] = {
            'aid': aid,
            'username': username
        }
        
        return jsonify({
            "code": 200,
            "message": "登录成功",
            "cookie": cookie
        })
    
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    上传附件接口
    请求: multipart/form-data
    - file: 要上传的文件
    返回: {"code": 200, "token": "xxx", "filename": "xxx"}
    """
    try:
        if 'file' not in request.files:
            return jsonify({"code": 400, "message": "缺少 file 字段"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"code": 400, "message": "未选择文件"}), 400
        
        token = generate_token()
        
        upload_dir = get_upload_dir(token)
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = file.filename
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return jsonify({
            "code": 200,
            "message": "上传成功",
            "token": token,
            "filename": filename
        })
    
    except Exception as e:
        return jsonify({"code": 500, "message": f"上传失败: {str(e)}"}), 500


@app.route('/send', methods=['POST'])
def send_email():
    """
    发件接口
    请求体: {
        "cookie": "xxx",
        "to": "dvs6666@163.com",
        "subject": "邮件主题",
        "content": "邮件内容（支持HTML）",
        "token": "xxx"  # 可选
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "message": "请求体不能为空"}), 400
        
        cookie = data.get('cookie')
        to_email = data.get('to')
        subject = data.get('subject')
        content = data.get('content')
        token = data.get('token')
        
        if not cookie:
            return jsonify({"code": 400, "message": "缺少 cookie"}), 400
        if not to_email:
            return jsonify({"code": 400, "message": "缺少收件人"}), 400
        if not subject:
            return jsonify({"code": 400, "message": "缺少主题"}), 400
        if not content:
            return jsonify({"code": 400, "message": "缺少内容"}), 400
        
        # 验证 Cookie（永久有效）
        session_data = validate_cookie(cookie)
        if not session_data:
            return jsonify({"code": 401, "message": "Cookie 无效，请重新登录"}), 401
        
        if not EMAIL_PASSWORD:
            return jsonify({"code": 500, "message": "系统未配置邮件密码，请联系管理员"}), 500
        
        # 获取附件列表（如果有令牌）
        attachments = []
        if token:
            upload_dir = get_upload_dir(token)
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    file_path = os.path.join(upload_dir, filename)
                    if os.path.isfile(file_path):
                        attachments.append(file_path)
        
        # 发送邮件
        success, result = send_mail(to_email, subject, content, attachments, EMAIL_PASSWORD)
        
        if success:
            # 发送成功后删除令牌目录（一次性使用）
            if token:
                delete_upload_dir(token)
            trigger_callback(to_email, subject, "成功")
            return jsonify({"code": 200, "message": result})
        else:
            trigger_callback(to_email, subject, f"失败: {result}")
            return jsonify({"code": 500, "message": result}), 500
    
    except Exception as e:
        return jsonify({"code": 500, "message": f"服务器错误: {str(e)}"}), 500


def send_mail(to_email, subject, content, attachments, email_password):
    """发送邮件核心函数"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if content.strip().startswith('<') or '</html>' in content.lower():
            msg.attach(MIMEText(content, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    continue
                with open(file_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = os.path.basename(file_path)
                    part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                    msg.attach(part)
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, email_password)
            server.send_message(msg)
        
        return True, "邮件发送成功"
    
    except Exception as e:
        return False, f"发送失败: {str(e)}"


def trigger_callback(to_email, subject, status):
    """回调函数"""
    print("=" * 60)
    print(f"[回调] 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[回调] 收件人: {to_email}")
    print(f"[回调] 主题: {subject}")
    print(f"[回调] 状态: {status}")
    print("=" * 60)


# ==================== 启动服务 ====================

if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), 'uploads'), exist_ok=True)
    
    print("=" * 60)
    print("Zoho 邮件发送 API 服务")
    print("=" * 60)
    print(f"SMTP 服务器: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"发件邮箱: {SENDER_EMAIL}")
    print(f"邮件密码已配置: {'✅ 是' if EMAIL_PASSWORD else '❌ 否（请先配置）'}")
    print(f"有效账户数: {len(AUTH_ACCOUNTS)}")
    print(f"Cookie 有效期: 永久")
    print("=" * 60)
    
    if not EMAIL_PASSWORD:
        print("\n⚠️ 警告: 请先在代码中设置 EMAIL_PASSWORD 变量!")
        print("   位置: 第 18 行 EMAIL_PASSWORD = '你的邮箱密码'")
        print("=" * 60)
    
    print("\n🚀 服务启动中...")
    print(f"📍 登录接口: POST http://localhost:5000/login")
    print(f"📍 上传接口: POST http://localhost:5000/upload")
    print(f"📍 发件接口: POST http://localhost:5000/send")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
