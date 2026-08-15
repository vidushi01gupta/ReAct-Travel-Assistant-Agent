import os
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from datetime import datetime
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.messages import AIMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver

import requests

load_dotenv()


# weather tool
@tool
def get_weather(city: str):
    """Get current weather and, when dates are provided, forecast weather
    for the requested travel dates.
    
    Dates must be in YYYY-MM-DD format.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    response = requests.get(url, params= params)

    if response.status_code != 200:
        return f"Error: Unable to fetch weather data for {city}. Status code: {response.status_code}"
    data = response.json()

    location = data["name"]
    country = data["sys"]["country"]
    temperature = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    condition = data["weather"][0]["description"]
    wind_speed = data["wind"]["speed"]

    return (
        f"Weather in {location}, {country}: "
        f"{temperature}°C, feels like {feels_like}°C, "
        f"{condition}, humidity {humidity}%, "
        f"wind speed {wind_speed} m/s"
    )


# hotel tool
@tool
def get_hotels(city: str,check_in_date: str,check_out_date: str,adults: int):
    """Get hotel information for the given city and dates using SerpApi."""

    api_key = os.getenv("HOTEL_API_KEY")

    if not api_key:
        return "Error: HOTEL_API_KEY is not configured."

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_hotels",
        "q": f"{city} hotels",
        "check_in_date": check_in_date,
        "check_out_date": check_out_date,
        "adults": adults,
        "currency": "INR",
        "api_key": api_key
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return (
            f"Error: Unable to fetch hotel data for {city}. "
            f"Status code: {response.status_code}. "
            f"Response: {response.text[:500]}"
        )

    data = response.json()

    if "error" in data:
        return f"SerpApi error: {data['error']}"

    hotels = data.get("properties", [])

    if not hotels:
        return f"No hotels found in {city} for the selected dates."

    results = []

    for hotel in hotels[:5]:
        rate = hotel.get("rate_per_night") or {}
        total = hotel.get("total_rate") or {}

        results.append({
        "name": hotel.get("name"),
        "rating": hotel.get("overall_rating"),

        "price_per_night": rate.get("extracted_lowest"),
        "total_price": total.get("extracted_lowest"),
        "price_before_taxes": total.get("extracted_before_taxes_fees"),

        "check_in_time": hotel.get("check_in_time"),
        "check_out_time": hotel.get("check_out_time"),

        "location": hotel.get("gps_coordinates"),
        "link": hotel.get("link"),
        "nearby_places": hotel.get("nearby_places", [])
    })

    return results

# flight tool
@tool
def get_flights(departure_id: str,arrival_id: str,outbound_date: str,return_date: str):
    """Get flight information between two airports for the given dates."""

    api_key = os.getenv("FLIGHT_API_KEY")

    url = "https://serpapi.com/search.json"

    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
        "return_date": return_date,
        "type": "1",              
        "travel_class": "1",    
        "currency": "INR",
        "stops": "0",            
        "api_key": api_key
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            return (
                f"Error: Unable to fetch flight data. "
                f"Status code: {response.status_code}. "
                f"Response: {response.text}"
            )

        data = response.json()

        if "error" in data:
            return f"SerpAPI error: {data['error']}"

        best_flights = data.get("best_flights", [])

        if not best_flights:
            return (
                f"No flights found from {departure_id} "
                f"to {arrival_id} for {outbound_date}."
            )

        results = []

        all_flights = data.get("best_flights", []) + data.get("other_flights", [])

        for option in all_flights[:5]:
            segments = option.get("flights", [])
            if not segments:
                continue

            first_segment = segments[0]
            last_segment = segments[-1]
            departure = first_segment.get("departure_airport", {})
            arrival = last_segment.get("arrival_airport", {})

            results.append({
                "airline": first_segment.get("airline"),
                "flight_number": first_segment.get("flight_number"),

                "departure_airport": departure.get("name"),
                "departure_code": departure.get("id"),
                "departure_time": departure.get("time"),

                "arrival_airport": arrival.get("name"),
                "arrival_code": arrival.get("id"),
                "arrival_time": arrival.get("time"),

                "duration_minutes": option.get("total_duration"),
                "price_inr": option.get("price"),
                "stops": len(segments) - 1,
                "booking_url": data.get("search_metadata", {}).get("google_flights_url")
            })

        return results

    except requests.RequestException as e:
        return f"Flight API request failed: {str(e)}"

# train tool
@tool
def get_trains(departure_station: str, arrival_station: str, travel_date: str):
    """Get trains running between two Indian railway stations on a given date."""

    api_key = os.getenv("TRAIN_API_KEY")

    url = (f"https://api.railradar.in/v1/trains/between/{departure_station}/{arrival_station}")

    params = {
        "date": travel_date,
        "live": "false",
        "byCity": "true"
    }

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        return f"Error: Unable to fetch train data. Status code: {response.status_code}"

    data = response.json()

    trains = data.get("data", {}).get("trains", [])
    if not trains:
        return "No trains found for this route and date."


    results = []

    for option in trains[:5]:
        train = option.get("train", {})
        from_data = option.get("from", {})
        to_data = option.get("to", {})

        results.append({
            "train_number": train.get("number"),
            "train_name": train.get("name"),
            "train_type": train.get("type"),
            "departure_station": departure_station,
            "departure_time": from_data.get("departure"),
            "arrival_station": arrival_station,
            "arrival_time": to_data.get("arrival"),
            "duration": option.get("duration"),
            "distance": option.get("distance"),
            "halts": option.get("totalHaltsBetween"),
            "booking_url": "https://www.irctc.co.in/nget/train-search"
        })

    return results


# bus tool
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
@tool
def get_buses(departure_city: str, arrival_city: str, travel_date: str):
    """
    Find bus options including operator name, departure/arrival time,
    price and booking URL.
    """

    query = f"""
    Find bus tickets from {departure_city} to {arrival_city}
    for {travel_date}.

    Search specifically for actual bus ticket listings.
    I need:
    - bus operator name
    - departure time
    - arrival time
    - duration
    - ticket price in INR
    - booking URL

    Prefer booking websites such as AbhiBus, EaseMyTrip,
    redBus, Paytm Bus, MakeMyTrip or similar.
    Do not return general travel articles.
    """

    tavily_search = TavilySearch(
        api_key=TAVILY_API_KEY,
        max_results=5,
        search_depth="advanced"
    )

    results = tavily_search.invoke(query)

    if not results or not results.get("results"):
        return "No bus information found."

    buses = []

    for result in results["results"]:

        title = result.get("title", "")
        content = result.get("content", "")
        url = result.get("url", "")

        buses.append({
            "booking_website": title,
            "information": content,
            "url": url
        })

    return {
        "route": f"{departure_city} → {arrival_city}",
        "travel_date": travel_date,
        "buses": buses
    }


# tools
tools = [get_weather, get_flights, get_trains, get_buses, get_hotels]

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0.4)
llm_with_tools = llm.bind_tools(tools, tool_choice='auto')


# StateGraph

class AgentState(TypedDict):
    messages:Annotated[list[AnyMessage], add_messages]

# system prompt
system_prompt = """
You are an intelligent AI Travel Assistant with more than 15 years of travel-planning experience.

