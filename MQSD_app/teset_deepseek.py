import openai
from openai import OpenAIError

def test_openai():
    try:
       

        # Ensure API key is picked up
        api_key = openai.api_key or os.getenv("OPENAI_API_KEY")

        

        # Simple request to OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"}
            ]
        )

        
        print( {"status": "success", "response": response["choices"][0]["message"]["content"]})

    except openai.error.RateLimitError as e:
        return {"status": "fail", "error": "Rate limit exceeded", "details": str(e)}, 429

    except openai.error.AuthenticationError as e:
        return {"status": "fail", "error": "Authentication failed", "details": str(e)}, 401

    except Exception as e:
        return {"status": "fail", "error": "Unexpected error", "details": str(e)}, 500


# OPENAI_API_KEY='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'


api_key = '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'

# Set the API key
openai.api_key = api_key

# Create a chat completion
response = openai.ChatCompletion.create(
    model="gpt-4.1",  # Using gpt-4 as gpt-4.1 is not a valid model name
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
    temperature=1,
    max_tokens=2048,
    top_p=1
)

print(response)