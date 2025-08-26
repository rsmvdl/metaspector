# metaspector/matrices/language_matrix.py
# !/usr/bin/env python3

from typing import List, Tuple, Optional


def get_language_matrix() -> List[Tuple[str, ...]]:
    """Returns the comprehensive language matrices."""
    language_matrix_references = [
        ("aa-ET", "aa", "aar", "Afar", "Qafar af (Ethiopia)", "Ethiopia"),
        ("ab-GE", "ab", "abk", "Abkhazian", "аҧсуа бызшәа (Georgia)", "Georgia"),
        ("ae-IR", "ae", "ave", "Avestan", "Avesta (Iran)", "Iran"),
        ("af-ZA", "af", "afr", "Afrikaans", "Afrikaans (South Africa)", "South Africa"),
        ("ak-GH", "ak", "aka", "Akan", "Akan (Ghana)", "Ghana"),
        ("am-ET", "am", "amh", "Amharic", "አማርኛ (Amarəñña)", "Ethiopia"),
        ("an-ES", "an", "arg", "Aragonese", "Aragonés (Spain)", "Spain"),
        ("ar-SA", "ar", "ara", "Arabic", "العربية (Saudi Arabia)", "Saudi Arabia"),
        ("as-IN", "as", "asm", "Assamese", "অসমীয়া (Ôxômiya)", "India"),
        ("av-RU", "av", "ava", "Avaric", "Авар мацӏ (Avar maⱬ)", "Russia"),
        ("ay-BO", "ay", "aym", "Aymara", "Aymar aru (Bolivia)", "Bolivia"),
        ("az-AZ", "az", "aze", "Azerbaijani", "Azərbaycan dili (Azerbaijan)", "Azerbaijan"),
        ("ba-RU", "ba", "bak", "Bashkir", "Башҡорт теле (Russia)", "Russia"),
        ("be-BY", "be", "bel", "Belarusian", "беларуская мова (Belarus)", "Belarus"),
        ("bg-BG", "bg", "bul", "Bulgarian", "български език (Bulgaria)", "Bulgaria"),
        ("bi-VU", "bi", "bis", "Bislama", "Bislama (Vanuatu)", "Vanuatu"),
        ("bm-ML", "bm", "bam", "Bambara", "Bamanankan (Mali)", "Mali"),
        ("bn-BD", "bn", "ben", "Bengali", "বাংলা (Bangla)", "Bangladesh"),
        ("bo-CN", "bo", "bod", "Tibetan", "བོད་ཡིག། (China)", "China"),
        ("br-FR", "br", "bre", "Breton", "Brezhoneg (France)", "France"),
        ("bs-BA", "bs", "bos", "Bosnian", "Bosanski jezik (Bosnia and Herzegovina)", "Bosnia and Herzegovina"),
        ("ca-ES", "ca", "cat", "Catalan", "Català (Spain)", "Spain"),
        ("ce-RU", "ce", "che", "Chechen", "Нохчийн мотт (Russia)", "Russia"),
        ("ch-GU", "ch", "cha", "Chamorro", "Chamorru (Guam)", "Guam"),
        ("co-FR", "co", "cos", "Corsican", "Corsu (France)", "France"),
        ("cr-CA", "cr", "cre", "Cree", "ᓀᐦᐃᔭᐍᐏᐣ (Canada)", "Canada"),
        ("cs-CZ", "cs", "ces", "Czech", "Český (Czechia)", "Czechia"),
        ("cu-BG", "cu", "chu", "Church Slavic", "Словѣньскъ (Bulgaria)", "Bulgaria"),
        ("cv-RU", "cv", "chv", "Chuvash", "Чӑвашла (Russia)", "Russia"),
        ("cy-GB", "cy", "cym", "Welsh", "Cymraeg (United Kingdom)", "United Kingdom"),
        ("da-DK", "da", "dan", "Danish", "Dansk (Denmark)", "Denmark"),
        ("de-DE", "de", "deu", "German", "Deutsch (Deutschland)", "Germany"),
        ("de-AT", "de", "deu", "German (Austria)", "Deutsch (Österreich)", "Austria"),
        ("de-CH", "de", "deu", "German (Switzerland)", "Deutsch (Schweiz)", "Switzerland"),
        ("de-LI", "de", "deu", "German (Liechtenstein)", "Deutsch (Liechtenstein)", "Liechtenstein"),
        ("en-US", "en", "eng", "English", "English (United States)", "United States of America"),
        ("en-GB", "en", "eng", "English (United Kingdom)", "English (United Kingdom)", "United Kingdom"),
        ("en-AU", "en", "eng", "English (Australia)", "English (Australia)", "Australia"),
        ("en-CA", "en", "eng", "English (Canada)", "English (Canada)", "Canada"),
        ("dv-MV", "dv", "div", "Divehi", "ދިވެހި (Divehi)", "Maldives"),
        ("dz-BT", "dz", "dzo", "Dzongkha", "རྫོང་ཁ་ (Dzongkha)", "Bhutan"),
        ("ee-GH", "ee", "ewe", "Ewe", "Ɛʋɛgbɛ (Ghana)", "Ghana"),
        ("el-GR", "el", "ell", "Greek", "Ελληνικά (Greece)", "Greece"),
        ("eo-001", "eo", "epo", "Esperanto", "Esperanto (International)", "International"),
        ("es-ES", "es", "spa", "Spanish", "Español (España)", "Spain"),
        ("es-419", "es", "spa", "Spanish (Latin America)", "Español (Latinoamérica)", "Latin America"),
        ("es-MX", "es", "spa", "Spanish (Mexico)", "Español (México)", "Mexico"),
        ("es-US", "es", "spa", "Spanish (United States)", "Español (Estados Unidos)", "United States of America"),
        ("et-EE", "et", "est", "Estonian", "Eesti keel (Estonia)", "Estonia"),
        ("eu-ES", "eu", "eus", "Basque", "Euskara (Spain)", "Spain"),
        ("fa-IR", "fa", "fas", "Persian", "فارسی (Iran)", "Iran"),
        ("ff-SN", "ff", "ful", "Fula", "Fulfulde (Senegal)", "Senegal"),
        ("fi-FI", "fi", "fin", "Finnish", "Suomi (Finland)", "Finland"),
        ("fil-PH", "fil", "phi", "Filipino", "Filipino (Philippines)", "Philippines"),
        ("fj-FJ", "fj", "fij", "Fijian", "Na Vosa Vakaviti (Fiji)", "Fiji"),
        ("fo-FO", "fo", "fao", "Faroese", "Føroyskt (Faroe Islands)", "Faroe Islands"),
        ("fr-FR", "fr", "fra", "French", "Français (France)", "France"),
        ("fr-CA", "fr", "fra", "French (Canada)", "Français (Canada)", "Canada"),
        ("fy-NL", "fy", "fry", "Western Frisian", "Frysk (Netherlands)", "Netherlands"),
        ("ga-IE", "ga", "gle", "Irish", "Gaeilge (Ireland)", "Ireland"),
        ("gd-GB", "gd", "gla", "Scottish Gaelic", "Gàidhlig (United Kingdom)", "United Kingdom"),
        ("gl-ES", "gl", "glg", "Galician", "Galego (Spain)", "Spain"),
        ("gn-PY", "gn", "grn", "Guaraní", "Avañe'ẽ (Paraguay)", "Paraguay"),
        ("gu-IN", "gu", "guj", "Gujarati", "ગુજરાત (Gujarātī)", "India"),
        ("gv-IM", "gv", "glv", "Manx", "Gaelg (Isle of Man)", "Isle of Man"),
        ("ha-NG", "ha", "hau", "Hausa", "هَوُس (Hausa)َ", "Nigeria"),
        ("he-IL", "he", "heb", "Hebrew", "עברית (Israel)", "Israel"),
        ("hi-IN", "hi", "hin", "Hindi", "मानक हिन्दी (India)", "India"),
        ("ho-PG", "ho", "hmo", "Hiri Motu", "Hiri Motu (Papua New Guinea)", "Papua New Guinea"),
        ("hr-HR", "hr", "hrv", "Croatian", "Hrvatski (Croatia)", "Croatia"),
        ("ht-HT", "ht", "hat", "Haitian Creole", "Kreyòl Ayisyen (Haiti)", "Haiti"),
        ("hu-HU", "hu", "hun", "Hungarian", "Magyar (Hungary)", "Hungary"),
        ("hy-AM", "hy", "hye", "Armenian", "հայերեն (Hayeren)", "Armenia"),
        ("hz-NA", "hz", "her", "Herero", "Otjiherero (Namibia)", "Namibia"),
        ("ia-001", "ia", "ina", "Interlingua", "Interlingua (International)", "International"),
        ("id-ID", "id", "ind", "Indonesian", "Bahasa (Indonesia)", "Indonesia"),
        ("ie-001", "ie", "ile", "Interlingue", "Interlingue (International)", "International"),
        ("ig-NG", "ig", "ibo", "Igbo", "Igbo (Nigeria)", "Nigeria"),
        ("ii-CN", "ii", "iii", "Nuosu", "Nuosu, ꆈꌠꉙ (China)", "China"),
        ("ik-US", "ik", "ipk", "Inupiaq", "Iñupiaq (United States of America)", "United States of America"),
        ("io-001", "io", "ido", "Ido", "Ido (International)", "International"),
        ("is-IS", "is", "isl", "Icelandic", "Íslenska (Iceland)", "Iceland"),
        ("it-IT", "it", "ita", "Italian", "Italiano (Italy)", "Italy"),
        ("iu-CA", "iu", "iku", "Inuktitut", "ᐃᓄᒃᑎᑐᑦ (Inuktitut)", "Canada"),
        ("ja-JP", "ja", "jpn", "Japanese", "日本語 (Japan)", "Japan"),
        ("jv-ID", "jv", "jav", "Javanese", "Jawa (Indonesia)", "Indonesia"),
        ("ka-GE", "ka", "kat", "Georgian", "ქართული (Georgia)", "Georgia"),
        ("kg-CD", "kg", "kon", "Kongo", "KiKongo (Congo, DR)", "Congo, DR"),
        ("ki-KE", "ki", "kik", "Kikuyu", "Gĩgĩkũyũ (Kenya)", "Kenya"),
        ("kj-NA", "kj", "kua", "Kwanyama", "Oshikwanyama (Namibia)", "Namibia"),
        ("kk-KZ", "kk", "kaz", "Kazakh", "қазақ тілі (Kazakhstan)", "Kazakhstan"),
        ("kl-GL", "kl", "kal", "Kalaallisut", "Kalaallisut (Greenland)", "Greenland"),
        ("km-KH", "km", "khm", "Khmer", "ខ្មែរ (Khmer)", "Cambodia"),
        ("kn-IN", "kn", "kan", "Kannada", "ಕನ್ನಡ (India)", "India"),
        ("ko-KR", "ko", "kor", "Korean", "한국말 (Korea)", "Korea"),
        ("kr-NG", "kr", "kau", "Kanuri", "Kanuri (Nigeria)", "Nigeria"),
        ("ks-IN", "ks", "kas", "Kashmiri", "کٲشُر (Koshur)", "India"),
        ("ku-TR", "ku", "kur", "Kurdish", "Kurdî (Turkiye)", "Turkiye"),
        ("kv-RU", "kv", "kom", "Komi", "коми кыв (Russia)", "Russia"),
        ("kw-GB", "kw", "cor", "Cornish", "Kernewek (United Kingdom)", "United Kingdom"),
        ("ky-KG", "ky", "kir", "Kyrgyz", "кыргыз тили (Kyrgyzstan)", "Kyrgyzstan"),
        ("la-VA", "la", "lat", "Latin", "Latina (Holy See)", "Holy See"),
        ("lb-LU", "lb", "ltz", "Luxembourgish", "Lëtzebuergesch (Luxembourg)", "Luxembourg"),
        ("lg-UG", "lg", "lug", "Ganda", "Luganda (Uganda)", "Uganda"),
        ("li-NL", "li", "lim", "Limburgan", "Lèmburgs (Netherlands)", "Netherlands"),
        ("ln-CD", "ln", "lin", "Lingala", "Lingala (Congo, DR)", "Congo, DR"),
        ("lo-LA", "lo", "lao", "Lao", "ພາສາລາວ (Lao People's Democratic Republic)", "Lao People's Democratic Republic"),
        ("lt-LT", "lt", "lit", "Lithuanian", "Lietuviškai (Lithuania)", "Lithuania"),
        ("lu-CD", "lu", "lub", "Luba-Katanga", "Kiluba (Congo, DR)", "Congo, DR"),
        ("lv-LV", "lv", "lav", "Latvian", "Latviešu (Latvia)", "Latvia"),
        ("mg-MG", "mg", "mlg", "Malagasy", "Fiteny (Madagascar)", "Madagascar"),
        ("mh-MH", "mh", "mah", "Marshallese", "Kajin (Marshall Islands)", "Marshall Islands"),
        ("mi-NZ", "mi", "mri", "Maori", "te reo Māori (New Zealand)", "New Zealand"),
        ("mk-MK", "mk", "mkd", "Macedonian", "македонски (North Macedonia)", "North Macedonia"),
        ("ml-IN", "ml", "mal", "Malayalam", "മലയാളം (India)", "India"),
        ("mn-MN", "mn", "mon", "Mongolian", "Монгол (Mongolia)", "Mongolia"),
        ("mo-MD", "mo", "mol", "Moldavian", "молдовеняскэ (Moldova)", "Moldova"),
        ("mr-IN", "mr", "mar", "Marathi", "मराठी (India)", "India"),
        ("ms-MY", "ms", "msa", "Malay", "Bahasa Melayu (Malaysia)", "Malaysia"),
        ("mt-MT", "mt", "mlt", "Maltese", "Malti (Malta)", "Malta"),
        ("my-MM", "my", "mya", "Burmese", "မြန်မာ (Myanmar)", "Myanmar"),
        ("na-NR", "na", "nau", "Nauru", "Naoero (Nauru)", "Nauru"),
        ("nb-NO", "nb", "nob", "Norwegian Bokmål", "Norsk bokmål (Norway)", "Norway"),
        ("nd-ZW", "nd", "nde", "North Ndebele", "isiNdebele (Zimbabwe)", "Zimbabwe"),
        ("ne-NP", "ne", "nep", "Nepali", "नेपाली (Nepal)", "Nepal"),
        ("ng-NA", "ng", "ndo", "Ndonga", "Oshindonga (Namibia)", "Namibia"),
        ("nl-NL", "nl", "nld", "Dutch", "Nederlands (Netherlands)", "Netherlands"),
        ("nn-NO", "nn", "nno", "Norwegian Nynorsk", "Norsk nynorsk (Norway)", "Norway"),
        ("no-NO", "no", "nor", "Norwegian", "Norsk (Norway)", "Norway"),
        ("nr-ZA", "nr", "nbl", "South Ndebele", "IsiNdebele (South Africa)", "South Africa"),
        ("nv-US", "nv", "nav", "Navajo", "Diné Bizaad (United States of America)", "United States of America"),
        ("ny-MW", "ny", "nya", "Chichewa", "Chicheŵa (Malawi)", "Malawi"),
        ("oc-FR", "oc", "oci", "Occitan", "Occitan (France)", "France"),
        ("oj-CA", "oj", "oji", "Ojibwe", "ᐊᓂᔑᓈᐯᒧᐎᓐ (Canada)", "Canada"),
        ("om-ET", "om", "orm", "Oromo", "Afaan Oromoo (Ethiopia)", "Ethiopia"),
        ("or-IN", "or", "ori", "Oriya", "ଓଡ଼ିଆ (Russia)", "India"),
        ("os-RU", "os", "oss", "Ossetian", "ирон æвзаг (Russia)", "Russia"),
        ("pa-IN", "pa", "pan", "Panjabi", "ਪੰਜਾਬੀ (India)", "India"),
        ("pi-IN", "pi", "pli", "Pali", "पालि (India)", "India"),
        ("pl-PL", "pl", "pol", "Polish", "Polski (Poland)", "Poland"),
        ("ps-AF", "ps", "pus", "Pashto", "(Afghanistan) پښ토", "Afghanistan"),
        ("pt-PT", "pt", "por", "Portuguese", "Português (Portugal)", "Portugal"),  # Default
        ("pt-BR", "pt", "por", "Portuguese (Brazil)", "Português (Brasil)", "Brazil"),
        ("qu-PE", "qu", "que", "Quechua", "Runa Simi (Peru)", "Peru"),
        ("rc-RE", "rc", "rcf", "Réunion Creole", "Kréol rénioné (Reunion)", "Reunion"),
        ("rm-CH", "rm", "roh", "Romansh", "Rumantsch (Switzerland)", "Switzerland"),
        ("rn-BI", "rn", "run", "Ikirundi", "Burundi (Burundi)", "Burundi"),
        ("ro-RO", "ro", "ron", "Romanian", "Româneşte (Romania)", "Romania"),
        ("ru-RU", "ru", "rus", "Russian", "русский (Russia)", "Russia"),
        ("rw-RW", "rw", "kin", "Kinyarwanda", "Ikinyarwanda (Rwanda)", "Rwanda"),
        ("sa-IN", "sa", "san", "Sanskrit", "संस्कृतम् (India)", "India"),
        ("sc-IT", "sc", "srd", "Sardinian", "Sardu (Italy)", "Italy"),
        ("sd-PK", "sd", "snd", "Sindhi", "سنڌي (Pakistan)", "Pakistan"),
        ("se-NO", "se", "sme", "Northern Sami", "Sámegiella (Norway)", "Norway"),
        ("sg-CF", "sg", "sag", "Sango", "Sango (Central African Republic)", "Central African Republic"),
        ("sh-BA", "sh", "hbs", "Serbo-Croatian", "Srpskohrvatski (Bosnia and Herzegovina)", "Bosnia and Herzegovina"),
        ("si-LK", "si", "sin", "Sinhala", "සිංහල (Sri Lanka)", "Sri Lanka"),
        ("sk-SK", "sk", "slk", "Slovak", "Slovenčina (Slovakia)", "Slovakia"),
        ("sl-SI", "sl", "slv", "Slovenian", "Slovenščina (Slovenia)", "Slovenia"),
        ("sm-WS", "sm", "smo", "Samoan", "Gagana (Samoa)", "Samoa"),
        ("sn-ZW", "sn", "sna", "Shona", "Chishona (Zimbabwe)", "Zimbabwe"),
        ("so-SO", "so", "som", "Somali", "Af-Soomaali (Somalia)", "Somalia"),
        ("sq-AL", "sq", "sqi", "Albanian", "Shqip (Albania)", "Albania"),
        ("sr-RS", "sr", "srp", "Serbian", "српски (Serbia)", "Serbia"),
        ("ss-SZ", "ss", "ssw", "Swati", "siSwati (Eswatini)", "Eswatini"),
        ("st-LS", "st", "sot", "Southern Sotho", "Sesotho (Lesotho)", "Lesotho"),
        ("su-ID", "su", "sun", "Sundanese", "Basa Sunda (Indonesia)", "Indonesia"),
        ("sv-SE", "sv", "swe", "Swedish", "Svenska (Sweden)", "Sweden"),
        ("sw-KE", "sw", "swa", "Swahili", "Kiswahili (Kenya)", "Kenya"),
        ("ta-IN", "ta", "tam", "Tamil", "தமிழ் (India)", "India"),
        ("te-IN", "te", "tel", "తెలుగు (India)", "India"),
        ("tg-TJ", "tg", "tgk", "Tajik", "тоҷикӣ (Tojiki - Tajikistan)", "Tajikistan"),
        ("th-TH", "th", "tha", "Thai", "ภาษาไทย‎ (Thailand)", "Thailand"),
        ("ti-ER", "ti", "tir", "Tigrinya", "ትግርኛ (Tigrinya - Eritrea)", "Eritrea"),
        ("tk-TM", "tk", "tuk", "Turkmen", "Türkmençe (Turkmenistan)", "Turkmenistan"),
        ("tl-PH", "tl", "tgl", "Tagalog", "Tagalog (Philippines)", "Philippines"),
        ("tn-BW", "tn", "tsn", "Tswana", "Setswana (Botswana)", "Botswana"),
        ("to-TO", "to", "ton", "Tongan", "Faka (Tonga)", "Tonga"),
        ("tr-TR", "tr", "tur", "Turkish", "Türkçe (Turkiye)", "Turkiye"),
        ("ts-ZA", "ts", "tso", "Tsonga", "Xitsonga (South Africa)", "South Africa"),
        ("tt-RU", "tt", "tat", "Tatar", "татарча (Russia)", "Russia"),
        ("tw-GH", "tw", "twi", "Twi", "Twi (Ghana)", "Ghana"),
        ("ty-PF", "ty", "tah", "Tahitian", "Reo Tahiti (French Polynesia)", "French Polynesia"),
        ("zh-CN", "zh", "zho", "Chinese (Simplified)", "中文 (中国大陆 - China)", "China"),  # Default
        ("zh-TW", "zh", "zho", "Chinese (Traditional)", "中文 (臺灣 - Taiwan)", "Taiwan"),
        ("zh-HK", "zh", "zho", "Chinese (Hong Kong)", "中文 (香港 - Hong Kong)", "Hong Kong"),
        ("ug-CN", "ug", "uig", "Uyghur", "ئۇيغۇرچە (China - Uyghurche)", "China"),
        ("uk-UA", "uk", "ukr", "Ukrainian", "українська (Ukraine)", "Ukraine"),
        ("ur-PK", "ur", "urd", "Urdu", "اردو (Pakistan - Urdū)", "Pakistan"),
        ("uz-UZ", "uz", "uzb", "Uzbek", "O'zbek (Uzbekistan)", "Uzbekistan"),
        ("ve-ZA", "ve", "ven", "Venda", "Tshivenḓa (South Africa)", "South Africa"),
        ("vi-VN", "vi", "vie", "Vietnamese", "Việt (Viet Nam)", "Viet Nam"),
        ("vo-001", "vo", "vol", "Volapük", "Volapük (International)", "International"),
        ("wa-BE", "wa", "wln", "Walloon", "Walon (Belgium)", "Belgium"),
        ("wo-SN", "wo", "wol", "Wolof", "Wolof (Senegal)", "Senegal"),
        ("xh-ZA", "xh", "xho", "Xhosa", "isiXhosa (South Africa)", "South Africa"),
        ("yi-001", "yi", "yid", "Yiddish", "ייִדיש (International)", "International"),
        ("yo-NG", "yo", "yor", "Yoruba", "Yorùbá (Nigeria)", "Nigeria"),
        ("za-CN", "za", "zha", "Zhuang", "Saɯ cueŋƅ (China)", "China"),
        ("zu-ZA", "zu", "zul", "Zulu", "isiZulu (South Africa)", "South Africa"),
    ]
    return language_matrix_references


