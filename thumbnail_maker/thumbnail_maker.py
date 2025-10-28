# bash에서
# pip install pillow
from PIL import Image, ImageDraw, ImageFont
import textwrap

def make_thumb(save_path, var_title): 
    var_max_w = 500
    var_max_h = 500
    var_font_path = "./fonts/Hakgyoansim_Allimjang_TTF_B.ttf"    # 실제 폰트 경로
    var_font_size = 45 
    # var_font_color = "#ff4d4d" # 레드 오렌지
    # var_font_color = "#d90429" # 비비드 레드 차가움
    #### var_font_color = "#e63946" # 코랄 레드
    var_font_color = "#0099FF" # 다크 퍼플레드
    # var_font_color = "#c1121f" # 퍼플레드
    var_back_color = "#f8f9fa"
    
    var_img = Image.new("RGB", (var_max_w, var_max_h), color=var_back_color)
    var_draw = ImageDraw.Draw(var_img) 
    var_font = ImageFont.truetype(var_font_path, var_font_size)

    var_title_wrap = textwrap.wrap(var_title, width=10)
    var_len_line = len(var_title_wrap)
    var_pad = 12 # 행 간격 조정


    # 첫 줄 높이 측정
    bbox = var_draw.textbbox((0, 0), var_title_wrap[0], font=var_font)
    var_textsize_h = bbox[3] - bbox[1]   
    var_y_point = (var_max_h - (var_textsize_h * var_len_line + var_pad * (var_len_line - 1))) / 2

    for var_line in var_title_wrap: 
        bbox = var_draw.textbbox((0, 0), var_line, font=var_font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        var_x_point = (var_max_w - line_w) / 2
        var_draw.text((var_x_point, var_y_point), var_line, font=var_font, fill=var_font_color)
        var_y_point += line_h + var_pad  

    var_img.save(save_path) 
    var_img.show()

title = input("제목을 입력하세요: ")
make_thumb("./썸네일.png", title)
