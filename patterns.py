# patterns.py - Regex Pattern Detection Module
# =============================================
# Contains regex patterns for membership and offer detection

"""
Regex patterns for detecting membership and offer emails

This module handles:
- Membership/subscription detection patterns
- Offer/discount/promotion detection patterns
- Shopping site domain filtering
- Case-insensitive matching using re.IGNORECASE
"""

import re
from typing import Tuple, List, Dict

# ============================================
# KNOWN SHOPPING / COMMERCIAL DOMAINS (USA Focus)
# ============================================
SHOPPING_DOMAINS = [
    # === MAJOR E-COMMERCE ===
    'amazon', 'ebay', 'walmart', 'target', 'bestbuy', 'costco',
    'aliexpress', 'shopify', 'etsy', 'wayfair', 'overstock', 'newegg',
    'wish', 'temu', 'shein', 'alibaba', 'rakuten', 'jet.com',
    
    # === DEPARTMENT STORES ===
    'macys', 'nordstrom', 'jcpenney', 'kohls', 'dillards', 'belk',
    'bloomingdales', 'saksoff5th', 'saksfifthavenue', 'neimanmarcus',
    'lordandtaylor', 'vonmaur', 'bergdorfgoodman', 'barneys',
    
    # === DISCOUNT / VALUE RETAILERS ===
    'tjmaxx', 'marshalls', 'homegoods', 'ross', 'burlington',
    'dollargeneral', 'dollartree', 'familydollar', 'fivebelow',
    'biglots', 'ollies', 'tuesdaymorning', 'dd.com', 'ddsdiscounts',
    
    # === WAREHOUSE / MEMBERSHIP CLUBS ===
    'costco', 'samsclub', 'sams club', 'bjs', 'bjswholesale',
    
    # === FASHION & APPAREL ===
    'nike', 'adidas', 'puma', 'reebok', 'underarmour', 'newbalance',
    'lululemon', 'athleta', 'fabletics', 'gymshark',
    'zara', 'hm', 'h&m', 'uniqlo', 'forever21', 'asos', 'shein',
    'gap', 'oldnavy', 'bananarepublic', 'athleta',
    'express', 'americaneagle', 'aerie', 'hollister', 'abercrombie',
    'pacsun', 'zumiez', 'tillys', 'buckle', 'journeys',
    'urbanoutfitters', 'anthropologie', 'freepeople',
    'jcrew', 'madewell', 'anntaylor', 'loft', 'chicos',
    'torrid', 'lanebryant', 'avenue', 'maurices', 'dressbarn',
    'ralphlauren', 'calvinklein', 'tommyhilfiger', 'guess', 'levis',
    'victoriassecret', 'bathandbodyworks', 'aerie', 'pinkbyvs',
    'dickssportinggoods', 'academy', 'reisportinggoods', 'footlocker',
    'finishline', 'champssports', 'eastbay',
    
    # === LUXURY / DESIGNER ===
    'louisvuitton', 'gucci', 'prada', 'chanel', 'hermes', 'burberry',
    'coach', 'katespade', 'michaelkors', 'toryburch', 'versace',
    'dior', 'armani', 'balenciaga', 'bottegaveneta', 'fendi',
    
    # === SHOES ===
    'footlocker', 'dsw', 'famousfootwear', 'shoecarnival', 'shoedazzle',
    'zappos', 'aldoshoes', 'stevemadden', 'clarks', 'skechers',
    'crocs', 'birkenstock', 'ugg', 'timberland', 'drmartens',
    
    # === HOME & FURNITURE ===
    'ikea', 'wayfair', 'overstock', 'ashleyfurniture', 'roomstogo',
    'westelm', 'potterybarn', 'crateandbarrel', 'cb2', 'zgallerie',
    'pier1', 'worldmarket', 'athome', 'homegoods', 'homesense',
    'bedbathandbeyond', 'surlatable', 'williamssonoma', 'restoration',
    'ethanallen', 'lazboy', 'arhaus', 'haverty', 'valuecityfurniture',
    # Designer Home / Lifestyle Brands
    'jonathanadler', 'jonathan adler', 'serenaandlily', 'serena & lily',
    'anthropologie', 'rejuvenation', 'lumens', 'ylighting', 'allmodern',
    'jossandmain', 'perigold', 'onekingslane', 'chairish', '1stdibs',
    'article', 'burrow', 'floyd', 'interior define', 'joybird', 'apt2b',
    'roveconcepts', 'modway', 'castlery', 'albanypark', 'insideweather',
    'maisonette', 'mcgeeandco', 'studiomcgee', 'ballarddesigns',
    'frontgate', 'grandinroad', 'garnethill', 'sundancecatalog',
    'horchow', 'neimanmarcushome', 'abchome', 'dwr', 'designwithinreach',
    'knoll', 'hermanmiller', 'roomandboard', 'bluedot', 'hivemodern',
    
    # === HOME IMPROVEMENT ===
    'homedepot', 'lowes', 'menards', 'acehardware', 'truevalue',
    'harborfreight', 'northerntool', 'tractorsupply', 'fleetfarm',
    
    # === GROCERY & SUPERMARKETS ===
    'kroger', 'safeway', 'albertsons', 'publix', 'wegmans',
    'wholefoods', 'traderjoes', 'aldi', 'lidl', 'sprouts',
    'harristeeter', 'giantfood', 'stopandshop', 'shaws', 'jewel',
    'ralphs', 'vons', 'smiths', 'frys', 'qfc', 'kingsooper',
    'heb', 'meijer', 'winn-dixie', 'foodlion', 'pigglywiggly',
    'freshmarket', 'earthfare', 'naturalgrocer', 'freshthyme',
    
    # === GROCERY DELIVERY ===
    'instacart', 'shipt', 'freshdirect', 'peapod', 'amazonfresh',
    'walmartgrocery', 'targetdelivery', 'gopuff', 'getir', 'gorillas',
    
    # === FOOD DELIVERY & RESTAURANTS ===
    'doordash', 'ubereats', 'grubhub', 'postmates', 'seamless',
    'dominos', 'pizzahut', 'papajohns', 'littlecaesars',
    'mcdonalds', 'burgerking', 'wendys', 'tacobell', 'chickfila',
    'chipotle', 'qdoba', 'panerabread', 'subway', 'jimmyjohns',
    'starbucks', 'dunkin', 'timhortons', 'peets', 'caribou',
    'dennys', 'ihop', 'applebees', 'chillis', 'olivegarden', 'redlobster',
    'outback', 'texasroadhouse', 'cracklebarrel', 'buffalowildwings',
    # Additional Restaurant Chains with Rewards
    'jackinthebox', 'hardees', 'carlsjr', 'whataburger', 'sonicsonic',
    'inandout', 'fiveguys', 'shakeshack', 'smashburger', 'culvers',
    'checkers', 'rallys', 'whitecastle', 'krystal', 'delltaco',
    'elpollo', 'moes', 'wingstop', 'zaxbys', 'raisingcanes', 'popeyes',
    'kfc', 'churchschicken', 'bostonmarket', 'noodles', 'noodlescompany',
    'potbelly', 'firehouse', 'firehousesubs', 'jerseymikes', 'blimpie',
    'schlotzskys', 'jasons deli', 'mcalisters', 'zoes kitchen',
    'sweetgreen', 'cava', 'chopt', 'justfalad', 'dig',
    'cheesecakefactory', 'bjs restaurant', 'yardhouserestaurant',
    'tgifridays', 'rubytuesday', 'goldencorral', 'ryans', 'hometown',
    'bobevans', 'friendlys', 'perkins', 'village inn', 'huddle house',
    'waffle house', 'firstwatch', 'brokenYolk', 'anotherbrokenEgg',
    'einsteins bagels', 'noahs', 'brueggers', 'aubon pain',
    'jamba', 'smoothieking', 'tropicalsmoothie', 'nekter', 'robeks',
    'coldstone', 'baskinrobbins', 'dairyqueen', 'carvel', 'ritascustard',
    'krispy kreme', 'insomnia cookies', 'crumbl', 'nothing bundt',
    
    # === GAS STATIONS & CONVENIENCE (Rewards Programs) ===
    'shell', 'chevron', 'texaco', 'exxon', 'mobil', 'bp', 'amoco',
    'sunoco', 'marathon', 'speedway', 'phillips66', 'conoco', '76',
    'valero', 'circlek', 'murphy', 'murphyusa', 'quiktrip', 'qt',
    'racetrac', 'kum&go', 'loves', 'pilotflyingj', 'ta petro',
    'casey', 'caseysgeneral', 'kwiktrip', 'kwikstar', 'maverik',
    'wawa', 'sheetz', 'bucees', 'royalfarms', 'rutters',
    '7-eleven', '7eleven', 'speedway', 'circlk', 'ampm',
    'cumberlandfarms', 'stewarts', 'getgo', 'thorntons',
    'parker', 'stripes', 'allsups', 'quikstop', 'onecue',
    
    # === MOVIE THEATERS (Rewards/Memberships) ===
    'amc', 'amctheatres', 'regal', 'cinemark', 'cineplex',
    'marcus theatres', 'harkins', 'showplace', 'landmark',
    'alamo drafthouse', 'ipic', 'angelika', 'arclight',
    'showcase', 'bow tie', 'reading', 'malco', 'emagine',
    
    # === WINE & LIQUOR ===
    'totalwine', 'bevmo', 'specsonline', 'abcfinewinespirits',
    'binny', 'goodygoody', 'twinliquors', 'argonaut liquors',
    'drizly', 'minibar delivery', 'saucey', 'reservebar',
    
    # === THEME PARKS & ENTERTAINMENT ===
    'disney', 'universal', 'sixflags', 'cedarfair', 'seaworld',
    'legoland', 'knotts', 'dollywood', 'hersheypark', 'buschgardens',
    'dave and busters', 'mainEvent', 'chuckecheese', 'round1',
    'topgolf', 'bowlero', 'amf', 'lucky strike',
    
    # === ELECTRONICS & TECH ===
    'bestbuy', 'newegg', 'microcenter', 'frys', 'bhphotovideo',
    'apple', 'samsung', 'dell', 'hp', 'lenovo', 'asus', 'acer',
    'microsoft', 'sony', 'lg', 'panasonic', 'bose', 'jbl', 'sonos',
    'logitech', 'razer', 'corsair', 'steelseries',
    'gamestop', 'playstation', 'xbox', 'nintendo',
    'oneplus', 'google', 'motorola',
    'verizon', 'att', 'tmobile', 'sprint', 'uscc',
    
    # === OFFICE & SCHOOL SUPPLIES ===
    'staples', 'officedepot', 'officemax', 'quill',
    
    # === BEAUTY & COSMETICS ===
    'sephora', 'ulta', 'bluemercury', 'maccosmetics', 'nars',
    'clinique', 'esteelauder', 'benefitcosmetics', 'urbandecay',
    'glossier', 'colourpop', 'morphe', 'tartecosmetics', 'toofaced',
    'maybelline', 'lorealparis', 'revlon', 'covergirl', 'nyx',
    'bathandbodyworks', 'thebodyshop', 'lush', 'kiehl',
    'dermstore', 'beautycounter', 'fenty', 'rarebeauty',
    
    # === HEALTH & WELLNESS ===
    'cvs', 'walgreens', 'riteaid', 'vitaminshoppe', 'gnc',
    'iherb', 'vitacost', 'swanson', 'puritan', 'luckyvitamin',
    
    # === PHARMACY ===
    'cvs', 'walgreens', 'riteaid', 'express-scripts', 'optumrx',
    'caremarkrx', 'amazon pharmacy', 'costcopharmacy',
    
    # === PET SUPPLIES ===
    'petco', 'petsmart', 'chewy', 'petfooddirect', 'entirelypets',
    'petflow', 'petmeds', '1800petmeds', 'petcarerx', 'allivet',
    
    # === AUTO & PARTS ===
    'autozone', 'oreillyauto', 'advanceautoparts', 'napaonline',
    'pepboys', 'carquest', 'rockauto', 'tirerack', 'discounttire',
    'carvana', 'carmax', 'vroom', 'shift', 'autonation',
    # Auto Service Rewards
    'jiffy lube', 'jiffylube', 'valvoline', 'takefive', 'expressoil',
    'midas', 'meineke', 'firestone', 'goodyear', 'ntb', 'bigotires',
    'pep boys', 'mavis', 'monro', 'sullivan tire', 'belle tire',
    'costcotires', 'sams club tires', 'america tire',
    
    # === CAR WASH MEMBERSHIPS ===
    'mister car wash', 'zips car wash', 'take 5 car wash',
    'tommy car wash', 'quick quack', 'club car wash', 'flagship',
    'autobell', 'mike car wash', 'super star car wash', 'soapy joe',
    
    # === FITNESS & GYM MEMBERSHIPS ===
    'planet fitness', 'planetfitness', 'la fitness', 'lafitness',
    '24hourfitness', '24 hour fitness', 'anytime fitness', 'anytimefitness',
    'goldsgym', 'golds gym', 'lifetime fitness', 'lifetimefitness',
    'equinox', 'soulcycle', 'barrys', 'orangetheory', 'f45',
    'crossfit', 'ymca', 'crunch fitness', 'blink fitness',
    'esporta', 'eos fitness', 'xsport', 'chuze', 'vasa fitness',
    'snap fitness', 'youfit', 'workout anytime', 'retro fitness',
    'club fitness', 'genesis health clubs', 'onelife fitness',
    'peloton', 'tonal', 'mirror', 'nordictrack', 'ifit',
    'classpass', 'mindbody', 'wellnessliving',
    
    # === SALON & SPA ===
    'greatclips', 'supercuts', 'sportclips', 'fantasticsams',
    'cost cutters', 'smartstyle', 'regis', 'ulta salon',
    'massage envy', 'handand stone', 'elements massage',
    'european wax center', 'waxingcity', 'brazilian wax',
    'drybar', 'blowout bar',
    
    # === PHONE/WIRELESS CARRIERS ===
    'verizon', 'att', 'tmobile', 'sprint', 'uscc', 'uscellular',
    'boost', 'boostmobile', 'cricket', 'cricketwireless',
    'metro', 'metropcs', 'metrobytmobile', 'visible', 'mint mobile',
    'googlefi', 'xfinity mobile', 'spectrum mobile', 'dish wireless',
    'consumer cellular', 'tracfone', 'straighttalk', 'total wireless',
    'simple mobile', 'pageplus', 'redpocket', 'tello', 'ting',
    
    # === INSURANCE (with rewards/member benefits) ===
    'statefarm', 'geico', 'progressive', 'allstate', 'libertymutual',
    'farmers', 'nationwide', 'travelers', 'usaa insurance',
    'amica', 'erie', 'auto-owners', 'american family', 'safeco',
    'thehartford', 'metlife', 'prudential', 'aetna', 'cigna',
    'united healthcare', 'humana', 'kaiser', 'bluecross', 'anthem',
    
    # === STREAMING & SUBSCRIPTIONS ===
    'netflix', 'hulu', 'disneyplus', 'disney', 'hbomax', 'hbo',
    'peacock', 'paramount', 'appletv', 'primevideo', 'amazonprime',
    'spotify', 'applemusic', 'pandora', 'tidal', 'deezer',
    'youtube', 'youtubepremium', 'youtubemusic', 'youtubtv',
    'siriusxm', 'audible', 'kindle', 'kindleunlimited', 'scribd',
    
    # === FINANCE / PAYMENTS / CREDIT CARDS ===
    'paypal', 'venmo', 'cashapp', 'zelle', 'applepay', 'googlepay',
    
    # --- MAJOR CREDIT CARD NETWORKS ---
    'visa', 'mastercard', 'amex', 'americanexpress', 'discover',
    
    # --- BIG 4 NATIONAL BANKS ---
    'chase', 'jpmorgan', 'jpmorganchase', 'bankofamerica', 'bofa',
    'wellsfargo', 'citi', 'citibank', 'citicards',
    
    # --- MAJOR REGIONAL/NATIONAL BANKS ---
    'usbank', 'pnc', 'truist', 'capitalone', 'tdbank', 'td bank',
    'fifththird', 'regions', 'keybank', 'huntington', 'mtb', 'm&t bank',
    'citizens', 'citizensbank', 'bmo', 'bmoharris', 'santander',
    'firstcitizens', 'websterbank', 'zionsbank', 'comerica', 'synovus',
    'eastwestbank', 'popularbank', 'valleynationalbank', 'oldnational',
    'umpqua', 'columbia bank', 'glacier bank', 'banner bank',
    'firsthorizon', 'atlanticcapitalbank', 'southstate', 'pinnaclebank',
    'simmons bank', 'renasant', 'cadence bank', 'trustmark',
    'bankofhope', 'pacificwesternbank', 'firstrepublic', 'signaturebank',
    'westernalliancebank', 'wintrust', 'associatedbank', 'byline bank',
    
    # --- CREDIT CARD SPECIFIC ISSUERS ---
    'synchrony', 'synchronybank', 'barclays', 'barclaycard', 'barclaycardus',
    'bread financial', 'comenity', 'comenitybank', 'td retail card',
    'citiretailservices', 'wellsfargocards', 'elan financial',
    'firstbankcard', 'merrick bank', 'credit one', 'creditonebank',
    'indigo', 'milestone', 'reflex', 'surge', 'fit mastercard',
    'avant', 'ollo', 'petal', 'deserve', 'tomo', 'jasper',
    'upgradecardservices', 'upgrade card', 'mission lane',
    'opensky', 'chime credit builder', 'self', 'grow credit',
    
    # --- CREDIT UNIONS (Issuing Credit Cards) ---
    'navyfederal', 'nfcu', 'penfed', 'pentagonfcu', 'becu',
    'alliant', 'alliantcreditunion', 'usaa', 'statefarm',
    'digitalfcu', 'goldenone', 'schoolsfirst', 'staronecu',
    'sdfcu', 'suncoastcu', 'vaborrowcreditunion', 'vystar',
    'americafirst', 'securityservicefcu', 'randolphbrooks', 'rbfcu',
    'connexus', 'langley', 'logix', 'firsttechfed', 'redstone',
    'nasa fcu', 'andrewsfcu', 'aerofcu', 'tinker fcu',
    
    # --- FINTECH / NEOBANK CARDS ---
    'sofi', 'marcus', 'marcusbygoldmansachs', 'goldmansachs',
    'chime', 'current', 'varo', 'monzo', 'revolut', 'n26',
    'ally', 'allybank', 'discover bank', 'discoverbank',
    'greenlight', 'gohenry', 'step', 'copper', 'till',
    'onefinance', 'one finance', 'aspiration', 'lili', 'novo',
    'bluevine', 'brex', 'ramp', 'divvy', 'airbase',
    
    # --- AIRLINE CO-BRANDED CARDS ---
    'delta skymiles', 'deltaamex', 'united mileageplus', 'unitedcard',
    'aadvantage', 'americanairlinescard', 'southwest rapid rewards',
    'jetblue', 'jetbluecard', 'alaskaairlines', 'alaskacard',
    'hawaiianairlines card', 'frontier miles', 'spirit card',
    
    # --- HOTEL CO-BRANDED CARDS ---
    'marriott bonvoy', 'marriottcard', 'hilton honors', 'hiltoncard',
    'ihg rewards', 'ihgcard', 'hyatt card', 'worldofhyatt',
    'wyndham rewards', 'wyndhamcard', 'choice privileges card',
    
    # --- STORE CREDIT CARDS (Major Retailers) ---
    'amazon store card', 'amazoncard', 'amazon prime card',
    'walmart card', 'walmartcredit', 'target redcard', 'targetcard',
    'costco anywhere', 'costcocard', 'sams club mastercard',
    'kohls charge', 'kohlscard', 'macys card', 'macyscredit',
    'nordstrom card', 'nordstromcredit', 'jcpenney card',
    'lowes card', 'lowescredit', 'homedepot card', 'homedepotcredit',
    'bestbuy card', 'bestbuycredit', 'apple card', 'applecard',
    'gap card', 'gapcard', 'oldnavy card', 'bananarepublic card',
    'tjmaxx card', 'tjx rewards', 'marshalls card',
    'ross card', 'burlington card', 'belk card', 'dillards card',
    'jcrew card', 'express card', 'buckle card', 'torrid card',
    
    # --- GAS STATION CARDS ---
    'shell card', 'shellcredit', 'chevron card', 'texaco card',
    'exxon card', 'mobil card', 'bp card', 'bpcredit',
    'sunoco card', 'marathon card', 'speedway card', 'phillips66 card',
    'circlek card', 'conoco card', '76 card', 'valero card',
    'costco gas', 'samsclub gas', 'bjs gas',
    
    # --- BUSINESS CREDIT CARDS ---
    'chase ink', 'inkbusiness', 'amex business', 'businessgold',
    'businessplatinum', 'capital one spark', 'sparkbusiness',
    'citi business', 'bank of america business',
    
    # General card terms
    'bluecash', 'platinum', 'gold card', 'rewards card', 'cashback card',
    
    # === TRAVEL & AIRLINES (USA) ===
    'delta', 'united', 'americanairlines', 'aa.com', 'southwest',
    'jetblue', 'alaskaair', 'spiritairlines', 'frontierairlines',
    'hawaiianairlines', 'suncountry', 'allegiant', 'breeze',
    'skymiles', 'aadvantage', 'mileageplus', 'rapidrewards',
    'marriott', 'hilton', 'hyatt', 'ihg', 'wyndham', 'choicehotels',
    'bestwestern', 'motel6', 'laquinta', 'radisson', 'omni',
    'booking', 'expedia', 'hotels.com', 'kayak', 'priceline',
    'tripadvisor', 'trivago', 'orbitz', 'travelocity', 'hotwire',
    'airbnb', 'vrbo', 'vacasa', 'evolve', 'getaway',
    'uber', 'lyft', 'hertz', 'enterprise', 'avis', 'budget',
    'nationalcar', 'alamo', 'sixt', 'turo',
    
    # === CRAFT & HOBBY ===
    'michaels', 'joann', 'hobbylobby', 'acmoore',
    
    # === BOOKS & MEDIA ===
    'barnesandnoble', 'booksamillion', 'thriftbooks', 'abebooks',
    'amazon', 'kindle', 'audible', 'googlebooks', 'kobo',
    
    # === TOYS & GAMES ===
    'target', 'walmart', 'amazon', 'gamestop',
    'lego', 'hasbro', 'mattel', 'buildabear',
    
    # === SPORTING GOODS ===
    'dickssportinggoods', 'academy', 'rei', 'basspro', 'cabelas',
    'fieldandstream', 'sportsmanswarehouse', 'backcountry',
    'moosejaw', 'evo', 'steepandcheap',
    
    # === JEWELRY ===
    'jared', 'zales', 'kay', 'signet', 'tiffany', 'bluenile',
    'jamesallen', 'brilliantearth', 'pandora', 'swarovski',
    
    # === EYEWEAR ===
    'lenscrafters', 'pearlevision', 'visionworks', 'americas best',
    'warbyparker', 'zennioptical', 'eyebuydirect', 'glassesusa',
    
    # === MATTRESS & BEDDING ===
    'mattressfirm', 'sleepnumber', 'tempurpedic', 'casper', 'purple',
    'leesa', 'nectar', 'tuftandneedle', 'saatva', 'brooklyn bedding',
    
    # === BABY & KIDS ===
    'buybuybaby', 'carters', 'oshkosh', 'gymboree', 'childrenplace',
    
    # === WEDDING & GIFTS ===
    'zola', 'theknot', 'registry', 'blueprintregistry',
    
    # === FLOWERS & GIFTS ===
    'ftd', '1800flowers', 'proflowers', 'teleflora', 'bloomstoday',
    'ediblearrangements', 'harryanddavid', 'hickoryfarms',
    'fromyouflowers', 'bouqs', 'urbanstems', 'bloomnation',
    'floom', 'farmgirl flowers', 'venus et fleur',
    
    # === SUBSCRIPTION BOXES ===
    'birchbox', 'ipsy', 'boxycharm', 'fabfitfun', 'causebox',
    'stitchfix', 'trunkclub', 'renttherunway', 'nuuly', 'armoire',
    'barkbox', 'chewy goody box', 'meowbox', 'petbox',
    'dollar shave club', 'harrys', 'billie', 'athena club',
    'quip', 'hello products', 'native', 'grove collaborative',
    'butcher box', 'omaha steaks', 'snake river farms', 'crowd cow',
    'winc', 'firstleaf', 'bright cellars', 'naked wines',
    'craft beer club', 'tavour', 'beer drop',
    'book of the month', 'scribd', 'kindle unlimited',
    'masterclass', 'skillshare', 'coursera', 'linkedin learning',
    'curiosity stream', 'nebula', 'great courses',
    
    # === OUTDOOR & GARDEN ===
    'tractorsupply', 'fleetfarm', 'ruralkingsupply', 'orchards hardware',
    'the home depot', 'lowes', 'menards', 'ace hardware',
    
    # === CAMPING & OUTDOOR RECREATION ===
    'rei', 'basspro', 'cabelas', 'sportsmans warehouse',
    'backcountry', 'moosejaw', 'campmor', 'ems', 'sierra',
    'patagonia', 'northface', 'columbia', 'marmot', 'arcteryx',
    
    # === HUNTING & FIREARMS ===
    'basspro', 'cabelas', 'sportsmans warehouse', 'scheels',
    'academy', 'dicks', 'palmetto state armory', 'brownells',
    'midwayusa', 'budsgunshop', 'grabagun', 'kygunco',
    
    # === MUSIC & INSTRUMENTS ===
    'guitar center', 'samash', 'sweetwater', 'musiciansfriend',
    'zzounds', 'americanmusical', 'music & arts',
    
    # === ART SUPPLIES ===
    'blick', 'dickblick', 'jerrysartarama', 'utrechtart',
    'michaels', 'joann', 'hobbylobby',
    
    # === PARTY SUPPLIES ===
    'partycity', 'orientaltrading', 'shindigz', 'stumps',
    
    # === UNIFORMS & WORKWEAR ===
    'cintas', 'aramark', 'unifirst', 'dickies', 'carhartt',
    'red kap', 'chef works', 'scrubs and beyond', 'uniform advantage',
    
    # === RESALE / CONSIGNMENT ===
    'poshmark', 'thredup', 'therealreal', 'mercari', 'depop',
    'tradesy', 'vestiaire collective', 'rebag', 'fashionphile',
    'ebay', 'stockx', 'goat', 'grailed', 'offerup', 'letgo',
]

