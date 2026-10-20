from dotenv import load_dotenv
from openai import OpenAI
import openai
import os, json
from openai import OpenAI, APIError, RateLimitError, APIConnectionError, AuthenticationError
import backoff
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# from base64 import b64encode
# from deepgram import (
#     DeepgramClient,
#     PrerecordedOptions
# )
load_dotenv()

# Access the API key
openai.api_key = os.getenv("OPENAI_API_KEY")

OPENAI_API_KEY  =  os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def read_text_file(file_path):
    """Reads the entire content of a text file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def save_best_Attributes(json_string, filename="best_Attributes.json"):
    """Parses a JSON string and saves it to a JSON file."""
    try:
        data = json.loads(json_string)  # Parse the JSON string
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)  # Save in a readable format
        print(f"JSON data saved to {filename}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")

# def transcribe_audio(audio_file_path: str):
#     """Transcribes an audio file using OpenAI's Whisper model with retry logic."""

#     supported_formats = {".wav", ".mp3", ".flac", ".m4a"}
#     if os.path.splitext(audio_file_path)[1].lower() not in supported_formats:
#         raise ValueError("Unsupported audio format. Use WAV, MP3, FLAC, or M4A.")
        
#     if not OPENAI_API_KEY:
#         print("OPENAI_API_KEY not found in environment variables")
#         return None
#     client = OpenAI(api_key=OPENAI_API_KEY)

#     @backoff.on_exception(backoff.expo, (APIError, RateLimitError, APIConnectionError), max_tries=3)
#     def _transcribe_with_retry(audio_file):
#         return client.audio.transcriptions.create(
#             model="whisper-1",
#             file=audio_file
#         )
#     try:
#         with open(audio_file_path, "rb") as audio_file:
#             transcription = _transcribe_with_retry(audio_file)
#         return transcription.text
#     except Exception as e:
#         print(f"Error transcribing audio: {str(e)}")
#         return None