_matrix = get_language_matrix()

# Map BCP 47 code (e.g., "en-US") to its long name ("English (United States)")
_bcp47_map = {entry[0]: entry[4] for entry in _matrix}

# Map ISO 639-2/B code (e.g., "eng") to its long name ("English")
# We use the designated default for this mapping
_iso639_2_defaults = {
    "deu": "de-DE",
    "eng": "en-US",
    "spa": "es-ES",
    "fra": "fr-FR",
    "por": "pt-PT",
    "zho": "zh-CN",
}
_iso639_2_map = {
    code: _bcp47_map.get(bcp47) for code, bcp47 in _iso639_2_defaults.items()
}

# Map for 2-letter codes to their designated default BCP 47 code
_iso639_1_defaults = {
    "de": "de-DE",
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "pt": "pt-PT",
    "zh": "zh-CN",
}


def get_long_language_name(code: str) -> Optional[str]:
    """
    Looks up the long, descriptive language name from various codes.
    - BCP 47 (e.g., "en-US")
    - ISO 639-2/B (e.g., "eng")
    - ISO 639-1 (e.g., "en"), respecting designated defaults.
    """
    if not code:
        return None

    # 1. Direct BCP 47 match (most specific)
    if "-" in code and code in _bcp47_map:
        return _bcp47_map[code]

    # 2. ISO 639-2/B (3-letter) match
    if len(code) == 3 and code in _iso639_2_map:
        return _iso639_2_map[code]

    # 3. ISO 639-1 (2-letter) match using defaults
    if len(code) == 2 and code in _iso639_1_defaults:
        default_bcp47 = _iso639_1_defaults[code]
        return _bcp47_map.get(default_bcp47)

    # Fallback for 3-letter codes without a specified default
    if len(code) == 3:
        for entry in _matrix:
            if entry[2] == code:
                return entry[4]

    # Fallback for 2-letter codes without a specified default
    if len(code) == 2:
        for entry in _matrix:
            if entry[1] == code:
                return entry[4]

    return None