# Domains to EXCLUDE (social media, forums, newsletters)
EXCLUDED_DOMAINS = [
    'reddit', 'twitter', 'x.com', 'facebook', 'instagram', 'linkedin',
    'quora', 'medium', 'substack', 'mailchimp', 'hubspot',
    'github', 'gitlab', 'bitbucket', 'stackoverflow',
    'slack', 'discord', 'telegram', 'whatsapp',
    'replit', 'codepen', 'jsfiddle', 'codesandbox',
    'coursera', 'udemy', 'edx', 'skillshare',  # Educational (unless you want them)
    'meetup', 'eventbrite',
    'noreply', 'no-reply', 'donotreply', 'do-not-reply',
    'newsletter', 'digest', 'weekly', 'daily',
]

# ============================================
# MEMBERSHIP / SUBSCRIPTION PATTERNS (Service subscriptions)
# Amazon Prime, Netflix, Costco membership, etc.
# ============================================
MEMBERSHIP_PATTERNS = [
    r'\bmembership\s*(started|activated|renewed|confirmed|cancelled|is\s*now\s*active)\b',
    r'\bsubscription\s*(started|activated|renewed|confirmed|cancelled|is\s*now\s*active)\b',
    r'\byour\s*(premium|pro|plus)\s*(membership|subscription|plan)\b',
    r'\bwelcome\s*to\s*(amazon\s*prime|netflix|spotify|disney|costco|hulu|hbo)\b',
    r'\btrial\s*(started|begins|activated|ends|expiring)\b',
    r'\bfree\s*trial\b',
    r'\brenewal\s*(notice|reminder|confirmation)\b',
    r'\bauto[-\s]?renew(al|ed)?\b',
    r'\bbilling\s*(statement|summary|receipt|invoice)\b',
    r'\bmonthly\s*(plan|subscription|membership)\b',
    r'\bannual\s*(plan|subscription|membership)\b',
    r'\bcancel(led|lation)?\s*(subscription|membership)\b',
    r'\brecurring\s*(charge|payment|billing)\b',
    r'\bmembership\s*(has|is)\s*(started|active|now\s*active)\b',
    r'\bgold\s*star\s*membership\b',
    r'\bprime\s*member(ship)?\b',
    r'\bwelcome\s*to\s*\w+!?\s*your\s*.*membership\b',
    r'\b(netflix|spotify|hulu|disney\+?|hbo\s*max|amazon\s*prime)\s*(subscription|membership|account)\b',
    r'\bstreaming\s*(subscription|membership)\b',
]

