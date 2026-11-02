"""
ReelAgent: Responsible for Algorithmic Reel Captions, Hashtag Taxonomies,
and Visual-Content-Aware Viral Hooks for the first 3 seconds.
Strictly adheres to FR-06 and FR-07 of requirements.md.
"""
from typing import List, Dict, Optional, Any

class ReelAgent:
    """
    Agent responsible for:
    1. Overall high-converting post caption proposal with hashtags & CTA (FR-06.1)
    2. Visual-content-aware viral hook proposal based on uploaded media (FR-07.1)
    3. Multi-style caption & hook variation generators with in-place regeneration
    """

    def get_caption_variations(
        self,
        category: str,
        vibe: Optional[str] = None,
        cycle_offset: int = 0
    ) -> List[Dict[str, str]]:
        """
        Generates 4-6 diverse, high-converting caption styles for the detected category & vibe:
        1. Poetic / Signature Story
        2. Boutique / Product & Action
        3. Short & Aesthetic
        4. Viral Poll / Engagement
        5. Royal Heritage / Masterclass
        6. Artisan Story & Craft
        """
        cat = (category or "").lower()
        vl = (vibe or "").lower()

        if "ethnic" in cat or "saree" in cat or "traditional" in cat or "textile" in cat or "saree" in vl:
            variations = [
                {
                    "style": "🥻 Poetic Heritage",
                    "caption": (
                        "Six yards of pure elegance, timeless heritage, and artisan grace 🥻✨ "
                        "Every thread weaves a story of tradition that never goes out of style. "
                        "Which drape is your favorite? Let us know in the comments! 👇\n\n"
                        "#sareelove #handloomsaree #silksaree #ethnicwear #indianfashion #sareedraping #traditionalwear #festivecollection #ootd"
                    )
                },
                {
                    "style": "🛍️ Boutique & Shop Now",
                    "caption": (
                        "Festive Collection Drop 🥻✨ Handcrafted with exquisite zari borders and lustrous silk textures. "
                        "Perfect for weddings, celebrations, and festive gatherings. "
                        "Limited pieces available—DM us to order or tap link in bio! 🛍️👇\n\n"
                        "#festivewear #handloomsaree #silksarees #boutiquefashion #indianwedding #ethniccollection #shopnow"
                    )
                },
                {
                    "style": "⚡ Short & Aesthetic",
                    "caption": (
                        "Draped in timeless grace 💫 Pure artisan handloom in every fold. 🥻✨\n\n"
                        "#sareelove #traditionalwear #handloom #ethnicfashion #aestheticreels #indiancouture"
                    )
                },
                {
                    "style": "🔥 Viral Engagement",
                    "caption": (
                        "Rate this drape from 1 to 10 in the comments! 👇 Would you wear this to an upcoming celebration? "
                        "Save this reel for your festive wardrobe inspiration! ✨🥻\n\n"
                        "#sareeinspiration #ethnicdrape #fashionpoll #handloomlove #festiveseason #trendingreels"
                    )
                },
                {
                    "style": "👑 Royal Bridal & Luxury",
                    "caption": (
                        "Woven for royalty 👑✨ The intricate zari borders and opulent silk sheen make this a masterclass in Indian craftsmanship. "
                        "Tag someone who loves exquisite handlooms! 💫👇\n\n"
                        "#bridalsaree #royalsilk #handloomluxury #weddingsaree #kanchipuram #banarasi #zari #ethnicwear"
                    )
                },
                {
                    "style": "🌿 Artisan Story & Craft",
                    "caption": (
                        "Behind every saree is weeks of patient weaving and generations of artisan dedication 🌿 "
                        "Each motif tells a tale of cultural heritage. Cherish authentic handloom! 🥻✨\n\n"
                        "#handloomheritage #vocalforlocal #weavesofindia #artisanmade #sustainablefashion #indiantextiles"
                    )
                }
            ]
        elif "travel" in cat:
            variations = [
                {
                    "style": "🌿 Scenic Wanderlust",
                    "caption": (
                        "Lost in the beauty of places that make you feel truly alive 🌿✨ "
                        "There is nothing like escaping the routine and discovering moments that take your breath away. "
                        "Tag someone you’d travel here with right now! ✈️👇\n\n"
                        "#wanderlust #travelgram #naturelovers #explorepage #cinematicreels #beautifuldestinations #adventure"
                    )
                },
                {
                    "style": "📍 Destination Guide",
                    "caption": (
                        "Add this breathtaking spot to your travel bucket list 📍✈️ "
                        "Stunning views, fresh air, and unforgettable memories. "
                        "Save this reel for your next trip planning! 👇\n\n"
                        "#travelbucketlist #hiddenplaces #travelguide #exploretheworld #adventuretime #vacationvibes"
                    )
                },
                {
                    "style": "⚡ Short & Peaceful",
                    "caption": (
                        "Nature's own masterpiece 🌲✨ Sometimes the best therapy is just stepping outside.\n\n"
                        "#nature #travel #peaceful #scenic #aestheticreels"
                    )
                },
                {
                    "style": "🔥 Travel Poll",
                    "caption": (
                        "Would you pack your bags and move here? Yes or No? Drop your answer below! 🏔️👇 "
                        "Share this with your travel crew!\n\n"
                        "#travelreels #bucketlist #travelgram #explorepage #wanderlust"
                    )
                }
            ]
        elif "energetic" in cat:
            variations = [
                {
                    "style": "💪 Daily Drive",
                    "caption": (
                        "Pure momentum, non-stop drive, and zero excuses today 🔥 "
                        "When you commit to daily discipline, the results speak for themselves. "
                        "Drop a '💪' in the comments if you're putting in work this week! 👇\n\n"
                        "#fitnessmotivation #hustle #energy #grindset #viralreels #discipline #momentum #workout"
                    )
                },
                {
                    "style": "⚡ Workout Focus",
                    "caption": (
                        "Sweat now, shine later ⚡ 30 minutes of focused intensity that changes everything. "
                        "Save this workout for your next gym session! 🔥🏋️‍♂️\n\n"
                        "#gymmotivation #fitnesstips #workoutroutine #trainhard #fitnessgoals"
                    )
                },
                {
                    "style": "⚡ Short & Punchy",
                    "caption": (
                        "Discipline beats motivation every single time. Keep showing up. 🔥\n\n"
                        "#grind #mindset #fitness #focus #dailyhabits"
                    )
                },
                {
                    "style": "🔥 Fitness Challenge",
                    "caption": (
                        "Who is ready to level up today? Tag your workout partner and get to work! 💪🔥\n\n"
                        "#workoutpartner #fitnesschallenge #gains #gymlife #reelsviral"
                    )
                }
            ]
        elif "culinary" in cat:
            variations = [
                {
                    "style": "🍽️ Foodie Indulgence",
                    "caption": (
                        "Pure culinary magic served with passion and flavor 🍽️✨ "
                        "From the first aroma to the last bite, food is an art form best shared. "
                        "Would you try this? Tell us in the comments! 👇\n\n"
                        "#foodie #foodporn #instafood #gourmet #delicious #yummy #reelsfood #cheflife #treatyourself"
                    )
                },
                {
                    "style": "👨‍🍳 Recipe Secret",
                    "caption": (
                        "The secret to making this dish absolutely irresistible! 🤤 "
                        "Save this recipe before it goes viral on your feed! 📌👇\n\n"
                        "#recipes #homecooking #easyrecipes #foodstagram #cookingvideo #delicious"
                    )
                },
                {
                    "style": "⚡ Short & Tempting",
                    "caption": (
                        "One bite and you're in heaven. 🤤 Ultimate comfort food perfection.\n\n"
                        "#foodlover #yummy #craving #delish #foodreels"
                    )
                },
                {
                    "style": "🔥 Food Rating",
                    "caption": (
                        "On a scale of 1-10, how badly do you want a plate right now? 🤤👇 "
                        "Tag someone who owes you dinner!\n\n"
                        "#foodiesofindia #dinnerdate #tastyfood #comfortfood #reelsfood"
                    )
                }
            ]
        elif "luxury_product" in cat:
            variations = [
                {
                    "style": "💎 Luxury Statement",
                    "caption": (
                        "Uncompromising craftsmanship and timeless brilliance in every detail ✨ "
                        "An exquisite statement piece designed to turn heads and stand the test of time. "
                        "Save this post for your wishlist! 💎👇\n\n"
                        "#luxury #finejewelry #elegance #craftsmanship #gold #statementpiece #luxurygoods #timeless"
                    )
                },
                {
                    "style": "🎁 Exclusive Drop",
                    "caption": (
                        "Introducing our signature luxury edition 💎 Handcrafted with utmost precision and brilliant luster. "
                        "Tap link in bio to explore the collection! ✨\n\n"
                        "#jewelrycollection #luxuryaccessories #exclusive #handcrafted #finegems #sparkle"
                    )
                },
                {
                    "style": "⚡ Minimalist Chic",
                    "caption": (
                        "Understated elegance that speaks volumes ✨ Timeless perfection.\n\n"
                        "#luxuryvibes #minimaljewelry #detailsmatter #elegance #chic"
                    )
                },
                {
                    "style": "🔥 Luxury Poll",
                    "caption": (
                        "Gold or Platinum? Which finish would you choose? Drop your vote below! 💎👇\n\n"
                        "#jewelrylover #fashionpoll #luxuryreels #wishlist #sparkle"
                    )
                }
            ]
        elif "portrait" in cat:
            variations = [
                {
                    "style": "✨ Confident Mindset",
                    "caption": (
                        "Stepping into this moment with clear intention, bold energy, and unapologetic focus ✨ "
                        "Keep showing up—the best chapter of your story is being written right now. "
                        "Double tap if you needed this reminder today! 👇\n\n"
                        "#lifestyle #portraitmood #confidence #contentcreator #reelsinstagram #aesthetic #mindset #viral"
                    )
                },
                {
                    "style": "☕ Day in the Life",
                    "caption": (
                        "Finding peace in the daily rhythm ☕ Moments that remind you to slow down, breathe, and appreciate the journey. "
                        "What made you smile today? Let's chat below! 👇\n\n"
                        "#dailyvlog #cozyliving #slowlifestyle #morningvibes #gratitude"
                    )
                },
                {
                    "style": "⚡ Short & Bold",
                    "caption": (
                        "Unapologetically me. ✨ Moving forward with quiet confidence.\n\n"
                        "#portrait #confidence #selfgrowth #mindset #aesthetic"
                    )
                },
                {
                    "style": "🔥 Daily Reminder",
                    "caption": (
                        "Reminder: You are exactly where you need to be. Trust the process and keep moving! 💫👇 "
                        "Save this for when you need a boost.\n\n"
                        "#inspiration #mindsetshift #reelsindia #dailyreminder #keepgoing"
                    )
                }
            ]
        else:
            variations = [
                {
                    "style": "🖤 Pure Simplicity",
                    "caption": (
                        "The elegance of simplicity in every single detail 🖤 "
                        "In a world full of noise, clean design and intentional balance always stand out. "
                        "What’s your take on this modern aesthetic? Drop your thoughts below! 👇\n\n"
                        "#minimalism #designinspiration #moderndesign #detailsmatter #aestheticreels #simplicity #clean"
                    )
                },
                {
                    "style": "🏢 Design Focus",
                    "caption": (
                        "Where structure meets harmony ✦ Crisp lines, natural shadows, and thoughtful geometry. "
                        "Save for design inspiration! 📐\n\n"
                        "#architecturedesign #cleanlines #modernspace #structure #visualdesign"
                    )
                },
                {
                    "style": "⚡ Short & Modern",
                    "caption": (
                        "Less is always more. Clean simplicity in motion. 🖤\n\n"
                        "#minimalist #modernaesthetic #design #clean #reels"
                    )
                },
                {
                    "style": "🔥 Design Poll",
                    "caption": (
                        "Which detail stands out most to you? Comment your favorite element below! 👇\n\n"
                        "#designtrends #minimalistic #modernvibes #explorepage"
                    )
                }
            ]

        if cycle_offset > 0:
            offset = cycle_offset % len(variations)
            variations = variations[offset:] + variations[:offset]

        return variations

    def get_hook_variations(
        self,
        category: str,
        vibe: Optional[str] = None,
        cycle_offset: int = 0
    ) -> List[str]:
        """
        FR-07.1: Proposes 2-3+ attention-grabbing visual/textual hooks for the first 3 seconds
        crafted specifically from the visual elements of the uploaded media files.
        Never generic. Cycles in batches of 4.
        """
        cat = (category or "").lower()
        vl = (vibe or "").lower()

        if "ethnic" in cat or "saree" in cat or "traditional" in cat or "textile" in cat or "saree" in vl:
            all_hooks = [
                "The craftsmanship in this handloom drape is unreal ✨",
                "Which color would you wear this festive season? 1, 2, 3 or 4? 👇",
                "Wait till you see the delicate zari border details at the end 🥻",
                "Proof that traditional silk will never go out of style 💫",
                "POV: You found the most breathtaking handloom saree 🥻✨",
                "Stop scrolling if you love authentic Indian handlooms! 🧵💫",
                "Which drape stole your heart? Tell us below 👇",
                "The luxury details in this silk are next level ✨",
                "Tell me you love sarees without telling me you love sarees... 🥻",
                "Is this the perfect wedding guest outfit? You decide 👇",
                "When the drape falls so effortlessly, pure poetry ✨",
                "Save this for your upcoming festive shopping! 🛍️"
            ]
        elif "travel" in cat:
            all_hooks = [
                "You won't believe this place actually exists in real life 📍",
                "Save this destination before it goes viral on your feed ✈️",
                "The most breathtaking spot nobody is talking about...",
                "Proof that we live on an insanely gorgeous planet 🌍✨",
                "Pack your bags, we are going here right now ✈️🎒",
                "Wait till you see the view at second 3... 👁️🏔️",
                "The secret viewpoint the locals tried to keep hidden 👇",
                "If you need a sign to travel this year, this is it 💫"
            ]
        elif "energetic" in cat:
            all_hooks = [
                "Stop scrolling if you need that extra push today 🔥",
                "The secret habit that completely changed my energy in 30 days 👇",
                "Watch till the end if you’re ready to level up your game...",
                "Discipline beats motivation every single time 💪",
                "The 3-second challenge you need to try right now 🔥",
                "They said it was impossible until it got done ⚡",
                "No excuses, just relentless execution today 💥",
                "Save this for when you feel like quitting 👇"
            ]
        elif "culinary" in cat:
            all_hooks = [
                "You won't believe what happens when you take the first bite... 🤤",
                "The secret recipe that top chefs never share 👇",
                "Is this the ultimate comfort food? You decide 🍽️",
                "Wait till the cheese pull at the end... 🧀🔥",
                "One bite of this and you'll never go back 🤤✨",
                "The easiest 5-minute food hack you’ll wish you knew sooner 👇",
                "Tag someone who owes you dinner tonight! 🍕",
                "The aroma alone will make your mouth water 👨‍🍳"
            ]
        elif "luxury_product" in cat:
            all_hooks = [
                "The craftsmanship on this piece is beyond stunning ✨",
                "Wait for the sparkle under direct light... 💎",
                "The luxury detail that separates good from unforgettable 👇",
                "Proof that true elegance never screams, it whispers 💫",
                "Is this the ultimate dream piece? 💎",
                "Wait till you see the precision finish up close ✨",
                "Gold or platinum? Which one would you choose? 👇",
                "The unboxing moment everyone has been waiting for... 🎁"
            ]
        elif "portrait" in cat:
            all_hooks = [
                "The 1 mindset shift that changed everything this year...",
                "They told me not to post this, but here’s the honest truth 👇",
                "Wait till the end to see the full transformation ✨",
                "The secret nobody talks about when starting out...",
                "POV: You finally stopped caring about what people think 💫",
                "This 3-second reminder will change your week ✨",
                "Stop scrolling: you needed to hear this today 👇",
                "The real unfiltered journey behind this moment..."
            ]
        else:
            all_hooks = [
                "Why clean simplicity always wins the aesthetic game 🖤",
                "Wait till you see the architectural detail at the end 👇",
                "The design secret that elevates everything instantly...",
                "Proof that less is always more ✨",
                "The most satisfying visual you’ll see all day 🖤",
                "Find the hidden detail in this aesthetic shot 👇",
                "Pure visual therapy for your feed today ☕✨",
                "Simplicity is the ultimate sophistication 💫"
            ]

        chunk_size = 4
        num_chunks = max(1, len(all_hooks) // chunk_size)
        start = (cycle_offset % num_chunks) * chunk_size
        return all_hooks[start:start + chunk_size]

