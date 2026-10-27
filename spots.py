"""Surf spots and the official monitoring stations each one is matched to.

Keys
  sd_sites   San Diego County DEH site IDs (sdbeachinfo.com)
  la_stations LA County DPH station codes as named on the DPH monitoring map
  oc_keywords text that identifies the spot's stretch of coast in OC Health Care
              Agency closure/warning/advisory listings (ocbeachinfo.com)
  htb        Heal the Bay Beach Report Card location IDs (grades). If omitted the
             nearest active Heal the Bay site within 1.5 km is used.
  official   human-readable official source page for the spot's county
Coordinates are the official sampling location closest to the break.
"""

LA_URL = "http://publichealth.lacounty.gov/phcommon/public/eh/water_quality/beach_grades.cfm"
OC_URL = "https://ocbeachinfo.com/"
SD_URL = "https://www.sdbeachinfo.com/"
VC_URL = "https://rma.venturacounty.gov/divisions/environmental-health/ocean-water-quality-sampling-results/"
SB_URL = "https://www.countyofsb.org/ch-ocean-water-monitoring-program"

S = []

def spot(name, county, lat, lon, blurb, **kw):
    S.append(dict(name=name, county=county, lat=lat, lon=lon, blurb=blurb, **kw))

# ---------------- Santa Barbara ----------------
spot("Sands (Coal Oil Point)", "Santa Barbara", 34.4076, -119.8800,
     "a sand-bottom reef and point setup below the UCSB bluffs that comes alive on west and northwest swells",
     sb_stations=['WP0000012'], htb=[71])
spot("Leadbetter Point", "Santa Barbara", 34.4024, -119.6950,
     "a mellow right-hand point in front of Santa Barbara City College, a longboard favorite on winter swells",
     sb_stations=['WP0000007'], htb=[75])
spot("Carpinteria State Beach", "Santa Barbara", 34.3899, -119.5195,
     "a family beach with soft beach-break peaks that light up on clean west swells",
     sb_stations=['WP0000180'], htb=[80])

# ---------------- Ventura ----------------
spot("Rincon", "Ventura", 34.3733, -119.4760,
     "the Queen of the Coast, a long right-hand cobblestone point break on the Santa Barbara/Ventura line",
     vc_stations=['1000', '1100'], htb=[83, 260])
spot("Ventura Point (Surfers' Point)", "Ventura", 34.2730, -119.3050,
     "a forgiving right-hand cobble point at the mouth of the Ventura River, great for longboards",
     vc_stations=['13000'], htb=[95])
spot("C Street (Promenade Park)", "Ventura", 34.2753, -119.2954,
     "Ventura's famous stretch of rights along the Promenade, from California Street toward the pier",
     vc_stations=['14000', '15000', '17000'], htb=[97, 98, 96])
spot("Silver Strand (Oxnard)", "Ventura", 34.1567, -119.2254,
     "a punchy jetty-protected beach break at the entrance to Channel Islands Harbor",
     vc_stations=['38000', '39000', '40000'], htb=[119, 120])
spot("Port Hueneme Beach Park", "Ventura", 34.1414, -119.1947,
     "a pier-side beach break that handles bigger swells better than most of the Oxnard coast",
     vc_stations=['41000'], htb=[82])

# ---------------- Los Angeles ----------------
LA = dict(county="Los Angeles")
spot("Leo Carrillo", "Los Angeles", 34.0445, -118.9338,
     "a rocky right point at Arroyo Sequit Creek with a beginner-friendly beach break inside",
     la_stations=["DPH10", "DPH10B"])
spot("Zuma Beach", "Los Angeles", 34.0138, -118.8213,
     "a long, exposed beach break that picks up almost any swell, with heavy shorebreak on bigger days",
     la_stations=["DPH7", "DPH7B", "DPH8", "DPH8B"])
spot("Point Dume", "Los Angeles", 34.0138, -118.7919,
     "a reef and point setup under the Point Dume headland that works on west swells",
     la_stations=["SMB-O-1"])