def transcribe_audio(audio_file_path: str):
    """Transcribes an audio file using OpenAI's Whisper model with retry logic."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    
    if os.path.getsize(audio_file_path) > 25 * 1024 * 1024:
        raise ValueError("File size exceeds 25MB limit.")
    
    client = OpenAI(api_key=OPENAI_API_KEY)

    @backoff.on_exception(backoff.expo, (APIError, RateLimitError, APIConnectionError, TimeoutError), max_tries=5)
    def _transcribe_with_retry(audio_file):
        # return client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = _transcribe_with_retry(audio_file)
        logger.info(f"Successfully transcribed {audio_file_path}")
        return transcription.text
    except AuthenticationError:
        logger.error("Authentication failed: Invalid or missing API key.")
        return "Authentication failed: Invalid or missing API key."
    except TimeoutError:
        logger.error(f"Timeout error for {audio_file_path}")
        return "Transcription timed out. Try a shorter audio file."
    except Exception as e:
        logger.error(f"Error transcribing {audio_file_path}: {str(e)}", exc_info=True)
        return f"Error transcribing audio: {str(e)}"


def analyzeCallTranscript(callRec):

    # callRec = read_text_file(file_path)

    system_prompt = f"""
    Prompt: Call Analysis & Evaluation - Ideal Standard Comparison

    Context:
    You are an AI assistant designed to analyze customer service call transcripts by comparing them against a predefined
    ideal standard based on the "Brian Burton Training" guidelines. This ideal case outlines best practices for initiating
    and conducting a call with a customer. The ideal standard emphasizes a warm, professional greeting, clear communication,
    thorough needs assessment, proper handling of logistical details, respectful engagement with all parties involved,
    and a structured process that builds trust and clarifies the project’s scope.

    Ideal Call Standard Key Points:
    - **Greeting & Introduction:** Start with a friendly, professional introduction (e.g., "Hi, I am Mike with Flat River Electric, Brian…") and include a personal touch by mentioning positive feedback from the office.
    - **Logistical Confirmation:** Ask about practical details such as whether there are any concerns with parking before entering the home, and mention protective measures (like using floor protectors) to ensure customer comfort.
    - **Establishing Purpose:** Clearly inquire about the customer’s needs (e.g., the reason for the call, such as adding recessed lighting) and confirm the timeline or urgency of the project.
    - **Engagement & Rapport:** Ask follow-up questions about the customer’s motivation, any previous experiences with other electricians, and whether other family members should be included in the conversation.
    - **Building Trust:** Address previous negative experiences with other service providers, emphasize the company’s strengths (e.g., quality, reliability, customer service, lifetime craftsmanship guarantee), and differentiate your services from competitors.
    - **Presentation of Options:** Clearly present multiple service options, explain their benefits, and inquire about the customer’s preferences while being flexible about scheduling.

    Instructions:
    Analyze the provided call transcript (denoted by {callRec}) with a focus on how closely the agent’s performance aligns with the ideal call standard above. Your analysis should address the following aspects:

    1. **Call Quality Check:** Evaluate the overall structure and professionalism of the call. Did the agent adhere to the ideal call flow from greeting to closing?
    2. **Conversation Summary:** Summarize the key points of the call, including the initial greeting, the clarification of the customer's needs, and the resolution or next steps.
    3. **Strong Points:** Identify specific moments where the agent effectively met or exceeded the ideal standards (e.g., a strong greeting, clear explanation of options, building trust).
    4. **Weak Points:** Highlight areas where the agent deviated from the ideal standard or missed opportunities to enhance the call (e.g., not confirming logistical details, insufficient probing of customer concerns).
    5. **Improvement Suggestions:** Provide actionable recommendations for aligning future calls more closely with the ideal guidelines.
    6. **Engagement & Tone:** Assess the tone, clarity, and effectiveness of the agent’s communication, and how well they built rapport compared to the ideal standard.
    7. **Strength & Weakness Scores:** Calculate and provide the percentage of strengths and weaknesses observed in the call.

    Important:
    --> Response must be in valid JSON.
    --> Do not hallucinate details.
    --> Use precise, professional language.
    --> Output MUST be in JSON format without any additional formatting or commentary.

    Your Response Must be like this:
    {{
      "call_quality_score": "",
      "conversation_summary": "",
      "strong_points": [],
      "weak_points": [],
      "improvement_suggestions": [],
      "customer_issues": [],
      "issues_addressed": "",
      "engagement_and_tone": "",
      "overall_recommendation": "",
      "strengths_percentage": "",
      "weakness_percentage": ""
    }}

    - Fill all the above JSON fields.
    - Keep responses precise and professional.
    - Do not hallucinate details.
    - Return only valid JSON.
    """

    # Modify system message based on context availability
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3
    )

    response = completion.choices[0].message.content
    return response

def label_transcript(raw_transcript):
    prompt = f"""
    You are an intelligent transcript labeling assistant. Your task is to analyze the following raw transcript, understand the context, identify the speakers, and label each message clearly.

    **Instructions:**
    - Identify and differentiate speakers based on conversational patterns.
    - Assign appropriate labels such as "Person 1", "Person 2", etc.
    - Maintain the original conversation structure and ensure readability.
    - Preserve names if mentioned, otherwise, use generic labels like "Person 1".
    - Format the output as a well-structured dialogue.

    **Example Formatting:**
    Person 1: Hey, how are you?
    Person 2: Hi! I'm good. What about you?
    Person 1: I'm doing well, thanks for asking.

    **Raw Transcript:**
    {raw_transcript}

    **Labeled Transcript:**
    """
    # Modify system message based on context availability
    messages = [
        {"role": "system", "content": prompt}
    ]

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3
    )

    response = completion.choices[0].message.content
    return response


# def speechToText(file_obj):
#     try:
#         # STEP 1 Create a Deepgram client using the API key
#         deepgram = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))
#         #STEP 2: Configure Deepgram options for audio analysis
#         options = PrerecordedOptions(     #https://developers.deepgram.com/docs/stt-pre-recorded-feature-overview
#             model="nova-2",
#             smart_format=True,
#         )
#         response = deepgram.listen.rest.v("1").transcribe_file({"buffer": file_obj}, options)
#         # print(response  )
#         transcript_text = response.results.channels[0].alternatives[0].transcript
#         return transcript_text
#     except Exception as e:
#         print(f"Exception: {e}")

# def text_to_speech(text: str) -> str:
#     """Converts text to speech using OpenAI TTS and returns base64 audio."""
#     try:
#         response = openai_client.audio.speech.create(
#             model="tts-1",
#             voice="nova",  # More natural sounding voice
#             input=text
#         )

#         # Convert directly to bytes without temp file
#         audio_bytes = response.content
#         return b64encode(audio_bytes).decode('utf-8')
#     except Exception as e:
#         print(f"TTS Generation error: {str(e)}")
#         return None

def text_to_speech(text: str, output_path: str) -> str:
    """Converts text to speech using OpenAI TTS and saves to MP3 file."""
    try:
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",  # More natural sounding voice
            input=text
        )

        # Get audio bytes and save to file
        audio_bytes = response.content
        with open(output_path, 'wb') as audio_file:
            audio_file.write(audio_bytes)

        return output_path
    except Exception as e:
        print(f"TTS Generation error: {str(e)}")
        return None



# process_voice

def analyzeBestCase(file_path):
    # read Best Case Call
    idealCaseCall = read_text_file(file_path)

    system_prompt = f"""
      Context:
      You are an AI assistant that extracts key attributes from a customer service call transcript. Your goal is to identify and categorize essential details such as customer concerns, agent responses, objections, resolutions, strong points, and weak points.

    --> Instructions:
      Analyze the following call transcript and extract the following attributes:

      1). Essential Attributes

      Customer concerns (issues, complaints, pain points)
      Agent responses (how the agent addressed concerns)
      Objections (hesitations, pushback from the customer)
      Resolutions (solutions offered and their effectiveness)

      2). Strong Points

      Positive engagement (rapport-building, politeness)
      Clear and helpful explanations
      Successful upselling or cross-selling

      3). Weak Points

      Missed objections (customer concerns not fully addressed)
      Lack of engagement (agent didn’t ask follow-up questions)
      Poor closing (did not confirm issue resolution or next steps)

    --> Call Transcript:
        {idealCaseCall}

    --> Output Format:
      Return the extracted attributes in structured JSON format for further processing.

      {{

        "essential_attributes": {{
          "customer_concerns": ["___", "___", "___"],
          "agent_responses": ["___", "___", "___"],
          "objections": ["___"],
          "resolutions": ["___", "___"]
        }},

        "strong_points": [
          "_______________________",
          "_______________________",
          "_______________________"
        ],

        "weak_points": [
          "_______________________",
          "_______________________"
        ]
      }}

    - Fill all the above JSON fields
    - Keep responses precise and professional.
    - Evaluate the conversation objectively, without hesitation in assigning positive or negative ratings where deserved.
    - Do not hallucinate details.
    - Return only valid JSON.
    """

    # Modify system message based on context availability
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.4
    )

    response = completion.choices[0].message.content
    return response

# Load extracted call attributes
def load_call_attributes():
    try:
        with open("best_Attributes.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return None

# Load extracted call attributes
def load_Chat_attributes():
    try:
        with open("Chat_responses.json", "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return None


# def chat_with_ai(user_input, call_attributes, user_id):
#     # Initialize memory storage if it doesn't exist in the global scope
#     if not hasattr(chat_with_ai, "memory"):
#         chat_with_ai.memory = {}

#     # Create a new conversation history for this user if it doesn't exist
#     if user_id not in chat_with_ai.memory:
#         chat_with_ai.memory[user_id] = []

#     system_prompt = f"""
#     You are a conversational AI assisting for Company Flat River Electic.
#     The extracted attributes from the Best case are:

