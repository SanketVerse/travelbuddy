import streamlit as st
import os
import requests
from typing import Dict, Any
from langchain.tools import tool
from langchain_tavily import TavilySearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate

# API Keys
GOOGLE_API_KEY = "AIzaSyDdZ3_8PHVaaVy2eURdU7fFiqctEnPhOwQ"
TAVILY_API_KEY = "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"
WEATHER_API_KEY = "367e01fcbd4941c6801101541251304"

# Streamlit Setup
st.set_page_config(page_title="Travel Assistant", page_icon="🌍")
st.title("🌍 AI Travel Assistant")

# User Input
destination = st.text_input("📍 Where are you planning to go?")

if st.button("Get Travel Info") and destination:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
    os.environ["WEATHER_API_KEY"] = WEATHER_API_KEY

    @tool
    def get_weather(location: str) -> Dict[str, Any]:
        """
        Get current weather for a location using OpenWeather API.
        """
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return {"error": f"{response.json().get('message', 'Weather unavailable')}"}

            data = response.json()
            return {
                "location": location,
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }

        except Exception as e:
            return {"error": str(e)}

    # Tools + LLM
    search_tool = TavilySearch(max_results=3)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    tools = [get_weather, search_tool]

    # Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel assistant."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    with st.spinner("Gathering travel details..."):
        result = agent_executor.invoke({"input": f"Tell me the current weather and top attractions in {destination}."})
        output = result.get("output", "")

        st.subheader("✈️ Travel Assistant Result")

        if "cannot get the current weather" in output.lower() or "weather api is not working" in output.lower():
            st.markdown("⚠️ Weather data is currently unavailable.")
            # Optional: you could still show a placeholder if needed
        else:
            st.markdown("**🌤️ Current Weather Info:**")
            # Try to extract weather summary from the output
            st.write(output.split("However")[0].strip())

        st.markdown("**📍 Top Attractions:**")
        if "which include" in output:
            attractions_text = output.split("which include", 1)[1].strip(". ")
            st.write(f"- {attractions_text.replace(',', '\n- ')}")
        else:
            st.write("Couldn't extract attractions properly. Full response:")
            st.write(output)

elif st.button("Get Travel Info"):
    st.warning("Please enter a destination.")
