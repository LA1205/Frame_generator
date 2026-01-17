'''
import os
from PIL import Image, ExifTags, ImageDraw, ImageFont
import glob
from fractions import Fraction

def process_image(input_path, output_path):
    # --- 1. 定义画布参数 ---
    CANVAS_WIDTH = 1280
    CANVAS_HEIGHT = 800
    DPI = (300, 300)
    BACKGROUND_COLOR = (255, 255, 255) # 白色背景
    
    # --- 2. 创建空白画布 ---
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color=BACKGROUND_COLOR)
    
    # --- 3. 打开输入照片并读取 EXIF 信息 ---
    try:
        photo = Image.open(input_path)
        exif_data = photo._getexif()
        exif_info = {}
        if exif_data:
            for tag, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                exif_info[tag_name] = value

        # 提取所需信息
        date_time = exif_info.get('DateTimeOriginal', 'N/A')
        camera_model = exif_info.get('Model', 'N/A')
        aperture = exif_info.get('FNumber', 'N/A')
        shutter_speed = exif_info.get('ExposureTime', 'N/A')
        iso = exif_info.get('ISOSpeedRatings', 'N/A')
        
       # 格式化 EXIF 文本
        if aperture != 'N/A':
            aperture = f"f/{aperture:.1f}" if isinstance(aperture, float) else f"f/{aperture}"

        if shutter_speed != 'N/A':
            if isinstance(shutter_speed, (int, float)):
                frac = Fraction(shutter_speed).limit_denominator(10000)
                if frac.numerator == 1:
                    # 常见情况：1/250, 1/60 等
                    shutter_speed = f"1/{frac.denominator}"
                else:
                    # 比如 2/1 → 2s, 30/1 → 30s
                    shutter_speed = f"{frac.numerator/frac.denominator:.0f}s"
            else:
                shutter_speed = str(shutter_speed)

        exif_text = (
            f"拍摄日期: {date_time} | 相机型号: {camera_model}\n"
            f"光圈: {aperture} | 快门: {shutter_speed} | 感光度: {iso}"
        )
    except Exception as e:
        print(f"无法读取 {input_path} 的 EXIF 信息或处理照片: {e}")
        exif_text = "无法读取 EXIF 信息"
        photo = None

    if photo:
        # --- 4. 调整照片大小和位置 (约占 50%) ---
        # 目标尺寸基于画布的 50% 面积，需要考虑长宽比
        # 假设希望照片在宽度或高度上占画布的约 70% 左右以达到 50% 面积的效果
        target_width = int(CANVAS_WIDTH * 0.7)
        target_height = int(CANVAS_HEIGHT * 0.7)

        photo.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        
        # 计算粘贴位置居中
        x = (CANVAS_WIDTH - photo.width) // 2
        y = (CANVAS_HEIGHT - photo.height) // 2
        
        canvas.paste(photo, (x, y))

    # --- 5. 在底部添加 EXIF 文本 ---
    draw = ImageDraw.Draw(canvas)
    try:
        # 尝试使用微软雅黑或默认字体
        font = ImageFont.truetype("msyh.ttc", 14)
    except IOError:
        font = ImageFont.load_default()
        print("使用默认字体，文本样式可能不理想。")

    # 测量文本大小以居中放置
    # PIL 的 textbbox 方法可以获取文本边界框
    bbox = draw.textbbox((0, 0), exif_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 放置在画布底部合适位置，例如底部留白 30 像素
    text_x = (CANVAS_WIDTH - text_width) // 2
    text_y = CANVAS_HEIGHT - text_height - 50

    draw.text((text_x, text_y), exif_text, font=font, fill=(0, 0, 0)) # 黑色文本

    # --- 6. 保存图片为 JPG 格式，设置 DPI ---
    canvas.save(output_path, "JPEG", dpi=DPI, quality=90) # quality 参数控制图片质量
    print(f"成功保存图片至: {output_path}")

def batch_process(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 查找所有 jpg 和 png 格式的图片
    files = glob.glob(os.path.join(input_dir, '*.jpg')) + glob.glob(os.path.join(input_dir, '*.png'))
    files += glob.glob(os.path.join(input_dir, '*.jpeg'))

    if not files:
        print(f"在 {input_dir} 目录中未找到任何图片。")
        return

    for file_path in files:
        file_name = os.path.basename(file_path)
        # 将输出文件扩展名统一改为 .jpg
        output_file_name = os.path.splitext(file_name)[0] + '.jpg' 
        output_path = os.path.join(output_dir, output_file_name)
        print(f"正在处理: {file_name}")
        process_image(file_path, output_path)

if __name__ == "__main__":
    # --- 指定输入输出路径 ---
    INPUT_DIR = r"V:\input_photos"  # 替换为您的输入目录路径
    OUTPUT_DIR =r"V:\output_images" # 替换为您的输出目录路径

    batch_process(INPUT_DIR, OUTPUT_DIR)
'''
import os
from PIL import Image, ExifTags, ImageDraw, ImageFont
import glob
from fractions import Fraction

