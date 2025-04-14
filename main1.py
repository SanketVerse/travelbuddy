import streamlit as st
import os
import requests
from typing import Dict, Any
from langchain.tools import tool  # Updated import
from langchain_tavily import TavilySearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate

# Set API keys directly
GOOGLE_API_KEY = "AIzaSyDdZ3_8PHVaaVy2eURdU7fFiqctEnPhOwQ"
TAVILY_API_KEY = "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"
WEATHER_API_KEY = "367e01fcbd4941c6801101541251304"  # Your Weather API key

st.set_page_config(page_title="Travel Assistant", page_icon="🌍")

st.title("🌍 AI Travel Assistant")

# 🌍 Destination Input
destination = st.text_input("📍 Where are you planning to go?")

# When user clicks the button
if st.button("Get Travel Info") and destination:
    # Set environment variables
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
    os.environ["WEATHER_API_KEY"] = WEATHER_API_KEY

    # 🌤️ Custom weather tool with error handling
    @tool
    def get_weather(location: str) -> Dict[str, Any]:
        """
        Get current weather for a location using OpenWeather API.
        """
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
            response = requests.get(url, timeout=10)  # Timeout set to 10 seconds
            
            # Check if the response is successful
            if response.status_code != 200:
                return {"error": f"Error {response.status_code}: {response.json().get('message', 'Failed to fetch weather data')}"}

            data = response.json()

            weather = {
                "location": location,
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
            return weather

        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}

        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}"}

    # 🔍 Tavily search tool
    search_tool = TavilySearch(max_results=3)

    # 🤖 Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

    # Tools and prompt
    tools = [get_weather, search_tool]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel assistant."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    # Agent setup
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    with st.spinner("Thinking... 🤔"):
        response = agent_executor.invoke({"input": f"Tell me the current weather and top attractions in {destination}."})
        st.subheader("✈️ Travel Assistant Result")
        st.write(response["output"])

elif st.button("Get Travel Info"):
    st.warning("Please enter a destination.")
