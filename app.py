import streamlit as st
import json
import networkx as nx
import faiss
import numpy as np
import ollama
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import re
import os

# Load base resources
def load_base_resources():
    index = faiss.read_index("curriculum_index.faiss")
    with open("curriculum_metadata.json", "r", encoding='utf-8') as f:
        metadata_store = json.load(f)
    G = nx.readwrite.node_link_graph(json.load(open("curriculum_graph.json", "r", encoding='utf-8')), edges="edges")
    return index, metadata_store, G

index, metadata_store, G = load_base_resources()

# Get list of learning areas
learning_areas = sorted(set(chunk["metadata"]["learning_area"] for chunk in metadata_store))

# Levels dropdown options
levels = ["Foundation"] + [f"Year {i}" for i in range(1, 11)]

# Hybrid retrieval function
def query_graph_rag(query, selected_area, selected_level, top_k=3):
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        st.error(f"Oops! Something went wrong with the learning tool: {e}")
        return []

    level_map = {"Foundation": "Foundation"} | {f"YearElena: "Level {i}" for i in range(1, 11)}
    selected_level_internal = level_map[selected_level]

    filtered_chunks = [
        (i, chunk) for i, chunk in enumerate(metadata_store)
        if chunk["metadata"]["learning_area"] == selected_area
        and (selected_level_internal in chunk["metadata"]["level"] or chunk["metadata"]["level"] == "Unknown")
    ]
    
    if not filtered_chunks:
        return []

    filtered_indices = [i for i, _ in filtered_chunks]
    filtered_texts = [chunk["text"] for _, chunk in filtered_chunks]
    try:
        filtered_embeddings = np.array([model.encode(text).astype('float32') for text in filtered_texts])
        query_embedding = model.encode(query).astype('float32').reshape(1, -1)
        distances, indices = index.search(query_embedding, top_k)
    except Exception as e:
        st.error(f"Uh-oh! Trouble with the magic words: {e}")
        return []

    results = []
    for idx in indices[0]:
        if idx < len(filtered_chunks):
            chunk_idx, chunk = filtered_chunks[idx]
            results.append({
                "chunk_id": chunk["id"],
                "text": chunk["text"]
            })
    
    return results

# Get available Ollama models with environment variable
def get_ollama_models():
    try:
        ollama_host = os.getenv("OLLAMA_HOST", "localhost:11434")
        response = ollama.Client(host=ollama_host).list()
        models = [model.model for model in response.get("models", [])]
        return models if models else ["llama3"]
    except Exception as e:
        st.error(f"Failed to connect to the tutor robot: {e}")
        return ["llama3"]

# Fetch models
ollama_models = get_ollama_models()

# Register monochrome emoji font (Segoe UI Emoji for Windows)
emoji_font = "Segoe UI Emoji"
try:
    pdfmetrics.registerFont(TTFont("Segoe UI Emoji", "seguiemj.ttf"))
except:
    st.warning("Segoe UI Emoji not found. Emojis may not display in PDF. Using default font instead.")
    emoji_font = "Helvetica"

# Function to create PDF with professional formatting
def create_pdf(content, filename="lesson.pdf"):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=20, bottomMargin=20, leftMargin=20, rightMargin=20)
    styles = getSampleStyleSheet()
    
    # Custom styles with monochrome emoji font
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName=emoji_font,
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=12,
        alignment=1,  # Center
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName=emoji_font,
        fontSize=12,
        leading=14,  # Line spacing
        spaceAfter=8,
    )
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=emoji_font,
        fontSize=10,
        textColor=colors.grey,
        spaceBefore=12,
        alignment=1,  # Center
    )
    note_style = ParagraphStyle(
        'Note',
        parent=styles['Normal'],
        fontName=emoji_font,
        fontSize=8,
        textColor=colors.black,
        spaceBefore=6,
        alignment=0,  # Left
    )
    
    story = []
    
    # Add curriculum note at the top
    story.append(Paragraph("This content is based on the Victorian Curriculum F–10 Version 2.0.", note_style))
    story.append(Spacer(1, 12))
    
    # Split content into lines
    lines = content.split('\n')
    current_section = []
    
    for line in lines:
        line = line.strip()
        if line.startswith("### "):  # Title
            if current_section:
                story.append(Paragraph("<br/>".join(current_section), body_style))
                current_section = []
            title = re.sub(r'### (.+)', r'\1', line)
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
        elif line == "---":
            if current_section:
                story.append(Paragraph("<br/>".join(current_section), body_style))
                current_section = []
            story.append(Spacer(1, 12))
        elif line.startswith("**") and line.endswith("**"):
            if current_section:
                story.append(Paragraph("<br/>".join(current_section), body_style))
                current_section = []
            footer = line.replace("**", "")
            story.append(Paragraph(footer, footer_style))
        elif line:
            current_section.append(line)
    
    if current_section:
        story.append(Paragraph("<br/>".join(current_section), body_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Streamlit UI with professional theme
st.set_page_config(page_title="Curriculum Tutor", page_icon="📚")
st.title("📚 Curriculum Tutor")

# Sidebar: Learning Hub
with st.sidebar:
    st.header("Learning Hub")
    st.write("Select your learning options below:")
    st.markdown("---")
    st.write("📅 **Select Year Level**")
    st.write("📖 **Select Subject** (for Custom)")
    st.write("📋 **Select Activity Type**")
    st.write("🤖 **Select Model**")
    st.write("❓ **Enter Query** (for Custom)")
    st.markdown("---")
    st.write("Aligned with the Victorian Curriculum F–10 Version 2.0.")

# Main interface
st.subheader("What Would You Like to Explore Today?")
st.write("This content is based on the *Victorian Curriculum F–10 Version 2.0*.")

# Define question_type first
question_type = st.selectbox("Select Activity Type", ["Story", "Maths", "Science", "Custom"], index=3, help="Choose an activity type.")  # Default Custom

# Layout
col1, col2, col3 = st.columns(3)
with col1:
    selected_level = st.selectbox("Select Year Level", levels, index=2, help="Choose your year level.")  # Default Year 2
with col2:
    if question_type == "Custom":
        selected_area = st.selectbox("Select Subject", learning_areas, index=learning_areas.index("Science"), help="Choose a subject.")
    else:
        selected_area = None
        st.write("No subject selection required.")
with col3:
    st.write(f"Activity Type: {question_type}")

selected_model = st.selectbox("Select Model", ollama_models, index=0, help="Choose a model to generate content.")

# Custom query input
if question_type == "Custom":
    query = st.text_input("Enter Your Query (e.g., 'What are reading strategies?')", "CPU")
else:
    query = f"Generate a {question_type.lower()} activity for {selected_level}"
    st.write(f"Ready to generate a {question_type} activity for {selected_level}. Click below!")

# Button for all types
if st.button("Generate Activity"):
    if question_type == "Custom" and not query:
        st.warning("Please enter a query first.")
    else:
        with st.spinner("Generating your activity..."):
            if question_type == "Custom":
                results = query_graph_rag(query, selected_area, selected_level, top_k=3)
                context = "\n\n".join([f"Excerpt: {r['text']}" for r in results]) if results else "No curriculum data found, but I’ll provide a response!"
                
                subject_keywords = {
                    "English": ["reading", "writing", "story", "words", "sentence", "book", "letter"],
                    "Mathematics": ["number", "count", "add", "subtract", "multiply", "divide", "shape"],
                    "Science": ["plant", "animal", "weather", "space", "rock", "water", "light", "sound"],
                }

                def is_query_relevant(query, subject):
                    query_lower = query.lower()
                    return any(keyword in query_lower for keyword in subject_keywords.get(subject, []))

                if is_query_relevant(query, selected_area):
                    prompt = f"""You are a professional tutor teaching {selected_area} at {selected_level}. The student asked: '{query}'. Using this curriculum data as a guide, create an educational lesson aligned with the Victorian Curriculum F–10 Version 2.0. Keep it 1-2 pages (300-500 words) on a single page. Start with foundational concepts, progress to {selected_level} skills, and include clear examples. Use emojis like 📖, ✅, 🔍, ✍️, 📝 for Foundation to Year 6, or fewer for higher levels:\n\n{context}"""
                else:
                    examples = {
                        "Foundation": ["The sun is big and yellow!", "A bunny hops quickly.", "Flowers grow in soil!"],
                        "Year 1": ["The moon shines at night.", "Fish swim in water.", "Trees grow tall!"],
                        "Year 2": ["Stars shine in the sky!", "Frogs live near ponds.", "The sun helps plants grow!"],
                        "Year 3": ["Rivers flow to the sea.", "Birds use wings to fly.", "Magnets attract metal!"],
                        "Year 4": ["Volcanoes release lava!", "Fish live in oceans.", "Shadows change with the sun!"],
                        "Year 5": ["Planets orbit the sun!", "Wind carries seeds.", "Light creates rainbows!"],
                        "Year 6": ["Earth’s plates cause quakes!", "Clouds form rain.", "Electricity powers lights!"],
                        "Year 7": ["Cells are life’s building blocks!", "Rocks reveal Earth’s past.", "Gravity keeps us grounded!"],
                        "Year 8": ["Atoms form everything!", "Heat turns water to steam.", "Sound travels in waves!"],
                        "Year 9": ["Stars explode in space!", "Chemicals react together.", "Forces affect motion!"],
                        "Year 10": ["Genes control traits!", "Earth orbits the sun.", "Energy flows in circuits!"]
                    }.get(selected_level, ["Here’s an example sentence for you!"])
                    prompt = f"""You are a professional tutor teaching {selected_area} at {selected_level}. The student asked: '{query}'. This query doesn’t align with {selected_area}—it seems technical! Create an educational lesson aligned with the Victorian Curriculum F–10 Version 2.0, 1-2 pages (300-500 words) on a single page. Note it’s not part of {selected_area}, then use these examples for {selected_level} and expand with clear, relevant content. Use emojis like 📖, ✅, 🔍, ✍️, 📝 for Foundation to Year 6, or fewer for higher levels:\n\n{', '.join(examples)}"""
            else:
                context = f"Create a {question_type.lower()} activity for {selected_level}"
                if question_type == "Story":
                    prompt = f"""You are a professional tutor for {selected_level}. Create a narrative activity aligned with the Victorian Curriculum F–10 Version 2.0 that students at {selected_level} can read. Keep it 1-2 pages (300-500 words) on a single page. Include a short story with a setting, a challenge, and a resolution, using appropriate vocabulary. Use emojis like 📖, ✅, 🔍, ✍️, 📝, 🌳, 🐾 for Foundation to Year 6, or fewer for higher levels:\n\n{context}"""
                elif question_type == "Maths":
                    prompt = f"""You are a professional tutor for {selected_level}. Create a 'Treasure Hunt Maths Activity' aligned with the Victorian Curriculum F–10 Version 2.0 that matches {selected_level} mathematics skills. Keep it 1-2 pages (300-500 words) on a single page. Include 5 sums with answers (using addition, subtraction, or multiplication), a brief narrative about a 'Maths Explorer' solving them, and clear explanations. Use emojis like 📏, ➕, 🔢, ✏️, 🧮, 🍎, ⭐ for Foundation to Year 6, or fewer for higher levels:\n\n{context}"""
                elif question_type == "Science":
                    prompt = f"""You are a professional tutor for {selected_level}. Create a science activity aligned with the Victorian Curriculum F–10 Version 2.0 that matches {selected_level} skills. Keep it 1-2 pages (300-500 words) on a single page. Include 5 questions with answers, a brief narrative about a student investigating them, and clear explanations. Use emojis like 🔬, 🌍, 💡, 🌱, ☀️, 🐾, ⚗️ for Foundation to Year 6, or fewer for higher levels:\n\n{context}"""

            try:
                response = ollama.generate(model=selected_model, prompt=prompt)["response"]
            except Exception as e:
                st.error(f"Error generating activity: {e}")
                response = "Unable to generate the activity. Please check the model connection."
            
            st.markdown(f"### {question_type} Activity for {selected_level}")
            st.write(response)
            st.markdown("---")
            st.write("**Complete your activity!**")

            # Download PDF button
            pdf_buffer = create_pdf(response)
            st.download_button(
                label="Download as PDF",
                data=pdf_buffer,
                file_name=f"{question_type.lower()}_{selected_level.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )

# Footer
st.markdown("---")
st.write("Explore educational activities aligned with the Victorian Curriculum F–10 Version 2.0.")