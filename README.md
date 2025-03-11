# VicEduTutor

## Victorian-Curriculum-Tutor

**Victorian-Curriculum-Tutor** is a professional educational tool designed to deliver engaging, curriculum-aligned activities for students, with a focus on primary levels (Foundation to Year 10). Built to support the *Victorian Curriculum F–10 Version 2.0*, this application offers interactive lessons in Story, Maths, Science, and Custom subjects, enhanced with emojis to captivate young learners. Packaged in Docker for seamless deployment, it leverages Streamlit for the user interface, ReportLab for PDF generation, and Ollama for content generation.

## Features
- **Curriculum Alignment:** Lessons and activities are based on the *Victorian Curriculum F–10 Version 2.0*, covering Foundation to Year 10, with extra emoji-rich content for primary students.
- **Activity Types:** Includes Narrative (Story), Treasure Hunt Maths, Science Investigation, and Custom query-based lessons.
- **Engaging Design:** Uses black-and-white emojis (e.g., 📚, ✅, 🔍, ✍️, 📝, 📏, ➕, 👢, 🔬, 🌍, 💡) to enhance readability and engagement, especially for Foundation to Year 6.
- **PDF Export:** Downloadable activity sheets in a professional format with curriculum notes.
- **Dockerized:** Ensures consistent setup across environments with a single command.
- **Extensible:** Integrates FAISS for retrieval, NetworkX for graph-based data, and Ollama for AI-generated content.

## Prerequisites
- **Docker:** Installed on your system ([Install Docker](https://docs.docker.com/get-docker/)).
- **Ollama:** Running on `localhost:11434` (separately or via Docker Compose) with a model like `llama3` pulled (`ollama pull llama3`).

## Setup Instructions

### 1. Clone the Repository:
```bash
git clone https://github.com/yourusername/Victorian-Curriculum-Tutor.git
cd Victorian-Curriculum-Tutor
```

### 2. Build the Docker Image:
```bash
docker build -t curriculum-tutor .
```

### 3. Run Ollama (if not already running):
```bash
docker run -d -p 11434:11434 ollama/ollama:latest ollama serve
ollama pull llama3
```

### 4. Run the Container:
```bash
docker run -p 8501:8501 --network host curriculum-tutor
```

### 5. Access the App:
Open your browser at [http://localhost:8501](http://localhost:8501).

