import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import find_dotenv, load_dotenv
import os


load_dotenv(find_dotenv())
API_Key = os.getenv("API_KEY")

API_KEY = os.getenv("API_KEY")
client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="Chat con PDF", page_icon="📄")
st.title("📄 Chat que responde dudas generales y FAQs")

# ----------------------------
# Upload PDF
# ----------------------------
pdf_file = st.file_uploader("Sube un PDF", type=["pdf"])
pdf_text = None

if pdf_file is not None:
    reader = PdfReader(pdf_file)
    text_parts = [page.extract_text() for page in reader.pages if page.extract_text()]
    pdf_text = "\n".join(text_parts)
    st.success(f"PDF cargado ✅ ({len(reader.pages)} páginas)")

# ----------------------------
# HISTORIAL
# ----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "Eres un asistente en español. Usa el contenido del PDF si está disponible para responder."}
    ]

# Mostrar historial (excepto system)
for m in st.session_state["messages"]:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# ----------------------------
# CHAT
# ----------------------------
if prompt := st.chat_input("Haz tu pregunta sobre el PDF..."):
    # Guardar mensaje del usuario
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Si hay PDF, añadirlo como contexto
    messages_for_llm = st.session_state["messages"].copy()
    if pdf_text:
        messages_for_llm.insert(
            1,
            {"role": "system", "content": f"Contenido del PDF:\n\n{pdf_text}"}
        )

    # Llamada a OpenAI
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_llm,
            temperature=0.2
        )
        answer = resp.choices[0].message.content
    except Exception as e:
        answer = f"⚠️ Error al llamar OpenAI: {e}"

    # Guardar y mostrar respuesta
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
