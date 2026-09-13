"""
Hindu puja catalog for PurohitConnect.

Covers commonly booked household, samskara, wedding, festival, deity,
planetary, ancestral, and special rituals used by Indian families and
online pandit marketplaces. Seed is idempotent by puja name.
"""

from apps.pujas.models import Puja, PujaCategory
from apps.pujas.venues import VENUE_HOME, VENUE_OTHER, VENUE_PUROHIT, VENUE_TEERTH, VENUE_TEMPLE, encode_venues

CATEGORY_VENUES = {
    'Household Pujas': (VENUE_HOME,),
    'Life Events': (VENUE_HOME,),
    'Weddings': (VENUE_HOME,),
    'Festivals': (VENUE_HOME, VENUE_TEMPLE),
    'Deity Pujas': (VENUE_HOME, VENUE_TEMPLE),
    'Planetary Shanti': (VENUE_HOME, VENUE_TEMPLE),
    'Ancestral Rites': (VENUE_HOME, VENUE_TEERTH),
    'Special Rituals': (VENUE_HOME, VENUE_PUROHIT),
}

NAME_VENUES = {
    'Bhoomi Puja': (VENUE_OTHER,),
    'Land / Plot Purchase Puja': (VENUE_OTHER,),
    'Office Opening Puja': (VENUE_OTHER,),
    'Shop / Factory Opening': (VENUE_OTHER,),
    'Vahan Puja': (VENUE_OTHER, VENUE_HOME),
    'Chulha Puja': (VENUE_HOME,),
    'Rudrabhishek': (VENUE_TEMPLE, VENUE_HOME),
    'Laghu Rudrabhishek': (VENUE_TEMPLE, VENUE_HOME),
    'Maha Rudrabhishek': (VENUE_TEMPLE,),
    'Balaji Puja': (VENUE_TEMPLE, VENUE_HOME),
    'Kaal Sarp Dosh Puja': (VENUE_TEMPLE,),
    'Narayan Bali': (VENUE_TEERTH, VENUE_TEMPLE),
    'Narayan Nagbali': (VENUE_TEERTH, VENUE_TEMPLE),
    'Pind Daan': (VENUE_TEERTH, VENUE_TEMPLE),
    'Asthi Visarjan': (VENUE_TEERTH,),
    'Antyeshti': (VENUE_OTHER, VENUE_HOME),
    'Gau Daan': (VENUE_TEMPLE, VENUE_OTHER),
    'Chhath Puja': (VENUE_TEERTH, VENUE_HOME),
    'Holika Dahan': (VENUE_OTHER, VENUE_HOME),
    'Ayudha Puja': (VENUE_OTHER, VENUE_HOME),
    'Vishwakarma Puja': (VENUE_OTHER,),
    'Navchandi Yagya': (VENUE_TEMPLE, VENUE_HOME),
    'Akhand Ramayan Path': (VENUE_HOME, VENUE_PUROHIT, VENUE_TEMPLE),
    'Shrimad Bhagwat Katha': (VENUE_HOME, VENUE_TEMPLE, VENUE_PUROHIT),
}


def venues_for(name, category_name):
    return NAME_VENUES.get(name) or CATEGORY_VENUES.get(category_name) or (VENUE_HOME,)

CATEGORIES = [
    ('Household Pujas', 'home', 'Home, vastu, and everyday household rituals'),
    ('Life Events', 'baby', 'Shodasha samskaras and life-milestone rites'),
    ('Weddings', 'heart-handshake', 'Engagement, vivah, and related ceremonies'),
    ('Festivals', 'calendar-heart', 'Seasonal vrat and festival observances'),
    ('Deity Pujas', 'flame', 'Devotion to a specific deity'),
    ('Planetary Shanti', 'orbit', 'Navagraha and dosh-nivaran rituals'),
    ('Ancestral Rites', 'flower-2', 'Shraddha, pind daan, and pitru karma'),
    ('Special Rituals', 'sparkles', 'Havan, path, jaap, and other ceremonies'),
]

CATEGORY_ORDER = [name for name, _, _ in CATEGORIES]

FEATURED_PUJA_NAMES = [
    'Satyanarayan Puja',
    'Griha Pravesh',
    'Navagraha Shanti',
    'Rudrabhishek',
]

