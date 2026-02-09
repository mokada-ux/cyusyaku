import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile

def add_text_to_image(image, text, font_path, font_size, text_color, stroke_width, stroke_color, x, y):
    """画像にテキストを追加する関数"""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    
    # フォントの読み込み（失敗時はデフォルト）
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        # フォントファイルがない場合はデフォルトを使用（日本語非対応の可能性あり）
        font = ImageFont.load_default()
        st.warning("指定されたフォントが読み込めないため、デフォルトフォントを使用します。")

    # テキスト描画（境界線付き）
    draw.text((x, y), text, font=font, fill=text_color, stroke_width=stroke_width, stroke_fill=stroke_color)
    
    return img

st.title("一括画像テキスト追加アプリ 🖼️")

# --- サイドバー：設定 ---
st.sidebar.header("テキスト設定")
text_input = st.sidebar.text_input("画像に入れるテキスト", "Sample Text")

# フォント設定
st.sidebar.subheader("フォント")
uploaded_font = st.sidebar.file_uploader("フォントファイル(.ttf/.otf)をアップロード", type=["ttf", "otf"])
# デフォルトのフォントパス（アップロードがない場合）
font_path = uploaded_font if uploaded_font else "arial.ttf" 

# スタイル設定
font_size = st.sidebar.slider("文字サイズ", 10, 200, 50)
text_color = st.sidebar.color_picker("文字色", "#FFFFFF")
stroke_width = st.sidebar.slider("境界線の太さ", 0, 20, 2)
stroke_color = st.sidebar.color_picker("境界線の色", "#000000")

# 位置設定
st.sidebar.subheader("位置調整")
pos_x = st.sidebar.number_input("X座標 (横)", value=50)
pos_y = st.sidebar.number_input("Y座標 (縦)", value=50)

# --- メインエリア：画像アップロード ---
uploaded_files = st.file_uploader("画像をアップロード (複数可)", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)

if uploaded_files:
    st.write(f"合計 {len(uploaded_files)} 枚の画像を処理します。")
    
    # ZIP作成用のバッファ
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # プレビューは最初の数枚だけ表示（負荷軽減）
        st.subheader("プレビュー (最初の1枚)")
        
        for i, uploaded_file in enumerate(uploaded_files):
            # 画像を開く
            image = Image.open(uploaded_file)
            
            # フォントファイルがアップロードされているかチェック
            current_font = uploaded_font if uploaded_font else "DejaVuSans.ttf" # Linux環境(Streamlit Cloud)向けフォールバック

            # テキスト追加処理
            processed_img = add_text_to_image(
                image, text_input, current_font, font_size, text_color, stroke_width, stroke_color, pos_x, pos_y
            )
            
            # 1枚目だけ画面に表示して確認させる
            if i == 0:
                st.image(processed_img, caption="プレビュー", use_container_width=True)
            
            # 画像をバイト列に変換してZIPに追加
            img_byte_arr = io.BytesIO()
            # 元のフォーマットを維持、なければPNG
            fmt = image.format if image.format else 'PNG'
            processed_img.save(img_byte_arr, format=fmt)
            zf.writestr(f"processed_{uploaded_file.name}", img_byte_arr.getvalue())

    # ZIPダウンロードボタン
    st.download_button(
        label="すべての画像をまとめてダウンロード (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="processed_images.zip",
        mime="application/zip"
    )

# 補足説明
st.info("日本語を使用する場合は、必ず日本語対応のフォントファイル(.ttf)をサイドバーからアップロードしてください。")
