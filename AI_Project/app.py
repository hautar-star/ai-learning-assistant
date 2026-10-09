import streamlit as st
from openai import OpenAI
import io
import docx
import pandas as pd
from pypdf import PdfReader
from pptx import Presentation
import urllib.parse
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="AI智能学习助手", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    .stButton>button {
        background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
        color: white;
        border-radius: 8px;
        border: none;
    }
    .stApp { background-color: #f8f9fa; }
    .stChatMessage { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

client = OpenAI(
    api_key="sk-362c7a0e5df84e7c947ff1728628360d", 
    base_url="https://api.deepseek.com"
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "wrong_book" not in st.session_state:
    st.session_state.wrong_book = []
if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0

def read_pdf(file):
    reader = PdfReader(file)
    return "".join([page.extract_text() or "" for page in reader.pages])

def read_pptx(file):
    prs = Presentation(file)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"): text += shape.text + "\n"
    return text

def read_docx(file):
    doc = docx.Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells: text += cell.text + " "
            text += "\n"
    return text

def read_excel(file):
    xls = pd.ExcelFile(file)
    text = ""
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        text += f"\n[{sheet_name}]\n" + df.to_markdown(index=False) + "\n"
    return text

def read_txt(file):
    content = file.getvalue()
    try: return content.decode("utf-8")
    except: return content.decode("gbk", errors="ignore")

def get_ai_image_url(prompt):
    short_prompt = prompt[:50].replace("\n", " ")
    encoded_prompt = urllib.parse.quote(f"educational illustration of {short_prompt}, clean diagram, flat design")
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=500&nologo=true"

with st.sidebar:
    st.title("⚙️ 控制面板")
    uploaded_file = st.file_uploader("上传课件（PDF/PPT/Word/Excel/TXT）", 
                                     type=["pdf", "ppt", "pptx", "docx", "xlsx", "xls", "csv", "txt", "md"])
    
    st.markdown("---")
    st.subheader("🎯 学习画像")
    user_level = st.selectbox("你的水平：", ["初学者", "普通学生", "学霸拔高"])
    user_style = st.selectbox("你的偏好：", ["通俗易懂", "严谨学术", "风趣幽默"])
    
    st.markdown("---")
    st.subheader("📚 错题本")
    if st.session_state.wrong_book:
        for i, q in enumerate(st.session_state.wrong_book):
            st.caption(f"{i+1}. {q}")
    else:
        st.caption("暂无错题")
    if st.button("清空错题本"):
        st.session_state.wrong_book = []
        st.rerun()

    st.markdown("---")
    st.subheader("🖼️ AI 概念配图")
    img_prompt = st.text_input("输入名词生成示意图：", placeholder="例如：神经网络、牛顿第一定律")
    if st.button("生成配图") and img_prompt:
        with st.spinner("AI 正在作画..."):
            img_url = get_ai_image_url(img_prompt)
            st.image(img_url, caption=f"AI 生成：{img_prompt}", use_container_width=True)

    st.markdown("---")
    st.subheader("⏱️ 专注番茄钟")
    if st.toggle("开启 25 分钟专注"):
        st.info("专注模式已开启，加油！")
        progress_bar = st.progress(0)
        for percent in range(100):
            time.sleep(0.02)
            progress_bar.progress(percent + 1)
        st.success("专注结束，休息一下吧！")

    st.markdown("---")
    st.metric(label="累计消耗 Token（估算）", value=f"{st.session_state.total_tokens}")
    if st.button("🧹 清空对话记录"):
        st.session_state.messages = []
        st.rerun()

if uploaded_file is not None and st.session_state.doc_text == "":
    ext = uploaded_file.name.split('.')[-1].lower()
    with st.spinner("正在解析课件，建立RAG知识库..."):
        try:
            if ext == 'pdf': text = read_pdf(uploaded_file)
            elif ext in ['ppt', 'pptx']: text = read_pptx(io.BytesIO(uploaded_file.getvalue()))
            elif ext == 'docx': text = read_docx(io.BytesIO(uploaded_file.getvalue()))
            elif ext in ['xlsx', 'xls']: text = read_excel(io.BytesIO(uploaded_file.getvalue()))
            else: text = read_txt(uploaded_file)
            st.session_state.doc_text = text[:30000]
            st.success(f"课件《{uploaded_file.name}》解析完成！")
            
            if st.session_state.doc_text:
                with st.expander("📊 查看课件高频词云"):
                    try:
                        words = " ".join(jieba.cut(st.session_state.doc_text))
                        wc = WordCloud(font_path="msyh.ttc", width=800, height=400, background_color="white").generate(words)
                        fig, ax = plt.subplots()
                        ax.imshow(wc, interpolation="bilinear")
                        ax.axis("off")
                        st.pyplot(fig)
                    except:
                        st.warning("词云生成失败，请检查系统字体文件或跳过此功能。")
        except Exception as e:
            st.error(f"文件解析失败：{e}")

st.title("🚀 自适应 AI 学习助手")
st.caption("基于大语言模型与 RAG 增强的智能学习辅助系统")
st.divider()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if "选择题" in msg["content"]:
                if st.button("➕ 加入错题本", key=f"btn_{len(st.session_state.messages)}"):
                    st.session_state.wrong_book.append(msg["content"][:50] + "...")
                    st.toast("已加入错题本！")
            
            if st.button("🔊 语音朗读", key=f"tts_{len(st.session_state.messages)}"):
                tts_js = f"""
                <script>
                    var msg = new SpeechSynthesisUtterance({repr(msg["content"][:500])});
                    msg.lang = 'zh-CN';
                    window.speechSynthesis.speak(msg);
                </script>
                """
                components.html(tts_js, height=0)

if prompt := st.chat_input("输入你的要求，比如：总结课件，出两道题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        result_area = st.empty()
        
        system_prompt = f"你是一个{user_style}的学习助手。用户水平是：{user_level}。请根据以下课件内容回答问题。\n\n"
        if st.session_state.doc_text:
            system_prompt += f"【课件内容如下】：\n{st.session_state.doc_text}\n\n"
        
        system_prompt += """请严格按以下格式输出：
1. 【核心总结】：...
2. 【知识点】：分点列出...
3. 【选择题】：一道带答案的单选题
4. 【思维导图】：用 Mermaid 语法生成知识结构图，格式为 ```mermaid graph TD ... ```
另外，如果你觉得某个概念需要配图，请在回答末尾追加一行：
![概念图](https://image.pollinations.ai/prompt/英文概念词?width=800&height=500&nologo=true)"""

        messages_for_api = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages[-5:]:
            messages_for_api.append(m)

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages_for_api,
                temperature=0.3,
                stream=True
            )
            
            def stream_generator():
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
            
            full_response = st.write_stream(stream_generator())
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            estimated_tokens = int((len(system_prompt) + len(full_response)) * 1.5)
            st.session_state.total_tokens += estimated_tokens
            
            st.download_button(
                label="📥 下载笔记 (Markdown)",
                data=full_response,
                file_name="AI学习笔记.md",
                mime="text/markdown"
            )
            
        except Exception as e:
            st.error(f"报错：{str(e)}")