# ============================================
# OFFER PATTERNS (Credit cards, rewards cards, benefits)
# Amex, Delta SkyMiles, Chase, etc.
# ============================================
OFFER_PATTERNS = [
    r'\bcard\s*benefits\b.*\b(activated|active|now\s*active)\b',
    r'\bbenefits\s*(are|is)\s*now\s*active\b',
    r'\bplatinum\s*(card|membership|member|business)\b',
    r'\bgold\s*card\b',
    r'\bskymiles\b',
    r'\brewards?\s*(card|program)\s*(activated|active|benefits)\b',
    r'\bcredit\s*card\s*(benefits|rewards|activated|welcome)\b',
    r'\b(amex|american\s*express)\b.*\b(card|benefits|activated)\b',
    r'\bblue\s*cash\b',
    r'\b(visa|mastercard|discover)\s*(card|benefits|rewards)\b',
    r'\b(chase|citi|capital\s*one)\s*(card|benefits|rewards)\b',
    r'\bfrequent\s*flyer\b',
    r'\bairline\s*(miles|rewards|card)\b',
    r'\bmiles\s*(card|rewards|earned)\b',
    r'\bpoints\s*(card|rewards|earned|balance)\b',
    r'\byour\s*card\s*(is|has)\s*(ready|active|activated)\b',
    r'\bwelcome\s*(to\s*your|kit|bonus)\b.*\b(card|rewards)\b',
    r'\bcardmember\b',
    r'\bcard\s*member\s*(benefits|rewards|exclusive)\b',
]

