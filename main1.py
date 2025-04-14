import streamlit as st
import os
import requests
import re
from typing import Dict, Any
from langchain.tools import tool
from langchain_tavily import TavilySearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate

# 🔐 API Keys
GOOGLE_API_KEY = "AIzaSyDdZ3_8PHVaaVy2eURdU7fFiqctEnPhOwQ"
TAVILY_API_KEY = "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"
WEATHER_API_KEY = "367e01fcbd4941c6801101541251304"

# 🌍 Streamlit Page Setup
st.set_page_config(page_title="Travel Assistant", page_icon="🌍")
st.title("🌍 AI Travel Assistant")

# 📍 User Input
destination = st.text_input("📍 Where are you planning to go?")

# 📦 Get Travel Info
if st.button("Get Travel Info") and destination:
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
    os.environ["WEATHER_API_KEY"] = WEATHER_API_KEY

    # 🌦️ Weather Tool
    @tool
    def get_weather(location: str) -> Dict[str, Any]:
        """
        Get current weather for a location using OpenWeatherMap API.
        """
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                return {"error": response.json().get("message", "Weather unavailable.")}

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

    # 🔍 Tavily + Gemini Setup
    search_tool = TavilySearch(max_results=3)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    tools = [get_weather, search_tool]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel assistant."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

    # ⏳ Invoke Agent
    with st.spinner("Gathering travel details..."):
        result = agent_executor.invoke({"input": f"Tell me the current weather and top attractions in {destination}."})
        output = result.get("output", "")

        # 🎯 Output Formatting
        st.subheader("✈️ Travel Assistant Result")

        # ➤ Weather Section
        if "cannot get the current weather" in output.lower() or "weather api" in output.lower():
            st.markdown("⚠️ Weather data is currently unavailable.")
        else:
            weather_match = re.search(r"(?:current weather in .*? is|it's|It is)\s.*?(\d+[\.,]?\d*)°?C?.*?(?:with|and)\s+(.*?)(?:\.|,)", output, re.IGNORECASE)
            if weather_match:
                temp = weather_match.group(1)
                desc = weather_match.group(2)
                st.markdown("**🌦️ Weather:**")
                st.write(f"- Temperature: {temp}°C")
                st.write(f"- Condition: {desc}")
            else:
                st.markdown("**🌦️ Weather info:**")
                st.write("Weather details could not be clearly extracted.")
                st.write(output)

        # ➤ Attractions Section
        st.markdown("**📍 Top Attractions:**")

        # Use regex to extract attractions
        match = re.search(r"(?:top attractions in .*? (?:are|include|which include)) (.*?)(?:\.|$)", output, re.IGNORECASE)
        if match:
            attractions_text = match.group(1)
            attractions = [item.strip() for item in re.split(r",| and ", attractions_text) if item.strip()]
            for item in attractions:
                st.write(f"- {item}")
        else:
            st.write("Couldn't extract attractions properly. Full response:")
            st.write(output)

elif st.button("Get Travel Info"):
    st.warning("Please enter a destination.")

