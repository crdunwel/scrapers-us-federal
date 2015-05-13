import re


CODE_TO_STATE = {
    'WA': 'Washington', 'WI': 'Wisconsin', 'WV': 'West Virginia',
    'FL': 'Florida', 'FM': 'Federated States of Micronesia',
    'WY': 'Wyoming', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NC': 'North Carolina', 'ND': 'North Dakota',
    'NE': 'Nebraska', 'NY': 'New York', 'RI': 'Rhode Island',
    'NV': 'Nevada', 'GU': 'Guam', 'CO': 'Colorado',
    'CA': 'California', 'GA': 'Georgia', 'CT': 'Connecticut',
    'OK': 'Oklahoma', 'OH': 'Ohio', 'KS': 'Kansas', 'SC': 'South Carolina',
    'KY': 'Kentucky', 'OR': 'Oregon', 'SD': 'South Dakota', 'DE': 'Delaware',
    'DC': 'District of Columbia', 'HI': 'Hawaii', 'PR': 'Puerto Rico',
    'PW': 'Palau', 'TX': 'Texas', 'LA': 'Louisiana', 'TN': 'Tennessee',
    'PA': 'Pennsylvania', 'AA': 'Armed Forces Americas', 'VA': 'Virginia',
    'AE': 'Armed Forces Middle East', 'VI': 'Virgin Islands', 'AK': 'Alaska',
    'AL': 'Alabama', 'AP': 'Armed Forces Pacific', 'AS': 'American Samoa',
    'AR': 'Arkansas', 'VT': 'Vermont', 'IL': 'Illinois', 'IN': 'Indiana',
    'IA': 'Iowa', 'AZ': 'Arizona', 'ID': 'Idaho', 'ME': 'Maine',
    'MD': 'Maryland', 'MA': 'Massachusetts', 'UT': 'Utah',
    'MO': 'Missouri', 'MN': 'Minnesota', 'MI': 'Michigan', 'MH': 'Marshall Islands',
    'MT': 'Montana', 'MP': 'Northern Mariana Islands', 'MS': 'Mississippi'
}


NAME_PREFIX_LIST = ['Ms.', 'Mrs.', 'Mr.', 'Dr.', 'Miss', 'Reverend',
                    'Sister', 'Pastor', 'Hon.', 'Reverend', 'the Honorable',
                    'the Speaker', 'Rep.', 'Sen.', 'Representative', 'Senator',
                    'Rabbi', 'Governor', 'Gov.', 'Congressman']


BILL_REGEX = re.compile('((S\.|H\.)(\s*J\.|\s?R\.|\s?Con\.|\s*)(\s*Res\.?)*\s*\d+)', re.I)


# this may catch a number of them, but not all
PERSON_REGEX = re.compile('(' + '|'.join(NAME_PREFIX_LIST) +
                          ')\s([A-Z]{1}\S+\s)+(of\s)?(\()?(' +
                          '|'.join(CODE_TO_STATE.keys()) + ')(\))?')


# https://github.com/unitedstates/congress/wiki/bills#basic-information
TYPE_MAP = {
     # "H.R. 1234". It stands for House of Representatives, but it is the prefix used for bills introduced in the House.
    'hr': {'chamber':'lower', 'canonical': 'HR'},
     # "H.Res. 1234". It stands for House Simple Resolution.
    'hres': {'chamber':'lower', 'canonical': 'HRes'},
     # "H.Con.Res. 1234". It stands for House Concurrent Resolution.
    'hconres': {'chamber':'joint', 'canonical':'HConRes'},
     # "H.J.Res. 1234". It stands for House Joint Resolution.
    'hjres': {'chamber':'joint', 'canonical':'HJRes'},
     # "S. 1234". It stands for Senate and it is the prefix used for bills introduced in the Senate. Any abbreviation besides "S." is incorrect.
    's': {'chamber':'upper', 'canonical': 'S'},
     # "S.Res. 1234". It stands for Senate Simple Resolution.
    'sres': {'chamber':'upper', 'canonical': 'SRes'},
     # "S.Con.Res. 1234". It stands for Senate Concurrent Resolution.
    'sconres': {'chamber':'joint', 'canonical': 'SConRes'},
    # "S.J.Res. 1234". It stands for Senate Joint Resolution.
    'sjres': {'chamber':'joint', 'canonical': 'SJRes'}
}


TITLE_CHAMBER_MAP = {
    'Rep': 'lower',
    'Sen': 'upper'
}


# http://www.gpo.gov/help/index.html#about_congressional_bills.htm
VERSION_MAP = {
    'eh': 'Engrossed in House',
    'rcs': 'Reference Change Senate',
    'iph': 'Indefinitely Postponed House',
    'cdh': 'Committee Discharged House',
    'ris': 'Referral Instructions Senate',
    'rah': 'Referred with Amendments House',
    'pwah': 'Ordered to be Printed with House Amendment',
    'ih': 'Introduced in House',
    'as': 'Amendment Ordered to be Printed Senate',
    'renr': 'Re-enrolled Bill',
    'ras': 'Referred with Amendments Senate',
    'rts': 'Referred to Committee Senate',
    'cds': 'Committee Discharged Senate',
    'sas': 'Additional Sponsors Senate',
    'lts': 'Laid on Table in Senate',
    'pap': 'Printed as Passed',
    'pp': 'Public Print',
    'rfh': 'Referred in House',
    'pav': 'Previous Action Vitiated',
    'ash': 'Additional Sponsors House',
    'pcs': 'Placed on Calendar Senate',
    'rs': 'Reported in Senate',
    'fph': 'Failed Passage House',
    'enr': 'Enrolled Bill',
    'rch': 'Reference Change House',
    'fps': 'Failed Passage Senate',
    'rh': 'Reported in House',
    'is': 'Introduced in Senate',
    'eah': 'Engrossed Amendment House',
    'reah': 'Re-engrossed Amendment House',
    'es': 'Engrossed in Senate',
    'ops': 'Ordered to be Printed Senate',
    'rth': 'Referred to Committee House',
    'fah': 'Failed Amendment House',
    'eas': 'Engrossed Amendment Senate',
    'oph': 'Ordered to be Printed House',
    'cph': 'Considered and Passed House',
    'lth': 'Laid on Table in House',
    'hds': 'Held at Desk Senate',
    'rds': 'Received in Senate',
    'ips': 'Indefinitely Postponed Senate',
    'rfs': 'Referred in Senate',
    'hdh': 'Held at Desk House',
    'ath': 'Agreed to House',
    'rih': 'Referral Instructions House',
    'pch': 'Placed on Calendar House',
    'ats': 'Agreed to Senate',
    'eph': 'Engrossed and Deemed Passed by House',
    'res': 'Re-engrossed Amendment Senate',
    'sc': 'Sponsor Change',
    'cps': 'Considered and Passed Senate',
    'rdh': 'Received in House'
}