#     **Essential Attributes:**
#     - Customer Concerns: {", ".join(call_attributes["essential_attributes"]["customer_concerns"])}
#     - Agent Responses: {", ".join(call_attributes["essential_attributes"]["agent_responses"])}
#     - Objections: {", ".join(call_attributes["essential_attributes"]["objections"])}
#     - Resolutions: {", ".join(call_attributes["essential_attributes"]["resolutions"])}

#     **Strong Points:**
#     - {", ".join(call_attributes["strong_points"])}

#     **Weak Points:**
#     - {", ".join(call_attributes["weak_points"])}

#     Engage in a discussion about these points.
#     Answer questions from the user regarding the Best Case's performance and improvements.
#     Be precise, professional, and insightful.

#     Instuctions:
#     - Do not mention about the Attributes you are given.
#     - Do not response to irrelevent questions.
#     """

#     # Create the messages array with the system prompt
#     messages = [
#         {"role": "system", "content": system_prompt}
#     ]

#     # Add all previous conversation history for this user
#     messages.extend(chat_with_ai.memory[user_id])

#     # Add the current user input
#     messages.append({"role": "user", "content": user_input})

#     openai_client = openai.OpenAI()  # Initialize OpenAI client

#     response = openai_client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=messages,
#         temperature=0.5
#     )