# ============================================
# COUPON PATTERNS (Discounts, promo codes, sales)
# ============================================
COUPON_PATTERNS = [
    r'\b\d+%\s*off\b',
    r'\bflat\s*\d+%?\s*(off|discount)\b',
    r'\bsave\s*(up\s*to\s*)?\$?\₹?\d+',
    r'\bget\s*\$?\₹?\d+\s*off\b',
    r'\bpromo\s*code\b',
    r'\bcoupon\s*code\b',
    r'\bdiscount\s*code\b',
    r'\buse\s*code\b',
    r'\bredeem\s*(code|coupon|offer)\b',
    r'\bcashback\b',
    r'\bcash\s*back\b',
    r'\bfree\s*shipping\b',
    r'\bfree\s*delivery\b',
    r'\bbuy\s*\d+\s*get\s*\d+\b',
    r'\bbogo\b',
    r'\bflash\s*sale\b',
    r'\blimited\s*time\s*(offer|deal|sale)\b',
    r'\bexclusive\s*(offer|deal|discount|sale)\b',
    r'\bspecial\s*(offer|deal|discount|price)\b',
    r'\bclearance\s*sale\b',
    r'\bend\s*of\s*season\s*sale\b',
    r'\bfestival\s*(sale|offer)\b',
    r'\bholiday\s*(sale|offer|deal)\b',
    r'\bblack\s*friday\b',
    r'\bcyber\s*monday\b',
    r'\bprime\s*day\b',
    r'\bbig\s*(billion|sale|savings)\b',
    r'\bgift\s*card\b',
    r'\bvoucher\b',
    r'\bshopping\s*(fest|festival|carnival)\b',
    r'\border\s*now\s*&?\s*(get|save)\b',
    r'\bhurry!?\s*(limited|offer|ends)\b',
    r'\bdon\'?t\s*miss\s*(this|out|the)\b',
    r'\blast\s*chance\b',
    r'\bends?\s*(today|tonight|tomorrow|soon|in\s*\d+)\b',
]

