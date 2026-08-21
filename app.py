import os
import gradio as gr
import uvicorn
from pulseroute.main import app as fastapi_app

# Mount Gradio helper to comply with Hugging Face Gradio SDK
demo = gr.Blocks(title="PulseRoute Interface")
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run(app, host="0.0.0.0", port=port)
