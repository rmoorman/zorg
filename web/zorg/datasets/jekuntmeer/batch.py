"""Bij jekuntmeer is een organisatie een lokatie van een activiteit"""

# Packages
import requests
import xmltodict
# Project
from datasets.normalized import models

USER_GUID = 'jekm'
OFFESET_STEP = 100

URLS = {
    'activiteiten':  'http://amsterdam.jekuntmeer.nl/beheer/eigen-projecten/projects/inforing?c-Offset={offset}',
    'activiteitenDetails': 'http://amsterdam.jekuntmeer.nl/aanbod/eigen-projecten/detail/{activiteit_id}/2/inforing',
    'activiteitenLink': 'http://amsterdam.jekuntmeer.nl/aanbod/eigen-projecten/detail/{activiteit_id}/',
    'organisaties': 'http://amsterdam.jekuntmeer.nl/aanbod/eigen-projecten/orglist/inforing',
    'organisatieDetails': 'http://amsterdam.jekuntmeer.nl/aanbod/eigen-projecten/orgdetail/{location_id}/inforing',
    'organisatieLink': 'http://amsterdam.jekuntmeer.nl/aanbod/eigen-projecten/orgdetail/{location_id}/',
}


def normalize_location(data):
    # Normalizing postcode to be 6 chars long
    try:
        postcode = data.get('POSTCODE', '').replace(' ', '')
    except AttributeError:
        postcode = None
    try:
        # Retrieve house number from the adres field
        huisnummer_potentials = data['ADRES'].split(' ')
        # No point in starting in the first location
        pos = 1
        huisnummer = ''
        openbare_ruimte_naam = ''
        while pos < len(huisnummer_potentials):
            if huisnummer_potentials[pos].isdigit():
                huisnummer = huisnummer_potentials[pos]
                openbare_ruimte_naam = ' '.join(huisnummer_potentials[:pos])
                break
            pos += 1
        # If nothing was found taking and the last part starts with a digit
        # Take that as house number. This will account for 34-36, 15D, etc
        if not huisnummer and huisnummer_potentials[-1][0].isdigit() and len(huisnummer_potentials) > 1:
            huisnummer = huisnummer_potentials[-1]
            openbare_ruimte_naam = ' '.join(huisnummer_potentials[:-1])
    except AttributeError:
        huisnummer = ''
        openbare_ruimte_naam = ''

    return {
        'id': data['ID'],
        'naam': data['NAAM'],
        'openbare_ruimte_naam': openbare_ruimte_naam,
        'huisnummer': huisnummer,
        'postcode': postcode,
    }


def normalize_activity(data):
    return {
        'id': data['ID'],
        'locatie_id': f"{USER_GUID}-{data['ORGANISATIEID']}",
        'organisatie_id': f'{USER_GUID}',
        'naam': data['NAAM'],
        'beschrijving': data['OMSCHRIJVING'],
        'bron_link': URLS['activiteitenLink'].format(activiteit_id=data['ID'])
    }


def load_org():
    try:
        return models.Organisatie.objects.get(pk='jekuntmeer')
    except models.Organisatie.DoesNotExist:
        # Creating the jekuntmeer organistaie. Dit moet uit de poc
        jekuntmeer = models.Organisatie(id='jekuntmeer')
        jekuntmeer.guid = USER_GUID
        jekuntmeer.naam = 'jekuntmeer.nl'
        jekuntmeer.beschrijving = 'Jekuntmeer.nl is de site voor vraag en aanbod in passend werk, opleiding en activiteiten bij jou in de buurt.'
        jekuntmeer.afdeling = ''
        jekuntmeer.contact = {'tel': '085 - 273 36 37', 'email': 'redactie@jekuntmeer.nl'}
        jekuntmeer.save()


def import_location():
    # Retriving the locations, refered to as organistaie in the xml
    xml_resp = requests.get(URLS['organisaties'])
    locations = xmltodict.parse(xml_resp.text)
    for location in locations['ORGANISATIONS']['ORGANISATION']:
        location_id = location['ID']
        # Creating a location event
        try:
            location_xml = requests.get(URLS['organisatieDetails'].format(location_id=location_id))
            location_data = xmltodict.parse(location_xml.text)['ORGANISATION']
        except Exception as e:
            continue
        guid = f'{USER_GUID}-{location_id}'
        data = normalize_location(location_data)
        event = models.LocatieEventLog(event_type='C', guid=guid, data=data)
        event.save()


def import_activities():
    # Making sure at least one request is sent
    offset = 0
    total = 1

    while offset < total:
        xml_resp = requests.get(URLS['activiteiten'].format(offset=offset))
        activiteiten = xmltodict.parse(xml_resp.text)

        for activiteit in activiteiten['PRODUCTEN']['PRODUCT']:
            # Reading the activiteit data
            activiteit_xml = requests.get(URLS['activiteitenDetails'].format(activiteit_id=activiteit['ID']))
            try:
                activiteit_data = xmltodict.parse(activiteit_xml.text)['PRODUCT']
            except Exception as e:
                continue
            guid = f"{USER_GUID}-{activiteit['ID']}"
            data = normalize_activity(activiteit_data)
            event = models.ActiviteitEventLog(event_type='C', guid=guid, data=data)
            event.save()

        # Setting total the first time only
        if total == 1:
            total = int(activiteiten['PRODUCTEN']['@MAXAANTAL'])
        offset += OFFESET_STEP


def run():
    # Loading the organisatie
    load_org()
    # Retriving the locations, refered to as organistaie in the xml
    import_location()
    # Retriving the activities
    import_activities()
