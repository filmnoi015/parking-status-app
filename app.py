from ultralytics import YOLO
from flask import Flask, render_template, request, jsonify, session
import os
import cv2
import glob

app = Flask(__name__)
# ต้องตั้งค่า SECRET_KEY สำหรับการใช้งาน Session
app.secret_key = 'your_super_secret_key_here' # ***เปลี่ยนข้อความนี้เป็นข้อความลับของคุณ***

# โฟลเดอร์สำหรับเก็บรูปภาพที่คุณต้องการหมุนเวียน
IMAGE_FOLDER = 'images'
os.makedirs(IMAGE_FOLDER, exist_ok=True)
app.config['IMAGE_FOLDER'] = IMAGE_FOLDER

# โหลดโมเดล YOLOv8
model = YOLO('yolov8n.pt')

# รายการชื่อไฟล์รูปภาพทั้งหมดในโฟลเดอร์ images (เรียงตามชื่อไฟล์)
# ***คุณต้องแน่ใจว่ารูปภาพของคุณถูกใส่ไว้ในโฟลเดอร์ images แล้ว***
IMAGE_FILES = sorted(glob.glob(os.path.join(IMAGE_FOLDER, '*.*')))

def count_cars_in_image(image_path):
    """
    ตรวจจับและนับจำนวนรถยนต์ในรูปภาพ
    """
    if not os.path.exists(image_path):
        return 0
    try:
        # Note: YOLOv8 model will handle HEIC conversion if necessary/supported, 
        # but it is best to convert HEIC to JPG/PNG beforehand for stability.
        results = model(image_path)
        car_count = 0
        for r in results:
            for cls in r.boxes.cls:
                # Class id 2 ในโมเดล YOLOv8 คือ 'car'
                if model.names[int(cls)] == 'car':
                    car_count += 1
        return car_count
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการประมวลผลรูปภาพ: {e}")
        return 0

def get_status_color(car_count):
    """
    คืนค่าสีตามจำนวนรถยนต์ที่กำหนดตามเงื่อนไขใหม่
    """
    if 5 <= car_count <= 6:
        return 'red'
    elif 3 <= car_count <= 4:
        return 'yellow'
    elif 1 <= car_count <= 2:
        return 'green'
    else: # สำหรับกรณี 0 คัน หรือ มากกว่า 6 คัน
        # อาจจะกำหนดสีอื่นสำหรับกรณีเกิน 6 คัน หรือกำหนดให้ 0 คันเป็นสีเขียวด้วย
        return 'green' if car_count == 0 else 'red'

@app.route('/')
def index():
    # ตรวจสอบว่ามีรูปภาพในโฟลเดอร์หรือไม่
    if not IMAGE_FILES:
        return "ไม่พบไฟล์รูปภาพในโฟลเดอร์ 'images' โปรดใส่รูปภาพเข้าไป", 500

    # ตั้งค่า index รูปภาพเริ่มต้นเป็น 0 (รูปที่ 1)
    if 'current_index' not in session:
        session['current_index'] = 0
        
    current_image_file = IMAGE_FILES[session['current_index']]
    
    # ดำเนินการนับรถและหาข้อมูลสถานะ
    car_count = count_cars_in_image(current_image_file)
    status_color = get_status_color(car_count)
    
    # ส่งชื่อไฟล์รูปภาพ (เฉพาะชื่อ) และข้อมูลสถานะไปยังหน้าเว็บ
    image_name = os.path.basename(current_image_file)
    
    return render_template('index.html', 
                           image_name=image_name,
                           car_count=car_count,
                           status_color=status_color)

@app.route('/next_image', methods=['POST'])
def next_image():
    """
    ฟังก์ชันสำหรับวนไปรูปภาพถัดไป
    """
    if not IMAGE_FILES:
        return jsonify({'error': 'ไม่พบไฟล์รูปภาพ'}), 400
        
    current_index = session.get('current_index', 0)
    
    # วนลูปไปรูปถัดไป (ถ้าถึงรูปสุดท้าย จะกลับไปรูปแรก)
    next_index = (current_index + 1) % len(IMAGE_FILES)
    session['current_index'] = next_index
    
    # ส่งสัญญาณกลับไปให้ JavaScript เพื่อโหลดหน้าใหม่
    return jsonify({'success': True})

@app.route('/images/<filename>')
def serve_image(filename):
    """
    ฟังก์ชันสำหรับดึงรูปภาพมาแสดงผลในหน้าเว็บ
    """
    return send_from_directory(app.config['IMAGE_FOLDER'], filename)

if __name__ == '__main__':
    # ***สำคัญ: ต้องสร้างโฟลเดอร์ 'images' และใส่รูปภาพทั้ง 8 รูปไว้ก่อนรันโค้ด***
    from flask import send_from_directory
    app.run(debug=True)