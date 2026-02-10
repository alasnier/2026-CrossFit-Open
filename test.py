from google import genai

client = genai.Client(api_key="AIzaSyAHGKFFPHYQ98y7yFp4KwsVyP6QGqA-KNM")
for m in client.models.list():
    print(m.name)
