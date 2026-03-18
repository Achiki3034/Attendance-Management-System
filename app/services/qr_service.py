import qrcode
import os
from flask import current_app

def generate_qr_code(session_token):
    """
    Generate a QR code image for an attendance session on the Railway app.
    This uses the deployed app URL and the session token.
    """
    # Railway app URL (hardcoded)
    base_url = "https://checkinhub-digital-attendance-management-systems.up.railway.app"
    
    # Full URL for this attendance session
    url = f"{base_url}/attendance/mark/{session_token}"
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generate image
    img = qr.make_image(fill_color="#1a1a2e", back_color="white")
    
    # Save image in configured directory
    filename = f"qr_{session_token[:8]}.png"
    qr_dir = current_app.config['QR_CODE_DIR']
    filepath = os.path.join(qr_dir, filename)
    img.save(filepath)
    
    return filename