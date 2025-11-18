from http.server import BaseHTTPRequestHandler
import json
import base64
import io
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import traceback

class Handler(BaseHTTPRequestHandler):
    def set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.set_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            image_b64 = body.get('image', '')
            target_width = int(body.get('target_width', 200))
            
            if ',' in image_b64:
                image_b64 = image_b64.split(',')[-1]
            
            image_data = base64.b64decode(image_b64)
            img = Image.open(io.BytesIO(image_data))
            
            # 核心处理算法
            img = img.convert("L")
            w, h = img.size
            scale = target_width / w
            new_size = (target_width, int(h * scale))
            small = img.resize(new_size, Image.Resampling.LANCZOS)
            small = small.filter(ImageFilter.SHARPEN)
            
            brightened = ImageEnhance.Brightness(small).enhance(1.1)
            contrasted = ImageEnhance.Contrast(brightened).enhance(1.5)
            dithered = contrasted.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
            output = dithered.resize((w, h), Image.Resampling.NEAREST)
            output = ImageOps.invert(output.convert("L"))
            
            output_buffer = io.BytesIO()
            output.save(output_buffer, format='PNG')
            output_b64 = base64.b64encode(output_buffer.getvalue()).decode()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'image': f"data:image/png;base64,{output_b64}"
            }).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': str(e)
            }).encode())
