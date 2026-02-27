from llm_engine import analyze_sentiment_batch
import json

print("--- STARTING ISOLATION TEST ---")

# We use 3 hardcoded headlines to remove the scraper from the equation
test_headlines = [
    "Nvidia surges 10% on massive new AI chip demand.",
    "Tesla stock plummets after factory fire in Berlin.",
    "Federal reserve leaves interest rates unchanged, market flat."
]

print("Sending data to Local Llama 3.2...\n")

# Run the engine
result = analyze_sentiment_batch(test_headlines)

print("\n--- FINAL RESULT RETURNED TO DASHBOARD ---")
print(result)

# Verify it is perfect JSON
try:
    parsed = json.loads(result)
    if isinstance(parsed, list) and len(parsed) > 0:
        print("\n✅ SUCCESS! The data is perfectly formatted for the dashboard.")
    else:
        print("\n❌ FAILURE: The AI returned an empty list.")
except Exception as e:
    print(f"\n❌ FAILURE: The AI did not return valid JSON. Error: {e}")