spot("Malibu Surfrider", "Los Angeles", 34.0311, -118.6823,
     "First Point Malibu, the iconic right-hand point break next to the Malibu Pier and Malibu Lagoon",
     la_stations=["DPH3", "SMB-MC2", "DPH 002", "DPH 002B"])
spot("Topanga", "Los Angeles", 34.0381, -118.5829,
     "a fast right-hand cobble point at the mouth of Topanga Creek",
     la_stations=["SMB-1-18", "SMB-2-1"])
spot("Sunset Point (Will Rogers)", "Los Angeles", 34.0391, -118.5507,
     "a right point at the bottom of Sunset Boulevard with mellow peaks along Will Rogers State Beach",
     la_stations=["DPH101", "DPH102", "DPH102B"])
spot("Santa Monica Pier", "Los Angeles", 34.0079, -118.4978,
     "a beach break alongside the Santa Monica Pier, best on south swells with a morning offshore",
     la_stations=["SMB 3-3", "SMB-3-4", "DPH106"])
spot("Venice Breakwater", "Los Angeles", 33.9889, -118.4787,
     "a sand-bar peak that forms beside the Venice breakwater, the classic Dogtown wave",
     la_stations=["DPH107", "DPH107B", "SMB-3-8"])
spot("Venice Pier", "Los Angeles", 33.9782, -118.4679,
     "peaky beach-break waves on both sides of the Venice Fishing Pier",
     la_stations=["DPH108"])
spot("Dockweiler (Toes Beach)", "Los Angeles", 33.9440, -118.4441,
     "a consistent, uncrowded beach break under the LAX flight path with jetties that shape the sand",
     la_stations=["DPH110", "SMB-2-11"])
spot("El Porto", "Los Angeles", 33.9019, -118.4218,
     "the South Bay's most consistent beach break, at the north end of Manhattan Beach",
     la_stations=["SMB 5-1"])
spot("Manhattan Beach Pier", "Los Angeles", 33.8937, -118.4183,
     "peaky beach-break waves on either side of the Manhattan Beach Pier",
     la_stations=["DPH113", "DPH113B"])
spot("Hermosa Beach Pier", "Los Angeles", 33.8729, -118.4077,
     "a fun beach break by the Hermosa Pier that's best on combo swells",
     la_stations=["DPH114"])
spot("Redondo Breakwater", "Los Angeles", 33.8386, -118.3912,
     "a heavy wedging peak at the south end of the King Harbor breakwater that needs a big west swell",
     la_stations=["SMB-6-2", "SMB-6-3", "DPH116"])
spot("Torrance Beach (Haggerty's)", "Los Angeles", 33.8044, -118.3942,
     "a beach break at Torrance Beach leading to the Haggerty's reef at the foot of Palos Verdes",
     la_stations=["SMB-6-6", "SMB-7-1"])
spot("Royal Palms", "Los Angeles", 33.7177, -118.3220,
     "a rocky reef and point zone on the south side of Palos Verdes that likes winter swells",
     la_stations=["SMB-7-6"])
spot("Cabrillo Beach", "Los Angeles", 33.7092, -118.2830,
     "an outer-breakwater beach in San Pedro that only breaks on big south swells",
     la_stations=["SMB-7-9"])

# ---------------- Orange ----------------
spot("Seal Beach Pier", "Orange", 33.7377, -118.1062,
     "a beach break beside the Seal Beach pier, with a jetty-shaped wave at the river mouth",
     htb=[508, 140], oc_keywords=["Seal Beach"])
spot("Bolsa Chica", "Orange", 33.7018, -118.0552,
     "a long, mellow state beach that is a go-to for beginners and longboarders",
     htb=[143, 144], oc_keywords=["Bolsa Chica"])
spot("Huntington Cliffs (Dog Beach)", "Orange", 33.6756, -118.0285,
     "soft, sand-bottom peaks below the bluffs at Dog Beach, a longboard favorite",
     htb=[145], oc_keywords=["Huntington"])
