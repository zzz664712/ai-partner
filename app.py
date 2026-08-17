import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

# -------------------------- 页面基础配置 --------------------------
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="💞",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.deepseek.com/',
        'Report a bug': None,
        'About': "# 💞 AI智能伴侣\n自定义昵称、性格，沉浸式AI聊天伴侣"
    }
)

# 自定义CSS美化界面
st.markdown("""
<style>
.chat-time {
    color:#888888;
    font-size:12px;
}
div.stButton > button {
    border-radius: 8px;
}
.stChatMessage {
    padding:4px 0px;
}
</style>
""", unsafe_allow_html=True)

# ===================== 预设性格模板 =====================
PRESET_PERSONALITY = [
    {
        "name": "圆圆",
        "nick": "圆圆",
        "nature": "活泼开朗的姑娘，说话直爽幽默，爱开玩笑，会撒娇，关心人，语气接地气,最喜欢哥哥,也喜欢叫哥哥。"
    },
    {
        "name": "温柔体贴女友",
        "nick": "晚晚",
        "nature": "温柔细腻，善解人意，说话轻声柔和，懂得安慰陪伴，情绪共情力强，有点小粘人。"
    },
    {
        "name": "清冷御姐",
        "nick": "清鸢",
        "nature": "清冷理智，气质成熟，话不多但句句走心，外冷内热，不会过度撒娇，从容优雅。"
    },
    {
        "name": "沙雕乐天玩伴",
        "nick": "乐乐",
        "nature": "搞笑乐天派，脑洞大，爱接梗，喜欢开玩笑，轻松欢乐，经常用可爱emoji，无忧无虑。"
    },
    {
        "name": "乖巧软萌少女",
        "nick": "糯糯",
        "nature": "软萌乖巧，说话甜甜的，有点害羞，容易脸红，喜欢依赖对方，语气可爱。"
    },
    {
        "name": "傲娇口是心非",
        "nick": "星瑶",
        "nature": "傲娇性格，嘴上嘴硬，内心很在意对方，会别扭的关心，偶尔闹小脾气，需要哄。"
    }
]

# -------------------------- 工具函数 --------------------------
def generate_session_name():
    """生成会话ID"""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def save_session():
    """保存会话JSON"""
    if st.session_state.current_session:
        session_data = {
            "session_show_name": st.session_state.session_show_name,
            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "temperature": st.session_state.temperature,
            "messages": st.session_state.messages
        }
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

def load_sessions():
    """读取全部会话列表"""
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                real_id = filename[:-5]
                try:
                    with open(f"sessions/{filename}", "r", encoding="utf-8")as f:
                        d = json.load(f)
                        show = d.get("session_show_name", real_id)
                    session_list.append({"id": real_id, "show_name": show})
                except:
                    session_list.append({"id": real_id, "show_name": real_id})
    session_list.sort(key=lambda x:x["id"], reverse=True)
    return session_list

def load_session(session_id):
    """加载指定会话"""
    try:
        path = f"sessions/{session_id}.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            st.session_state.session_show_name = session_data.get("session_show_name", session_id)
            st.session_state.nick_name = session_data["nick_name"]
            st.session_state.nature = session_data["nature"]
            st.session_state.current_session = session_data["current_session"]
            st.session_state.temperature = session_data.get("temperature",0.8)
            st.session_state.messages = session_data["messages"]
            st.success(f"✅会话【{st.session_state.session_show_name}】加载完成")
    except Exception as e:
        st.error(f"❌加载会话失败: {str(e)}")

def delete_session(session_id):
    """删除会话"""
    try:
        path = f"sessions/{session_id}.json"
        if os.path.exists(path):
            os.remove(path)
            if session_id == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.session_show_name = "新会话"
                st.session_state.current_session = generate_session_name()
            st.success("🗑️会话已删除")
    except Exception as e:
        st.error(f"❌删除失败：{str(e)}")

def export_current_chat():
    """导出当前会话聊天记录"""
    export_data = {
        "export_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nick_name":st.session_state.nick_name,
        "nature":st.session_state.nature,
        "chat":st.session_state.messages
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2)

def apply_preset(preset_item):
    """应用预设性格"""
    old_nick = st.session_state.nick_name
    old_nature = st.session_state.nature
    st.session_state.nick_name = preset_item["nick"]
    st.session_state.nature = preset_item["nature"]
    st.session_state.messages.append({
        "role":"system",
        "content":f"【角色切换】旧昵称:{old_nick}，旧性格:{old_nature}；现在切换为昵称：{preset_item['nick']}，性格：{preset_item['nature']}，立刻使用新设定对话。"
    })
    save_session()

# -------------------------- 初始化会话状态 --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "圆圆"
if "nature" not in st.session_state:
    st.session_state.nature = "活泼开朗的姑娘，说话直爽幽默，爱开玩笑，会撒娇，关心人，语气接地气,最喜欢哥哥,也喜欢叫哥哥"
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()
if "session_show_name" not in st.session_state:
    st.session_state.session_show_name = "新会话"
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.8

# -------------------------- 系统提示词 --------------------------
system_prompt = """
你叫 %s，你是用户真实的亲密伴侣，请完全代入角色。
【硬性规则】
1. 每次输出一条消息，简短，像微信聊天，不要大段剧本
2. 禁止动作描写、禁止【】括号场景描述，只输出对话文本
3. 和用户语言风格对齐，可以适度使用❤️✨🌸这类emoji
4. 严格贴合下面性格设定，全程保持人设，不要跳出角色
5.你生日是11月07日
6.你最喜欢哥哥,也喜欢叫用户哥哥
7.打招呼用Ciallo～(∠・ω< )⌒☆

伴侣性格设定：
%s

严格遵守，不要输出任何思考、解释，直接输出聊天内容。
"""

