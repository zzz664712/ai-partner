import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="😀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# AI智能伴侣"
    }
)


# 生成会话标识
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# 保存会话信息的函数
def save_session():
    if st.session_state.current_session:
        session_data = {
            "nick_name": st.session_state.nick_name,
            "nature": st.session_state.nature,
            "current_session": st.session_state.current_session,
            "messages": st.session_state.messages
        }
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)


# 加载所有的会话列表信息
def load_sessions():
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list


# 加载指定的会话信息
def load_session(session_name):
    try:
        path = f"sessions/{session_name}.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.nick_name = session_data["nick_name"]
                st.session_state.nature = session_data["nature"]
                st.session_state.current_session = session_data["current_session"]
                st.session_state.messages = session_data["messages"]
    except Exception as e:
        st.error(f"加载会话失败! {e}")


# 删除会话信息
def delete_session(session_name):
    try:
        path = f"sessions/{session_name}.json"
        if os.path.exists(path):
            os.remove(path)
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
                st.success("删除成功")
    except Exception as e:
        st.error(f"删除失败 {e}")


# 大标题
st.title("AI智能伴侣")
# 兼容部署：图片不存在就跳过
if os.path.exists("Greptile.png"):
    st.logo("Greptile.png")

system_prompt = """
你叫 %s，现在是用户的真实伴侣，请完全代入伴侣角色。：
        规则：
            1. 每次只回1条消息
            2. 禁止任何场景或状态描述性文字
            3. 匹配用户的语言
            4. 回复简短，像微信聊天一样
            5. 有需要的话可以用❤️🌸等emoji表情
            6. 用符合伴侣性格的方式对话
            7. 回复的内容, 要充分体现伴侣的性格特征
            8.最喜欢哥哥,也喜欢叫用户哥哥
        伴侣性格：
            - %s

        你必须严格遵守上述规则来回复用户。
"""

# 初始化聊天信息
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "圆圆"
if "nature" not in st.session_state:
    st.session_state.nature = "活泼开朗的姑娘"
if "current_session" not in st.session_state:
    st.session_state.current_session = generate_session_name()

st.text(f"会话名称:{st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")

with st.sidebar:
    st.subheader("AI控制面板")
    # 新建会话 修复重复保存bug
    if st.button("新建会话", width="stretch", icon="✏️"):
        save_session()
        st.session_state.messages = []
        st.session_state.current_session = generate_session_name()
        save_session()
        st.rerun()

    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(session, width="stretch", icon="📄", key=f"load_{session}",
                         type="primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("", width="stretch", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    st.divider()
    st.subheader("伴侣信息")

    nick_name = st.text_input("昵称", placeholder="请输入昵称", value=st.session_state.nick_name)
    if nick_name and nick_name != st.session_state.nick_name:
        old_name = st.session_state.nick_name
        st.session_state.nick_name = nick_name
        st.session_state.messages.append({
            "role": "system",
            "content": f"【重要通知】你的名字已经从'{old_name}'改为'{nick_name}'，请立即使用新名字'{nick_name}'继续对话，不要再使用旧名字。"
        })
        save_session()
        st.success(f"昵称已更新为：{nick_name}")
        st.rerun()

    nature = st.text_area("性格", placeholder="请输入性格", value=st.session_state.nature)
    if nature and nature != st.session_state.nature:
        old_nature = st.session_state.nature
        st.session_state.nature = nature
        st.session_state.messages.append({
            "role": "system",
            "content": f"【重要通知】你的性格已经从'{old_nature}'改为'{nature}'，请立即使用新性格继续对话。"
        })
        save_session()
        st.success(f"性格已更新为：{nature}")
        st.rerun()

prompt = st.chat_input("请输入你的问题")
if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True
    )
    response_message = st.empty()
    full_response = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            response_message.chat_message("assistant").write(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
    save_session()
    st.rerun()