import re
import datetime
import warnings

import yaml
from lxml import etree
import pytz
from unidecode import unidecode

from pupa.utils import make_pseudo_id
from pupa.scrape import Scraper, Event

from .constants import BILL_REGEX


def bill_code_to_id(code):
    split = code.replace('.', '').split()
    return ''.join(split[0:-1]).replace(' ', '') + ' ' + split[-1]


def vote_code_to_id(code):
    # TODO what will the identifer look like for votes?
    return ''


class UnitedStatesFloorUpdateScraper(Scraper):

    HOUSE_BASE_URL = 'http://clerk.house.gov/floorsummary'
    HOUSE_BACKSEARCH_DAYS = 90

    def _html_scrape_and_parse(self, url):
        """
        Convenience shortcut for retrieving HTML and parsing it using lxml.

        @param url: url to scrape
        @type url: string
        @return: lxml representation of the DOM tree
        @rtype: ElementTree
        """
        return etree.fromstring(self.get(url).text, etree.HTMLParser())

    def _xml_parser(self, xml, encoding='utf-8'):
        """
        Convenience shortcut for parsing XML using lxml.

        @param xml: XML to parse
        @type xml: string
        @param encoding: what encoding to use to parse
        @type encoding: string
        @return: lxml root element representation
        @rtype: ElementTree
        """
        return etree.fromstring(xml.encode(encoding), etree.XMLParser(encoding=encoding))

    def _house_floor_src_url(self, **kwargs):
        """
        Constructs the url for the source of the floor updates XML for a particular date or congress + session.

        @param kwargs: dictionary of different arguments type
        @type kwargs: dict
        @keyword date_str
        @keyword congress
        @keyword session
        @return: url string for source of floor updates XML
        @rtype: string
        """
        if 'date_str' in kwargs and re.match(r"\d{8}", kwargs['date_str']):
            return self.HOUSE_BASE_URL + '/Download.aspx?file={0}.xml'.format(kwargs['date_str'])
        elif 'congress' in kwargs and 'session' in kwargs:
            return self.HOUSE_BASE_URL + '/HDoc-{0}-{1}-FloorProceedings.xml'.format(kwargs['congress'],
                                                                                     kwargs['session'])
    def _get_current_house_committee_names(self):
        """
        Get all current house committee names from unitedstates repo source.

        @return: list of committee names
        @rtype: list[string]
        """
        url = 'https://raw.githubusercontent.com/unitedstates/congress-legislators/master/committees-current.yaml'
        yml = yaml.safe_load(self.get(url).text)
        return [item['name'] for item in yml if item['type'] == 'house']

    def _public_law_detail_scraper(self, **kwargs):
        """
        Retrieves the bill identifier and congress number from its public_law content detail page.

        @param kwargs: multiple input types
        @keyword congress: congress as string
        @keyword number: public law number as string
        @keyword url: pass complete url to bypass forming it from congress and number
        @type kwargs: dict
        @return: dictionary with identifier and congress e.g. {'identifier': 'HR 3', 'congress': '113'}
        @rtype: dict
        """
        if {'congress', 'number'}.issubset(kwargs.keys()):
            url = 'http://www.gpo.gov/fdsys/pkg/PLAW-{0}publ{1}/content-detail.html'.format(kwargs['congress'],
                                                                                            kwargs['number'])
        elif 'url' in kwargs:
            url = kwargs['url']
            kwargs['congress'] = re.search(r'(?<=PLAW-)\d{1,3}', url, re.I).group(0)
        else:
            raise(ValueError("kwargs must contain either 'url' or both 'congress' and 'number'."))

        tree = self._html_scrape_and_parse(url)
        # search through full text of page and find the bill ID
        bill_id = bill_code_to_id(unidecode(re.search(BILL_REGEX, tree.xpath('string()')).group(0)))
        return {'identifier': bill_id, 'congress': kwargs['congress']}

    def _house_floor_update_get_latest_xml(self):
        """
        Retrieves the latest XML found. If none found for today, try previous days until found.

        @return: XML of floor updates
        @rtype: string
        """
        date = datetime.date.today()
        for i in range(1, self.HOUSE_BACKSEARCH_DAYS+1):
            xml = self._house_floor_update_xml_for(date_str=date.strftime('%Y%m%d'))
            if 'The requested file was not found' not in xml:
                return xml
            date = date - datetime.timedelta(days=i)
        warnings.warn('No floor updates found between now and {0} days ago.'.format(str(self.HOUSE_BACKSEARCH_DAYS)))

    def _parse_house_floor_xml_legislative_activity(self, xml):
        """
        Parses XML string of House floor updates and yields them in loop.

        @param xml: XML of field update
        @type xml: string
        @return: complete Event object
        @rtype: Event
        """
        tree = self._xml_parser(xml)

        congress = tree.xpath('//legislative_congress')[0].get('congress')

        house_committees = self._get_current_house_committee_names()

        for fa in tree.xpath('//floor_actions/floor_action'):
            fa_text = fa.xpath('action_description')[0].xpath('string()')

            eastern = pytz.timezone('US/Eastern')
            dt = datetime.datetime.strptime(fa.xpath('action_time')[0].get('for-search'), '%Y%m%dT%H:%M:%S')
            event = Event('House Floor Update on {0} at {1}.'.format(dt.strftime('%Y-%m-%d'), dt.strftime('%H:%M:%S')),
                          eastern.localize(dt).astimezone(pytz.utc),
                          'US/Eastern',
                          {'name': "East Capitol Street Northeast & First St SE, Washington, DC 20004",
                           'note': 'House Floor',
                           'url': 'http://www.house.gov/',
                           'coordinates': {'latitude': '38.889931', 'longitude': '-77.009003'}
                           },
                          description=fa_text,
                          classification='floor_update')

            event.add_source(self._house_floor_src_url(date_str=tree.xpath('//legislative_day')[0].get('date')),
                             note="Scraped from the Office of the Clerk, U.S. House of Representatives website.")

            event.extras['act-id'] = fa.get('act-id')
            event.extras['unique-id'] = fa.get('unique-id')

            # bills
            ai_b = event.add_agenda_item(description='Bills referenced by this update.')
            for bill in fa.xpath("//a[@rel='bill']"):
                bill_name = bill.xpath('string()')
                ai_b.add_bill(bill_name, id=make_pseudo_id(identifier=bill_code_to_id(bill_name), congress=congress),
                              note="Bill was referenced on the House floor.")

            # publaws
            ai_p = event.add_agenda_item(description='Public laws referenced by this update.')
            for law in fa.xpath("//a[@rel='publaw']"):
                detail_url = '/'.join(law.get('href').split('/')[0:-2]) + '/content-detail.html'
                ai_p.add_bill(law.xpath('string()'),
                              id=make_pseudo_id(**self._public_law_detail_scraper(url=detail_url)),
                              note='Law was referenced on the House floor.')

            # votes
            ai_v = event.add_agenda_item(description='Votes referenced by this update.')
            for vote in fa.xpath("//a[@rel='vote']"):
                vote_name = vote.xpath('string()')
                ai_v.add_vote(vote_name,
                              id=make_pseudo_id(identifier=vote_code_to_id(vote_name), congress=congress),
                              note='Vote was referenced on the House floor.')

            # reports
            for report in fa.xpath("//a[@rel='report']"):
                event.add_document('Document referenced by this update.', report.get('href'), media_type='text/html')

            for name in house_committees:
                if name.replace('House ', '') in fa_text:
                    event.add_committee(name, id=make_pseudo_id(name=name))

            # TODO identify legislators and add them as participants?

            yield event

    def _house_floor_update_get_available_bulk_xml(self):
        """
        Retrieves the available bulk floor updates by congress + session

        @return: list of dicts with 'congress' and 'session' keys
        @rtype: list[dict[str, str]]
        """
        tree = self._html_scrape_and_parse(self.HOUSE_BASE_URL + 'floor-download.aspx')
        return list(map(lambda x: dict(zip(['congress','session'], x.get('href').split('-')[1:3])),
                        tree.xpath("//div[@id='intro_content']//a")))

    def _house_floor_update_xml_for(self, **kwargs):
        """
        Retrieves the current XML for a particular date.

        @keyword date_str: date string to get floor updates for
        @type date_str: string
        @keyword congress: congress to get floor updates for
        @type congress: string
        @keyword session: session number [1,2] corresponding to the two years of the congress
        @type session: string
        @return: XML of floor updates
        @rtype: string
        """
        try:
            return self.get(self._house_floor_src_url(**kwargs)).text
        except:
            print('Unable to retrieve XML from clerk website. Is the site down?')

    def _scrape_house_floor_update(self):
        """
        Gets the latest floor update XML, parses it, instantiate and yield event object

        @return: an Event generator
        @rtype: generator[Event]
        """
        yield from self._parse_house_floor_xml_legislative_activity(self._house_floor_update_get_latest_xml())

    def scrape(self):
        yield self._scrape_house_floor_update()
        # TODO senate floor updates