import discord
from discord.ext import commands
import requests
import random
import re
from pyedhrec import EDHRec

# Dictionary of keywords and their definitions
keywords = {
    "ward": "Whenever this creature becomes the target of a spell or ability an opponent controls, counter that spell or ability unless its controller pays {COST}.",
    "hexproof": "This permanent can't be the target of spells or abilities your opponents control.",
    "flying": "This creature can't be blocked except by creatures with flying and/or reach.",
    "first strike": "If this creature is blocking or being blocked by a creature without first strike or double strike, it deals combat damage first.",
    "deathtouch": "Any amount of damage this deals to a creature is enough to destroy it.",
    "trample": "This creature can deal excess combat damage to the player or planeswalker it's attacking.",
    "haste": "This creature can attack and {T} as soon as it comes under your control.",
    "vigilance": "Attacking doesn't cause this creature to tap.",
    "reach": "This creature can block creatures with flying.",
    "lifelink": "If this creature deals damage, you gain that much life.",
    "menace": "This creature can't be blocked except by two or more creatures.",
    "indestructible": "Damage and effects that say 'destroy' don't destroy this.",
    "double strike": "This creature deals both first-strike and regular combat damage.",
    "flash": "You may cast this spell any time you could cast an instant.",
    "prowess": "Whenever you cast a noncreature spell, this creature gets +1/+1 until end of turn.",
    "defender": "This creature can't attack.",
    "landwalk": "This creature can't be blocked as long as defending player controls a [LAND TYPE] (e.g., Islandwalk).", 
    "scry": "Look at the top X cards of your library, then put any number of them on the bottom of your library and the rest on top in any order.",
    "affinity": "This spell costs {1} less to cast for each [THING] you control (e.g., Affinity for artifacts).",
    "convoke": "You may tap any number of creatures you control as you cast this spell. Each creature tapped this way pays for {1} or one mana of that creature's color.",
    "equip": "({COST}: Attach to target creature you control. Equip only as a sorcery.)",
    "flashback": "You may cast this card from your graveyard for its flashback cost. Then exile it.",
    "morph": "(You may cast this card face down as a 2/2 creature for {3}. Turn it face up any time for its morph cost.)",
    "regenerate": "({COST}: The next time this creature would be destroyed this turn, it isn't. Instead tap it, remove all damage from it, and remove it from combat.)",
    # ... and keep adding more if you like!
}

intents = discord.Intents.default()  # Select the intents you need
intents.message_content = True  # This is needed to read message content

bot = commands.Bot(command_prefix='!', intents=intents)
edhrec = EDHRec()

@bot.command(name='define')
async def define_keyword(ctx, keyword):
  """Defines a Magic: The Gathering keyword ability."""
  keyword = keyword.lower()
  if keyword in keywords:
    definition = keywords[keyword]
    await ctx.send(f"**{keyword.capitalize()}**: {definition}")
  else:
    await ctx.send(f"I don't know the keyword '{keyword}'.")

@bot.command(name='search')
async def search_commander(ctx, *, commander_name):
    """Searches for decks with the specified commander (using EDHRec API)."""
    try:
        # Get commander data from EDHRec
        commander_data = edhrec.get_commander_data(commander_name)

        # Access the Moxfield URI
        commander_moxfield_uri = commander_data['container']['json_dict']['card']['moxfield_uri']

        # Check if 'similar' key exists before accessing it
        if 'similar' in commander_data['container']['json_dict']:
            similar_commanders = commander_data['container']['json_dict']['similar']
            if similar_commanders:
                random_commander = random.choice(similar_commanders)
                random_moxfield_uri = random_commander['moxfield_uri']
            else:
                random_moxfield_uri = None
        else:
            random_moxfield_uri = None

        # Send the Moxfield URIs to the channel
        await ctx.send(f"Moxfield decks for {commander_name}: {commander_moxfield_uri}")
        if random_moxfield_uri:
            await ctx.send(f"Random similar commander decks on Moxfield: {random_moxfield_uri}")

    except Exception as e:  # Catch potential pyedhrec or other exceptions
        await ctx.send(f"An error occurred while fetching data from EDHRec: {e}")