# (category_name, puja_name, hours, description)
PUJAS = [
    # Household
    ('Household Pujas', 'Satyanarayan Puja', 2.5, 'Auspicious vrat-katha dedicated to Lord Vishnu as Satyanarayan, performed for family peace and prosperity.'),
    ('Household Pujas', 'Griha Pravesh', 4.0, 'Housewarming ceremony for first entry into a new or renovated home, with ganesh, vastu, and havan rites.'),
    ('Household Pujas', 'Vastu Shanti', 3.0, 'Ritual to appease Vastu Purusha and balance the five elements of a home or plot.'),
    ('Household Pujas', 'Bhoomi Puja', 2.5, 'Worship of Bhoomi Devi before construction or groundbreaking on a new plot.'),
    ('Household Pujas', 'Griha Shanti Puja', 3.0, 'Household peace ritual to remove negativity and restore harmony in the family home.'),
    ('Household Pujas', 'Kalash Sthapana', 1.5, 'Sacred kalash installation to invite divine presence at the start of a vrata or ceremony.'),
    ('Household Pujas', 'Chulha Puja', 1.0, 'First lighting of the kitchen fire; milk is often boiled as a sign of overflowing abundance.'),
    ('Household Pujas', 'Nitya Puja', 1.0, 'Daily household worship as per family tradition, including sankalpa, naivedya, and aarti.'),
    ('Household Pujas', 'Office Opening Puja', 2.0, 'Ganesh-Lakshmi puja to bless a new office, shop, clinic, or workplace.'),
    ('Household Pujas', 'Shop / Factory Opening', 2.5, 'Inauguration puja for a store, warehouse, or manufacturing unit.'),
    ('Household Pujas', 'Vahan Puja', 1.0, 'Vehicle blessing for a new car, bike, or commercial vehicle.'),
    ('Household Pujas', 'Land / Plot Purchase Puja', 2.0, 'Sankalpa and bhumi worship after buying land, before fencing or construction.'),
    ('Household Pujas', 'Tulsi Puja', 1.0, 'Worship of Tulsi Devi in the courtyard for purity and daily blessings.'),
    ('Household Pujas', 'Gau Puja', 1.5, 'Cow worship and go-seva offering for punya and household prosperity.'),

    # Life events / 16 samskaras
    ('Life Events', 'Garbhadhana', 1.5, 'Prenatal samskara performed by a couple seeking a healthy, blessed conception.'),
    ('Life Events', 'Pumsavana', 1.5, 'Early-pregnancy rite for the wellbeing of the mother and the unborn child.'),
    ('Life Events', 'Simantonnayana', 2.0, 'Seemantham / Godh bharai rite for protection of the mother in later pregnancy.'),
    ('Life Events', 'Jatakarma', 1.5, 'Newborn welcome ritual performed soon after birth, with mantras and honey-ghee touching.'),
    ('Life Events', 'Namkaran', 1.5, 'Naming ceremony for a newborn, choosing an auspicious name as per nakshatra.'),
    ('Life Events', 'Nishkramana', 1.5, 'Baby’s first outing, often to a temple or into sunlight for Surya darshan.'),
    ('Life Events', 'Annaprasana', 1.5, 'First rice-feeding ceremony, usually in the sixth month.'),
    ('Life Events', 'Mundan', 2.0, 'Chudakarana / first tonsure for a child’s health, longevity, and a fresh start.'),
    ('Life Events', 'Karnavedha', 1.0, 'Ear-piercing samskara for a child, performed with Vedic mantras.'),
    ('Life Events', 'Vidyarambha', 1.5, 'Aksharabhyasam — a child’s first letters, invoking Saraswati before schooling.'),
    ('Life Events', 'Upanayana', 4.0, 'Janeu / sacred-thread ceremony initiating Vedic study and Gayatri mantra.'),
    ('Life Events', 'Vedarambha', 2.0, 'Formal beginning of Veda study after upanayana.'),
    ('Life Events', 'Samavartana', 2.0, 'Graduation samskara marking the completion of gurukula or formal study.'),
    ('Life Events', 'Ritushuddhi', 1.5, 'Coming-of-age blessing for a girl at maturity.'),
    ('Life Events', 'Ayushya Homa', 2.5, 'Longevity homa performed on birthdays or for a child’s health.'),
    ('Life Events', 'Birthday Puja', 1.5, 'Janmadina puja with ganesh, ishta-devata, and ayush blessings.'),
    ('Life Events', 'Shastiapthapoorthi', 4.0, '60th-birthday celebration with ayush homa and couple blessings.'),
    ('Life Events', 'Sathabhishekam', 4.0, '80th-year milestone ritual with abhishekam and family sankalpa.'),

    # Weddings
    ('Weddings', 'Engagement Ceremony', 2.0, 'Roka / nischitartham — formal engagement and sankalpa between families.'),
    ('Weddings', 'Vivah', 6.0, 'Complete Vedic wedding with kanyadaan, saptapadi, and vivaha homa.'),
    ('Weddings', 'Haldi Ceremony', 1.5, 'Mangal snan / haldi ritual before the wedding day.'),
    ('Weddings', 'Ganesh Puja for Wedding', 1.5, 'Obstacle-removing ganesh puja at the start of wedding festivities.'),
    ('Weddings', 'Kanyadaan', 1.5, 'Standalone kanyadaan rite when performed separately from the main vivah.'),
    ('Weddings', 'Vadhu Pravesh', 2.0, 'Bride’s first entry into the grooms’s home after marriage.'),
    ('Weddings', 'Kumbh Vivah', 3.0, 'Symbolic kalash marriage performed to pacify certain mangal or nadi doshas.'),
    ('Weddings', 'Punar Vivah', 4.0, 'Remarriage rites as per family and regional custom.'),
    ('Weddings', 'Anniversary Puja', 1.5, 'Wedding-anniversary thanksgiving with lakshmi-ganesh or satyanarayan katha.'),

    # Festivals
    ('Festivals', 'Ganesh Chaturthi Puja', 2.5, 'Vinayaka chavithi / Ganesh utsav sthapana, daily worship, and visarjan guidance.'),
    ('Festivals', 'Navratri Puja', 2.0, 'Nine-night worship of Durga, Lakshmi, and Saraswati with daily sankalpa.'),
    ('Festivals', 'Durga Puja', 4.0, 'Sharadiya Durga puja with bodhon, pushpanjali, and sandhi puja rites.'),
    ('Festivals', 'Vijayadashami Puja', 2.0, 'Dussehra / Aparajita puja marking Durga’s victory and new beginnings.'),
    ('Festivals', 'Diwali Lakshmi-Ganesh Puja', 2.0, 'Deepavali night lakshmi-ganesh puja for wealth and an auspicious year.'),
    ('Festivals', 'Dhanteras Puja', 1.5, 'Dhantrayodashi worship of Lakshmi and Dhanvantari for prosperity and health.'),
    ('Festivals', 'Govardhan Puja', 1.5, 'Annakut / Govardhan worship the day after Diwali.'),
    ('Festivals', 'Bhai Dooj Puja', 1.0, 'Bhratri dwitiya tilak and aarti for brothers and sisters.'),
    ('Festivals', 'Holika Dahan', 1.5, 'Holika fire ritual on the eve of Holi.'),
    ('Festivals', 'Maha Shivaratri Puja', 3.0, 'Night-long Shiva worship with abhishekam and rudra path.'),
    ('Festivals', 'Ram Navami Puja', 2.0, 'Birthday of Shri Rama with ram raksha and sundarkand options.'),
    ('Festivals', 'Janmashtami Puja', 2.5, 'Krishna jayanti midnight puja, bhog, and jhulan.'),
    ('Festivals', 'Hanuman Jayanti Puja', 2.0, 'Birthday of Hanuman with sundarkand or hanuman chalisa path.'),
    ('Festivals', 'Raksha Bandhan Puja', 1.0, 'Rakhi sankalpa and sibling blessing ritual.'),
    ('Festivals', 'Karva Chauth Puja', 1.5, 'Karaka chaturthi vrat katha and moon-sighting puja for married women.'),
    ('Festivals', 'Vat Savitri Puja', 1.5, 'Vat-savitri vrat for the long life of the husband.'),
    ('Festivals', 'Hartalika Teej Puja', 1.5, 'Parvati-Shiva vrat observed by women for marital bliss.'),
    ('Festivals', 'Varalakshmi Vratham', 2.5, 'South-Indian Friday vrat for Goddess Lakshmi’s blessings.'),
    ('Festivals', 'Vasant Panchami Puja', 1.5, 'Saraswati puja marking spring and the start of learning.'),
    ('Festivals', 'Makar Sankranti Puja', 1.5, 'Surya worship at uttarayana; includes Pongal / Lohri family rites.'),
    ('Festivals', 'Ugadi / Gudi Padwa Puja', 1.5, 'Hindu new-year puja for Telugu, Kannada, and Marathi households.'),
    ('Festivals', 'Vishu Puja', 1.5, 'Kerala new-year kani and vishukkani worship.'),
    ('Festivals', 'Onam Puja', 2.0, 'Mahabali / Thrikkakara Appan puja during Onam.'),
    ('Festivals', 'Chhath Puja', 3.0, 'Four-day Surya-Shashti vrata on a riverbank or terrace.'),
    ('Festivals', 'Kali Puja', 3.0, 'Kartik amavasya Kali worship, especially in Bengal and the east.'),
    ('Festivals', 'Ayudha Puja', 1.5, 'Navami worship of tools, vehicles, and instruments of livelihood.'),
    ('Festivals', 'Vishwakarma Puja', 2.0, 'Worship of Vishwakarma for workshops, factories, and craftsmen.'),
    ('Festivals', 'Kartik Purnima Puja', 2.0, 'Kartik snan, deepdan, and tulsi-vivah associated rites.'),
    ('Festivals', 'Tulsi Vivah', 2.0, 'Ceremonial marriage of Tulsi with Shaligram or Vishnu.'),
    ('Festivals', 'Guru Purnima Puja', 1.5, 'Vyasa puja honouring the guru and teachers.'),
    ('Festivals', 'Nag Panchami Puja', 1.5, 'Worship of Naga Devata for protection from sarpa dosha.'),
    ('Festivals', 'Akshaya Tritiya Puja', 1.5, 'Gold, land, and new-venture sankalpa on the everlasting tithi.'),
    ('Festivals', 'Skanda Shashti Puja', 2.0, 'Kartikeya / Murugan worship, especially in Tamil tradition.'),

    # Deity pujas
    ('Deity Pujas', 'Ganesh Puja', 1.5, 'Siddhi-vinayaka worship to remove obstacles before any new work.'),
    ('Deity Pujas', 'Lakshmi Puja', 1.5, 'Goddess Lakshmi worship for wealth, harmony, and a stable home.'),
    ('Deity Pujas', 'Lakshmi Kubera Puja', 2.5, 'Combined Lakshmi-Kubera ritual for cash flow and business growth.'),
    ('Deity Pujas', 'Mahalakshmi Puja', 2.0, 'Ashtalakshmi / Mahalakshmi worship for complete prosperity.'),
    ('Deity Pujas', 'Saraswati Puja', 1.5, 'Goddess of learning — for students, exams, arts, and new studies.'),
    ('Deity Pujas', 'Durga Mata Puja', 2.5, 'Home or hall worship of Durga for protection and shakti.'),
    ('Deity Pujas', 'Annapurna Puja', 1.5, 'Goddess of food and nourishment, often before a new kitchen or grain store.'),
    ('Deity Pujas', 'Santoshi Mata Puja', 2.0, 'Friday vrat-katha of Santoshi Mata for family fulfilment.'),
    ('Deity Pujas', 'Lalita Tripura Sundari Puja', 3.0, 'Sri Vidya / Lalita worship for grace and spiritual progress.'),
    ('Deity Pujas', 'Baglamukhi Puja', 3.0, 'Stambhana shakti puja performed for protection and legal or speech obstacles.'),
    ('Deity Pujas', 'Shiva Puja', 1.5, 'Abhishekam and archana of Shiva at home or temple.'),
    ('Deity Pujas', 'Rudrabhishek', 2.5, 'Laghu-to-standard Rudrabhishek with panchamrit and rudra mantras.'),
    ('Deity Pujas', 'Laghu Rudrabhishek', 2.0, 'Shorter Rudrabhishek suitable for regular Monday worship.'),
    ('Deity Pujas', 'Maha Rudrabhishek', 5.0, 'Extended Rudra abhishekam with larger sankalpa and multiple priests if needed.'),
    ('Deity Pujas', 'Parvati Puja', 1.5, 'Gauri / Parvati worship for marital harmony and household grace.'),
    ('Deity Pujas', 'Hanuman Puja', 1.5, 'Sankat-mochan Hanuman worship for courage and protection.'),
    ('Deity Pujas', 'Vishnu Puja', 2.0, 'Vishnu sahasranama archana and panchamrit abhishek.'),
    ('Deity Pujas', 'Krishna Puja', 1.5, 'Worship of Krishna / Bal Gopal with bhog and kirtan.'),
    ('Deity Pujas', 'Rama Puja', 1.5, 'Shri Rama archana with ram raksha stotra.'),
    ('Deity Pujas', 'Balaji Puja', 2.0, 'Venkateswara / Tirupati Balaji home or temple-style archana.'),
    ('Deity Pujas', 'Jagannath Puja', 2.0, 'Jagannath, Balabhadra, and Subhadra worship.'),
    ('Deity Pujas', 'Khatu Shyam Puja', 2.0, 'Shyam baba worship popular in North India.'),
    ('Deity Pujas', 'Sai Baba Puja', 1.5, 'Shirdi Sai Thursday worship with shej / kakad aarti style offering.'),
    ('Deity Pujas', 'Murugan Puja', 2.0, 'Kartikeya / Subrahmanya worship with kavadi or shashti rites.'),
    ('Deity Pujas', 'Ayyappa Puja', 2.0, 'Mandala-kala Ayyappa swamy puja for Sabarimala devotees.'),
    ('Deity Pujas', 'Gayatri Puja', 2.0, 'Gayatri mata worship and initiation-support puja.'),
    ('Deity Pujas', 'Surya Puja', 1.5, 'Aditya / Surya namaskar archana for health and vitality.'),
    ('Deity Pujas', 'Santan Gopal Puja', 2.5, 'Krishna-as-Gopala puja and jaap for progeny blessings.'),

    # Planetary
    ('Planetary Shanti', 'Navagraha Shanti', 3.0, 'Worship of the nine grahas to balance the horoscope and remove general doshas.'),
    ('Planetary Shanti', 'Surya Shanti', 2.0, 'Pacification of Surya for authority, health, and father’s wellbeing.'),
    ('Planetary Shanti', 'Chandra Shanti', 2.0, 'Moon shanti for mind, mother, and emotional balance.'),
    ('Planetary Shanti', 'Mangal Dosh Nivaran', 2.5, 'Manglik / kuja dosha shanti for marriage and vitality issues.'),
    ('Planetary Shanti', 'Budh Shanti', 2.0, 'Mercury shanti for speech, studies, and business clarity.'),
    ('Planetary Shanti', 'Guru Shanti', 2.0, 'Brihaspati / Jupiter shanti for wisdom, children, and dharma.'),
    ('Planetary Shanti', 'Shukra Shanti', 2.0, 'Venus shanti for marriage, arts, and comforts.'),
    ('Planetary Shanti', 'Shani Shanti', 2.5, 'Saturn / Shani dosh nivaran, often with sesame and iron offerings.'),
    ('Planetary Shanti', 'Rahu Shanti', 2.0, 'Rahu pacification for confusion, foreign travel, and sudden obstacles.'),
    ('Planetary Shanti', 'Ketu Shanti', 2.0, 'Ketu shanti for spiritual blocks, health, and ancestral knots.'),
    ('Planetary Shanti', 'Rahu-Ketu Shanti', 2.5, 'Combined rahu-ketu ritual, often recommended around eclipses or sade-period.'),
    ('Planetary Shanti', 'Kaal Sarp Dosh Puja', 3.5, 'Kaal sarp yoga nivaran typically done with navagraha and nag devata worship.'),
    ('Planetary Shanti', 'Gandmool Nakshatra Shanti', 2.5, 'Shanti for births in gandanta / gandmool nakshatras.'),
    ('Planetary Shanti', 'Kalathra Dosha Shanti', 2.5, 'Marriage-delay or marital-harmony graha shanti.'),
    ('Planetary Shanti', 'Drishti Dosh Nivaran', 1.5, 'Nazar / evil-eye removal with homa or simple shanti.'),
    ('Planetary Shanti', 'Rin Mukti Puja', 2.5, 'Debt-relief sankalpa with Lakshmi-Kubera or Kuber mantra rites.'),

    # Ancestral
    ('Ancestral Rites', 'Pitru Shraddha', 2.5, 'Periodic shraddha to honour ancestors with pinda and tarpan.'),
    ('Ancestral Rites', 'Pind Daan', 3.0, 'Offering of pindas at a sacred site or home for the departed.'),
    ('Ancestral Rites', 'Tarpan', 1.5, 'Water and sesame offerings to pitrs, rishis, and devas.'),
    ('Ancestral Rites', 'Tripindi Shraddha', 3.5, 'Special shraddha when annual rites were missed or for unfulfilled souls.'),
    ('Ancestral Rites', 'Pitra Dosh Nivaran', 3.0, 'Ritual to ease pitru dosha seen in the horoscope or family hardship.'),
    ('Ancestral Rites', 'Narayan Bali', 4.0, 'Rite for unnatural death or unfulfilled last wishes, often with nagbali.'),
    ('Ancestral Rites', 'Narayan Nagbali', 5.0, 'Combined narayan bali and nagbali, classically performed at Trimbakeshwar.'),
    ('Ancestral Rites', 'Antyeshti', 4.0, 'Funeral / last rites as per Vedic antyeshti samskara.'),
    ('Ancestral Rites', 'Asthi Visarjan', 2.0, 'Immersion of ashes in a sacred river with sankalpa and tarpan.'),
    ('Ancestral Rites', 'Gau Daan', 1.5, 'Ceremonial cow donation or go-seva in the name of the departed.'),
    ('Ancestral Rites', 'Varshik Shraddha', 2.5, 'Annual death-anniversary shraddha at home or a teerth.'),

    # Special / path / havan
    ('Special Rituals', 'Havan', 2.0, 'General sacred-fire ritual for purification and blessings.'),
    ('Special Rituals', 'Gayatri Havan', 2.5, 'Gayatri mantra homa for clarity, study, and spiritual growth.'),
    ('Special Rituals', 'Ganapati Homa', 2.5, 'Ganesh havan before new ventures, exams, or house events.'),
    ('Special Rituals', 'Sudarshana Homa', 3.0, 'Vishnu’s sudarshana chakra homa for protection and obstacle removal.'),
    ('Special Rituals', 'Maha Mrityunjaya Jaap', 3.0, 'Mrityunjaya mantra jaap and homa for health, recovery, and longevity.'),
    ('Special Rituals', 'Mrityunjaya Homa', 3.0, 'Fire offering with maha mrityunjaya mantras.'),
    ('Special Rituals', 'Sundarkand Path', 3.0, 'Recitation of Sundarkand for courage, travel, and family protection.'),
    ('Special Rituals', 'Akhand Ramayan Path', 8.0, 'Continuous Ramcharitmanas path, typically over a day or more.'),
    ('Special Rituals', 'Shrimad Bhagwat Katha', 4.0, 'Bhagavata saptah session; book a pandit for a day’s katha.'),
    ('Special Rituals', 'Shiv Mahapuran Katha', 4.0, 'Shiva purana katha for devotion and family welfare.'),
    ('Special Rituals', 'Durga Saptashati Path', 4.0, 'Chandi path — recitation of 700 verses of the Devi Mahatmyam.'),
    ('Special Rituals', 'Navchandi Yagya', 6.0, 'Nine-fold Chandi recitation with homa, usually over a full day.'),
    ('Special Rituals', 'Vishnu Sahasranama Path', 2.0, 'Chanting of the thousand names of Vishnu.'),
    ('Special Rituals', 'Rudri Path', 2.5, 'Rudrashtadhyayi / rudri recitation with or without abhishekam.'),
    ('Special Rituals', 'Santan Gopal Jaap', 2.5, 'Mantra jaap for progeny, often paired with Santan Gopal puja.'),
    ('Special Rituals', 'Bhagavad Gita Path', 2.5, 'Recitation of the Gita for peace, grief support, or a sankalpa.'),
]


