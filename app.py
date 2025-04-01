from flask import Flask, jsonify, request, render_template
import random
import asyncio
import sys
from flask_cors import CORS

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Import the radios library and required enums
from radios import RadioBrowser, FilterBy, Order

app = Flask(__name__)
CORS(app)

def get_stations_by_country(country: str):
    """Return a list of stations filtered by the given country name."""

    async def _fetch():
        async with RadioBrowser(user_agent="WorldRadioApp/1.0") as radios:
            print(f"📡 Fetching stations for country: {country}")
            stations = await radios.stations(
                filter_by=FilterBy.COUNTRY_EXACT,
                filter_term=country,
                limit=100,
                order=Order.CLICK_COUNT,
                reverse=True
            )

            if not stations:
                print(f"⚠ No stations found for {country}.")
                return []

            print(f"✅ Found {len(stations)} stations for {country}.")
            return stations

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_fetch())
    except Exception as e:
        print(f"❌ Error fetching stations for {country}:", e)
        return []


def get_all_countries():
    """Return a list of all available countries (as provided by the radios library)."""

    async def _fetch():
        async with RadioBrowser(user_agent="WorldRadioApp/1.0") as radios:
            countries = await radios.countries()
            if not countries:
                print("⚠ No countries available from API.")
            else:
                print(f"🌍 Found {len(countries)} countries.")
            return countries

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_fetch())
    except Exception as e:
        print("❌ Error fetching country list:", e)
        return []


def get_random_station():
    """Pick a random country and a station from it."""

    async def _fetch():
        async with RadioBrowser(user_agent="WorldRadioApp/1.0") as radios:
            try:
                print("📡 Fetching available countries...")
                countries = await radios.countries()

                if not countries:
                    print("❌ No countries found!")
                    return None, "No available countries"

                # ✅ Filter countries with at least 5 stations
                valid_countries = [c for c in countries if int(c.station_count) > 5]
                if not valid_countries:
                    print("❌ No valid countries with enough stations!")
                    return None, "No valid countries"

                # 🌍 Pick a random country
                country = random.choice(valid_countries)
                country_name = country.name  # ✅ Access attributes directly
                print(f"🌍 Selected country: {country_name}")

                print(f"📡 Fetching stations for {country_name}...")
                stations = await radios.stations(
                    filter_by=FilterBy.COUNTRY,
                    filter_term=country_name,
                    limit=100,
                    order=Order.CLICK_COUNT,
                    reverse=True
                )

                if not stations:
                    print(f"❌ No stations found in {country_name}!")
                    return None, country_name  # Still return country name

                # 📻 Pick a random station
                station = random.choice(stations)
                print(f"📻 Selected station: {station.name} ({station.url})")
                return station, country_name

            except Exception as e:
                print(f"❌ Error fetching stations: {e}")
                return None, "Error fetching station"

    try:
        return asyncio.run(_fetch())
    except Exception as e:
        print("❌ Unexpected error in get_random_station:", e)
        return None, "Unexpected error"

    try:
        return asyncio.run(_fetch())
    except Exception as e:
        print("❌ Unexpected error in get_random_station:", e)
        return None, "Unexpected error"


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/api/station', methods=["GET"])
def api_station():
    mode = request.args.get("mode", "normal")

    if mode == "normal":
        country = request.args.get("country")
        frequency = request.args.get("frequency")

        if not country or not frequency:
            return jsonify({"error": "For normal mode, provide both 'country' and 'frequency' parameters."}), 400

        try:
            freq_index = int(float(frequency))
        except ValueError:
            return jsonify({"error": "Frequency must be a number."}), 400

        stations = get_stations_by_country(country)
        if not stations:
            return jsonify({"error": f"No stations found for country {country}."}), 404

        index = freq_index % len(stations)
        station = stations[index]

        return jsonify({
            "mode": "normal",
            "country": country,
            "frequency": frequency,
            "station": {
                "name": station.name,
                "country": station.country,
                "url": station.url,
                "homepage": station.homepage,
                "favicon": station.favicon
            }
        })

    elif mode == "random":
        station, country = get_random_station()
        if not station:
            return jsonify({"error": f"No station found for country {country}."}), 404

        return jsonify({
            "mode": "random",
            "country": country,
            "station": {
                "name": station.name,
                "country": station.country,
                "url": station.url,
                "homepage": station.homepage,
                "favicon": station.favicon
            }
        })

    else:
        return jsonify({"error": "Invalid mode. Choose 'normal' or 'random'."}), 400


if __name__ == '__main__':
    app.run(debug=True)