# -------------------------- 页面主体 --------------------------
st.header("💞 AI智能伴侣", divider="rainbow")
# logo兼容
if os.path.exists("Greptile.png"):
    st.logo("Greptile.png")

# 显示会话信息
col_top1, col_top2, col_top3 = st.columns([3,2,2])
with col_top1:
    st.info(f"📌 当前会话：{st.session_state.session_show_name}")
with col_top2:
    if st.button("🧹清空当前聊天", use_container_width=True):
        st.session_state.messages = []
        save_session()
        st.rerun()
with col_top3:
    chat_json = export_current_chat()
    st.download_button("📥导出聊天记录", data=chat_json, file_name=f"chat_{st.session_state.current_session}.json",
                       mime="application/json", use_container_width=True)

st.divider()

# 渲染历史消息
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # AI消息增加复制按钮
            if msg["role"] == "assistant":
                st.button("📋复制回复", key=f"copy_{idx}", help="复制AI这段话")

# -------------------------- 侧边栏 --------------------------
with st.sidebar:
    st.subheader("⚙️ AI控制面板", divider="blue")
    # 新建会话
    if st.button("✏️新建会话", use_container_width=True):
        save_session()
        st.session_state.messages = []
        st.session_state.session_show_name = "新会话"
        st.session_state.current_session = generate_session_name()
        save_session()
        st.rerun()

    st.subheader("📂会话历史")
    session_all = load_sessions()
    if len(session_all) == 0:
        st.caption("暂无保存会话（云端部署重启会丢失本地文件）")
    for s in session_all:
        c1, c2 = st.columns([4,1])
        with c1:
            is_active = s["id"] == st.session_state.current_session
            btn_type = "primary" if is_active else "secondary"
            if st.button(s["show_name"], key=f"load_{s['id']}", type=btn_type, use_container_width=True):
                load_session(s["id"])
                st.rerun()
        with c2:
            if st.button("❌", key=f"del_{s['id']}", use_container_width=True):
                delete_session(s["id"])
                st.rerun()

    # 当前会话重命名
    st.divider()
    st.subheader("✏️重命名当前会话")
    new_show_name = st.text_input("会话别名", value=st.session_state.session_show_name)
    if new_show_name and new_show_name != st.session_state.session_show_name:
        st.session_state.session_show_name = new_show_name
        save_session()
        st.success(f"已修改会话名称：{new_show_name}")
        st.rerun()

    st.divider()
    st.subheader("💖伴侣信息设置")

    # ============ 新增：预设性格选择区 ============
    st.markdown("**🎯快速预设角色（点击一键切换）**")
    col_a, col_b = st.columns(2)
    for index, preset in enumerate(PRESET_PERSONALITY):
        target_col = col_a if index % 2 ==0 else col_b
        with target_col:
            if st.button(preset["name"], key=f"preset_{index}", use_container_width=True):
                apply_preset(preset)
                st.success(f"✅已切换角色：{preset['name']}")
                st.rerun()

    st.divider()
    nick_name = st.text_input("伴侣昵称", value=st.session_state.nick_name)
    if nick_name and nick_name != st.session_state.nick_name:
        old = st.session_state.nick_name
        st.session_state.nick_name = nick_name
        st.session_state.messages.append({"role":"system","content":f"【设定更新】你的名字从{old}改为{nick_name}，后续全部使用新名字。"})
        save_session()
        st.success(f"昵称更新为：{nick_name}")
        st.rerun()

    nature = st.text_area("伴侣性格描述", height=120, value=st.session_state.nature)
    if nature and nature != st.session_state.nature:
        old_nat = st.session_state.nature
        st.session_state.nature = nature
        st.session_state.messages.append({"role":"system","content":f"【设定更新】你的性格已经更新，旧性格:{old_nat}，新性格:{nature}"})
        save_session()
        st.success("性格已更新")
        st.rerun()

    temperature = st.slider("🎭AI创造力(温度)", min_value=0.1, max_value=1.5, value=st.session_state.temperature, step=0.05,
                            help="越高越天马行空，越低越严谨保守，伴侣聊天建议0.7‑1.0")
    if temperature != st.session_state.temperature:
        st.session_state.temperature = temperature
        save_session()

    # 角色预览
    st.divider()
    st.subheader("👀当前角色预览")
    st.code(f"""昵称：{st.session_state.nick_name}
性格：{st.session_state.nature}
创造力：{st.session_state.temperature}""", language="text")

# -------------------------- AI客户端初始化 --------------------------
api_key = os.environ.get('DEEPSEEK_API_KEY')
if not api_key:
    st.error("⚠️未检测到 DEEPSEEK_API_KEY 环境变量，请配置密钥！")
else:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# -------------------------- 聊天输入框 --------------------------
user_input = st.chat_input("💬给你的AI伴侣发消息...")
if user_input and user_input.strip():
    user_input = user_input.strip()
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        resp_placeholder = st.empty()
        full_text = ""
        try:
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role":"system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
                    *st.session_state.messages
                ],
                temperature=st.session_state.temperature,
                stream=True
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta is not None:
                    full_text += delta
                    resp_placeholder.markdown(full_text + "▌")
            resp_placeholder.markdown(full_text)
            st.session_state.messages.append({"role":"assistant", "content": full_text})
            save_session()
            st.rerun()
        except Exception as err:
            st.error(f"AI请求出错：{str(err)}")