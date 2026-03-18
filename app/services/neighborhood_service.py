# app/services/neighborhood_service.py
# Responsibility: Neighborhood business logic — fetch, seed, and address lookup.

from app import db
from app.models.neighborhood import Neighborhood


def get_all_neighborhoods():
    """
    Purpose: Return all neighborhoods as a list of dicts.
    @returns {list} All neighborhood dicts ordered by number
    """
    neighborhoods = Neighborhood.query.order_by(Neighborhood.number).all()
    return [n.to_dict() for n in neighborhoods]


def get_neighborhood_by_id(neighborhood_id):
    """
    Purpose: Fetch a single neighborhood by primary key.
    @param {int} neighborhood_id - The neighborhood PK
    @returns {dict|None} Neighborhood dict or None if not found
    """
    n = Neighborhood.query.get(neighborhood_id)
    return n.to_dict() if n else None


def lookup_neighborhood_by_name(query_text):
    """
    Purpose: Search neighborhoods by name or number (for address/name search bar).
    @param {str} query_text - Search string from the user
    @returns {list} List of matching neighborhood dicts (up to 10)
    Algorithm:
    1. Sanitize query
    2. Search by name (LIKE) and number (exact if numeric)
    3. Return top 10 matches
    """
    if not query_text or len(query_text.strip()) < 1:
        return []

    term = f'%{query_text.strip()}%'
    matches = Neighborhood.query.filter(Neighborhood.name.ilike(term)).limit(10).all()

    # Also try exact number match if query is numeric
    if query_text.strip().isdigit():
        number_match = Neighborhood.query.filter_by(number=int(query_text.strip())).first()
        if number_match and number_match not in matches:
            matches.insert(0, number_match)

    return [n.to_dict() for n in matches]


def seed_neighborhoods():
    """
    Purpose: Populate the neighborhoods table with the ~60 Poway neighborhoods.
    Only runs if the table is empty. Coordinator data is placeholder.
    @returns {int} Number of records inserted
    Algorithm:
    1. Check if any rows exist — skip if so
    2. Insert all neighborhood seed records
    3. Commit and return count
    """
    if Neighborhood.query.first():
        return 0

    seed_data = [
        {'number': 1,  'name': 'Old Poway Village',           'zone': 'A'},
        {'number': 2,  'name': 'Poway Road Corridor',         'zone': 'A'},
        {'number': 3,  'name': 'Twin Peaks Area',             'zone': 'B'},
        {'number': 4,  'name': 'Community Road',              'zone': 'A'},
        {'number': 5,  'name': 'Garden Road',                 'zone': 'A'},
        {'number': 6,  'name': 'Espola Road North',           'zone': 'B'},
        {'number': 7,  'name': 'Espola Road South',           'zone': 'B'},
        {'number': 8,  'name': 'Hilleary Park Area',          'zone': 'A'},
        {'number': 9,  'name': 'Midland Road',                'zone': 'A'},
        {'number': 10, 'name': 'Scripps Poway Parkway West',  'zone': 'A'},
        {'number': 11, 'name': 'Scripps Poway Parkway East',  'zone': 'B'},
        {'number': 12, 'name': 'Stowe Drive Area',            'zone': 'A'},
        {'number': 13, 'name': 'Martincoit Road',             'zone': 'B'},
        {'number': 14, 'name': 'Kirkham Road',                'zone': 'B'},
        {'number': 15, 'name': 'Poway Valley Road',           'zone': 'B'},
        {'number': 16, 'name': 'Crestridge Road',             'zone': 'C'},
        {'number': 17, 'name': 'Rattlesnake Creek Area',      'zone': 'C'},
        {'number': 18, 'name': 'Lake Poway Recreation Area',  'zone': 'C'},
        {'number': 19, 'name': 'Blue Sky Reserve North',      'zone': 'C'},
        {'number': 20, 'name': 'Blue Sky Reserve South',      'zone': 'C'},
        {'number': 21, 'name': 'Poway Industrial Area',       'zone': 'A'},
        {'number': 22, 'name': 'Creekside Village',           'zone': 'A'},
        {'number': 23, 'name': 'Oak Knoll Area',              'zone': 'B'},
        {'number': 24, 'name': 'Summerfield',                 'zone': 'A'},
        {'number': 25, 'name': 'Tierra Bonita',               'zone': 'B'},
        {'number': 26, 'name': 'Valley Rim',                  'zone': 'B'},
        {'number': 27, 'name': 'Heritage Hills',              'zone': 'B'},
        {'number': 28, 'name': 'Country Manor',               'zone': 'B'},
        {'number': 29, 'name': 'Los Ranchitos',               'zone': 'C'},
        {'number': 30, 'name': 'Silverset',                   'zone': 'A'},
        {'number': 31, 'name': 'Eastview',                    'zone': 'B'},
        {'number': 32, 'name': 'Alta Vista',                  'zone': 'B'},
        {'number': 33, 'name': 'Casa Blanca',                 'zone': 'A'},
        {'number': 34, 'name': 'Valle Verde',                 'zone': 'A'},
        {'number': 35, 'name': 'Meadowbrook',                 'zone': 'A'},
        {'number': 36, 'name': 'Morning Star',                'zone': 'B'},
        {'number': 37, 'name': 'Sun Country Estates',         'zone': 'C'},
        {'number': 38, 'name': 'Spring Ranch',                'zone': 'C'},
        {'number': 39, 'name': 'Chaparral Ranch',             'zone': 'C'},
        {'number': 40, 'name': 'Rocky Road Estates',          'zone': 'C'},
        {'number': 41, 'name': 'Stonebridge',                 'zone': 'B'},
        {'number': 42, 'name': 'Poway Town Center',           'zone': 'A'},
        {'number': 43, 'name': 'South Poway Industrial',      'zone': 'A'},
        {'number': 44, 'name': 'Windmill Farms',              'zone': 'B'},
        {'number': 45, 'name': 'Ridgeway',                    'zone': 'B'},
        {'number': 46, 'name': 'Pintail Landing',             'zone': 'A'},
        {'number': 47, 'name': 'Budwin Lane Area',            'zone': 'B'},
        {'number': 48, 'name': 'Sunset Hills',                'zone': 'B'},
        {'number': 49, 'name': 'Canyon Crest',                'zone': 'C'},
        {'number': 50, 'name': 'Carriage Hills',              'zone': 'C'},
        {'number': 51, 'name': 'Brookside',                   'zone': 'A'},
        {'number': 52, 'name': 'Sycamore Canyon Area',        'zone': 'C'},
        {'number': 53, 'name': 'Upper Poway Estates',         'zone': 'C'},
        {'number': 54, 'name': 'El Capitan Estates',          'zone': 'D'},
        {'number': 55, 'name': 'Donart Drive Area',           'zone': 'B'},
        {'number': 56, 'name': 'Olive Hills',                 'zone': 'B'},
        {'number': 57, 'name': 'Poway Park Area',             'zone': 'A'},
        {'number': 58, 'name': 'Welton Drive Area',           'zone': 'A'},
        {'number': 59, 'name': 'Cobblestone Creek',           'zone': 'B'},
        {'number': 60, 'name': 'Hidden Meadows (Poway)',      'zone': 'D'},
    ]

    records = []
    for d in seed_data:
        records.append(Neighborhood(
            number=d['number'],
            name=d['name'],
            zone=d['zone'],
            coordinator_name='[Coordinator TBD]',
            coordinator_email='info@powaynec.com',
        ))

    db.session.add_all(records)
    db.session.commit()
    return len(records)