@bot.command(name='rec')
async def get_recommendations(ctx, *, commander_name):
    """Gets top card recommendations with high synergy for a commander from EDHRec."""
    try:
        # Get commander data from EDHRec
        commander_data = edhrec.get_commander_data(commander_name)
        
        recommendations = []
        for cardlist in commander_data['container']['json_dict']['cardlists']:
            # Sort cards by synergy in descending order
            sorted_cards = sorted(cardlist['cardviews'], key=lambda card: card['synergy'], reverse=True)
            
            count = 0
            for card in sorted_cards:
                if card['synergy'] >= 0.65 and count < 5:
                    recommendations.append(card['name'])
                    count += 1

        if recommendations:
            await ctx.send(f"Top recommendations with high synergy for {commander_name} on EDHRec:\n- " + "\n- ".join(recommendations))
        else:
            await ctx.send(f"No recommendations with high synergy found for {commander_name} on EDHRec.")

    except Exception as e:
        await ctx.send(f"An error occurred while fetching recommendations from EDHRec: {e}")

@bot.command(name='combos')
async def get_combos(ctx, *, commander_name):
    """Gets a random combo for a commander from EDHRec."""
    try:
        # Get combos data from EDHRec
        combos_data = edhrec.get_card_combos(commander_name)

        # Extract the combo list and total count
        combo_list = combos_data['container']['json_dict']['cardlists']
        total_combos = len(combo_list)

        # Select 1 random combo
        if combo_list:
            random_combo = random.choice(combo_list)
            combo_name = random_combo['header']
            combo_link = "https://edhrec.com" + random_combo['href']  # Construct full combo link

            # Construct and send the response message (corrected line)
            response_message = (
                f"**{combos_data['header']} ({total_combos} total)**\n"
                f"Random combo: {combo_name}\n{combo_link}\n"
                f"See all combos for {commander_name} on EDHRec: https://edhrec.com{list(combos_data['container']['breadcrumb'][1].keys())[0]}"  # Convert to list
            )
            await ctx.send(response_message)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # Suggest checking the spelling if 404 Not Found
            await ctx.send(f"Could not find combos for '{commander_name}'. Please double-check the spelling.")
        else:
            # Generic error message for other HTTP errors
            await ctx.send(f"An error occurred while fetching combos from EDHRec: {e}")

    except Exception as e:
        await ctx.send(f"An error occurred while fetching combos from EDHRec: {e}")


@bot.command(name='details')
async def get_card_details(ctx, *, card_name):
    """Gets card details for a card from EDHRec."""
    try:
        details = edhrec.get_card_details(card_name)
        card_link = edhrec.get_card_link(card_name)

        await ctx.send(f"Card details for {card_name} on EDHRec: {card_link}")
        await ctx.send(f"```\n{details['oracle_text']}\n```")  # Using code block for formatting

    except Exception as e:
        await ctx.send(f"An error occurred while fetching card details from EDHRec: {e}")

@bot.command(name='rules')
async def get_card_rulings(ctx, *, card_name):
    """Fetches rulings for a specific Magic: The Gathering card from Scryfall."""
    try:
        # Use Scryfall API to search for the card and get rulings URI
        response = requests.get(f"https://api.scryfall.com/cards/named?fuzzy={card_name}")
        response.raise_for_status()
        card_data = response.json()
        rulings_uri = card_data['rulings_uri']

        # Fetch rulings from the rulings URI
        response = requests.get(rulings_uri)
        response.raise_for_status()
        rulings_data = response.json()

        # Extract published date and comment for each ruling
        rulings_info = []
        for ruling in rulings_data['data']:
            published_at = ruling['published_at']
            comment = ruling['comment']
            rulings_info.append(f"**{published_at}**: {comment}")

        # Send the rulings information to the channel
        if rulings_info:
            await ctx.send(f"Rulings for {card_data['name']}:\n" + "\n".join(rulings_info))
        else:
            await ctx.send(f"No rulings found for {card_data['name']}.")

    except requests.exceptions.RequestException as e:
        # If card not found or API error, send error message
        await ctx.send(f"Could not find card '{card_name}' or an error occurred.")

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run('YOUR_BOT_TOKEN')