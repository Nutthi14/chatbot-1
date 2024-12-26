import streamlit as st
import time
from datetime import datetime
from H_supervisor import TyphoonAgent
from dotenv import load_dotenv

import os
import hashlib  # สำหรับ hash password

# กำหนด path สำหรับเก็บไฟล์และข้อมูลผู้ใช้
BASE_FOLDER = "user_data"
UPLOAD_FOLDER = "uploads"
USER_DATA_FILE = "users.txt"  # ไฟล์เก็บข้อมูลผู้ใช้
os.makedirs(BASE_FOLDER, exist_ok=True)

# ตรวจสอบว่ามีไฟล์ users.txt หรือยัง ถ้าไม่มีให้สร้าง
if not os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "w") as f:
        pass  # สร้างไฟล์เปล่า

# ตั้งค่า session_state
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []
if "current_session" not in st.session_state:
    st.session_state.current_session = None
if "username" not in st.session_state:
    st.session_state.username = None
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

# ฟังก์ชันสำหรับจัดการข้อมูลผู้ใช้
def get_user_folder(username):
    return os.path.join(BASE_FOLDER, username)

def save_user_data(username, data):
    user_folder = get_user_folder(username)
    os.makedirs(user_folder, exist_ok=True)
    with open(os.path.join(user_folder, "data.json"), "w") as f:
        json.dump(data, f)

def load_user_data(username):
    user_folder = get_user_folder(username)
    data_file = os.path.join(user_folder, "data.json")
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            return json.load(f)
    return {"chat_sessions": [], "uploaded_files": {}}

def save_current_session():
    if st.session_state.current_session is not None:
        user_data = load_user_data(st.session_state.username)
        user_data["chat_sessions"] = st.session_state.chat_sessions
        user_data["uploaded_files"] = st.session_state.uploaded_files
        save_user_data(st.session_state.username, user_data)

def load_user_sessions():
    user_data = load_user_data(st.session_state.username)
    st.session_state.chat_sessions = user_data.get("chat_sessions", [])
    st.session_state.uploaded_files = user_data.get("uploaded_files", {})


# ฟังก์ชันเริ่มต้นเซสชันใหม่
def start_new_session():
    st.session_state.current_session = None

