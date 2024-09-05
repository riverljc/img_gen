import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import re
import openai
from openai import OpenAI
import base64
from io import BytesIO
from PIL import Image
import streamlit as st

st.set_page_config(layout="wide")
        
@st.experimental_dialog("放大圖片")
def show_dialog(img_name: str):
    # 載入圖片
    image = Image.open(img_name)
    
    results = re.sub(r'\d+', '', img_name.name[:-4]).replace('  ',' ').split('_')
    
    if(len(results) > 1):
        prompt = results[0]
        tag = results[1]
    else: 
        prompt = results[0]
        tag = results[0]
        
    st.subheader('Prompt: ' + prompt.strip())
    
    width, height = image.size

    # 計算縮放比例
    scale = 0.4

    # 計算新的寬度和高度
    new_width = int(width * scale)
    new_height = int(height * scale)

    # 調整圖片大小
    resized_image = image.resize((new_width, new_height))

    # 顯示圖片
    st.image(resized_image)
    
    st.subheader('Tag: ' + tag.strip().replace(' ','/'))
            
    if st.button("關閉視窗", key=2):
        st.rerun()

def select_photo():
    st.write('')
    
    st.subheader('從圖庫找靈感⬇️⬇️')

    # 指定目錄路徑
    directory_path = 'data'

    # 使用 pathlib 讀取所有檔案
    files = [file for file in Path(directory_path).iterdir()]
    current_page_images = sorted(files, key=lambda x: x.stat().st_ctime, reverse=True)

    if(len(current_page_images) > 0):
        n_o_i = 8
        
        cols = st.columns(n_o_i)
        
        # 显示当前页的图片和复选框
        for i, img in enumerate(current_page_images[:48]):
            current_col = cols[i % n_o_i]
        
            with current_col:
                if st.button(f"原圖", key=f"enlarge_{i}"):
                    show_dialog(img)
                
                # 載入圖片
                image = Image.open(img)
                
                width, height = image.size

                # 縮放比例
                scale = 0.15

                # 計算新的寬度和高度
                new_width = int(width * scale)
                new_height = int(height * scale)

                # 調整圖片大小
                resized_image = image.resize((new_width, new_height))

                # 顯示圖片
                st.image(resized_image)#, caption=img_name.name[:-18]) 

def filter_words(results: str):
    # 定義要排除的詞彙
    excluded_words = {'請', '幫', '產', '產生', '給', '可否', '圖片', '圖'}

    ini_words = results.replace('、',' ').replace('。',' ').replace(',',' ').split()
    final_words = [w for w in ini_words if w not in excluded_words]
    return ' '.join(final_words)

def extract_keywords(sentence):
    client = OpenAI()
	
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": f"從以下的句子中提取重要的詞彙:\n\n{sentence}\n\n重要詞彙:"}],
        temperature=0,
        max_tokens=50
    )
	
    return filter_words(response.choices[0].message.content)

def base64_to_image(base64_string, save_path=None):
    try:
        image_data = base64.b64decode(base64_string)
        image_buffer = BytesIO(image_data)
        image = Image.open(image_buffer)
        
        if save_path:
            image.save(save_path)
            
        return image
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == '__main__':        
    st.subheader("敘述您想要的圖片內容🚀")
    text_input = st.text_area('敘述您想要的圖片內容：', label_visibility='collapsed')
       
    # 創建兩個列
    if st.button("生成圖片"):
        if text_input and len(text_input.strip()) > 0:
            text_input = text_input.strip()
            
            tags = extract_keywords(text_input)
            
            n_of_img = 2

            client = OpenAI()
            
            with st.spinner('圖片生成中... 請稍候!'):                 
                for i in range(n_of_img):
                    try:
                        response = client.images.generate(
                            model="dall-e-3",
                            prompt=text_input,
                            size="1024x1792", #"1024x1024","1792x1024"
                            quality="standard",
                            n=1,  # Each call generates one image
                            response_format='b64_json'
                        )

                        image_b64 = response.data[0].b64_json

                        # 清除特殊符號，只保留字母、中文、空白和下劃線
                        clean_string = re.sub(r'[^a-zA-Z\u4e00-\u9fff_\s]', '', text_input + '_' + tags)

                        # 使用當前時間的時間戳記
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

                        # 組合最終的檔名
                        f_name = "data/" + clean_string + timestamp + ".png"
                        
                        generated_image = base64_to_image(image_b64, f_name)
                    except openai.APIError as err:
                        err_json = err.response.json()
                        st.error(err_json['error']['message'])            
        else:  # 如果內容為空
            st.error('請輸入提示!')    
        
    select_photo()
    