spot("Huntington Beach Pier", "Orange", 33.6559, -118.0026,
     "Surf City's centerpiece: competitive peaks on both sides of the Huntington Beach Pier",
     htb=[147, 146], oc_keywords=["Huntington"])
spot("Huntington State Beach", "Orange", 33.6382, -117.9755,
     "a long run of beach-break peaks from Beach Boulevard toward the Santa Ana River",
     htb=[149, 148, 150], oc_keywords=["Huntington State", "Huntington"])
spot("Newport Point & 56th St", "Orange", 33.6220, -117.9444,
     "jetty-groomed beach-break wedges along West Newport's groins",
     htb=[153, 152, 154], oc_keywords=["Newport Beach", "West Newport"])
spot("The Wedge", "Orange", 33.5936, -117.8816,
     "the world-famous bodysurf and bodyboard shorebreak at the Newport Harbor jetty",
     htb=[157], oc_keywords=["Wedge", "Balboa"])
spot("Corona del Mar", "Orange", 33.5930, -117.8755,
     "a family beach in the lee of the Newport jetty that only breaks on big south swells",
     htb=[295, 203], oc_keywords=["Corona del Mar"])
spot("Crystal Cove", "Orange", 33.5783, -117.8491,
     "a state park coastline of reefs and coves between Newport and Laguna",
     htb=[296, 207], oc_keywords=["Crystal Cove"])
spot("Laguna Main Beach", "Orange", 33.5419, -117.7854,
     "Laguna Beach's downtown beach, with reef-and-sand waves and good bodysurfing",
     htb=[210, 211], oc_keywords=["Laguna Beach", "Main Beach"])
spot("Thalia Street (Laguna)", "Orange", 33.5295, -117.7738,
     "a sand-bottom beach break in Laguna that is one of the town's most popular spots",
     htb=[212, 1071], oc_keywords=["Laguna Beach", "Thalia", "Bluebird"])
spot("Salt Creek", "Orange", 33.4791, -117.7242,
     "a powerful reef-and-sand break in Dana Point below the Monarch Beach headland",
     htb=[255, 225], oc_keywords=["Salt Creek", "Dana Point"])
spot("Doheny", "Orange", 33.4617, -117.6865,
     "a gentle longboard and beginner wave next to Dana Point Harbor at San Juan Creek",
     htb=[228, 227, 229], oc_keywords=["Doheny", "San Juan Creek", "Dana Point"])
spot("Poche Beach", "Orange", 33.4407, -117.6457,
     "a fun beach break at the north end of San Clemente, near the Poche Creek outlet",
     htb=[238, 1062], oc_keywords=["Poche", "San Clemente"])
spot("San Clemente Pier", "Orange", 33.4193, -117.6205,
     "peaky waves next to the San Clemente Municipal Pier",
     htb=[1051, 240], oc_keywords=["San Clemente"])
spot("T-Street", "Orange", 33.4173, -117.6189,
     "a reef-and-sand break south of the San Clemente Pier that handles a range of swells",
     htb=[535], oc_keywords=["San Clemente", "T Street", "T-Street"])

# ---------------- San Diego ----------------
spot("Trestles (San Onofre)", "San Diego", 33.3855, -117.5952,
     "Lower and Upper Trestles, the world-class cobblestone peaks at San Mateo Creek in San Onofre State Beach",
     htb=[2112])
spot("Oceanside Harbor", "San Diego", 33.2044, -117.3941,
     "jetty-shaped beach-break peaks near the mouth of Oceanside Harbor",
     sd_sites=["184", "183"])
spot("Oceanside Pier", "San Diego", 33.1937, -117.3843,
     "a classic North County beach break on both sides of the Oceanside Pier",
     sd_sites=["181", "180"])
spot("Tamarack", "San Diego", 33.1454, -117.3451,
     "a consistent beach break in Carlsbad at the Tamarack Avenue stairs",
     sd_sites=["82"])