def category_sort_key(category):
    try:
        return CATEGORY_ORDER.index(category.name)
    except ValueError:
        return len(CATEGORY_ORDER)


def seed_hindu_pujas():
    """Create or refresh catalog rows. Existing names keep their current text."""
    category_map = {}
    categories_created = 0
    for name, icon, description in CATEGORIES:
        category, created = PujaCategory.objects.get_or_create(
            name=name,
            defaults={'icon': icon, 'description': description},
        )
        updates = []
        if not category.icon:
            category.icon = icon
            updates.append('icon')
        if not category.description:
            category.description = description
            updates.append('description')
        if updates:
            category.save(update_fields=updates)
        category_map[name] = category
        if created:
            categories_created += 1

    pujas_created = 0
    for category_name, name, hours, description in PUJAS:
        category = category_map[category_name]
        typical = encode_venues(venues_for(name, category_name))
        puja = Puja.objects.filter(name__iexact=name).first()
        if puja:
            fields = []
            if puja.category_id != category.id:
                puja.category = category
                fields.append('category')
            if puja.typical_venues != typical:
                puja.typical_venues = typical
                fields.append('typical_venues')
            if fields:
                puja.save(update_fields=fields)
            continue
        Puja.objects.create(
            category=category,
            name=name,
            description=description,
            base_duration_hours=hours,
            typical_venues=typical,
        )
        pujas_created += 1

    return {
        'categories_created': categories_created,
        'pujas_created': pujas_created,
        'category_total': PujaCategory.objects.count(),
        'puja_total': Puja.objects.count(),
    }