# ฟังก์ชันเพิ่มข้อความในเซสชันปัจจุบัน
def add_to_current_session(role, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if st.session_state.current_session is not None:
        st.session_state.chat_sessions[st.session_state.current_session]["history"].append(
            {"role": role, "content": content, "timestamp": timestamp}
        )

# ฟังก์ชัน hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ฟังก์ชัน register
def register():
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    if st.button("Register"):
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        elif not new_username:
            st.error("Please Input Username.")
        else:
            hashed_password = hash_password(new_password)
            try:
                with open(USER_DATA_FILE, "r") as f:
                    for line in f:
                        user, _ = line.strip().split(",")
                        if user == new_username:
                            st.error("Username already exists.")
                            return
                with open(USER_DATA_FILE, "a") as f:
                    f.write(f"{new_username},{hashed_password}\n")
                st.success("Registration successful! Please login.")
            except Exception as e:
                st.error(f"An error occurred during registration: {e}")

# ฟังก์ชัน login (ปรับปรุง)
def login():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        hashed_password = hash_password(password)
        try:
            with open(USER_DATA_FILE, "r") as f:
                for line in f:
                    user, stored_hash = line.strip().split(",")
                    if user == username and stored_hash == hashed_password:
                        st.session_state.username = username
                        st.success("Login successful!")
                        return
            st.error("Invalid username or password.")
        except FileNotFoundError:
            st.error("No user data found. Please register.")
        except Exception as e:
            st.error(f"An error occurred during login: {e}")

# ส่วนของ app
if not st.session_state.username:
    auth_choice = st.radio("Login or Register", ("Login", "Register"))
    if auth_choice == "Login":
        login()
    else:
        register()
    st.stop()

# ส่วนของ app หลังจาก login
st.sidebar.write(f"Logged in as: {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.username = None
    st.experimental_rerun()
    
# Sidebar สำหรับการตั้งค่า
with st.sidebar.expander("⚙️ Settings", expanded=True):
    model_options = {
        "gpt-4o-mini": "GPT-4o Mini",
        "llama-3.1-405b": "Llama 3.1 405B",
        "llama-3.2-3b": "Llama 3.2 3B",
        "Gemini Pro 1.5": "Gemini Pro 1.5",
    }
    model = st.selectbox("Choose your AI Model:", options=list(model_options.keys()))
    temperature = st.slider("Set Temperature:", min_value=0.0, max_value=2.0, value=1.0)
    
    api_key = st.text_input("API Key", type="password")
    st.session_state["api_key"] = api_key

# ส่วนสำหรับอัปโหลดไฟล์ใน Sidebar
st.sidebar.markdown("### 📂 File Upload")
uploaded_files = st.sidebar.file_uploader("Choose files", accept_multiple_files=True)

# ฟังก์ชันสำหรับบันทึกไฟล์
def save_uploaded_file(username, uploaded_file):
    user_folder = get_user_folder(username)
    upload_folder = os.path.join(user_folder, "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# ฟังก์ชันโหลดไฟล์ที่เกี่ยวข้องกับผู้ใช้เมื่อเริ่มต้นเซสชัน
def load_user_files(username):
    user_folder = get_user_folder(username)
    upload_folder = os.path.join(user_folder, "uploads")
    os.makedirs(upload_folder, exist_ok=True)  # สร้างโฟลเดอร์ถ้ายังไม่มี
    return [
        os.path.join(upload_folder, file_name) for file_name in os.listdir(upload_folder)
    ]

# ส่วนจัดการไฟล์ใน Sidebar
if uploaded_files:
    if st.session_state.current_session is not None:
        if st.session_state.current_session not in st.session_state.uploaded_files:
            st.session_state.uploaded_files[st.session_state.current_session] = []

        for uploaded_file in uploaded_files:
            # บันทึกไฟล์ในโฟลเดอร์ของผู้ใช้
            file_path = save_uploaded_file(st.session_state.username, uploaded_file)
            st.session_state.uploaded_files[st.session_state.current_session].append(file_path)

        # แสดงไฟล์ที่อัปโหลดใน Sidebar
        #st.sidebar.markdown("#### Uploaded Files:")
        #for file_path in st.session_state.uploaded_files[st.session_state.current_session]:
        #    file_name = os.path.basename(file_path)
        #    st.sidebar.write(f"- {file_name}")

uploaded_file_paths = {}
if uploaded_files:
    st.sidebar.markdown("### 📂 File Upload")
    for file in uploaded_files:
        st.sidebar.write(f"- {file.name}")
        # สร้างพาธชั่วคราวสำหรับไฟล์ที่อัปโหลด
        with open(f"./{file.name}", "wb") as f:
            f.write(file.getbuffer())
        uploaded_file_paths[file.name] = f"./{file.name}"


# Sidebar สำหรับจัดการประวัติการสนทนา
st.sidebar.title("Chat History")

# ปุ่มเริ่มต้นเซสชันใหม่
if st.sidebar.button("Start New Chat"):
    if st.session_state.current_session is not None:
        # บันทึกเซสชันเก่าด้วย title จากข้อความแรก
        if len(st.session_state.chat_sessions[st.session_state.current_session]["history"]) > 0:
            first_message = st.session_state.chat_sessions[st.session_state.current_session]["history"][0]["content"]
            st.session_state.chat_sessions[st.session_state.current_session]["title"] = first_message
    start_new_session()

# แสดงรายการเซสชันใน Sidebar โดยแชทใหม่อยู่ข้างบน
if st.session_state.chat_sessions:
    for idx, session in reversed(list(enumerate(st.session_state.chat_sessions))):
        title = session.get("title", f"Session {idx + 1}")
        if st.sidebar.button(title, key=f"session_{idx}"):
            st.session_state.current_session = idx
  
def response_generator():
    load_dotenv()
    
    file_paths = uploaded_file_paths

    if not file_paths:
        st.error("Please upload files to proceed.")
        return
    
    agent = TyphoonAgent(
        temperature=0.1,
        base_url="https://api.opentyphoon.ai/v1",
        model_name="typhoon-v1.5x-70b-instruct", 
        dataset_paths=file_paths
    )

    response = agent.agent_executor.invoke({"input": user_input})
    return response['output']


st.title("Chat Application")

# Layout สำหรับการสนทนาและ Log
col1, col2 = st.columns([175, 100])  # เพิ่มสัดส่วนของคอลัมน์ด้านขวา


# คอลัมน์หลักสำหรับการสนทนา
with col1:
    chat_container = st.container()  # พื้นที่แสดงข้อความ
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # หากไม่มีเซสชัน เริ่มเซสชันใหม่
        if st.session_state.current_session is None:
            st.session_state.chat_sessions.append({"title": "", "history": []})
            st.session_state.current_session = len(st.session_state.chat_sessions) - 1

        # เพิ่มข้อความใหม่ในเซสชันปัจจุบัน
        add_to_current_session("user", user_input)

        # ตัวอย่างการตอบกลับ
        response = response_generator()
        add_to_current_session("assistant", response)

    # แสดงข้อความใน Chat
with chat_container:
    if st.session_state.current_session is not None:
        session = st.session_state.chat_sessions[st.session_state.current_session]
        st.subheader(f"Session: {session.get('title', 'New Chat')}")
        for chat in session["history"]:
            message_alignment = "flex-end" if chat["role"] == "user" else "flex-start"
            st.markdown(
                f"""
                <style>
                .message {{
                    padding: 10px;
                    border-radius: 8px;
                    max-width: 80%;
                    word-wrap: break-word;
                    background-color: var(--background-color);
                    color: invert(var(--background-color));
                    transition: background-color 0.3s ease, color 0.3s ease;
                }}
                </style>
                <div style="display: flex; justify-content: {message_alignment}; margin-bottom: 10px;">
                    <div class="message">
                        {chat['content']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )



# คอลัมน์สำหรับ Log
with col2:
    with st.expander("📝 Chat Log", expanded=False):
        if st.session_state.chat_sessions:
            for idx, session in reversed(list(enumerate(st.session_state.chat_sessions))):
                title = session.get("title", f"Session {idx + 1}")
                st.markdown(f"**{title}**")
                for chat in session["history"]:
                    st.write(f"{chat['timestamp']} | {chat['role'].capitalize()}: {chat['content']}")
        else:
            st.write("No chat logs available.")

# ปุ่มอัปโหลดไฟล์ทางซ้ายล่างสุด
st.markdown(
    """
    <style>
        #file-upload {
            position: fixed;
            bottom: 10px;
            left: 10px;
            z-index: 1000;
            background-color: #000000;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 2px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
        }
    </style>
    <div id="file-upload">
        <input type="file">
    </div>
    """,
    unsafe_allow_html=True,
)