# Compile patterns for better performance
MEMBERSHIP_REGEX = re.compile('|'.join(MEMBERSHIP_PATTERNS), re.IGNORECASE)
OFFER_REGEX = re.compile('|'.join(OFFER_PATTERNS), re.IGNORECASE)
COUPON_REGEX = re.compile('|'.join(COUPON_PATTERNS), re.IGNORECASE)


def is_shopping_domain(sender: str) -> bool:
    """
    Check if the sender is from a known shopping/commercial domain.
    
    Args:
        sender: Email sender (e.g., "Amazon <noreply@amazon.com>")
    
    Returns:
        True if from a shopping domain
    """
    sender_lower = sender.lower()
    
    # Check for shopping domains
    for domain in SHOPPING_DOMAINS:
        if domain in sender_lower:
            return True
    
    return False


def is_excluded_domain(sender: str) -> bool:
    """
    Check if the sender should be excluded (social media, forums, etc.)
    
    Args:
        sender: Email sender
    
    Returns:
        True if should be excluded
    """
    sender_lower = sender.lower()
    
    for domain in EXCLUDED_DOMAINS:
        if domain in sender_lower:
            return True
    
    return False


def is_membership(text: str) -> bool:
    """
    Check if text contains membership/subscription related content.
    (Amazon Prime, Netflix, Costco, etc.)
    
    Args:
        text: Email content (subject + body)
    
    Returns:
        True if membership-related content detected
    """
    if not text:
        return False
    return bool(MEMBERSHIP_REGEX.search(text))