spot("Ponto (South Carlsbad)", "San Diego", 33.1063, -117.3215,
     "a reliable beach break at the south end of South Carlsbad State Beach near Batiquitos Lagoon",
     sd_sites=["95", "78"])
spot("Moonlight Beach", "San Diego", 33.0481, -117.2989,
     "Encinitas's town beach, a playful beach break at Cottonwood Creek",
     sd_sites=["72"])
spot("Swami's", "San Diego", 33.0344, -117.2931,
     "a famous right-hand reef point below the Self-Realization Fellowship gardens",
     sd_sites=["71"])
spot("Pipes (San Elijo)", "San Diego", 33.0283, -117.2889,
     "a reef break at the north end of San Elijo State Beach campground",
     sd_sites=["68", "205"])
spot("Cardiff Reef", "San Diego", 33.0157, -117.2819,
     "a forgiving reef break at the San Elijo Lagoon mouth, a longboard and beginner staple",
     sd_sites=["204", "203"])
spot("Seaside Reef", "San Diego", 33.0013, -117.2783,
     "a quality right and left reef at Cardiff's south end",
     sd_sites=["201", "202"])
spot("Del Mar (15th Street)", "San Diego", 32.9600, -117.2685,
     "beach-break peaks off Powerhouse Park and the Del Mar river mouths",
     sd_sites=["63", "65"])
spot("Torrey Pines State Beach", "San Diego", 32.9345, -117.2619,
     "a long beach break below the Torrey Pines bluffs at Los Peñasquitos Lagoon",
     sd_sites=["109"])
spot("Black's Beach", "San Diego", 32.8778, -117.2514,
     "San Diego's most powerful beach break, focused by the Scripps submarine canyon",
     sd_sites=["107"])
spot("La Jolla Shores", "San Diego", 32.8556, -117.2581,
     "the region's classic beginner beach, a gentle break south of Scripps Pier",
     sd_sites=["106", "54", "55", "56", "206"])
spot("La Jolla Cove", "San Diego", 32.8504, -117.2727,
     "a protected marine reserve cove that's popular with swimmers and snorkelers",
     sd_sites=["105"])
spot("Windansea", "San Diego", 32.8294, -117.2805,
     "a legendary La Jolla reef break with a powerful peak in front of the palm shack",
     sd_sites=["45", "103", "43"])
spot("Tourmaline", "San Diego", 32.8050, -117.2628,
     "a mellow longboard reef at Tourmaline Surf Park in north Pacific Beach",
     sd_sites=["101"])
spot("Pacific Beach (Crystal Pier)", "San Diego", 32.7945, -117.2562,
     "a busy beach break around Crystal Pier at the end of Grand Avenue",
     sd_sites=["37"])
spot("Mission Beach", "San Diego", 32.7713, -117.2535,
     "beach-break peaks from Belmont Park south to the Mission Bay jetty",
     sd_sites=["195", "148"])
spot("Ocean Beach Pier", "San Diego", 32.7467, -117.2549,
     "a punchy beach break on both sides of the OB Pier",
     sd_sites=["192", "193"])
spot("Sunset Cliffs", "San Diego", 32.7193, -117.2569,
     "a string of reef breaks below the Point Loma cliffs",
     sd_sites=["189", "190"])
spot("Coronado", "San Diego", 32.6818, -117.1852,
     "a wide, gentle beach break in front of the Hotel del Coronado",
     sd_sites=["7", "10", "121"])
spot("Silver Strand State Beach", "San Diego", 32.6264, -117.1394,
     "a long beach break on the strand between Coronado and Imperial Beach",
     sd_sites=["118", "120"])
spot("Imperial Beach Pier", "San Diego", 32.5787, -117.1331,
     "a beach break beside the Imperial Beach pier near the Tijuana River mouth",
     sd_sites=["4", "1", "116", "115"])

SPOTS = S