#     assistant_response = response.choices[0].message.content

#     # Update the memory with the current interaction
#     chat_with_ai.memory[user_id].append({"role": "user", "content": user_input})
#     chat_with_ai.memory[user_id].append({"role": "assistant", "content": assistant_response})

#     # Optional: Implement a maximum history size to prevent token limits
#     max_history_pairs = 10  # Store last 10 exchanges (20 messages)
#     if len(chat_with_ai.memory[user_id]) > max_history_pairs * 2:
#         # Keep only the most recent exchanges
#         chat_with_ai.memory[user_id] = chat_with_ai.memory[user_id][-max_history_pairs*2:]

#     return assistant_response

def chat_with_ai(user_input, qa_pairs, user_id):
    # Initialize memory storage if it doesn't exist in the global scope
    if not hasattr(chat_with_ai, "memory"):
        chat_with_ai.memory = {}

    # Create a new conversation history for this user if it doesn't exist
    if user_id not in chat_with_ai.memory:
        chat_with_ai.memory[user_id] = []

    system_prompt = f"""

    You have access to a predefined set of best questions and responses from past interactions, listed below. Your responses must be strictly based on this database. Do not generate any new information or answers that are not directly derived from the database.

    *Best Questions and Responses:*
    {json.dumps(qa_pairs, indent=2)}

    *Instructions:*
    - Analyze the user's input and match it to the most relevant question in the database.
    - Provide the corresponding answer from the database, adapting it if necessary to fit the user's exact question.
    - If you are unsure how to respond, give a neutral, general response that makes sense in the context.
    - Do not acknowledge that you are using a predefined database or following a script.
    - Maintain a friendly, professional, and conversational tone.
    - Do Not respond to irrelevant questions. Simply say sorry and re-direct to our main topic
    - If the user's query doesn't match the questions and answers provided, respond with:
        "Sorry, could you clarify what you're specifically looking for?"

    *Handling Unrecognized Questions:*
    - If the salesperson asks something not covered in the database, respond like a real customer would, using the existing script as a guide.
    - Example (if no matching response exists):
      - Salesperson: "What do you think about smart home installations?"
      - AI (Customer): "I haven’t really thought about that before. Do you recommend it?"
    - If a response cannot be inferred, use a *neutral reply* such as:
      - "I’m not sure, could you tell me more?"
      - "That’s a good question, I’ll have to think about it."

    *Engagement Guidelines:*
    - Keep the conversation *friendly, professional, and natural*.
    - You may ask follow-up questions, but only if they are *directly related* to Flat River Electric's services.
    - Avoid repetitive responses—vary your language while staying within the database scope.
    - *Keep responses short and to the point*, addressing only what the user asks.
    - If a question is *outside the provided database*, redirect the user to relevant topics within the database.
    """

    print(system_prompt)
    # Create the messages array with the system prompt
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add all previous conversation history for this user
    messages.extend(chat_with_ai.memory[user_id])

    # Add the current user input
    messages.append({"role": "user", "content": user_input})

    openai_client = openai.OpenAI()  # Initialize OpenAI client

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.5
    )

    assistant_response = response.choices[0].message.content

    # Update the memory with the current interaction
    chat_with_ai.memory[user_id].append({"role": "user", "content": user_input})
    chat_with_ai.memory[user_id].append({"role": "assistant", "content": assistant_response})

    # Optional: Implement a maximum history size to prevent token limits
    max_history_pairs = 10  # Store last 10 exchanges (20 messages)
    if len(chat_with_ai.memory[user_id]) > max_history_pairs * 2:
        # Keep only the most recent exchanges
        chat_with_ai.memory[user_id] = chat_with_ai.memory[user_id][-max_history_pairs*2:]

    return assistant_response