def is_offer(text: str) -> bool:
    """
    Check if text contains credit card/rewards card related content.
    (Amex, Delta SkyMiles, Chase rewards, etc.)
    
    Args:
        text: Email content (subject + body)
    
    Returns:
        True if offer/card-related content detected
    """
    if not text:
        return False
    return bool(OFFER_REGEX.search(text))


def is_coupon(text: str) -> bool:
    """
    Check if text contains discount/promo/coupon related content.
    (50% off, promo codes, flash sales, etc.)
    
    Args:
        text: Email content (subject + body)
    
    Returns:
        True if coupon-related content detected
    """
    if not text:
        return False
    return bool(COUPON_REGEX.search(text))


def get_membership_matches(text: str) -> List[str]:
    """
    Get all membership-related matches found in text.
    
    Args:
        text: Email content (subject + body)
    
    Returns:
        List of matched patterns/keywords
    """
    if not text:
        return []
    matches = MEMBERSHIP_REGEX.findall(text)
    # Clean up tuple results and remove empty strings
    cleaned = []
    for m in matches:
        if isinstance(m, tuple):
            cleaned.extend([x for x in m if x])
        elif m:
            cleaned.append(m)
    return list(set(cleaned))


def get_offer_matches(text: str) -> List[str]:
    """
    Get all offer/credit card-related matches found in text.
    
    Args:
        text: Email content (subject + body)
    
    Returns:
        List of matched patterns/keywords
    """
    if not text:
        return []
    matches = OFFER_REGEX.findall(text)
    # Clean up tuple results and remove empty strings
    cleaned = []
    for m in matches:
        if isinstance(m, tuple):
            cleaned.extend([x for x in m if x])
        elif m:
            cleaned.append(m)
    return list(set(cleaned))


