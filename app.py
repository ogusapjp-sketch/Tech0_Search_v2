import streamlit as st
import json
import os
from crawler import crawl_url
from search_fulltext import search_fulltext

st.set_page_config(page_title="Tech0 Search v0.2", layout="wide")  # 画面を広く使う

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "pages.json")

@st.cache_data
def load_pages():
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:   
            return json.load(f)
    except FileNotFoundError:
        return[]

def save_pages(pages):
        with open(JSON_PATH, "w", encoding="utf-8") as f:   
            json.dump(pages, f, ensure_ascii=False, indent=2)

def next_id(pages_list):
    """pages が list[dict]（各要素に 'id' を持つ）想定。最大ID+1を返す。"""
    if not pages_list:
        return 1
    return max((p.get("id", 0) for p in pages_list if isinstance(p, dict)), default=0) + 1

#マスターデータの読み込み
pages = load_pages()

# サイドバーを作る
with st.sidebar:
    st.markdown("🚪テスト ")
    add_selectbox = st.sidebar.selectbox(
    "検索したいカテゴリを選択してください",
    ("ALL", "製品", "事業", "自己紹介")
)

# ページ設定・タイトル
st.title("Tech0 Search v0.2")
st.caption("PROJECT ZERO -検索エンジン")
st.divider()

st.markdown("""
<style>
.scroll-box {    
    max-height: 70vh;   /* 画面高の7割を一覧用スクロール領域に */    
    overflow: auto;     /* この中だけスクロール */    
    padding-right: .5rem;
    }
</style>
""", unsafe_allow_html=True)

#検索・URLから自動登録(単体)・URLから自動登録(複数)・手動で登録・登録データ一覧・削除修正の５タブをつくる
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "検索",
        "URLから自動登録(単体)", 
        "URLから自動登録(複数)", 
        "手動で登録", 
        "登録データ一覧"
    ])

# 検索タブ
with tab1:
    query = st.text_input("検索したいキーワードを入力してください(例：DX, IoT)")
    st.divider()
    
    if query:
    #全文検索
        if query:
            results = search_fulltext(query, pages)
            
            # 絞り込み（ALL 以外のみ）
            if add_selectbox != "ALL":
                results = [r for r in results if r.get("category") == add_selectbox]
            
        else:
            results = pages
        
    #検索結果の表示
        st.success(f"検索結果件数: {len(results)} 件")
   
        for item in results:
            st.markdown(f"### [{item.get('title','無題')}]({item.get('url','#')})")
            
            #属性の表示
            st.caption(f"カテゴリ: {item.get('category','未分類')}")
            st.caption(f"入力者: {item.get('author','不明')}")
            st.caption(f"登録日: {item.get('created_at','不明')}")
            
            #キーワードの表示
            keywords = item.get("keywords", [])
            if keywords:
                st.markdown(f"**キーワード:** {', '.join(keywords)}")
            
            #プレビューの表示
            preview_text = item.get("preview", item.get("description", "")) or ""
            preview_text = str(preview_text)
            
            max_len = 180
            if preview_text:
                short = (preview_text[:max_len] + "…") if len(preview_text) > max_len else preview_text
                st.caption(short)
            
    
with tab2:
    st.markdown("### Webページを1件自動取得")
    single_url = st.text_input("取得したいURLを入力してください")
      
    if st.button("自動登録を開始"):
      if single_url:
        with st.spinner("情報を取得中・・・"):
            "クローラーモジュール呼び出し"
            new_page_data = crawl_url(single_url)
            
            if new_page_data.get("crawl_status") == "success":
                #IDの付与
                new_page_data["id"] = next_id(pages)
                pages.append(new_page_data)
                save_pages(pages)
                
                st.cache_data.clear()
                st.success(f"「{new_page_data.get('title')}」の登録が完了しました！")
                st.toast("登録が完了しました！", icon="✅")
                st.rerun()
            else:
                st.error(f"取得に失敗しました: {new_page_data.get('error')}")
      else:
          st.warning("URLを入力してください")
          
