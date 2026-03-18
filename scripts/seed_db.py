#!/usr/bin/env python3
# scripts/seed_db.py
# Responsibility: One-time database seeder — populates FAQ categories, FAQ items,
# neighborhood records, and sample events. Safe to run multiple times (idempotent).

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app import db
from app.models.faq import FaqCategory, FaqItem
from app.models.event import Event
from app.services.neighborhood_service import seed_neighborhoods
from datetime import datetime, timedelta


# ─── FAQ Seed Data ─────────────────────────────────────────────────────────────

FAQ_SEED = [
    {
        'name': 'Wildfire', 'icon': '🔥', 'order': 1,
        'items': [
            ('What should I do if I receive an evacuation order?',
             'Leave immediately. Do not wait. Take your go-bag, important documents, medications, and pets. Lock your home, turn off gas, and follow designated evacuation routes. Never drive through smoke — pull over, turn on hazard lights, and wait if visibility drops below 100 feet.'),
            ('How do I find my evacuation zone?',
             'Poway uses lettered evacuation zones (A–D). Zone A is highest priority. Find your zone at the San Diego County Office of Emergency Services website or call 2-1-1. PNEC also maintains a neighborhood map on this site — enter your neighborhood to see your zone.'),
            ('What should be in my go-bag for wildfire evacuation?',
             'A wildfire go-bag should include: water (1 gallon/person/day for 3 days), non-perishable food, N95 respirator masks, medications, copies of ID and insurance documents, cash, phone charger, change of clothes, and pet supplies. Keep it in an easily reachable location — ideally near your front door.'),
            ('How do I protect my home before leaving?',
             'Close all windows, doors, and vents. Remove flammable doormats and patio furniture. Connect garden hoses. Turn off propane tanks. Leave a light on so firefighters can see the structure in smoke. Leave the front door unlocked so firefighters can access if needed.'),
            ('Where are Poway evacuation routes?',
             'Primary evacuation routes from Poway include Poway Road, Scripps Poway Parkway, and Community Road. Secondary routes include Espola Road and Midland Road. Avoid freeways during mass evacuations — surface streets may move faster. Always follow instructions from law enforcement on-scene.'),
        ]
    },
    {
        'name': 'Flood & Rain', 'icon': '🌊', 'order': 2,
        'items': [
            ('What should I do if my street is flooding?',
             'Move to higher ground immediately. Do not walk, swim, or drive through floodwaters. Six inches of moving water can knock a person down. Two feet of water will float most vehicles. Call 9-1-1 if you or someone else is in immediate danger. Report flooded roads to the City of Poway at (858) 668-4700.'),
            ('Is it safe to drive through flooded roads?',
             'No. "Turn Around, Don\'t Drown" is the guiding principle. Just 12 inches of water can float many small cars. Floodwater often hides washed-out pavement or downed power lines. If your car stalls in water, exit immediately and move to higher ground.'),
            ('How do I prepare for heavy rain season?',
             'Clear gutters and downspouts before rain season (October–April in Poway). Store sandbags if your property is in a flood-prone area — the City of Poway provides free sandbags at Public Works (14467 Lake Poway Rd). Keep emergency supplies on a high shelf, not on the floor of a garage.'),
            ('What are the flood-prone areas in Poway?',
             'Areas near Poway Creek, Old Poway Park, and low-lying sections along Poway Road are historically flood-prone. The City maintains a Flood Hazard map — contact the Engineering Department for your property\'s flood zone designation. FEMA flood maps are also available at msc.fema.gov.'),
        ]
    },
    {
        'name': 'Earthquake', 'icon': '🌍', 'order': 3,
        'items': [
            ('What should I do during an earthquake?',
             'DROP to your hands and knees. Take COVER under a sturdy table or desk, or against an interior wall away from windows. HOLD ON until the shaking stops. Stay away from windows, heavy furniture, and exterior walls. If outdoors, move away from buildings, trees, and power lines.'),
            ('How do I prepare my home for earthquakes?',
             'Strap water heaters and tall furniture to wall studs. Store heavy items on lower shelves. Install latches on cabinet doors. Know how to shut off your gas. Create a family emergency plan with a meeting point. Keep shoes and a flashlight under your bed.'),
            ('What is Drop, Cover, and Hold On?',
             'DROP to your hands and knees to prevent being knocked down. Take COVER under a sturdy desk or table, or against an interior wall covering your head and neck with your arms. HOLD ON to your shelter (or head) until the shaking stops. This is the internationally recommended response — not running outside or standing in a doorway.'),
            ('How do I shut off my gas after an earthquake?',
             'Only shut off gas if you smell gas, hear hissing, or see damage to your meter or lines. Use an adjustable wrench or special gas shutoff tool — turn the valve a quarter turn so it is perpendicular to the pipe. Once shut off, do not turn gas back on yourself — call SoCalGas at 1-800-427-2200. Keep a wrench near your meter.'),
        ]
    },
    {
        'name': 'Extreme Heat', 'icon': '🌡️', 'order': 4,
        'items': [
            ('What temperature is considered dangerous?',
             'The National Weather Service issues Heat Advisories when heat index values reach 100–104°F and Excessive Heat Warnings at 105°F+. For elderly residents, young children, and those with chronic illness, risk increases at lower temperatures. In Poway, summer temperatures regularly exceed 95°F — take all heat events seriously.'),
            ('Where are cooling centers in Poway?',
             'During Excessive Heat Warnings, Poway opens cooling centers at the Poway Community Park Recreation Center (13094 Civic Center Dr) and the Poway Library (13137 Poway Rd). San Diego County 2-1-1 maintains a current list — call or text 211 during heat events for the nearest open location.'),
            ('How do I check on vulnerable neighbors during a heat wave?',
             'Knock on the door of elderly or disabled neighbors at least twice a day. Signs of heat stroke: confusion, loss of consciousness, hot dry skin, no sweating. Call 9-1-1 immediately for heat stroke. Heat exhaustion (heavy sweating, weakness, cool skin) can be treated by moving the person to a cool area and providing water.'),
        ]
    },
    {
        'name': '72-Hour Kit', 'icon': '📦', 'order': 5,
        'items': [
            ('What goes in a 72-hour emergency kit?',
             'Water (1 gallon/person/day), non-perishable food, battery-powered or hand-crank radio, flashlight, first aid kit, whistle, dust masks, plastic sheeting and duct tape, moist towelettes, garbage bags, wrench or pliers, manual can opener, local maps, and a cell phone with chargers or a backup battery.'),
            ('How much water do I need per person?',
             'FEMA recommends 1 gallon per person per day — more if you live in a hot climate (which Poway is). For a family of 4, that\'s 12 gallons for a 72-hour kit. Store water in sealed, food-grade containers. Replace stored water every 6–12 months. Don\'t forget water for pets.'),
            ('What documents should I keep in my kit?',
             'Copies of: driver\'s license / ID, passport, birth certificate, Social Security card, insurance policies, bank account info, medication lists, medical records, property records or lease, and utility account numbers. Store these in a waterproof, fireproof bag or a USB drive. Keep originals in a bank safe deposit box.'),
            ('How often should I update my kit?',
             'Check your kit twice a year — a good reminder is when Daylight Saving Time changes. Rotate food and water (replace before expiration). Check battery charge. Update medications and first aid supplies. Review documents for any changes. Make sure children\'s clothing and shoes still fit.'),
        ]
    },
    {
        'name': 'Neighborhood Coordinators', 'icon': '🏘️', 'order': 6,
        'items': [
            ('What is a Neighborhood Emergency Coordinator?',
             'A Neighborhood Emergency Coordinator (NEC) is a trained volunteer who serves as the point of contact for their block or neighborhood during and after a disaster. They check on neighbors, relay information to PNEC, and help organize local response. Poway has ~60 neighborhoods — each ideally has a trained NEC.'),
            ('How do I find my coordinator?',
             'Use the Neighborhood Map on this site to find your neighborhood. Click your zone to see your coordinator\'s name and contact info. If your neighborhood shows "[Coordinator TBD]" — that means we need a volunteer! Contact PNEC at info@powaynec.com to learn how to become your neighborhood\'s coordinator.'),
            ('How do I become a coordinator?',
             'Contact PNEC at info@powaynec.com or attend a monthly PNEC meeting (usually the third Thursday of each month). You\'ll complete a short PNEC Coordinator Training. No prior emergency experience required — just a willingness to know your neighbors and be a calm point of contact during emergencies.'),
            ('What does PNEC do?',
             'PNEC (Poway Neighborhood Emergency Corps) is an all-volunteer nonprofit that has served Poway since 1995. We train and support Neighborhood Emergency Coordinators, partner with the City of Poway and CERT, maintain a ham radio network (PACT) for backup communication, and provide preparedness education to Poway residents.'),
        ]
    },
    {
        'name': 'Ham Radio & PACT', 'icon': '📻', 'order': 7,
        'items': [
            ('What is PACT?',
             'PACT (Poway Amateur Communications Team) is PNEC\'s volunteer ham radio group. During a disaster, when cell networks and internet are down, PACT operators provide emergency communications for PNEC, the City of Poway, and San Diego County emergency management using licensed amateur radio frequencies.'),
            ('How do ham radio operators help during emergencies?',
             'Ham radio operators can communicate when all other infrastructure is down — no internet, no cell towers, no power required. During wildfires and earthquakes, PACT operators relay shelter locations, resource needs, and status reports between neighborhoods and the EOC (Emergency Operations Center).'),
            ('How do I get a ham radio license?',
             'The entry-level Technician license requires passing a 35-question exam on basic radio theory and regulations. Study materials are free at hamstudy.org. The ARRL (arrl.org) lists exam sessions in San Diego County. Once licensed, you can join PACT — contact PNEC at info@powaynec.com for more information.'),
        ]
    },
    {
        'name': 'Volunteering', 'icon': '🙋', 'order': 8,
        'items': [
            ('How do I volunteer with PNEC?',
             'Visit our Volunteer page or email info@powaynec.com. Volunteer opportunities include: Neighborhood Emergency Coordinator, PACT ham radio operator, CERT-trained community responder, event organizer, or administrative support. No special background required — just dedication to your community.'),
            ('What is CERT training?',
             'CERT (Community Emergency Response Team) is a FEMA-sponsored program that teaches disaster response basics: fire safety, light search and rescue, team organization, and first aid. Poway offers CERT training through the City — visit poway.org for the current schedule. CERT graduates are key PNEC volunteers.'),
            ('How do I donate to PNEC?',
             'PNEC is a 501(c)(3) nonprofit — donations are tax-deductible. You can donate online via our Donate page, mail a check to PNEC at P.O. Box 414, Poway CA 92074, or donate emergency supplies directly. Every dollar supports training, outreach, and equipment for Poway\'s volunteer emergency network.'),
        ]
    },
]