def get_coupon_matches(text: str) -> List[str]:
    """
    Get all coupon/discount-related matches found in text.
    
    Args:
        text: Email content (subject + body)
    
    Returns:
        List of matched patterns/keywords
    """
    if not text:
        return []
    matches = COUPON_REGEX.findall(text)
    # Clean up tuple results and remove empty strings
    cleaned = []
    for m in matches:
        if isinstance(m, tuple):
            cleaned.extend([x for x in m if x])
        elif m:
            cleaned.append(m)
    return list(set(cleaned))


def categorize_email(text: str, sender: str = "") -> Tuple[str, List[str]]:
    """
    Categorize email based on content and sender.
    
    Categories:
    - 'Membership': Service subscriptions (Amazon Prime, Netflix, Costco, etc.)
    - 'Offer': Credit card benefits/rewards (Amex, Delta SkyMiles, etc.)
    - 'Coupon': Discounts, promo codes, sales
    - 'Excluded': Social media, forums, newsletters
    - 'Normal': Other emails
    
    Args:
        text: Email content (subject + body)
        sender: Email sender for domain filtering
    
    Returns:
        Tuple of (category, matched_keywords)
    """
    # Check if sender should be excluded
    if sender and is_excluded_domain(sender):
        return ('Excluded', [])
    
    is_mem = is_membership(text)
    is_off = is_offer(text)
    is_coup = is_coupon(text)
    
    matches = []
    
    # Priority: Membership > Offer > Coupon
    # If it's a membership email (Prime, Costco, Netflix), classify as Membership
    if is_mem:
        matches = get_membership_matches(text)
        return ('Membership', matches)
    # If it's a credit card/rewards email, classify as Offer
    elif is_off:
        matches = get_offer_matches(text)
        return ('Offer', matches)
    # If it's a discount/promo email, classify as Coupon
    elif is_coup:
        matches = get_coupon_matches(text)
        return ('Coupon', matches)
    else:
        return ('Normal', [])


