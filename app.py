from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import os
import json
import shutil
import time

# Import necessary functions from your existing code
from functions import (
    transcribe_audio,
    text_to_speech,
    label_transcript,
    analyzeCallTranscript,
    load_call_attributes,
    load_Chat_attributes,
    chat_with_ai
)

app = FastAPI(title="Sales Script API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize attributes
call_attributes = load_call_attributes()
chat_attributes = load_Chat_attributes()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "APIs for Sales Script are Running, Hello World! | V-IV Live"}

@app.post("/process-voice/")
async def process_voice(text_file: UploadFile = File(...)):
    if not text_file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are allowed")

    file_path = os.path.join(UPLOAD_DIR, text_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(text_file.file, buffer)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        labeled_audio_data = label_transcript(raw_text)
        analysis_report = analyzeCallTranscript(labeled_audio_data)

        if isinstance(analysis_report, str):
            analysis_report = json.loads(analysis_report)

        return {"filename": text_file.filename, "analysis_report": analysis_report}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/chat-with-bot/")
async def chat_with_bot(request: Request):
    if not chat_attributes:
        raise HTTPException(status_code=400, detail="No call analysis data found. Please run the attribute extraction first.")

    body = await request.json()
    user_input = body.get("user_input")
    user_id = body.get("user_id")

    if not user_input or not user_id:
        raise HTTPException(status_code=400, detail="Missing user_input or user_id in request")

    try:
        response = chat_with_ai(user_input, chat_attributes, user_id)
        return {"user_input": user_input, "user_id": user_id, "bot_response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/voice-chat/")
async def voice_chat(audio: UploadFile = File(...), user_id: str = Form(...)):
    temp_input_path = None
    temp_output_path = None

    try:
        extension = os.path.splitext(audio.filename)[1].lower()
        supported_formats = ['.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm']

        if extension not in supported_formats:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {extension}. Use: {', '.join(supported_formats)}")

        temp_input_path = os.path.join(UPLOAD_DIR, f"temp_{user_id}{extension}")
        with open(temp_input_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        user_input = transcribe_audio(temp_input_path)
        if not user_input:
            raise ValueError("Failed to transcribe audio")

        bot_response = chat_with_ai(user_input, chat_attributes, user_id)

        temp_output_path = os.path.join(UPLOAD_DIR, f"output_{user_id}.mp3")
        audio_path = text_to_speech(bot_response, temp_output_path)

        if not audio_path or not os.path.exists(temp_output_path):
            raise ValueError("Failed to generate speech")

        return FileResponse(
            path=temp_output_path,
            media_type='audio/mpeg',
            filename=f"response_{user_id}.mp3",
            headers={"Content-Disposition": f"attachment; filename=response_{user_id}.mp3"}
        )

    except Exception as e:
        for path in [temp_input_path, temp_output_path]:
            if path and os.path.exists(path):
                time.sleep(2)
                os.remove(path)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        for path in [temp_input_path, temp_output_path]:
            if path and os.path.exists(path):
                os.remove(path)




































# from flask import Flask, request, jsonify
# import os
# import json
# import time

# from flask_cors import CORS
# from flask import send_file, after_this_request


# app = Flask(__name__)

# # Import necessary functions from your existing code
# from functions import (
#     transcribe_audio,  # Changed from speechToText
#     text_to_speech,    # New import
#     label_transcript,
#     analyzeCallTranscript,
#     load_call_attributes,
#     load_Chat_attributes,
#     chat_with_ai
# )


# # Configure CORS globally with explicit settings
# CORS(app, resources={
#     r"/*": {
#         "origins": "*",                      # Allow all origins (adjust for production if needed)
#         "methods": ["GET", "POST", "OPTIONS"], # Allow specific HTTP methods
#         "allow_headers": ["Content-Type", "Authorization"] # Allow common headers
#     }
# })

# # Load call attributes from file
# call_attributes = load_call_attributes()
# chat_attributes = load_Chat_attributes()
# UPLOAD_DIR = "uploads"

# # Ensure upload directory exists
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# @app.route('/')
# def hello_world():
#     return "APIs for Sales Script are Running, Hello World! | V-IV Live "


# @app.route("/process-voice/", methods=["POST"])
# def process_voice_endpoint():
#     """API endpoint to process a text file and return analysis report."""
#     try:
#         # Check if a file is part of the request
#         if 'text_file' not in request.files:
#             return jsonify({"error": "No file part in the request"}), 400
        
#         text_file = request.files['text_file']
        
#         # Validate file
#         if text_file.filename == '':
#             return jsonify({"error": "No file selected"}), 400
#         if not text_file.filename.lower().endswith('.txt'):
#             return jsonify({"error": "Only .txt files are allowed"}), 400

#         # Save uploaded file
#         file_path = os.path.join(UPLOAD_DIR, text_file.filename)
#         text_file.save(file_path)

#         # Read text content from file
#         with open(file_path, 'r', encoding='utf-8') as f:
#             raw_text = f.read()

#         # Process the text
#         labeled_audio_data = label_transcript(raw_text)
#         analysis_report = analyzeCallTranscript(labeled_audio_data)

#         # Ensure proper JSON format
#         if isinstance(analysis_report, str):
#             analysis_report = json.loads(analysis_report)

#         # Cleanup decorator to delete file after response
#         @after_this_request
#         def remove_file(response):
#             try:
#                 if os.path.exists(file_path):
#                     os.remove(file_path)
#             except Exception as e:
#                 print(f"Error removing file: {str(e)}")
#             return response

#         return jsonify({
#             "filename": text_file.filename,
#             "analysis_report": analysis_report
#         })

#     except Exception as e:
#         # Ensure cleanup even on error
#         if 'file_path' in locals() and os.path.exists(file_path):
#             os.remove(file_path)
#         return jsonify({"error": str(e)}), 500
    

# @app.route("/chat-with-bot/", methods=["POST"])
# def chat_endpoint():
#     """
#     API endpoint to interact with the call analysis chatbot.
#     """
#     if not chat_attributes:
#         return jsonify({"error": "No call analysis data found. Please run the attribute extraction first."}), 400
#     try:
#         # Get JSON data from request
#         data = request.get_json()
#         if not data or 'user_input' not in data or 'user_id' not in data:
#             return jsonify({"error": "Missing user_input or user_id in request"}), 400
#         user_input = data['user_input']
#         user_id = data['user_id']
#         # Get AI response based on user input
#         response = chat_with_ai(user_input, chat_attributes, user_id)
#         return jsonify({
#             "user_input": user_input,
#             "user_id": user_id,
#             "bot_response": response
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# # # Add new endpoint
# # @app.route("/voice-chat/", methods=["POST"])
# # def voice_chat():
# #     """End-to-end voice conversation endpoint"""
# #     try:
# #         # Validate input
# #         if 'audio' not in request.files or 'user_id' not in request.form:
# #             return jsonify({"error": "Missing audio file or user ID"}), 400
# #         audio_file = request.files['audio']
# #         user_id = request.form['user_id']
# #         # Save audio temporarily
# #         temp_path = os.path.join(UPLOAD_DIR, f"temp_{user_id}.wav")
# #         audio_file.save(temp_path)
# #         # STT - Convert audio to text
# #         user_input = transcribe_audio(temp_path)
# #         if not user_input:
# #             raise ValueError("Failed to transcribe audio")
# #         # Get text response
# #         bot_response = chat_with_ai(user_input, chat_attributes, user_id)
# #         # TTS - Convert response to audio
# #         audio_response = text_to_speech(bot_response)
# #         if not audio_response:
# #             raise ValueError("Failed to generate speech")
# #         # Cleanup
# #         os.remove(temp_path)
# #         return jsonify({
# #             "user_id": user_id,
# #             "bot_response": bot_response,
# #             "bot_response": audio_response
# #         })
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 500


# # @app.route("/voice-chat/", methods=["POST"])
# # def voice_chat():
# #     """End-to-end voice conversation endpoint"""
# #     try:
# #         # Validate input
# #         if 'audio' not in request.files or 'user_id' not in request.form:
# #             return jsonify({"error": "Missing audio file or user ID"}), 400
# #         audio_file = request.files['audio']
# #         user_id = request.form['user_id']
# #         # Save audio temporarily
# #         temp_input_path = os.path.join(UPLOAD_DIR, f"temp_{user_id}.wav")
# #         audio_file.save(temp_input_path)
# #         # STT - Convert audio to text
# #         user_input = transcribe_audio(temp_input_path)
# #         if not user_input:
# #             raise ValueError("Failed to transcribe audio")
# #         # Get text response
# #         bot_response = chat_with_ai(user_input, chat_attributes, user_id)
# #         # TTS - Convert response to audio (MP3)
# #         temp_output_path = os.path.join(UPLOAD_DIR, f"output_{user_id}.mp3")
# #         audio_path = text_to_speech(bot_response, temp_output_path)
# #         if not audio_path or not os.path.exists(temp_output_path):
# #             raise ValueError("Failed to generate speech")
# #         # Cleanup function to delete files after successful response
# #         @after_this_request
# #         def cleanup(response):
# #             try:
# #                 if os.path.exists(temp_input_path):
# #                     os.remove(temp_input_path)
# #                 if os.path.exists(temp_output_path):
# #                     os.remove(temp_output_path)
# #             except Exception as e:
# #                 print(f"Cleanup error: {str(e)}")
# #             return response
# #         # Send the MP3 file
# #         return send_file(
# #             temp_output_path,
# #             mimetype='audio/mpeg',
# #             as_attachment=True,
# #             download_name=f'response_{user_id}.mp3'
# #         )
# #     except Exception as e:
# #         # Clean up files in case of error
# #         for path in [temp_input_path, temp_output_path]:
# #             if 'path' in locals() and os.path.exists(path):
# #                 os.remove(path)
# #         return jsonify({"error": str(e)}), 500

# @app.route("/voice-chat/", methods=["POST"])
# def voice_chat():
#     """End-to-end voice conversation endpoint"""
#     temp_input_path = None
#     temp_output_path = None
#     try:
#         # Validate input
#         if 'audio' not in request.files or 'user_id' not in request.form:
#             return jsonify({"error": "Missing audio file or user ID"}), 400
#         audio_file = request.files['audio']
#         user_id = request.form['user_id']
#         # Save uploaded file with original extension
#         extension = os.path.splitext(audio_file.filename)[1].lower()
#         supported_formats = ['.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.mpga', '.webm']
#         if extension not in supported_formats:
#             return jsonify({"error": f"Unsupported format: {extension}. Use: {', '.join(supported_formats)}"}), 400
#         temp_input_path = os.path.join(UPLOAD_DIR, f"temp_{user_id}{extension}")
#         audio_file.save(temp_input_path)
#         # Transcribe directly
#         user_input = transcribe_audio(temp_input_path)
#         if not user_input:
#             raise ValueError("Failed to transcribe audio")
#         # Get chatbot response
#         bot_response = chat_with_ai(user_input, chat_attributes, user_id)
#         # Convert response to audio
#         temp_output_path = os.path.join(UPLOAD_DIR, f"output_{user_id}.mp3")
#         audio_path = text_to_speech(bot_response, temp_output_path)
#         if not audio_path or not os.path.exists(temp_output_path):
#             raise ValueError("Failed to generate speech")
#         # Cleanup after response
#         @after_this_request
#         def cleanup(response):
#             try:
#                 if temp_input_path and os.path.exists(temp_input_path):
#                     os.remove(temp_input_path)
#                 if temp_output_path and os.path.exists(temp_output_path):
#                     os.remove(temp_output_path)
#             except Exception as e:
#                 print(f"Cleanup error: {str(e)}")
#             return response
#         # Send audio response
#         return send_file(
#             temp_output_path,
#             mimetype='audio/mpeg',
#             as_attachment=True,
#             download_name=f'response_{user_id}.mp3'
#         )
#     except Exception as e:
#         # Cleanup on error
#         for path in [temp_input_path, temp_output_path]:
#             if path and os.path.exists(path):
#                 time.sleep(2)
#                 os.remove(path)
#         return jsonify({"error": str(e)}), 500

# if __name__ == "__main__":
#     # For PythonAnywhere, this block won't run directly as WSGI handles it
#     # app.run(host="127.0.0.1", port=8001, debug=True)
#     app.run(debug=True)

# # to activate myenv  -->
# # source /home/BigGreenMachine/.virtualenvs/myenv/bin/activate
