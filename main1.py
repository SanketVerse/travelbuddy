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
