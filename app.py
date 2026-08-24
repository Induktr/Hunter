import asyncio
import threading
import gradio as gr
from src.app.main import main as run_hunter
from src.shared.core.logger import logger
from src.sensors.search_engine import search_engine
from src.brain.ai_client import ai_researcher
from src.shared.utils.excel_manager import excel_manager

# Function to run the Hunter background supervisor loop in a dedicated thread
def start_background_hunter():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        logger.info("🚀 Background Hunter Engine Thread starting...")
        loop.run_until_complete(run_hunter())
    except Exception as e:
        logger.error(f"Hunter background loop error: {e}")

# Start background thread automatically when app.py loads
worker_thread = threading.Thread(target=start_background_hunter, daemon=True)
worker_thread.start()

# Gradio Web Interface for Monitoring and Manual Research
async def perform_web_research(topic: str):
    if not topic.strip():
        return "⚠️ Please enter a topic for research."
    try:
        search_data = await search_engine.search(topic)
        results = await ai_researcher.perform_research(topic, search_data['content'])
        if results:
            filepath = excel_manager.generate(results, filename=f"research_{topic.replace(' ', '_')}.xlsx")
            return f"✅ TSD Lead Matrix Generated! Found {len(results)} leads. File: {filepath}"
        return "❌ No structured leads found."
    except Exception as e:
        return f"Error: {e}"

def get_status():
    return "🟢 **Hunter AI Sniper Status:** RUNNING 24/7 (Djinni, LinkedIn, Upwork, Telegram Listeners Active)"

with gr.Blocks(title="Hunter AI Job Sniper", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎯 Hunter AI Job Sniper — Control Dashboard")
    gr.Markdown("### Socratic Dialogue Protocol (TSD v27.2.2) Cognitive Engine")
    
    status_box = gr.Markdown(get_status())
    
    with gr.Tab("🔍 Deep B2B Research (TSD Matrix)"):
        with gr.Row():
            topic_input = gr.Textbox(label="Research Topic / Target Market", placeholder="e.g. FinTech startups hiring React developers Europe", scale=4)
            submit_btn = gr.Button("🚀 Run TSD Research", variant="primary", scale=1)
        
        output_box = gr.Textbox(label="Research Result", interactive=False)
        submit_btn.click(fn=perform_web_research, inputs=topic_input, outputs=output_box)

    with gr.Tab("ℹ️ System Info"):
        gr.Markdown("""
        **Active Scrapers & Listeners:**
        - 🟢 **Djinni.co Scraper:** 15-min adaptive polling with DedupStore
        - 🟢 **LinkedIn Jobs Scraper:** European remote feed with 2-stage AI cascade
        - 🟢 **Telegram Listener:** Real-time MTProto channel socket
        - 🟢 **TSD Cognitive Engine:** 19-point First Principles & Chris Voss Negotiation
        """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