with tab3:
    st.markdown("### 複数のWebページを自動取得")
    urls_input = st.text_area("取得したいURLをURLを改行区切りで入力してください")
    
    if st.button("登録を開始"):
        if urls_input.strip():
            # 改行で分割し、空行を除外してリスト化
            url_list = [url.strip() for url in urls_input.split("\n") if url.strip()]
            
            success_count = 0
            error_count = 0
    
            # プログレスバーの表示
            progress_text = "情報を取得中..."
            my_bar = st.progress(0, text=progress_text)
    
            for i, url in enumerate(url_list):
                new_page_data = crawl_url(url)
                if new_page_data.get("crawl_status") == "success":
                    new_page_data["id"] = next_id(pages)
                    pages.append(new_page_data)
                    success_count += 1
                else:
                    error_count += 1
        
                #進捗状況の確認
                progress = (i + 1) / len(url_list)
                my_bar.progress(progress, text=f"{i+1}/{len(url_list)}件処理完了・・・")
    
            #全処理後に保存
            save_pages(pages)
            st.cache_data.clear()
    
            st.success(
                f"一括登録完了！(成功:{success_count}件, 失敗:{error_count}件)"
            )
            st.toast("登録が完了しました！", icon="✅")
            st.rerun()
        else:
            st.warning("URLを入力してください")
            
with tab4:    
    st.markdown("### 新規情報の手動登録")
    with st.form("register_form", clear_on_submit=True):
        new_title = st.text_input("タイトル", key="new_title")
        new_url = st.text_input("URL", key="new_url")
        new_desc = st.text_area("説明文", key="new_desc")
        new_author = st.text_input("担当者名", key="new_author")
        new_category = st.selectbox(
            "カテゴリ", ["自己紹介", "プロダクト", "事例", "その他"], key="new_category"
        )
        # ★【追加】キーワードの入力欄（文字列として受け取る）  
        new_keywords_input = st.text_input(
            "キーワード（カンマ区切りで入力。例: DX, AI, 営業）", key="new_keywords_input"
        )
        submitted = st.form_submit_button("登録")
               
    if submitted:
        if new_title and new_url:

            # ★【追加】文字列("DX, AI")を、カンマで分割してリスト(["DX", "AI"])に変換する
            # .strip() を使うことで、ユーザーが「DX, AI」と余計なスペースを入れても綺麗に消してくれる
            new_keywords = [
                k.strip() for k in new_keywords_input.split(",") if k.strip()
            ]
            from datetime import date  # もし上部でインポートしていなければ

            today_str = date.today().isoformat()

            new_page = {
                "id": next_id(pages),
                "title": new_title,
                "url": new_url,
                "description": new_desc,
                "full_text": "", #手動登録なので空文字
                "keywords": new_keywords,  # ★ 空リスト [] から変更し、加工したリストを入れる
                "author": new_author,
                "created_at": today_str,  # 「今日」から実際の日付にアップグレード
                "category": new_category,
            }
            pages.append(new_page)
            
            save_pages(pages)
            st.cache_data.clear()
            
            st.success("登録が完了しました！")
            st.toast("登録が完了しました！", icon="✅")
            st.rerun()
            
        else:
            st.error("タイトルとURLは必須です。")

with tab5:
    st.markdown("### 登録データ一覧")
    
    # “一覧だけ” をスクロール領域に
    st.markdown('<div class="scroll-box">', unsafe_allow_html=True)
    
    for i, item in enumerate(pages): #固定のidではなく、ループの回数(i+1)を使って綺麗に連番にする
        with st.expander(
            f"{i + 1}. {item.get('title', 'No tilte')}"):
            
             # 1. 現在のデータ表示（Read）
            st.write(f"**URL:** {item.get('url')}")
            st.write(f"**カテゴリ:** {item.get('category')}")
            st.write(f"**担当者:** {item.get('author')}")
            st.write(f"**説明:** {item.get('description')}")
            if item.get("word_count"):
                st.write(f"**文字数:** {item.get('word_count')}語")

            st.divider()  # 区切り線