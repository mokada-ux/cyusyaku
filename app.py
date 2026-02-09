import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import os

# --- 設定 ---
FONTS_DIR = "fonts"
st.set_page_config(page_title="一括画像テキスト追加", layout="wide")

# --- 関数定義 ---
def load_fonts():
    """fontsディレクトリからフォントファイルをリストアップ"""
    if not os.path.exists(FONTS_DIR):
        os.makedirs(FONTS_DIR)
        return []
    return sorted([f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))])

def add_text_to_image(image, text, font_path, font_size, text_color, stroke_width, stroke_color, x, y):
    """画像にテキストを描画"""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    # 境界線（縁取り）描画
    if stroke_width > 0:
        draw.text((x, y), text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color)
    else:
        draw.text((x, y), text, font=font, fill=text_color)
    
    return img

# --- サイドバー設定 ---
st.sidebar.header("🛠 テキスト設定")

# 設定変更時に過去の生成データをクリア（プレビューとダウンロードの不一致を防ぐ）
def clear_cache():
    if 'zip_buffer' in st.session_state:
        del st.session_state['zip_buffer']

text_input = st.sidebar.text_input("テキスト", "Sample Text", on_change=clear_cache)

# フォント選択
available_fonts = load_fonts()
if available_fonts:
    selected_font = st.sidebar.selectbox("フォント", available_fonts, on_change=clear_cache)
    font_path = os.path.join(FONTS_DIR, selected_font)
else:
    st.sidebar.error(f"'{FONTS_DIR}' フォルダにフォントがありません。")
    font_path = "arial.ttf" # フォールバック

# スタイル設定
font_size = st.sidebar.slider("サイズ", 10, 300, 60, on_change=clear_cache)
text_color = st.sidebar.color_picker("文字色", "#FFFFFF", on_change=clear_cache)
stroke_width = st.sidebar.slider("枠線の太さ", 0, 20, 3, on_change=clear_cache)
stroke_color = st.sidebar.color_picker("枠線の色", "#000000", on_change=clear_cache)

st.sidebar.subheader("📍 位置調整")
col_x, col_y = st.sidebar.columns(2)
with col_x:
    pos_x = st.number_input("X座標", value=50, step=10, on_change=clear_cache)
with col_y:
    pos_y = st.number_input("Y座標", value=50, step=10, on_change=clear_cache)

# --- メインエリア ---
st.title("一括画像テキスト追加アプリ 🖼️")

uploaded_files = st.file_uploader(
    "1. 画像をアップロード (複数可)", 
    type=['png', 'jpg', 'jpeg', 'webp'], 
    accept_multiple_files=True
)

if uploaded_files:
    # --- プレビュー表示 ---
    st.markdown("### 2. プレビュー確認")
    st.caption("設定を変更するとリアルタイムで反映されます。問題なければ下のボタンで一括作成してください。")
    
    # 1枚目をプレビュー用に使用
    first_image = Image.open(uploaded_files[0])
    
    # プレビュー生成
    preview_img = add_text_to_image(
        first_image, text_input, font_path, font_size, text_color, stroke_width, stroke_color, pos_x, pos_y
    )
    
    # プレビュー表示（枠内に収める）
    st.image(preview_img, caption=f"プレビュー: {uploaded_files[0].name}", width=500)

    st.divider()

    # --- 一括処理ボタン ---
    st.markdown("### 3. 一括作成とダウンロード")
    
    # ボタンが押されたら処理を実行し、結果をSession Stateに保存
    if st.button("🚀 画像を一括作成する", type="primary"):
        zip_buffer = io.BytesIO()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            total = len(uploaded_files)
            for i, file in enumerate(uploaded_files):
                # 画像処理
                img = Image.open(file)
                processed = add_text_to_image(
                    img, text_input, font_path, font_size, text_color, stroke_width, stroke_color, pos_x, pos_y
                )
                
                # ZIPに追加
                img_byte = io.BytesIO()
                fmt = img.format if img.format else 'PNG'
                processed.save(img_byte, format=fmt)
                zf.writestr(f"edited_{file.name}", img_byte.getvalue())
                
                # 進捗更新
                progress_bar.progress((i + 1) / total)
                status_text.text(f"処理中... {i+1}/{total} 枚完了")
        
        # 処理完了後、データを保存
        st.session_state['zip_buffer'] = zip_buffer.getvalue()
        status_text.success(f"完了！ {total} 枚の画像を処理しました。")

    # --- ダウンロードボタン ---
    # Session Stateにデータがあればボタンを表示
    if 'zip_buffer' in st.session_state:
        st.download_button(
            label="📥 ZIPファイルをダウンロード",
            data=st.session_state['zip_buffer'],
            file_name="processed_images.zip",
            mime="application/zip"
        )
        
else:
    st.info("👈 サイドバーでテキストを設定し、画像をアップロードしてください。")