def analyze_text(text: str, sender: str = "") -> Dict:
    """
    Comprehensive text analysis for membership, offers, and coupons.
    
    Args:
        text: Email content (subject + body)
        sender: Email sender for domain filtering
    
    Returns:
        Dictionary with analysis results
    """
    category, matches = categorize_email(text, sender)
    
    return {
        'is_membership': is_membership(text),
        'is_offer': is_offer(text),
        'is_coupon': is_coupon(text),
        'is_shopping_domain': is_shopping_domain(sender) if sender else False,
        'is_excluded': is_excluded_domain(sender) if sender else False,
        'category': category,
        'membership_matches': get_membership_matches(text),
        'offer_matches': get_offer_matches(text),
        'coupon_matches': get_coupon_matches(text),
        'all_matches': matches
    }


# ============================================
# TEST FUNCTION
# ============================================
def test_patterns():
    """Test the pattern detection with sample texts."""
    
    test_cases = [
        # Membership tests (Service subscriptions)
        ("Welcome to Amazon Prime – Your Membership Has Started", "amazon@amazon.com", "Membership"),
        ("Your Netflix subscription has been renewed", "netflix@netflix.com", "Membership"),
        ("Welcome to Costco! Your Gold Star Membership Is Now Active", "costco@costco.com", "Membership"),
        ("Your Spotify Premium subscription is active", "spotify@spotify.com", "Membership"),
        ("Disney+ free trial ends tomorrow", "disney@disney.com", "Membership"),
        
        # Offer tests (Credit cards, rewards cards)
        ("Your Delta SkyMiles Platinum Business Card Benefits Are Now Active", "delta@delta.com", "Offer"),
        ("Your American Express Blue Cash Everyday Card Benefits Are Now Active", "amex@amex.com", "Offer"),
        ("Welcome to your Chase Sapphire Rewards Card", "chase@chase.com", "Offer"),
        ("Your Visa Platinum Card is ready", "visa@visa.com", "Offer"),
        ("Earn miles with your airline rewards card", "airline@airline.com", "Offer"),
        
        # Coupon tests (Discounts, promo codes, sales)
        ("50% OFF - Limited time offer!", "deals@flipkart.com", "Coupon"),
        ("Use promo code SAVE20 for flat 20% discount", "myntra@myntra.com", "Coupon"),
        ("Flash Sale - Free shipping on all orders!", "shop@amazon.com", "Coupon"),
        ("Get ₹500 cashback on your next purchase", "paytm@paytm.com", "Coupon"),
        ("Big Billion Days Sale starts now!", "flipkart@flipkart.com", "Coupon"),
        ("Don't miss out - Last chance for 30% off!", "store@store.com", "Coupon"),
        
        # Excluded (social media, forums)
        ("Check out this deal on Reddit", "noreply@reddit.com", "Excluded"),
        ("Your weekly Replit newsletter", "contact@replit.com", "Excluded"),
        
        # Normal
        ("Meeting reminder for tomorrow", "calendar@google.com", "Normal"),
        ("Your order has shipped", "orders@shipping.com", "Normal"),
    ]
    
    print("=" * 60)
    print("PATTERN DETECTION TEST")
    print("=" * 60)
    print("\nCategories:")
    print("  • Membership: Service subscriptions (Prime, Netflix, Costco)")
    print("  • Offer: Credit card benefits (Amex, Delta, Chase)")
    print("  • Coupon: Discounts & promo codes (50% off, sales)")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for text, sender, expected in test_cases:
        result = analyze_text(text, sender)
        actual = result['category']
        status = "✓" if actual == expected else "✗"
        
        if actual == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n{status} Text: \"{text[:45]}...\"" if len(text) > 45 else f"\n{status} Text: \"{text}\"")
        print(f"   Sender: {sender}")
        print(f"   Expected: {expected} | Got: {actual}")
        if result['all_matches']:
            print(f"   Matches: {result['all_matches']}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)


# For testing this module directly
if __name__ == "__main__":
    test_patterns()
