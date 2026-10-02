import os
from flask import Flask, render_template, request
from dotenv import load_dotenv
from groq import Groq, AuthenticationError

load_dotenv()

app = Flask(__name__)

MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

SYSTEM_PROMPT = (
    "Answer the user's request clearly. Keep paragraphs short, use headings or "
    "bullet points when helpful, avoid unnecessary introductions, and keep the response readable."
)

PRECISE_TEMP = 0.2
CREATIVE_TEMP = 0.8

def call_groq_with_fallback(prompt, temperature):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None, None, "Groq API key is missing. Please set GROQ_API_KEY in your .env file."

    client = Groq(api_key=api_key)
    
    for model in MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            content = response.choices[0].message.content
            return content, model, None
        except AuthenticationError:
            return None, None, "Invalid Groq API key. Please check your credentials in .env."
        except Exception as e:
            continue

    return None, None, "Unable to reach any AI model. Please check your network connection or API limits."

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        if not prompt:
            return render_template("index.html", error="Please enter a prompt before comparing.")
        
        if len(prompt) > 2000:
            return render_template("index.html", error="Prompt is too long (maximum 2000 characters).")

        precise_text, precise_model, precise_err = call_groq_with_fallback(prompt, PRECISE_TEMP)
        creative_text, creative_model, creative_err = call_groq_with_fallback(prompt, CREATIVE_TEMP)

        return render_template(
            "index.html",
            prompt=prompt,
            precise_result={"text": precise_text, "model": precise_model, "temp": PRECISE_TEMP, "error": precise_err},
            creative_result={"text": creative_text, "model": creative_model, "temp": CREATIVE_TEMP, "error": creative_err}
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