def seed_faq():
    """
    Purpose: Insert FAQ categories and items if the table is empty.
    @returns {int} Number of FAQ items inserted
    Algorithm:
    1. Check if any items already exist
    2. Insert all categories
    3. Insert all items per category
    4. Commit once
    """
    if FaqItem.query.first():
        print('FAQ already seeded — skipping.')
        return 0

    count = 0
    for cat_data in FAQ_SEED:
        category = FaqCategory(
            name=cat_data['name'],
            icon=cat_data['icon'],
            display_order=cat_data['order'],
        )
        db.session.add(category)
        db.session.flush()  # get category.id

        for question, answer in cat_data['items']:
            db.session.add(FaqItem(
                category_id=category.id,
                question=question,
                answer=answer,
            ))
            count += 1

    db.session.commit()
    print(f'FAQ seeded: {count} items across {len(FAQ_SEED)} categories.')
    return count


def seed_sample_events():
    """
    Purpose: Insert a few sample PNEC events so the calendar isn't empty.
    @returns {int} Number of events inserted
    """
    if Event.query.first():
        print('Events already seeded — skipping.')
        return 0

    now = datetime.utcnow()
    sample_events = [
        Event(
            title='PNEC Monthly Meeting',
            description='Join PNEC volunteers for our monthly coordination meeting. All community members welcome. We\'ll discuss upcoming drills, coordinator vacancies, and neighborhood preparedness initiatives.',
            date=now + timedelta(days=10),
            location='Poway Community Park Recreation Center, 13094 Civic Center Dr, Poway CA',
        ),
        Event(
            title='CERT Basic Training — Spring Cohort',
            description='Six-week CERT training covering disaster response, fire safety, light search and rescue, first aid, and team organization. Registration required — contact the City of Poway.',
            date=now + timedelta(days=18),
            location='Poway City Hall, 13325 Civic Center Dr, Poway CA',
        ),
        Event(
            title='Neighborhood Preparedness Fair',
            description='Hands-on fair with booths on go-bag building, earthquake safety, wildfire defensible space, ham radio demonstrations, and PNEC coordinator sign-ups. Free admission, family friendly.',
            date=now + timedelta(days=32),
            location='Old Poway Park, 14134 Midland Rd, Poway CA',
        ),
        Event(
            title='Ham Radio License Exam Session',
            description='Take your FCC Technician or General license exam. Study resources available at hamstudy.org. No registration required — arrive 30 minutes early with valid ID.',
            date=now + timedelta(days=45),
            location='Poway Library, 13137 Poway Rd, Poway CA',
        ),
    ]

    db.session.add_all(sample_events)
    db.session.commit()
    print(f'Events seeded: {len(sample_events)} sample events.')
    return len(sample_events)


def main():
    with app.app_context():
        n_faq    = seed_faq()
        n_hoods  = seed_neighborhoods()
        n_events = seed_sample_events()
        print(f'\nSeed complete — {n_faq} FAQ items, {n_hoods} neighborhoods, {n_events} events.')


if __name__ == '__main__':
    main()
