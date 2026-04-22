"""
Flask Web Interface for the Project Documentation Agent System
Wraps Agent 1 and Agent 2 with a beautiful browser UI.
"""

from flask import Flask, render_template, request, jsonify, send_file, Response
import os, json, threading, queue, sys

# Ensure stdout is UTF-8
sys.stdout.reconfigure(encoding='utf-8')

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── SSE log streaming ────────────────────────────────────────────────────────
log_queues: dict[str, queue.Queue] = {}

def stream_log(session_id: str, msg: str):
    if session_id in log_queues:
        log_queues[session_id].put(msg)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run-agent1", methods=["POST"])
def run_agent1():
    data = request.json
    topic    = data.get("topic", "").strip()
    desc     = data.get("description", "").strip()
    degree   = data.get("degree", "BE").strip() or "BE"
    dept     = data.get("dept", "Information Technology").strip() or "Information Technology"
    college  = data.get("college", "").strip()
    guide    = data.get("guide", "").strip()
    part     = data.get("part", "3").strip()
    model    = data.get("model", "phi3").strip() or "phi3"
    session  = data.get("session_id", "default")

    if not topic:
        return jsonify({"error": "Project topic is required"}), 400

    log_queues[session] = queue.Queue()

    def run():
        try:
            from agent1_prompt_generator import PromptGeneratorAgentV2, build_mega_prompt
            agent = PromptGeneratorAgentV2(ollama_model=model)

            stream_log(session, "Generating literature study titles via Ollama...")
            study_titles = agent.customizer.get_literature_study_titles(topic, desc)
            for i, t in enumerate(study_titles):
                stream_log(session, f"  2.{i+1} {t}")

            stream_log(session, "Generating module names via Ollama...")
            module_names = agent.customizer.get_module_names(topic, desc)
            for i, m in enumerate(module_names):
                stream_log(session, f"  5.{i+1} {m}")

            stream_log(session, "Building mega-prompt...")
            prompt = build_mega_prompt(
                topic=topic, degree=degree, college=college,
                department=dept, guide=guide, description=desc,
                study_titles=study_titles, module_names=module_names
            )

            import re
            safe_topic = re.sub(r"[^\w\s]", "", topic)[:30].replace(' ', '_').upper()
            fname = f"PROMPT_ALL_CHAPTERS_{safe_topic}.txt"
            fpath = os.path.join(BASE_DIR, fname)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(prompt)

            stream_log(session, f"DONE:Saved as {fname}")
            results = [{"part": "All Chapters (1-7)", "file": fname, "preview": prompt[:800]}]

            stream_log(session, f"RESULT:{json.dumps(results)}")
        except Exception as e:
            import traceback
            stream_log(session, f"ERROR:{str(e)}\n{traceback.format_exc()}")

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"session_id": session, "status": "started"})


@app.route("/api/stream/<session_id>")
def stream(session_id):
    def generate():
        q = log_queues.get(session_id)
        if not q:
            yield "data: ERROR:No session found\n\n"
            return
        while True:
            try:
                msg = q.get(timeout=120)
                yield f"data: {msg}\n\n"
                if msg.startswith("RESULT:") or msg.startswith("ERROR:"):
                    break
            except queue.Empty:
                yield "data: ERROR:Timeout\n\n"
                break
        log_queues.pop(session_id, None)
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/run-agent2", methods=["POST"])
def run_agent2():
    data       = request.json
    content_file = data.get("content_file", "").strip()
    title      = data.get("title", "").strip()
    student    = data.get("student", "").strip()
    roll       = data.get("roll", "").strip()
    college    = data.get("college", "").strip()
    dept       = data.get("dept", "").strip()
    guide      = data.get("guide", "").strip()
    hod        = data.get("hod", "").strip()
    out_file   = data.get("out_file", "FinalProjectDoc.docx").strip() or "FinalProjectDoc.docx"
    model      = data.get("model", "phi3").strip() or "phi3"
    session    = data.get("session_id", "default2")

    if not content_file:
        return jsonify({"error": "Content file path is required"}), 400

    # Strip any surrounding quotes the user may have typed
    content_file = content_file.strip('"').strip("'")
    content_path = os.path.join(BASE_DIR, content_file) if not os.path.isabs(content_file) else content_file
    if not os.path.exists(content_path):
        return jsonify({"error": f"File not found: {content_file} (looked at: {content_path})"}), 400

    out_file  = data.get("out_file", "FinalProjectDoc.docx").strip() or "FinalProjectDoc.docx"
    out_path  = os.path.join(BASE_DIR, out_file)
    degree    = data.get("degree", "B.Tech").strip() or "B.Tech"
    year      = data.get("year", "MAY 2026").strip() or "MAY 2026"

    log_queues[session] = queue.Queue()

    def run():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("agent2", os.path.join(BASE_DIR, "agent2_formatter.py"))
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            stream_log(session, "Starting Agent 2 - Document Formatter...")

            formatter = mod.DocumentFormatterAgentV2(
                ollama_model=model,
                ollama_host="http://localhost:11434",
                use_summarizer=True
            )

            with open(content_path, "r", encoding="utf-8") as f:
                tagged_content = f.read()

            stream_log(session, f"Loaded content file: {os.path.basename(content_path)}")
            stream_log(session, "Building document...")

            formatter.format_document(
                tagged_content=tagged_content,
                project_title=title,
                student_name=student,
                roll_no=roll,
                college=college,
                department=dept,
                guide=guide,
                hod=hod,
                degree=degree,
                year=year,
                output_path=out_path
            )

            stream_log(session, f"RESULT:{json.dumps({'file': out_file})}")
        except Exception as e:
            import traceback
            stream_log(session, f"ERROR:{str(e)}\n{traceback.format_exc()}")

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"session_id": session, "status": "started"})


@app.route("/api/download/<path:filename>")
def download(filename):
    # If filename is an absolute path, use it directly, else join with BASE_DIR
    path = filename if os.path.isabs(filename) else os.path.join(BASE_DIR, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404


@app.route("/api/files")
def list_files():
    files = []
    for f in os.listdir(BASE_DIR):
        if f.endswith(".txt") or f.endswith(".docx"):
            files.append({"name": f, "size": os.path.getsize(os.path.join(BASE_DIR, f))})
    return jsonify(files)


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    print("Starting Agent Web UI at http://localhost:5050")
    app.run(debug=True, port=5050, threaded=True)