def format_exposure_time(value, long_exposure_as_seconds=True):
    frac = None
    if isinstance(value, tuple) and len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
        num, den = value
        frac = Fraction(num, den).limit_denominator(10000)
    elif hasattr(value, 'numerator') and hasattr(value, 'denominator'):
        frac = Fraction(int(value.numerator), int(value.denominator)).limit_denominator(10000)
    else:
        try:
            frac = Fraction(float(value)).limit_denominator(10000)
        except Exception:
            return str(value)

    if frac < 1:
        return f"1/{frac.denominator}"
    else:
        if long_exposure_as_seconds:
            seconds = frac.numerator / frac.denominator
            if abs(round(seconds) - seconds) < 1e-6:
                return f"{int(round(seconds))}s"
            else:
                return f"{seconds:.1f}s"
        else:
            return f"{frac.numerator}/{frac.denominator}s"

def process_image(input_path, output_path):
    CANVAS_WIDTH = 1280
    CANVAS_HEIGHT = 800
    DPI = (300, 300)
    BACKGROUND_COLOR = (255, 255, 255)
    canvas = Image.new('RGB', (CANVAS_WIDTH, CANVAS_HEIGHT), color=BACKGROUND_COLOR)

    try:
        photo = Image.open(input_path)
        exif_data = photo._getexif()
        exif_info = {}
        if exif_data:
            for tag, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                exif_info[tag_name] = value

        # 提取所需信息
        date_time = exif_info.get('DateTimeOriginal', 'N/A')
        camera_model = exif_info.get('Model', 'N/A')
        aperture = exif_info.get('FNumber', 'N/A')
        shutter_speed = exif_info.get('ExposureTime', 'N/A')
        iso = exif_info.get('ISOSpeedRatings', 'N/A')
        focal_length = exif_info.get('FocalLength', 'N/A')
        lens_model = exif_info.get('LensModel', 'N/A')
        exposure_bias = exif_info.get('ExposureBiasValue', 'N/A')

        # 格式化 EXIF 文本
        if aperture != 'N/A':
            aperture = f"f/{aperture:.1f}" if isinstance(aperture, float) else f"f/{aperture}"
        if shutter_speed != 'N/A':
            shutter_speed = format_exposure_time(shutter_speed)
        if focal_length != 'N/A':
            if isinstance(focal_length, (int, float)):
                focal_length = f"{focal_length:.0f}mm"
            elif hasattr(focal_length, 'numerator') and hasattr(focal_length, 'denominator'):
                focal_length = f"{focal_length.numerator / focal_length.denominator:.0f}mm"
            else:
                focal_length = str(focal_length)
        if exposure_bias != 'N/A':
            if isinstance(exposure_bias, (int, float)):
                exposure_bias = f"{exposure_bias:+.1f} EV"
            elif hasattr(exposure_bias, 'numerator') and hasattr(exposure_bias, 'denominator'):
                val = exposure_bias.numerator / exposure_bias.denominator
                exposure_bias = f"{val:+.1f} EV"
            else:
                exposure_bias = str(exposure_bias)

        exif_text = (
            f"拍摄日期: {date_time} | 相机型号: {camera_model} | 镜头型号: {lens_model}\n"
            f"光圈: {aperture} | 快门: {shutter_speed} | 感光度: {iso}\n"
            f"焦距: {focal_length} | 曝光补偿: {exposure_bias}"
        )
    except Exception as e:
        print(f"无法读取 {input_path} 的 EXIF 信息或处理照片: {e}")
        exif_text = "无法读取 EXIF 信息"
        photo = None

    if photo:
        target_width = int(CANVAS_WIDTH * 0.7)
        target_height = int(CANVAS_HEIGHT * 0.7)
        photo.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        x = (CANVAS_WIDTH - photo.width) // 2
        y = (CANVAS_HEIGHT - photo.height) // 2
        canvas.paste(photo, (x, y))

    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("msyh.ttc", 14)
    except IOError:
        font = ImageFont.load_default()
        print("使用默认字体，文本样式可能不理想。")

    bbox = draw.textbbox((0, 0), exif_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (CANVAS_WIDTH - text_width) // 2
    text_y = CANVAS_HEIGHT - text_height - 50
    draw.text((text_x, text_y), exif_text, font=font, fill=(0, 0, 0))

    canvas.save(output_path, "JPEG", dpi=DPI, quality=90)
    print(f"成功保存图片至: {output_path}")

def batch_process(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    files = glob.glob(os.path.join(input_dir, '*.jpg')) + glob.glob(os.path.join(input_dir, '*.png'))
    files += glob.glob(os.path.join(input_dir, '*.jpeg'))

    if not files:
        print(f"在 {input_dir} 目录中未找到任何图片。")
        return

    for file_path in files:
        file_name = os.path.basename(file_path)
        output_file_name = os.path.splitext(file_name)[0] + '.jpg'
        output_path = os.path.join(output_dir, output_file_name)
        print(f"正在处理: {file_name}")
        process_image(file_path, output_path)

if __name__ == "__main__":
    INPUT_DIR = r"V:\input_photos"
    OUTPUT_DIR = r"V:\output_images"
    batch_process(INPUT_DIR, OUTPUT_DIR)
