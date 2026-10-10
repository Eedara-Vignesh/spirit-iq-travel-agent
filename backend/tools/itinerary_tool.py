"""
backend/tools/itinerary_tool.py
==============================
Day-wise itinerary generation tool.
Assigned to: Member 4 (Frontend, Itinerary and Group Planning)

Synthesizes activities, time blocks, and geographical sequencing into DayPlan items.
Provides destination-grounded activities with authentic local sights, culinary stops,
and pace-sensitive timing blocks.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from backend.schemas import ActivityItem, DayPlan, ToolResult, TravelPace
from backend.tools.destination_tool import get_destination_catalog_entry

# Curated daily attraction templates for popular destinations
DESTINATION_ACTIVITIES_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "goa": [
        {
            "theme": "North Goa Heritage & Beach Coastal Trail",
            "morning": ("Fort Aguada & Lighthouse", "Explore 17th-century Portuguese fortress and coastal views of Sinquerim.", "Sinquerim, North Goa", 300.0),
            "afternoon": ("Calangute & Baga Beach Walk", "Stroll along famous golden sand shores, enjoy beach shacks and fresh seafood.", "Baga Beach", 600.0),
            "evening": ("Anjuna Sunset & Flea Market", "Scenic sunset over rocky cliffs followed by local handicrafts and music.", "Anjuna Beach", 400.0),
        },
        {
            "theme": "Old Goa UNESCO Churches & Latin Quarter",
            "morning": ("Basilica of Bom Jesus & Se Cathedral", "Tour UNESCO World Heritage Baroque church housing the relics of St. Francis Xavier.", "Old Goa", 200.0),
            "afternoon": ("Fontainhas Latin Quarter Heritage Walk", "Wander through colourful Portuguese colonial streets, vintage bakeries, and art galleries.", "Panaji", 500.0),
            "evening": ("Mandovi River Sunset Cruise", "Evening river cruise featuring traditional Goan folk performances and river breezes.", "Panaji Jetty", 700.0),
        },
        {
            "theme": "South Goa Serenity & Spice Plantation",
            "morning": ("Sahakari Spice Farm Guided Tour", "Walk through organic spice gardens with traditional buffet lunch on banana leaf.", "Ponda", 800.0),
            "afternoon": ("Dudhsagar Waterfalls Viewpoint", "Majestic four-tiered waterfall surrounded by lush Western Ghats forest.", "Mollem", 1000.0),
            "evening": ("Palolem Beach Leisure Sunset", "Tranquil crescent beach relaxation and seaside dining under palm canopies.", "Canacona, South Goa", 500.0),
        },
    ],
    "kerala": [
        {
            "theme": "Fort Kochi Colonial Heritage & Coastal Arts",
            "morning": ("Chinese Fishing Nets & St. Francis Church", "Observe iconic cantilevered fishing nets and India's oldest European church.", "Fort Kochi", 200.0),
            "afternoon": ("Mattancherry Palace & Jew Town", "Explore murals depicting Hindu epics and browse antique spice markets in Jew Town.", "Mattancherry", 400.0),
            "evening": ("Kathakali Classical Dance Performance", "Witness elaborate traditional makeup and vivid storytelling at the cultural centre.", "Kochi Cultural Centre", 600.0),
        },
        {
            "theme": "Alleppey Backwaters & Countryside Cruise",
            "morning": ("Alleppey Houseboat / Shikara Cruise", "Glide through tranquil palm-fringed canals, paddy fields, and backwater lagoons.", "Punnamada, Alleppey", 1500.0),
            "afternoon": ("Traditional Kuttanad Village Lunch", "Savour authentic Kerala banana-leaf meal with pearl spot fish (Karimeen) and red rice.", "Kuttanad", 500.0),
            "evening": ("Marari Beach Sunset Walk", "Pristine white sand fishing village beach, perfect for quiet evening sunset viewing.", "Mararikulam", 200.0),
        },
        {
            "theme": "Munnar Rolling Tea Hills & High Peaks",
            "morning": ("Kolukkumalai Tea Estate Trail", "Walk among high-altitude tea plantations with tea tasting and plantation history.", "Munnar", 500.0),
            "afternoon": ("Eravikulam National Park Safari", "Spot endangered Nilgiri Tahr mountain goats amidst rolling shola grasslands.", "Rajamalai, Munnar", 600.0),
            "evening": ("Mattupetty Dam & Echo Point Walk", "Picturesque lakeside stroll surrounded by misty tea-covered hills.", "Mattupetty", 300.0),
        },
    ],
    "coorg": [
        {
            "theme": "Coffee Trails & Cascading Waterfalls",
            "morning": ("Abbey Falls Canopy Walk", "Walk through lush spice and coffee estates to the roaring Abbey waterfall bridge.", "Madikeri", 200.0),
            "afternoon": ("Dubare Elephant Camp & River Crossing", "Learn about elephant conservation and observe gentle river bathing by caretakers.", "Kaveri River", 500.0),
            "evening": ("Raja's Seat Sunset Pavilion", "Historic viewpoint of Kodagu kings with panoramic sunset across rolling misty hills.", "Madikeri", 150.0),
        },
        {
            "theme": "Spiritual Heritage & Tibetan Enclave",
            "morning": ("Namdroling Monastery (Golden Temple)", "Explore grand 40-foot gilded Buddha statues, prayer wheels, and Tibetan artwork.", "Bylakuppe", 200.0),
            "afternoon": ("Traditional Kodava Culinary Experience", "Taste authentic Pandi Curry, Kadambuttu (steamed rice balls), and Coorg honey.", "Kushalnagar", 600.0),
            "evening": ("Madikeri Fort & Omkareshwara Temple", "Visit Gothic-Islamic fusion architecture and feed sacred temple pond fish.", "Madikeri", 100.0),
        },
    ],
    "udaipur": [
        {
            "theme": "Royal Palaces & Serene Pichola Waters",
            "morning": ("City Palace & Crystal Gallery", "Marvel at Rajasthan's largest palace complex, courtyards, and mirror work.", "Old Udaipur", 600.0),
            "afternoon": ("Lake Pichola Boat Cruise to Jag Mandir", "Scenic boat ride past Lake Palace to island garden palace of Jag Mandir.", "Lake Pichola", 750.0),
            "evening": ("Bagore Ki Haveli Folk Dance & Sunset", "Dharohar Rajasthani puppet and folk dance show at historic waterfront mansion.", "Gangaur Ghat", 350.0),
        },
        {
            "theme": "Royal Gardens & Panoramic Hilltop Forts",
            "morning": ("Saheliyon-ki-Bari Fountains", "Royal courtyard garden with marble elephants, lotus pools, and gentle fountains.", "Udaipur", 150.0),
            "afternoon": ("Jagdish Temple & Old City Silver Bazaars", "Intricately carved Indo-Aryan temple and bustling bazaar for miniature paintings.", "Old City", 300.0),
            "evening": ("Monsoon Palace (Sajjangarh) Sunset", "Hilltop fort with sweeping 360-degree panorama of Udaipur lakes and sunset.", "Sajjangarh", 400.0),
        },
    ],
    "jaipur": [
        {
            "theme": "Forts of the Rajputs & Royal Architecture",
            "morning": ("Amber Fort & Palace Courtyards", "Ascend grand hilltop fortress, Sheesh Mahal mirror hall, and Maota Lake.", "Amer, Jaipur", 500.0),
            "afternoon": ("Hawa Mahal & City Palace Complex", "Honeycomb palace of winds facade followed by royal armory and museum courtyards.", "Pink City", 600.0),
            "evening": ("Nahargarh Fort Sunset Over Pink City", "Panoramic sunset view overlooking the entire illuminated expanse of Jaipur.", "Aravalli Hills", 300.0),
        },
        {
            "theme": "Astronomy, Bazaars & Cultural Feast",
            "morning": ("Jantar Mantar UNESCO Astronomical Observatory", "World's largest stone sundial and precise medieval astronomical instruments.", "Pink City", 200.0),
            "afternoon": ("Johari & Bapu Bazaar Shopping", "Explore traditional tie-dye textiles (Bandhani), gemstones, and blue pottery.", "Jaipur Old City", 500.0),
            "evening": ("Chokhi Dhani Ethnic Village & Feast", "Authentic Rajasthani village experience with thali dining, folk dances, and music.", "Tonk Road", 1200.0),
        },
    ],
    "manali": [
        {
            "theme": "Alpine Valleys & High Mountain Passes",
            "morning": ("Solang Valley Adventure Sights", "Valley surrounded by snow-capped peaks with paragliding and zorbing viewpoints.", "Solang", 700.0),
            "afternoon": ("Atal Tunnel & Sissu Lahaul Valley", "Drive through historic 9km Himalayan engineering marvel to high altitude Lahaul.", "Sissu", 1200.0),
            "evening": ("Old Manali Riverside Cafes & Live Music", "Charming wooden houses, trout delicacies, and bohemian music cafes.", "Old Manali", 500.0),
        },
        {
            "theme": "Ancient Temples & Cedar Forest Trails",
            "morning": ("Hadimba Temple & Van Vihar Forest", "Pagoda-style wooden temple built in 1553 surrounded by towering deodar trees.", "Dhungri, Manali", 150.0),
            "afternoon": ("Vashisht Hot Water Sulphur Springs & Temple", "Natural mineral springs and traditional stone architecture village stroll.", "Vashisht", 200.0),
            "evening": ("Mall Road Stroll & Himalayan Handicrafts", "Browse Tibetan woollens, Kullu shawls, and savour warm street momos.", "Manali Mall Road", 400.0),
        },
    ],
    "shimla": [
        {
            "theme": "Colonial Heritage Ridge & Jakhoo Hill",
            "morning": ("The Ridge & Christ Church", "Iconic neo-Gothic church and open square with views of distant snow ranges.", "The Ridge", 100.0),
            "afternoon": ("Jakhoo Temple Ropeway & Monkey Hill", "Ropeway ride to Shimla's highest peak with giant Lord Hanuman statue.", "Jakhoo Peak", 500.0),
            "evening": ("Mall Road & Lakkar Bazaar Stroll", "Vehicle-free heritage promenade, wooden handicraft shopping, and cafe dining.", "Mall Road", 400.0),
        },
        {
            "theme": "Kufri Alpine Vistas & Viceregal Architecture",
            "morning": ("Kufri Himalayan Nature Park", "Panoramic mountain viewpoints, yak rides, and high-altitude flora.", "Kufri", 400.0),
            "afternoon": ("Viceregal Lodge (IIAS)", "Grand Scottish baronial castle where historic Indian treaties were drafted.", "Observatory Hill", 300.0),
            "evening": ("Scandal Point & Gaiety Theatre Heritage", "Historic meeting point and Victorian theatre heritage walk.", "The Mall", 250.0),
        },
    ],
    "varanasi": [
        {
            "theme": "Sacred Ganges Ghats & Evening Aarti",
            "morning": ("Sunrise Rowing Boat on Mother Ganges", "Witness morning rituals, bathing pilgrims, and rising sun over ancient ghats.", "Assi to Dashashwamedh", 400.0),
            "afternoon": ("Kashi Vishwanath Temple Corridor", "Spiritual corridor to sacred golden-spired Jyotirlinga shrine.", "Vishwanath Gali", 250.0),
            "evening": ("Dashashwamedh Ghat Grand Maha Aarti", "Spectacular synchronized flame ceremony, brass lamps, and devotional chants.", "Dashashwamedh Ghat", 200.0),
        },
        {
            "theme": "Buddhist Legacy of Sarnath & Silk Weaving",
            "morning": ("Sarnath Buddhist Stupa & Deer Park", "Site of Lord Buddha's first sermon, Dhamek Stupa, and Ashoka Pillar museum.", "Sarnath", 300.0),
            "afternoon": ("Banarasi Silk Weaving Village Workshop", "Watch master weavers create exquisite gold-brocade Banarasi silk sarees.", "Madanpura", 300.0),
            "evening": ("Assi Ghat Subah-e-Banaras Cultural Music", "Evening classical sitar recital and clay-cup Malaiyo saffron milk dessert.", "Assi Ghat", 250.0),
        },
    ],
    "pondicherry": [
        {
            "theme": "French Quarter Heritage & Promenade Waves",
            "morning": ("White Town French Heritage Walking Tour", "Stroll past pastel yellow colonial villas, vibrant bougainvillea, and French cafes.", "White Town", 250.0),
            "afternoon": ("Sri Aurobindo Ashram & French Bakery Lunch", "Peaceful meditation courtyard followed by fresh croissants and baguettes.", "Rue de la Marine", 400.0),
            "evening": ("Promenade Beach & Rock Beach Sunset", "Vehicle-free evening stroll along the seawall with crashing ocean waves.", "Goubert Avenue", 200.0),
        },
        {
            "theme": "Universal Township & Golden Matrimandir",
            "morning": ("Auroville Visitor Centre & Matrimandir View", "Experimental international township focused on human unity and peace pavilion.", "Auroville", 300.0),
            "afternoon": ("Paradise Beach Ferry Crossing & Water Sights", "Speedboat transfer to golden isolated sand spit between river and sea.", "Chunnambar", 450.0),
            "evening": ("Serenity Beach Surfers Bay Sunset", "Watch local surfers, stroll the rock pier, and enjoy fresh catch seaside dinners.", "Kottakuppam", 400.0),
        },
    ],
    "ooty": [
        {
            "theme": "Queen of Hills Nilgiri Railway & Peaks",
            "morning": ("Nilgiri Mountain Railway Toy Train Ride", "Heritage steam train traversing UNESCO mountain bridges and tea tunnels.", "Ooty to Coonoor", 350.0),
            "afternoon": ("Doddabetta Peak & Telescope House", "Highest summit in Nilgiri mountains offering sprawling valley panoramas.", "Doddabetta", 200.0),
            "evening": ("Ooty Botanical & Rose Garden Walk", "Over 20,000 varieties of blooming roses and rare fossilized tree trunks.", "Ooty Town", 200.0),
        },
        {
            "theme": "Pykara Waterfalls & Tea Factory Trails",
            "morning": ("Pykara Lake Boat Ride & Waterfalls", "Peaceful reservoir boat ride and cascading stepped forest waterfalls.", "Pykara", 400.0),
            "afternoon": ("Tea Museum & Factory Processing Tour", "Observe tea leaf withering to packaging with freshly brewed Nilgiri tea tasting.", "Dodabetta Road", 250.0),
            "evening": ("Ooty Lake Boating & Chocolate Bazaar", "Pedal boat ride on artificial lake followed by shopping for homemade fudge.", "Ooty Lake", 300.0),
        },
    ],
}


def _find_catalog_key(destination: str) -> Optional[str]:
    """Resolve destination string to matching catalog key."""
    cleaned = destination.strip().lower()
    for key in DESTINATION_ACTIVITIES_CATALOG:
        if key in cleaned or cleaned in key:
            return key
    return None


def build_daywise_itinerary(
    destination: str,
    start_date: date,
    end_date: date,
    interests: Optional[List[str]] = None,
    pace: TravelPace = TravelPace.BALANCED,
) -> ToolResult:
    """
    Generate an authentic, day-wise activity schedule grounded in the requested destination.
    Uses curated destination intelligence for supported destinations and synthesizes
    coherent, varied itineraries for any global or domestic location.
    """
    interests = [i.lower().strip() for i in (interests or [])]
    num_days = max(1, (end_date - start_date).days + 1)
    target_dest = destination.strip()

    catalog_key = _find_catalog_key(target_dest)
    curated_days = DESTINATION_ACTIVITIES_CATALOG.get(catalog_key, []) if catalog_key else []

    # Check destination catalog metadata for additional highlights
    catalog_entry = get_destination_catalog_entry(target_dest)
    highlights = catalog_entry.get("highlights", []) if catalog_entry else []

    day_plans: List[DayPlan] = []

    for i in range(1, num_days + 1):
        day_date = start_date + timedelta(days=i - 1)
        curated_idx = (i - 1) % len(curated_days) if curated_days else -1

        if curated_idx >= 0 and curated_days:
            # Use curated authentic activities for this destination
            c_day = curated_days[curated_idx]
            theme = f"Day {i}: {c_day['theme']}"

            # Morning
            m_title, m_desc, m_loc, m_cost = c_day["morning"]
            morning_act = ActivityItem(
                time_slot="Morning (09:00 - 12:30)",
                title=m_title,
                description=m_desc,
                location=m_loc,
                estimated_cost_inr=m_cost,
            )

            # Afternoon
            a_title, a_desc, a_loc, a_cost = c_day["afternoon"]
            afternoon_act = ActivityItem(
                time_slot="Afternoon (14:00 - 17:00)",
                title=a_title,
                description=a_desc,
                location=a_loc,
                estimated_cost_inr=a_cost,
            )

            # Evening
            e_title, e_desc, e_loc, e_cost = c_day["evening"]
            evening_act = ActivityItem(
                time_slot="Evening (18:00 - 20:30)",
                title=e_title,
                description=e_desc,
                location=e_loc,
                estimated_cost_inr=e_cost,
            )

            if pace == TravelPace.RELAXED:
                activities = [morning_act, evening_act]
            elif pace == TravelPace.PACKED:
                activities = [
                    morning_act,
                    afternoon_act,
                    evening_act,
                    ActivityItem(
                        time_slot="Night (21:00 - 22:30)",
                        title=f"{target_dest} Night Illumination & Stroll",
                        description=f"Leisure walk observing night-lit monuments and vibrant street cafes in {target_dest}.",
                        location=target_dest,
                        estimated_cost_inr=250.0,
                    ),
                ]
            else:
                activities = [morning_act, afternoon_act, evening_act]

            total_cost = sum(a.estimated_cost_inr for a in activities)
            day_plans.append(
                DayPlan(
                    day_number=i,
                    date=day_date,
                    theme_or_title=theme,
                    activities=activities,
                    estimated_daily_cost_inr=total_cost,
                    overnight_location=target_dest,
                    day_notes=f"Pace: {pace.value.capitalize()}. Highlights verified from destination catalog.",
                )
            )
        else:
            # Dynamic destination synthesis: Build diverse, logical daily themes using highlights or destination geography
            day_themes = [
                ("Arrival, Orientation & Landmark Exploration", "iconic_landmark"),
                ("Cultural Heritage, Architecture & Old Bazaars", "culture_heritage"),
                ("Scenic Nature Trails, Viewpoints & Photography", "nature_viewpoints"),
                ("Authentic Gastronomy, Local Markets & Craft Traditions", "local_crafts"),
                ("Relaxed Leisure, Hidden Gems & Sunset Farewell", "leisure_sunset"),
            ]
            theme_title, theme_focus = day_themes[(i - 1) % len(day_themes)]
            theme = f"Day {i}: {target_dest} — {theme_title}"

            # Pick destination-specific landmark if available
            hl_morning = highlights[(i * 2 - 2) % len(highlights)] if highlights else f"Iconic Landmarks of {target_dest}"
            hl_afternoon = highlights[(i * 2 - 1) % len(highlights)] if highlights else f"Cultural Quarter of {target_dest}"

            activities = [
                ActivityItem(
                    time_slot="Morning (09:00 - 12:30)",
                    title=f"Exploring {hl_morning}",
                    description=f"Guided morning exploration of {hl_morning} with focus on architecture and local history.",
                    location=f"{target_dest}",
                    estimated_cost_inr=450.0,
                ),
                ActivityItem(
                    time_slot="Afternoon (14:00 - 17:00)",
                    title=f"{hl_afternoon} & Regional Culinary Trail",
                    description=f"Visit {hl_afternoon} followed by sampling signature regional specialties at renowned local eateries.",
                    location=f"{target_dest} District",
                    estimated_cost_inr=650.0,
                ),
                ActivityItem(
                    time_slot="Evening (18:00 - 20:30)",
                    title=f"{target_dest} Sunset Viewpoint & Evening Bazaar",
                    description=f"Take in the sunset from an elevated viewpoint followed by traditional craft shopping in local bazaars.",
                    location=f"{target_dest}",
                    estimated_cost_inr=350.0,
                ),
            ]

            if pace == TravelPace.RELAXED:
                activities = [activities[0], activities[2]]

            total_cost = sum(a.estimated_cost_inr for a in activities)
            day_plans.append(
                DayPlan(
                    day_number=i,
                    date=day_date,
                    theme_or_title=theme,
                    activities=activities,
                    estimated_daily_cost_inr=total_cost,
                    overnight_location=target_dest,
                    day_notes=f"Pace: {pace.value.capitalize()}. Tailored for {', '.join(interests) if interests else 'sightseeing'}.",
                )
            )

    return ToolResult.ok(
        data={"itinerary": [d.model_dump() for d in day_plans]},
        metadata={
            "tool": "itinerary_tool",
            "destination": target_dest,
            "days_count": len(day_plans),
            "curated_catalog_used": bool(curated_days),
        },
    )