Your job is to help users plan trips using the available tools.

Available information:
- Flights
- Trains
- Buses
- Hotels
- Weather
- Estimated total trip cost

RULES:
1. Use the appropriate tools whenever real-time or external information is required.
2. You may call multiple tools, either sequentially or when appropriate.
3. After receiving all required tool results, DO NOT call another tool unless information is genuinely missing.
4. Give the user ONE final, well-organized answer.
5. NEVER expose tool calls, tool arguments, ToolMessage, Call ID, or internal reasoning.
6. Do not simply repeat raw API responses.
7. Extract and summarize the useful information from tool results.
8. If some information is unavailable, clearly say "Not available" instead of making it up.
9. Always include source/booking URLs when available.

FORMAT THE FINAL ANSWER LIKE THIS:

# ✈️ Trip Plan: Delhi → Goa

**Travel dates:** 20 August 2026 → 23 August 2026

## ✈️ Flights
Show the best available flight options in a small table:

| Airline | Departure | Arrival | Price | Source |

## 🚆 Trains
Show the best available train options:

| Train | Departure | Arrival | Duration | Price/Info | Source |

If train information is unavailable, say so clearly.

## 🚌 Buses

Show 2–3 available bus options for the requested route and travel date.

Include the following information whenever available:

| Bus Operator | Departure | Arrival | Duration | Price (₹) | Booking Website | Source |

Rules:
- Show the actual bus operator name when available.
- Show departure time, arrival time, duration, and ticket price when available.
- Show the booking website and source URL.
- Do not invent bus prices, timings, operators, or durations.
- If any information is unavailable, write "Not available".
- Treat each bus as an alternative transportation option.
- Do not add multiple bus prices together when calculating the total trip cost.
- Only the selected/recommended bus should be included in the final trip cost.

## 🏨 Hotels
Show the best available hotel options:

| Hotel | Location | Price | Rating | Source |

## 🌦️ Weather
Give a short weather summary for the destination for the requested dates.

## 💰 Estimated Trip Cost

### Selected Options

| Category | Selected Option | Cost |
| ✈️ Transportation | Air India Express | choose min |
| 🏨 Hotel | Moustache Goa Luxuria | choose minimum cost |
| 🍴 Other Expenses | Estimated | choose min cost |
| | **Total** | **price after adding** |

IMPORTANT:

- Never add alternative transportation options.
- Never add alternative hotels.
- Only the selected/recommended options are included in the final total.
- Clearly mention that other expenses are estimates.
- If a price is unavailable, write "Not available".
- Do not invent missing prices.

## 📌 Recommendation
Give a short recommendation for the best overall option based on price, duration, and convenience.

Keep the final response concise, readable, and useful.
"""

# Agent Node
def agent_node(state: AgentState):
    state_messages = state["messages"]
    recent_messages = state_messages[-6:]
    messages = [SystemMessage(content = system_prompt)] + recent_messages
    response = llm_with_tools.invoke(messages)
    return {"messages" : [response]}

builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START,"agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
builder.add_edge("agent", END)

# Memory 
from langgraph.checkpoint.memory import InMemorySaver
memory = InMemorySaver()
graph_memory = builder.compile(checkpointer=memory,name="react_agent_with_memory")


# Thread

def travel_assistant(query: str, thread_id: str = "1"):
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    response = graph_memory.invoke(
        {
            "messages": [
                ("user", query)
            ]
        },
        config=config
    )

    for msg in reversed(response["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            return msg.content

    return "Sorry, I could not generate a response."